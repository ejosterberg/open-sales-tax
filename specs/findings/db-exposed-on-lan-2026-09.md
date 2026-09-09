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

## Verification (2026-09-09)

| Check | Result |
|---|---|
| `docker port open-sales-tax-postgres-1` | `127.0.0.1:5432` only (IPv6 listener gone too) |
| `ss -ltn` on the host | `LISTEN 127.0.0.1:5432` — no longer `0.0.0.0` |
| TCP connect to `10.32.161.126:5432` from a workstation | **ConnectionRefusedError** |
| TCP connect to `10.32.161.126:8080` from a workstation (control) | reachable — confirms the refusal above is the bind, not a network fault |
| Old password, through the host port mapping | **`password authentication failed`** |
| No password, through the host port mapping | **`no password supplied`** |
| New password, through the host port mapping | succeeds |
| `ssh -L 5432:localhost:5432` tunnel | reachable — documented replacement path works |
| Live API probes (85629 AZ, 86401 AZ, 72396 AR, 55401 MN, 10001 NY) | 8.100 / 8.600 / 9.625 / 9.025 / 8.875 — all correct |
| Both containers | `healthy` |

**One nuance worth recording, because it produced a false negative.** The first
attempt to prove the old password was dead ran `psql -h 127.0.0.1` *inside* the
postgres container and got `1` back — appearing to show the rotation had not
taken. It had. The official Postgres image ships a `pg_hba.conf` whose first
rules are:

```
local   all   all                     trust
host    all   all   127.0.0.1/32      trust
host    all   all   ::1/128           trust
host    all   all   all               scram-sha-256
```

so a connection to the container's *own* loopback is trust-authenticated and any
password — or none — is accepted. Connections arriving through the Docker port
mapping are source-NAT'd to the bridge gateway, not `127.0.0.1`, so they fall
through to the `scram-sha-256` rule. Re-testing through the host mapping (a
throwaway `--network host` client container) gave the correct results above.

The `trust` rules are stock and were left alone: exploiting them requires shell
inside the database container, at which point the password is not the control
doing the work.

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

1. **Fleet sweep — done 2026-09-09. Both exposed Redis instances are now closed.**

   25 hosts were checked for database/cache ports bound to all interfaces.
   **Correction to the first pass:** it listed only *running* containers, which
   missed dormant mappings. Re-swept with `docker ps -a`.

   | Host | Container | Port | Status |
   |---|---|---|---|
   | `opensalestax-01` | `open-sales-tax-postgres-1` | 5432 | ✅ fixed (loopback + password rotated) |
   | `magento-demo` | `magento-redis-1` | 6379 | ✅ **fixed 2026-09-09** — was **unauthenticated** |
   | pmvm2 CT 104 | `resgrid-redis-1` | 6379 | ✅ **fixed 2026-09-09** — had auth, but a weak literal password |
   | pmvm2 CT 104 | `resgrid-db-1` | 5432 | ✅ **fixed 2026-09-09** — dormant mapping, missed by the first sweep |
   | `bagisto-test` | `bagisto-db` | 3306 | ⚠️ still open (MariaDB) |
   | `magento-demo` | `magento-db-1` | 3306 | ⚠️ still open (MariaDB) |
   | `magento-demo` | `magento-rabbitmq-1` | 5672, 15672 | ⚠️ still open |
   | `magento-demo` | `magento-opensearch-1` | 9200, 9300 | ⚠️ still open |

   The two Redis instances were the priority and are done. `magento-redis-1` had
   **no authentication at all** (`CONFIG GET requirepass` returned empty);
   `resgrid-redis-1` did require a password, but a weak literal one hardcoded in
   its compose `command:` line, so the open port made it brute-forceable. Both
   are now `127.0.0.1` only, verified refused from a workstation.

   Neither application used the host mapping: Magento connects to `redis:6379`
   (`app/etc/env.php`) and Resgrid to `172.16.193.56:6379`, both over their
   compose networks. Magento was re-verified working afterward (see below).

   The remaining rows are MariaDB/RabbitMQ/OpenSearch on test and demo hosts.
   OpenSearch is worth a look — dev images commonly ship with the security
   plugin disabled, which would make 9200 unauthenticated.

2. **`8080` is also published on `0.0.0.0`** on this host. That one is
   intentional — it is how the reverse proxy / tunnel reaches the API — but it
   means the API is directly reachable on the LAN, bypassing Cloudflare and its
   rate limiting. Worth deciding whether it should be bound to the proxy's
   interface instead.
3. **Consider a deployment-manifest lint** in the quality gate. A check that
   fails on any `ports:` entry lacking an explicit interface, and on any
   password literal in a compose file, would have caught this the day it was
   written.

## Addendum — Redis remediation, 2026-09-09

### magento-demo (VM 914 on pmvm2)

`compose.yaml` service `redis` (image `valkey/valkey:8.1-alpine`) bound to
`127.0.0.1:6379:6379`. The commented-out alternative `redis:7.2-alpine` block
in the same file was bound too, so uncommenting it cannot silently reintroduce
the hole.

Recreating the container emptied the cache — this Valkey has no volume, so its
data was always ephemeral. Magento repopulated it immediately.

**Verified working after the change:**

| Check | Result |
|---|---|
| Home page | HTTP 200, **30674 bytes — byte-identical size to the pre-change baseline**, title "Home page", same 78 content markers |
| `/customer/account/login/` | HTTP 200, title "Customer Login" |
| `/customer/account/create/` | HTTP 200, title "Create New Customer Account" |
| `/search/term/popular/` | HTTP 200, title "Popular Search Terms" |
| Redis in use again | 93 + 8 + 3 keys across db0/db1/db2, 1228 commands processed |
| Sessions in Redis | `db2 DBSIZE` = 2 — session storage working |
| `10.32.161.183:6379` from a workstation | **refused** |
| `10.32.161.183:443` (control) | still reachable |

The store has no sample catalog — the home page carries only static asset
links. That is the install's pre-existing state, not a regression; the dynamic
routes above are the meaningful functional test.

### pmvm2 CT 104 (Resgrid) — Redis closed, but the application was already down

`docker-compose.yml` service `redis` bound to `127.0.0.1:6379:6379`; the
container's static IP `172.16.193.56` and its persisted data survived the
recreate. The dormant `db` mapping was bound to loopback in the same pass.

**Resgrid itself has been broken since before this work and was not fixed here:**

- `resgrid-db-1` **exited 2026-05-19 with code 137** (SIGKILL; `OOMKilled=false`,
  so killed from outside — that date is the Proxmox move window). Its compose
  service has **no `restart:` policy at all** (`RestartPolicy=no`), so nothing
  ever brought it back. Down ~3.7 months.
- `resgrid-caddy-1` crash-loops on a Caddyfile error, independent of the above:
  `duplicate site address not allowed: 'http://10.32.161.207'`.
- `web`, `api`, `worker`, `events` restart every few minutes because they cannot
  reach the database.

Container states were captured before and after the Redis change and are
identical apart from Redis itself. **This outage predates and is unrelated to
the port binding.** Chipped separately.

Note the `restart: no` on `resgrid-db-1` is the same failure family Eric
documented for the OpenSalesTax stack in
`prod-outage-dockerd-oom-2026-07.md`: a container killed hard by something
outside Docker, and a restart policy that declines to bring it back, leaving the
deployment silently down until a human notices. It went unnoticed for ~3.7
months here.
