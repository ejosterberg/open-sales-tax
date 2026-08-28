# Finding: asyncmy SQL-injection (PYSEC-2026-286) — Critical, no upstream fix

**Opened:** 2026-07-04 (from pip-audit during the daily state-tax audit gate)
**Status:** **RESOLVED 2026-08-27** — fixed upstream in **asyncmy 0.2.12**;
constraint bumped to `^0.2.12` (lock resolves 0.2.14). Awaiting Eric's review
on branch `deps/asyncmy-fix-0.2.12`.
**Severity:** Critical (CVSS 9.8)

## Resolution 2026-08-27 — upstream fix shipped

asyncmy **0.2.12** (released 2026-08-06) fixes this. The upstream changelog
names the CVE directly:

> Security: remove unsafe `escape_dict` — dict keys could reach SQL
> unescaped (CVE-2025-65896). (#134, #135, thanks @Cycloctane)

Upstream issue [#134](https://github.com/long2ice/asyncmy/issues/134) — the
report this advisory came from — was closed 2026-08-06, the same day 0.2.12
published. Three independent signals agree:

| Signal | Result |
|---|---|
| Upstream CHANGELOG (authoritative) | 0.2.12 removes `escape_dict`, cites CVE-2025-65896 |
| OSV `PYSEC-2026-286` | range ends `last_affected: 0.2.11`; a version query for 0.2.14 returns **0 vulns** |
| `pip-audit` (dev venv, mariadb extra installed) | asyncmy row **gone** — no longer reported |

Note on OSV: the record carries **`last_affected: 0.2.11`, not a `fixed`
event**, and has not been re-modified since 2026-07-01 — when 0.2.11 *was*
the newest release. So OSV falling silent on 0.2.12+ is a range artifact and
is **not on its own** proof of a fix. The upstream changelog naming the CVE
is what makes this conclusive; OSV and pip-audit corroborate.

**Change applied:** `asyncmy = {version = "^0.2.12", optional = true}` — the
floor is the first fixed release; `poetry lock` resolves 0.2.14 (2026-08-12).

**Review risk to weigh before merging:** 0.2.12 is not a narrow security
patch. It bundles a large performance rewrite (buffered packet reading,
C-level bulk row parsing, pointer-based protocol reads, direct cell decoding
via the CPython C-API) plus several protocol fixes, and 0.2.13 adds
server-side prepared statements. The fix itself is an **API removal**
(`escape_dict` deleted, not merely corrected). This repo is unaffected by
that removal — there are zero direct `asyncmy` imports and no `escape_dict`
references in `src/` or `tests/`; every mention is a DSN string. But a
MariaDB self-hoster calling `escape_dict` directly would break, and the
rewrite is broad enough that the MariaDB path deserves a real smoke test
before this is advertised as supported. There is still no MariaDB test
infrastructure in-repo, so this bump is **verified by the Python-side gate
only, not against a live MariaDB server.**

The optional-extra structure is **retained** — it is install-surface
hygiene, not just a CVE workaround.

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

## Weekly watch log

- 2026-07-15: still unfixed (asyncmy latest 0.2.11; OSV PYSEC-2026-286 still `last_affected: 0.2.11`, no `fixed` event; pip-audit clean but asyncmy not resolved into the dev venv so it was not directly audited — PyPI+OSV are authoritative). aiomysql latest 0.3.2 (2025-10-22, maintained; its only advisory PYSEC-2026-1110 was fixed in 0.3.0, so 0.3.2 is unaffected).
- 2026-07-22: still unfixed (asyncmy latest 0.2.11, unchanged since 2026-01-15; OSV PYSEC-2026-286 still `last_affected: 0.2.11`, no `fixed` event; pip-audit reported no vulns but asyncmy is not installed in the dev venv so it was not directly audited — PyPI+OSV are authoritative). aiomysql latest 0.3.2 (2025-10-22, maintained; only advisory PYSEC-2026-1110 fixed in 0.3.0, so 0.3.2 is unaffected).
- 2026-07-31: still unfixed (asyncmy latest 0.2.11, unchanged since 2026-01-15; OSV PYSEC-2026-286 still `last_affected: 0.2.11`, no `fixed` event, advisory last modified 2026-07-01). asyncmy remains absent from the dev venv, so this week the locked 0.2.11 was audited directly (`pip-audit --no-deps -r` on a pinned `asyncmy==0.2.11`): PYSEC-2026-286 reported with an **empty Fix Versions column**, confirming no upstream patch. aiomysql latest 0.3.2 (2025-10-22, maintained; only advisory PYSEC-2026-1110 / GHSA-r397-ff8c-wv2g fixed in 0.3.0, so 0.3.2 is unaffected).
- 2026-08-27: **FIXED upstream.** asyncmy 0.2.12 (2026-08-06) removes the unsafe `escape_dict` and cites CVE-2025-65896 in its changelog; upstream issue #134 closed the same day. Latest is 0.2.14 (2026-08-12). OSV still shows no explicit `fixed` event (unchanged since 2026-07-01, `last_affected: 0.2.11`) but returns 0 vulns for 0.2.14; `pip-audit` no longer reports asyncmy at all. Bumped the constraint to `^0.2.12` on branch `deps/asyncmy-fix-0.2.12` (lock → 0.2.14); gate green (ruff, mypy, 1590 unit tests, pip-audit). Held for Eric's review — not pushed. aiomysql latest 0.3.2 (2025-10-22, unchanged; maintained; only advisory PYSEC-2026-1110 / GHSA-r397-ff8c-wv2g fixed in 0.3.0, so 0.3.2 is unaffected).
