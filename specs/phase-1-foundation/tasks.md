# Phase 1 — Tasks

> Ordered atomic checklist. Reads alongside `spec.md` (the WHAT)
> and `plan.md` (the HOW).

**Estimated total:** ~7 sessions of focused work.
**Drafted:** 2026-05-02.

Each task should fit a 15–60 minute focused work block. Cross items
off in commit messages (e.g., `chore(scaffold): tasks 01-03 done`).

## Task ordering rationale

The order is **scaffold → schema → state-module pattern → state
modules → API → ops** because each layer depends on the one before.
Skipping ahead causes rework. Don't reorder unless `plan.md` is
revising.

---

## Section A — Scaffolding (Session 1)

- [ ] **01. Initialize Poetry project**
  - `poetry init` with name `opensalestax`, Python `^3.11`
  - Add deps: `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]>=2.0`,
    `alembic`, `asyncpg`, `asyncmy`, `pydantic-settings`, `typer`,
    `slowapi`, `httpx`
  - Add dev deps: `pytest`, `pytest-asyncio`, `ruff`, `mypy`,
    `pre-commit`
  - Configure `[tool.ruff]` and `[tool.pytest.ini_options]` in
    `pyproject.toml`
  - Add `[project.scripts]` entry: `opensalestax = "opensalestax.cli.main:app"`

- [ ] **02. Create `src/opensalestax/` package skeleton**
  - `__init__.py` with `__version__ = "0.1.0a1"`
  - `__main__.py` enabling `python -m opensalestax`
  - Empty subpackages with `__init__.py` files: `api/`, `api/v1/`,
    `core/`, `db/`, `states/`, `data/`, `cli/`
  - Add SPDX header (`# SPDX-License-Identifier: Apache-2.0`) to
    every `.py` file

- [ ] **03. Create LICENSE, NOTICE, contributor docs**
  - `LICENSE` — Apache 2.0 full text + copyright line
    `Copyright 2026 Eric Osterberg and OpenSalesTax contributors`
  - `NOTICE` — empty stub with header comment explaining purpose
  - `CONTRIBUTING.md` — dev env setup, DCO instructions
    (`git commit -s`), per-state contributor pattern, link to
    constitution §2 (no reverse-engineering)
  - `MAINTAINERS.md` — Eric as initial maintainer; section for
    per-state maintainers (empty); decision-rule reference
  - `USERS.md` — empty deployer registry stub

- [ ] **04. Add SPDX/lint/format pre-commit config**
  - `.pre-commit-config.yaml` with ruff (lint + format), end-of-file
    fixer, trailing-whitespace fixer, mixed-line-ending fixer
  - Document `pre-commit install` in CONTRIBUTING.md

- [ ] **05. Configure CI on GitHub Actions**
  - `.github/workflows/ci.yml` — three jobs:
    1. **lint** — `ruff check` + `ruff format --check` + `mypy src/`
    2. **dco** — DCO sign-off check on all PR commits
    3. **test** — matrix `db: [postgres, mariadb]`, services for
       each, `pytest -v` against the engine
  - DCO check uses `tim-actions/dco@v1.1.0` or equivalent
  - Test job exports `OPENSALESTAX_DATABASE_URL` based on matrix

**Session 1 commit checkpoint:** working scaffold; `poetry install`
+ `pytest` + `ruff check` all succeed locally; CI yet to run
because no GitHub remote yet.

---

## Section B — Database layer (Session 2)

- [ ] **06. Settings module**
  - `src/opensalestax/settings.py` using `pydantic-settings`
  - Required: `DATABASE_URL`
  - Optional: `AUTH_MODE` (open|api_key, default open),
    `RATE_LIMIT_PER_MINUTE` (default 60), `LOG_LEVEL`
  - Reads from env vars with prefix `OPENSALESTAX_`

- [ ] **07. SQLAlchemy declarative models**
  - `src/opensalestax/db/models.py` matching the schema in
    `spec.md` §2 (post-portability fix)
  - Use `sqlalchemy.types.JSON`, not `JSONB`
  - Use portable types throughout
  - Define each model with `Mapped[]` annotations (SQLAlchemy 2.x style)

- [ ] **08. Async session factory**
  - `src/opensalestax/db/session.py`
  - Reads `settings.DATABASE_URL` and creates one `AsyncEngine`
  - Provides `get_session()` dependency for FastAPI
  - No engine-aware code beyond `create_async_engine(...)` call

