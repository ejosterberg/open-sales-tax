# Production database published on 0.0.0.0 with username-as-password

**Found:** 2026-09-05, during the AZ deploy; remediated 2026-09-09
**Status:** FIXED — port bound to loopback, password rotated, credentials moved to a gitignored `.env`
**Severity:** high on the LAN; **not** internet-exposed

## What was wrong

`docker-compose.yml` published the Postgres container's port to every interface:

```yaml
  postgres:
    environment:
      POSTGRES_USER: opensalestax
      POSTGRES_PASSWORD: opensalestax     # password == username
      POSTGRES_DB: opensalestax
    ports:
      - "5432:5432"                        # 0.0.0.0, not loopback
```

Confirmed on the production host (`opensalestax-01`, VM 906 on pmvm2,
10.32.161.126):

```
$ docker port open-sales-tax-postgres-1
5432/tcp -> 0.0.0.0:5432
5432/tcp -> [::]:5432

$ ss -ltn
LISTEN  0  4096  0.0.0.0:5432  0.0.0.0:*
LISTEN  0  4096     [::]:5432     [::]:*
```

So **any host on `10.32.161.0/24` could connect to the production sales-tax
database** with credentials that are guessable on the first try, as an account
that owns the database and can `CREATE`/`DROP` databases.

`mariadb` had the same shape (`3306:3306`, `MARIADB_PASSWORD: opensalestax`,
`MARIADB_ROOT_PASSWORD: rootpw`), though that service is profile-gated and was
not running.

## Not theoretical

This is exactly how the 2026-09-05 session verified the `data purge` regression
test — from a Windows workstation, with no credential beyond what is printed in
the repo:

```
postgresql+asyncpg://opensalestax:opensalestax@10.32.161.126:5432/ost_purge_selftest
```

That session created and dropped a database on the production server from
another machine. It was benign and deliberate; nothing stopped it from being
neither.

## Scope — LAN, not the internet

The host sits on the flat private LAN. `api.opensalestax.org` is
Cloudflare-fronted and only the HTTP service is reachable from outside, so
**5432 was not exposed to the internet**. The realistic threat is lateral: Eric's
LAN is currently one flat `/24` shared by workstations, IoT devices, throwaway
test VMs, and a Docker host that also terminates a public VPS tunnel. Segmenting
that is queued as `~/.claude/future-tasks.md` #4, and its stated motivation is
precisely "a compromised or buggy test container shouldn't be able to pivot."
This was a live instance of that risk.

## Fix

**1. Loopback binding.** The `api` service reaches Postgres over the compose
network as `postgres:5432` and never used the host mapping. The mapping exists
only so host-side tools (pytest with `OPENSALESTAX_DATABASE_URL`, `psql`, a GUI
client) can reach the database during local development, and `127.0.0.1` serves
that fully:

```yaml
    ports:
      - "127.0.0.1:5432:5432"
```

Same for `mariadb` (`127.0.0.1:3306:3306`).

**2. Password rotated and moved out of the compose file.** Passwords are now
`${POSTGRES_PASSWORD:-opensalestax}` etc. The literal default is retained purely
for local development, where it is safe *because* the port is loopback-bound. The
production host sets a real 32-character secret in its gitignored `.env`, and the
account password was changed inside the database with `ALTER USER`.

Per the standing credential rule, the secret's **location** is recorded in
`~/.claude/environment-inventory.md`; the value appears nowhere but the host file.

**3. Remote access is now a tunnel.** To reach a deployment's database from a
workstation:

```bash
ssh -L 5432:localhost:5432 opensalestax-01
```

This is strictly better than the old path — it is authenticated, encrypted, and
leaves an SSH audit trail.

## Verification

| Check | Result |
|---|---|
| `docker port open-sales-tax-postgres-1` | `127.0.0.1:5432` only |
| Connect to `10.32.161.126:5432` from a workstation | **refused** |
| Connect over an SSH tunnel with the new password | succeeds |
| Connect with the old password | **rejected** |
| Live API health + rate probes | correct (see below) |

## Why it survived this long

The compose file has read the same way since the project was scaffolded. A
port mapping is the kind of line that gets written once, during "make it work
locally," and then rides along into production without ever being re-read — the
production stack and the development stack share one file, and the default is
whatever was convenient on day one.

Nothing in the quality pipeline looks at deployment manifests. Tests, ruff, mypy
and SonarQube all analyze application code; none of them inspects
`docker-compose.yml`. SonarQube reports 0 BLOCKER/CRITICAL for this project and
has never had an opinion about a database published to the world with a
one-word password.

## Follow-ups

1. **Fleet sweep — done 2026-09-09; three other hosts are exposed.** 24 hosts
   were checked for database/cache ports published on `0.0.0.0`:

   | Host | Container | Port | Notes |
   |---|---|---|---|
   | `bagisto-test` | `bagisto-db` | 3306 | MariaDB, test host |
   | `magento-demo` | `magento-db-1` | 3306 | MariaDB, demo host |
   | `magento-demo` | `magento-redis-1` | 6379 | **Redis — no auth by default** |
   | pmvm2 CT 104 | `resgrid-redis-1` | 6379 | **Redis — no auth by default**; Resgrid is a dispatch platform |

   **The Redis instances are the worrying ones.** Redis ships with no
   authentication, so an exposed instance is not merely readable — `CONFIG SET
   dir` + `dbfilename` is a well-known path to writing arbitrary files (cron
   entries, `authorized_keys`) as the Redis user. Those two deserve attention
   ahead of the MariaDB ones.

   Clean (no exposed database ports): `scdock0` (the public VPS),
   `eost-docker0`, `sccllc-docker0`, `gdl-docker0`, `erpnext-test`,
   `invoice-ninja-test`, `odoo-test`, `customer-capture`, `opencart-test`,
   `drupal-commerce-test`, `wp-woocommerce-test`, `saleor-demo`, `medusa-test`,
   `vendure-demo`, `ticketscad-docker`, `rscop`, `rscop-dev`, `legiscan-01`,
   `scbooks`, `opencallbook`, `msp-arrivals`, pmvm2 CT 100, CT 102.

   These were **not** changed here — they belong to other projects and touching
   them from a sales-tax session would be out of scope. Chipped separately.
2. **`8080` is also published on `0.0.0.0`** on this host. That one is
   intentional — it is how the reverse proxy / tunnel reaches the API — but it
   means the API is directly reachable on the LAN, bypassing Cloudflare and its
   rate limiting. Worth deciding whether it should be bound to the proxy's
   interface instead.
3. **Consider a deployment-manifest lint** in the quality gate. A check that
   fails on any `ports:` entry lacking an explicit interface, and on any
   password literal in a compose file, would have caught this the day it was
   written.
