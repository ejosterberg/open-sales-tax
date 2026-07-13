# Finding: asyncmy SQL-injection (PYSEC-2026-286) — Critical, no upstream fix

**Opened:** 2026-07-04 (from pip-audit during the daily state-tax audit gate)
**Status:** MITIGATED (asyncmy made an optional extra 2026-07-04) — still
watching weekly for an upstream fix; asyncmy remains unfixed at 0.2.11.
**Severity:** Critical (CVSS 9.8)

## Update 2026-07-04 — mitigation applied

Eric approved making `asyncmy` optional. Shipped on branch
`deps/pytest9-pip-audit-2026-07`:

- `asyncmy` moved to `{optional = true}` + a `[tool.poetry.extras]`
  `mariadb = ["asyncmy"]`. Default (PostgreSQL) installs no longer pull the
  Critical-CVE wheel; confirmed via `poetry install --sync --dry-run`
  ("Removing asyncmy"). MariaDB users opt in: `pip install "opensalestax[mariadb]"`.
- `db/session.py` gained `_require_dsn_driver()`: a `mysql+asyncmy://` DSN
  without the extra now fails fast with the exact install command instead of
  a bare `ModuleNotFoundError` on first connect. Covered by
  `tests/unit/test_db_session.py` (4 tests).
- README + `settings.py` DSN docstring updated with the extra.

**Weekly watch:** a scheduled task re-checks PyPI/OSV for (a) an asyncmy
release > 0.2.11 that fixes PYSEC-2026-286 and (b) any change in aiomysql's
advisory/maintenance status. When a fix ships, pin asyncmy to it. The
optional-extra structure stays regardless — it's good hygiene, not just a
CVE workaround.

## What

`pip-audit` reports **PYSEC-2026-286** against `asyncmy` 0.2.11:
"SQL injection via crafted dict keys." Affects **all published versions
(0.1.1 – 0.2.11)**. There is **no fixed version** on PyPI as of this
writing (0.2.11 is the latest release).

`asyncmy` is a **direct runtime dependency** in `[tool.poetry.dependencies]`
(pyproject.toml). It is the async MariaDB/MySQL driver SQLAlchemy loads
when the database DSN uses the `mysql+asyncmy://` scheme — part of the
project's dual-database design (`asyncpg` for PostgreSQL, `asyncmy` for
MariaDB; see `settings.py` DSN docstring and `data/restore.py`).

## Exposure assessment

- **Production (`opensalestax-01`) runs PostgreSQL** (`postgresql+asyncpg://`).
  `asyncmy` is never imported at runtime there — SQLAlchemy only loads a
  dialect driver when a DSN of that scheme is opened. Confirmed: there are
  **zero direct `import asyncmy` statements** anywhere in `src/` or `tests/`.
- **All DB access is through the SQLAlchemy ORM / Core with bound
  parameters** — the app does not pass user-controlled data as raw dict
  keys into the driver's low-level cursor API, which is the vector the CVE
  describes. So even a MariaDB self-hoster on the current codebase is not
  obviously reachable by this vector via normal app paths.
- **Residual risk:** the package still ships in the dependency closure of
  *every* `pip install opensalestax`, so PostgreSQL-only and self-hosting
  users pull a Critical-CVE wheel they never load. That is the real problem
  worth fixing, independent of direct exploitability.

## Options considered

| Option | Verdict |
|---|---|
| Bump `asyncmy` to a fixed version | **Not possible** — no fix published (0.2.11 is latest). |
| Drop `asyncmy` entirely | **No** — breaks the documented MariaDB self-host path. |
| Replace with `aiomysql` (`mysql+aiomysql://`) | Possible but larger: needs the MariaDB dialect re-tested; no MariaDB test infra in-repo today. Deferred. |
| **Make `asyncmy` an optional extra** (`opensalestax[mariadb]`) | **Recommended.** Removes the Critical wheel from the default/PostgreSQL install surface; MariaDB users opt in. Low code risk (no direct imports). |

## Recommended fix (prepared, NOT yet applied — needs sign-off)

Because it changes the **published install contract**, this is left for
Eric to approve (constitution: API-surface changes get sign-off).

```toml
# pyproject.toml — [tool.poetry.dependencies]
asyncmy = {version = "^0.2.10", optional = true}

# add:
[tool.poetry.extras]
mariadb = ["asyncmy"]
```

Then:
- `poetry lock && poetry install --extras mariadb` for dev (so the
  MariaDB-path unit tests still resolve).
- Update `settings.py` DSN docstring + README install notes: MariaDB
  users install `pip install "opensalestax[mariadb]"`.
- Keep watching PYSEC-2026-286 for an upstream patch; when one ships,
  pin `asyncmy` to it regardless of the optional/required decision.

## Why not suppressed

Not added to a pip-audit ignore list. The scheduled state-tax audit's
gate does **not** block on pre-existing dependency CVEs (only on new
SonarQube BLOCKER/CRITICAL), so this stays visible without wedging the
daily run. Suppressing a Critical would need explicit approval.