- [ ] **09. Initialize Alembic + first migration**
  - `alembic init src/opensalestax/db/migrations/`
  - Configure `env.py` to use settings.DATABASE_URL + reflect models
  - Generate `0001_initial.py` covering all 6 tables
  - Test: `alembic upgrade head` works against both engines locally
    (run twice, once with each `OPENSALESTAX_DATABASE_URL`)

- [ ] **10. conftest.py with dual-engine fixture**
  - `tests/conftest.py` provides session-scoped engine fixture
    parameterized to current matrix engine
  - Tests use `async_session` fixture for ORM access
  - DB created/dropped per test session, not per test (perf)

**Session 2 commit checkpoint:** `alembic upgrade head` succeeds on
both engines; minimal `tests/test_smoke.py` exists and passes.

---

## Section C — Core engine + state-module pattern (Session 3)

- [ ] **11. State-module Protocol**
  - `src/opensalestax/states/protocol.py` defining `StateModule`
    Protocol per `plan.md`
  - Define `RateRow`, `BoundaryRow`, `TaxabilityRule`,
    `SpecialCase` dataclasses

- [ ] **12. State registry**
  - `src/opensalestax/states/__init__.py` provides
    `get_state_module(abbrev: str) -> StateModule | None`
  - Maintains internal map of registered modules

- [ ] **13. `no_tax` state module**
  - `src/opensalestax/states/no_tax.py`
  - Implements StateModule with `has_sales_tax = False`
  - Returns empty rates / boundaries / taxability
  - Used by AK, DE, MT, NH, OR (5 instances registered)
  - Test: `test_state_no_tax.py` covers all 5 states

- [ ] **14. Core lookup module**
  - `src/opensalestax/core/lookup.py`
  - `lookup_jurisdictions_by_zip(zip5, zip4=None) -> List[Jurisdiction]`
  - Pure DB query; no state-specific code

- [ ] **15. Core resolve + calculate modules**
  - `core/resolve.py` — given jurisdictions + effective date,
    return applicable rates
  - `core/calculate.py` — given rates + line items, return tax
    decomposition
  - `core/disclaimer.py` — constants + helper for the standard
    disclaimer string

**Session 3 commit checkpoint:** core engine compiles; no_tax
states work end-to-end; tests for the 5 no_tax states pass on
both engines.

---

## Section D — SST data ingestion (Session 4)

- [ ] **16. Document the SST file format** (research, not code)
  - Download a sample (e.g., MN current quarter rates ZIP +
    boundary ZIP) from SST
  - Inspect column headers, data types, encoding
  - Write `specs/research/sst-file-format.md` documenting:
    - Rates CSV columns + meaning
    - Boundary CSV/ZIP contents
    - Quirks discovered
  - Find SST conformance test fixtures (track down on streamlinedsalestax.org)
  - This is a documentation task, not a code task; ship the
    research doc before writing parsers

- [ ] **17. SST fetcher**
  - `src/opensalestax/data/sst.py` — `download_sst_file(state, version, kind)`
  - Validates filename pattern, downloads via httpx, caches under
    `~/.opensalestax/data/`

- [ ] **18. Generic SST parser scaffold**
  - `src/opensalestax/data/sst_parser.py`
  - Generic CSV/ZIP unpack; yields raw rows
  - State-specific normalization happens in each state module

**Session 4 commit checkpoint:** can download + unpack an SST
file; raw rows visible via a smoke test.

---

## Section E — Minnesota module (Session 5)

- [ ] **19. Minnesota module: parse_rates**
  - `src/opensalestax/states/minnesota.py`
  - Implements `StateModule.parse_rates` for MN's SST format
  - Yields `RateRow` instances

- [ ] **20. Minnesota module: parse_boundaries**
  - Same module, `parse_boundaries` for MN
  - ZIP+4-based per Phase 1 scope

- [ ] **21. Minnesota module: taxability + special cases**
  - `taxability_for("clothing", date)` returns
    `TaxabilityRule(is_taxable=False, ...)`
  - Other categories per MN DOR
  - `special_cases()` returns any MN quirks

- [ ] **22. Minnesota test fixtures**
  - `src/opensalestax/data/fixtures/mn/`
  - At least 10 known-good test cases per constitution §12
  - Real MN addresses + expected rate decomposition
  - `tests/unit/test_state_minnesota.py` exercises them

