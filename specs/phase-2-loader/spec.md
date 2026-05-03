# Phase 2 — Loader + auth + first non-SST state

> What v0.2 ships. Drafted 2026-05-03 immediately after the
> v0.1.0 tag.

**Scope:** the three priorities flagged in the Phase 1 acceptance
walkthrough's "what v0.2 should ship next":

1. **Data-load CLI** -- the missing piece between the v0.1
   fetcher and the v0.1 API
2. **API-key auth mode** -- already plumbed in settings
3. **First non-SST tier-1 state** -- California recommended

## Goal

A self-hoster runs:

```bash
docker compose run --rm api opensalestax data fetch --state MN --version 2026Q2FEB18
docker compose run --rm api opensalestax data load  --state MN --version 2026Q2FEB18
curl 'http://localhost:8080/v1/rates?zip5=55401'
# -> returns Minnesota's 6.875% state rate plus any local additions
#    that match the ZIP -- without ever writing a line of SQL.
```

Same flow against any tier-1 or tier-2 SST state; California
becomes the first "manual implementation" example in the docs.

## Sections (mirrors Phase 1's cadence)

| Section | What | Status |
|---|---|---|
| A | Data loader + load/status/purge CLI subcommands | 📝 next |
| B | API-key auth: middleware, api_keys table, key-mgmt CLI | ⏭️ |
| C | California tier-1 module (CDTFA data; documented manually) | ⏭️ |
| D | Acceptance walkthrough + v0.2.0 release | ⏭️ |

This file is intentionally short. Each section gets its own
sub-spec when it starts (or just lives in the commit message if
the work is mechanical).

## In scope for Section A (this batch)

- `src/opensalestax/data/loader.py` -- functional core: take a
  state + cached file, return DB-ready rows
- `opensalestax data load --state <X> --version <Y>` -- CLI that
  pulls rows from the loader and inserts them via SQLAlchemy
- `opensalestax data status` -- show what's loaded per state
- `opensalestax data purge --state <X> --version <Y>` -- remove
  a specific data version
- `opensalestax data fetch --state <X> --version <Y>` -- shortcut
  that constructs the SST filename from state + version label
- Tests against the bundled MN + WI fixtures
- Docs update so README's quickstart shows the full flow

## Out of scope for Section A

- Idempotency edge cases beyond "drop the data version row first
  if it exists" -- v0.2.x can refine
- Scheduled / cron-based auto-refresh -- v0.3+
- Web UI for data management -- not on the roadmap

## Acceptance criteria for Section A

- [ ] `opensalestax data load --state MN --version 2026Q2FEB18`
      reads the cached file, parses via the MN module, inserts
      into the database, prints a summary
- [ ] Re-running the same command is idempotent (no duplicate
      rates / boundaries)
- [ ] `opensalestax data status` shows MN with the loaded
      version label and row counts
- [ ] After load, `GET /v1/rates?zip5=55401` returns Minnesota's
      state rate (the actual rate from the loaded SST file)
- [ ] `data purge --state MN --version 2026Q2FEB18` removes the
      data version + cascades the rates / boundaries
- [ ] All tier-2 states load via the same command (mechanical
      proof the generic SstStateModule pipeline works end-to-end)
- [ ] Tests cover the loader with both engines (PostgreSQL +
      MariaDB) in CI
- [ ] Updated `docs/quickstart.md` shows the full
      fetch -> load -> calculate flow
