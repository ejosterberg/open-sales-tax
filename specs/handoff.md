# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

**v0.55.4 is the latest release (MO Jackson County KCZD fold-in).**
Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax)
and prod API at the Cloudflare-fronted public URL
[api.opensalestax.org](https://api.opensalestax.org/v1/docs).
All 52 jurisdictions tier-1. The SST loader/lookup engine matches
every published DOR rate within 0.05% across **420 sampled
ZIP+4s** on the live engine (every US jurisdiction covered).

**iter-63 (CA reconciliation + CI restored 2026-05-09 → 2026-05-10):**
A CA combined-rate audit against the CDTFA published table found 18
of 50 cities drifted; applied paired county+city corrections so all
50 now match exactly. Examples: Lancaster/Palmdale 11.250%,
Hayward 10.750%, LA 9.750%, Modesto 8.875%. Verified live on prod
post-deploy.

A separate CI fire was put out: the CA loader integration tests
(`test_load_california_without_a_file` and
`test_california_idempotent_load`) had been computing
`expected_rates = 1 + len(city-touched-counties) + len(CA_CITIES)`,
but the CA module's `parse_rates` actually emits one county RateRow
per `CA_COUNTY_RATE_PCT` entry (currently 55), not just for those
touched by cities (currently 20). CI was red for 7 commits straight
between v0.55.2 and the 4-CDTFA-pin commit. Fix in
`81a2488` switched the math to `1 + len(CA_COUNTY_RATE_PCT) +
len(CA_CITIES)` (currently 1+55+50 = 106). CI green again.

**iter-63 audit pin batches** added 11 new live-grid entries (407 →
420): MN Rochester, GA Savannah/Macon/Athens, IN Fort Wayne/
Evansville, MI Grand Rapids, NJ Jersey City, WV Morgantown/
Parkersburg/Wheeling. All cross-checked against the state DOR
publications before pinning. Other probes turned up real
discrepancies needing follow-up: WI Milwaukee city missing the 2%
Act 12 city tax, plus several WI counties (Eau Claire, Rock,
Columbia) returning state-only despite having adopted the 0.5%
county tax; SD Sioux Falls/Rapid City rate-finder discrepancy;
ND Fargo/Bismarck rate drift; UT SLC and AR Little Rock both
suspect.

**v0.54.1 closed a real security hole**: slowapi was registered but
`SlowAPIMiddleware` was never added, so the configured per-IP
rate limit was inert across every prior release. Verified
empirically against the public engine before the fix (80 rapid
POSTs all 200ed). Same release added a `SecurityHeadersMiddleware`
(HSTS / nosniff / X-Frame-Options DENY / Referrer-Policy /
Permissions-Policy) and the inaugural security audit baseline at
`specs/security/audit-2026-05-04.md`. SonarQube re-scan at v0.54.0
came back A across all four ratings, zero security findings; 308
code smells (mostly S1192 string-dup in data tables) flagged as
quality follow-up.

**Alaska is no longer a no-tax state** as of v0.49 — 42 verified
municipalities + 2 borough-wide rates (KPB 3%, KGB 2.5%) ship via
ARSSTC data (`src/opensalestax/states/alaska.py`). Anchorage and
Fairbanks correctly return 0% (in-state retail); the long tail of
small AK cities and seasonal rates remain deferred and documented
in `ak_data.py`. Decision 07 (WY multi-row counties) was closed
in iter 43 -- WY rates verified correct against SalesTaxHandbook.

**Lookup-engine changes are fragile.** v0.53 widened the
strict-lookup typez fallback, which regressed OK cross-county +4
lookups (Edmond 73034-1234, Tulsa 74008-1234). v0.53.1 reverted.
Lesson: ALWAYS run the full live DOR grid (`pytest -m liveapi`,
~4 min) after any lookup-engine change, not just the targeted
tests. Decision 10 captures the synthetic-+4 limitation (Casper
WY 82601-0001 under-collects by 1%) for a more careful future
fix.

**Pre-commit checklist (DON'T forget either gate):**

```bash
poetry run ruff check src tests        # lint
poetry run ruff format --check         # FORMAT -- separate gate, easy to skip
poetry run mypy src/                   # type
poetry run pytest tests/unit -q        # unit tests
```

Iter 57 shipped a CI-red commit (1e4a2ba) by running `ruff check`
locally but skipping `ruff format --check` -- the new test rows
fit on one line each but ruff format wanted line-wrap and CI
caught it. **Also check `gh run list --workflow=ci.yml --limit 3`
after every push** -- waiting for the GitHub email is too slow.

**Dedup logic stabilized in v0.43-v0.48** after a deep TN bug
hunt that found systemic issues:
- v0.43: TN code-63 county-equivalent overlays skipped at parse
- v0.44: Cross-county IMPROVE Act dedup (one district per ZIP)
- v0.45: Strict-lookup type-z fallback now applies the loose dedup
- v0.46: "Most rows for THIS ZIP" beats "has-typez" tiebreaker
- v0.47: Lone type-4-only district included as county-wide overlay
- v0.48: 20-row threshold filters stray district bindings

**VT Local Option Sales Tax now collected** (v0.40) via three
parser fixes: SST 'A' (address-level) record support, UTF-8 BOM
stripping on .csv files, blank rate-column tolerance. Burlington
05401 + 27 other VT LOST municipalities now correctly return 7%
combined.

**Pre-built data dumps now ship with every release** (CI workflow
`.github/workflows/build-data-dump.yml`). New users install via
`opensalestax data restore` instead of the 50-minute manual
`data fetch` + `data load` workflow. The manual path remains for
users who want fresher-than-tag DOR data (`Refresh from source`
section in README).

**Multi-agent worktree pattern is the cadence.** When a /loop iter
has multiple independent tracks (e.g. data work + bug fix + CI
infra), spawn 3-6 sub-agents with `Agent({isolation: "worktree"})`,
give each a self-contained brief stating what they CAN'T touch
to avoid file conflicts, then merge their branches. Iter 8
shipped 3 agents in parallel (~1900 lines, 1 hour wall-clock).

**Deploy gotchas:**

- **Parser changes** require a full SST reload (`docker compose
  exec api python -m opensalestax.cli.main data load --state XX
  --version YYYYQQqMMMDD`) — rebuilding the container isn't
  enough because boundary rows are baked into the DB at load
  time.
- **TN data** ships rates and boundaries in different version
  labels: `TNR2025Q1MAR07` for rates, `TNB2026Q2FEB23` for
  boundaries. Use the `--boundary-version` CLI flag to load
  both: `data load --state TN --version 2025Q1MAR07
  --boundary-version 2026Q2FEB23`.
- **ND data** has the same split: `NDR2026Q2FEB11` for rates,
  `NDB2026Q2FEB19` for boundaries. Without `--boundary-version`,
  ND loads with 0 boundaries -- locality lookups fall back to
  state-only. Iter-59 hit this; the fix is `data load --state ND
  --version 2026Q2FEB11 --boundary-version 2026Q2FEB19`.
- **Reloading SST data on top of v0.54.x is dangerous if you
  haven't refreshed since 2026-05-04.** Iter-59 surfaced two
  related issues that compound:
  - `c512354` (2026-05-05) added type-'A' (address-level) boundary
    record support. Files like KSB are 84% 'A' records, so a fresh
    parse adds large numbers of boundaries that the prior parser
    silently dropped.
  - For KS, the new bindings include code-63 CID/TDD rows which
    are special-purpose districts that should NOT apply at the ZIP
    level. Pre-fix this added ~6% to Lawrence/Salina/Wichita on
    general retail. Iter-59 fixed via the same per-state opt-out
    TN already used (`jurisdiction_types["63"] = None`).
  - **Lesson:** every time a state without an explicit per-state
    code-63 entry gets reloaded, audit a representative city
    afterwards. ND/AR were spot-clean here; KS was not.
- ~~**UT (and likely WA/large 'A'-record states) reloads OOM.**~~
  **Resolved 2026-05-08 (commit `fa21b06`).** The boundary loop now
  bulk-inserts via Core in batches of 5,000 instead of `session.add()`
  per row. UT reload (1.5M boundaries) and WA reload (1.2M boundaries)
  both complete cleanly post-fix. The SQL-rename workaround is no
  longer needed for placename pushes -- the natural reload path is
  back. Keeping the rename script in `~/.claude/`-adjacent scratch in
  case future scale exceeds the new headroom.

## Where the iter-loop is currently focused

Three parallel tracks:

1. **Probe-and-fix** — pick a batch of cities across diverse
   states, compare returned rates to published DOR rates, drill
   into outliers. The TN bug hunt (v0.43-v0.44) and GA Roswell
   discovery (v0.46-v0.48) were both born from probe sweeps.
2. **DOR-validation grid expansion** — add ZIP+4 entries to
   `tests/integration/test_sst_dor_validation.py` as fixes ship.
   312 entries as of iter 31; targeting steady growth.
3. **Friendly authority names** — for any state where the API
   still returns `XX-city-NNNNN` placeholders, build
   `src/opensalestax/states/<state>_names.py` with ZIP-probe-
   verified mappings (FIPS Place codes are NOT 1:1 with SST
   jurisdiction codes — empirical verification beats public
   lookup). Already done: TN, OH, GA, KS, NE, WA, OK, NC, WI
   county, AR, IA, ND, SD, UT, WV, VT (13 entries), WY (1).

Open follow-ups (decision docs):

- **Decision 04 / 05** — CO home-rule cities + LA parishes need
  `SubJurisdiction` Protocol abstraction. Big architectural work.
- **Decision 07** — WY multi-row county taxes need empirical
  jurisdiction-code capture and re-encoding.
- AK boroughs missing entirely; would need a new data source.
- NJ UEZ + Salem County reduced rates intentionally deferred (per
  `new_jersey.py` docstring) until per-seller exemption modeling
  lands.

## What to read first

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what's done, what's next (latest
   release status + feature ladder + v0.6 priorities)
3. `specs/decisions/` — three locked-in decisions (language,
   license, database)
4. `specs/phase-1-foundation/acceptance-walkthrough.md` — honest
   done/deferred per Phase 1 criterion (historical context)

5–10 minutes; saves you from re-deriving anything.

## ⚡ Active session kickoff (if present)

If `specs/NEXT-SESSION-KICKOFF.md` exists, read and execute it
before anything else. Eric reset a session deliberately and that
file contains the immediate next steps.

## If you're spawning state-research agents (Phase 6+)

Eric's directive from 2026-05-03: engage **multiple agents in
parallel**, each researching and implementing one state, with
references documented as we go. The orchestration is documented
in three companion files:

- **`specs/agent-briefs/per-state-research-brief.md`** — the
  canonical instructions for ONE agent assigned to ONE state.
  Spawn each per-state agent with this file as their primary
  brief.
- **`specs/agent-briefs/multi-agent-coordination.md`** — branch
  naming (`feat/state-XX`), worktree strategy, conflict-surface
  files, per-batch checklist for the orchestrator, suggested
  Phase 6/7/8 batching.
- **`specs/research/references.md`** — every external source
  consulted so far, organized by state. Per-state agents MUST
  append their sources here.

## v0.49+ candidate priorities (rough order)

The recent v0.43-v0.48 dedup-stabilization sprint closed all the
known city/county/district lookup bugs. Diminishing returns on
further probing without new data. Bigger-bite candidates:

1. **`SubJurisdiction` Protocol abstraction** (decisions 04 + 05)
   -- unblocks CO home-rule, LA parishes, AL ~700 home-rule cities,
   HI per-county GET surcharges, NM per-county GRT add-ons, NJ
   UEZ/Salem reduced rates. The single biggest architectural
   commitment left in v1.
2. **WY multi-row county tax encoding** (decision 07) -- audit
   the WY SST jurisdiction-code semantics empirically and re-
   encode so Cheyenne / Casper return the published WY DOR rates
   instead of sometimes 1% off.
3. **PostGIS address-level resolution** -- replaces the loose-
   lookup dedup heuristics with actual point-in-polygon precision.
4. **CDTFA loader** for California's ~1,700 district rates -- the
   first significant non-SST data ingestion at scale (CA is
   currently top-50-cities only via `ca_data.py`).
5. **AK boroughs** -- new data source needed (SST doesn't cover
   AK; AK DOR doesn't publish a single rates file). Currently
   every AK ZIP returns 0%.
6. **2027 holiday data** for TX, FL, MA, MD once 2027 dates are
   published.
7. **Client SDKs** (Python, JS/TS, PHP for SC Books integration).
8. **More friendly placenames** for the ~6,000 remaining
   `XX-city-NNNNN` placeholders. Pure cosmetic; rate is unaffected.

## Standing rules (mirror Eric's other projects)

- Standing permission to commit directly to `main`.
- **Push allowed without per-deploy approval** (Eric granted in
  the v0.1 ship-it conversation 2026-05-03).
- No AI co-author trailers in commits.
- **DCO sign-off (`-s`) is required on every commit**, including
  Claude's. CI enforces this on every PR.
- Run the test suite before declaring "done" (`poetry run pytest -q`).
- Run SonarQube scan after each major feature batch
  (~once per section). Token in `~/.claude/sonarqube-playbook.md`;
  scanner CLI lives at
  `/c/Users/ejosterberg/Documents/GITprojects/TicketsCADFixes/sonar-scanner-temp/`.
- Append, don't edit, security audits.

## Tooling notes

- Python 3.11.15 installed via `uv python install 3.11`
- Poetry 2.3.4 installed via `uv tool install poetry`
- Project venv lives in
  `~/AppData/Local/.../pypoetry/Cache/virtualenvs/opensalestax-DTELG93k-py3.11`
- Local Docker not available on Eric's box (CI tests both DBs)
- `gh` token has `gist, read:org, repo, workflow` scopes

## What you do NOT do

- ❌ Re-derive Phase 1 architecture from scratch — read the specs.
- ❌ Add commercial / paid data dependencies (Avalara, TaxJar
  feeds, etc.). Constitution §3.
- ❌ Reverse-engineer commercial sales-tax APIs to derive
  algorithms or schemas. Constitution §2.
- ❌ Skip the disclaimer in any new endpoint. Constitution §13.
- ❌ Promise that v0.1 supports CA, TX, NY, etc. — those are
  Phase 2+. Communicate honestly.
- ❌ Push to GitHub without DCO sign-off (CI will fail and
  embarrass us).
- ❌ Touch `specs/phase-1-foundation/spec.md` after the v0.1.0
  tag — historical record. Add a `changes.md` if implementation
  diverged.

## Where to find things on disk

- Repo root: `C:\Users\ejosterberg\Documents\GITprojects\sales_tax_api_service\`
  (note: local directory name still `sales_tax_api_service`,
  GitHub repo is `open-sales-tax`)
- Settings global: `~/.claude/CLAUDE.md`
- SonarQube playbook: `~/.claude/sonarqube-playbook.md`
- Spec-kit playbook: `~/.claude/spec-kit-playbook.md`

## When you finish

Update `current-state.md` to reflect what shipped. If a phase
completes, mark it ✅ and bump the "Status:" line. Update this
`handoff.md` to point the next session at the next concrete piece
of work. If you discovered something Eric should know but didn't
build, add it to a "Deferred items" section in the next handoff.