**Session 5 commit checkpoint:** MN module shipped; all MN tests
pass on both engines.

---

## Section F — Wisconsin module (Session 6, half session)

- [ ] **23. Wisconsin module** (mirrors MN; faster because pattern
      is established)
  - Parse rates + boundaries from WI SST format
  - `taxability_for("clothing", date)` returns
    `TaxabilityRule(is_taxable=True, ...)` (CONTRAST with MN)
  - 10+ test fixtures
  - `tests/unit/test_state_wisconsin.py` passes

**Session 6 (half) commit checkpoint:** WI module shipped; the
MN-vs-WI clothing-taxability contrast is demonstrated by tests.

---

## Section G — API surface (Session 6 second half)

- [ ] **24. FastAPI app factory**
  - `src/opensalestax/app.py` — `create_app()` returns configured
    FastAPI instance with v1 router mounted

- [ ] **25. /v1/health endpoint**
  - `api/v1/health.py` — returns version + DB connectivity status

- [ ] **26. /v1/states endpoint**
  - `api/v1/states.py` — lists 52 entries with coverage status

- [ ] **27. /v1/rates endpoint**
  - `api/v1/rates.py` — accepts zip5 (+ optional zip4)
  - Returns jurisdiction stack with rates

- [ ] **28. POST /v1/calculate endpoint**
  - `api/v1/calculate.py` — accepts address + line items
  - Returns full decomposition with disclaimer

- [ ] **29. API integration tests**
  - `tests/integration/test_api_*.py` covering all 4 endpoints
  - Use `httpx.AsyncClient(app=...)` pattern

**Session 6 commit checkpoint:** all 4 endpoints work; OpenAPI spec
auto-generated; integration tests pass on both engines.

---

## Section H — Auth + ops (Session 7)

- [ ] **30. Auth modes + rate limiting**
  - `slowapi` integration; respects `OPENSALESTAX_AUTH_MODE`
  - API key mode adds `api_keys` table + middleware

- [ ] **31. CLI entry point**
  - `cli/main.py` using Typer
  - Subcommands: `data fetch`, `data list-versions`,
    `data activate`
  - Wired up to package entry point (`opensalestax` command)

- [ ] **32. Dockerfile + docker-compose**
  - Multi-stage `Dockerfile` (builder + slim runtime)
  - `docker-compose.yml` with `postgres` and `mariadb` profiles
  - Document both profiles in README quickstart

- [ ] **33. Documentation pass**
  - Update `README.md` quickstart for both DB engines
  - `docs/quickstart.md`, `docs/api.md` (link to OpenAPI),
    `docs/state-modules.md` (per-state contributor entry point),
    `docs/data-refresh.md`, `docs/disclaimer.md`

- [ ] **34. Acceptance walkthrough**
  - Manually run through every checkbox in `spec.md`
    "Acceptance criteria"
  - Fix anything that fails
  - Update `current-state.md` to mark Phase 1 ✅ shipped

**Session 7 commit checkpoint:** all acceptance criteria pass;
ready to tag `v0.1.0`.

---

## Section I — Release (after acceptance)

- [ ] **35. Tag and release**
  - Update `__version__ = "0.1.0"` (drop the alpha)
  - Tag `v0.1.0` on GitHub
  - GitHub Release with notes summarizing what shipped
  - Build + push Docker image to GHCR with `:0.1.0` and `:latest`

- [ ] **36. Post-release**
  - Update `current-state.md` Phase 1 → ✅
  - Open `specs/phase-2-sst-rollout/spec.md`
  - Update `handoff.md` to point next session at Phase 2
  - Optional: Show HN / blog post / state-CPA-society outreach

---

## What "done" means for each task

A task is **done** when:
- Code is written and lints clean
- Tests for that task's scope pass on BOTH engines
- Pre-commit hooks pass
- Commit is signed off (`-s`)
- Any new public API has a docstring
- Any deviation from `plan.md` is noted in `changes.md`

A task is **NOT done** when:
- Tests pass only on PostgreSQL but fail on MariaDB (or vice versa)
- The DCO trailer is missing
- The work is "almost finished but I'll come back to it"

## Reordering rules

If a task needs to be reordered or split:

1. Update `tasks.md` to reflect the new order
2. Note the reason in `changes.md` (create if needed)
3. Re-link any downstream tasks that depended on the changed item

The whole point of this file is that a fresh Claude session can
drop in and execute. Keep it executable.
