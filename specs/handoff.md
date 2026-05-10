# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

**v0.55.4 is the latest release (MO Jackson County KCZD fold-in).**
Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax)
and prod API at the Cloudflare-fronted public URL
[api.opensalestax.org](https://api.opensalestax.org/v1/docs).
All 52 jurisdictions tier-1. The SST loader/lookup engine matches
every published DOR rate within 0.05% across **550 sampled
ZIP+4s** on the live engine (every US jurisdiction covered).
Untagged main is well ahead of v0.55.4 with **7 substantive bug
fixes** + **3 features** deployed since: CA reconciliation
(50 cities), WI structural rewrite, AK borough-stacks-with-city,
USPS PO-box ZCTA supplement (29 ZIPs), AL Madison Co Sp fold-in,
IA Johnson Co LOST friendly-name fix, plus wi_names.py
(31 cities), ID resort cities (12 cities), and **10 names
tables expanded** (WI / IA / WV / KS / OK / TN / SD / UT / WA /
ND adding 86+ friendly names) + a 143-entry pin growth -- next
release should bump significantly for these.

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

**iter-63 audit pin batches** added 15 new live-grid entries (407 →
424): MN Rochester, GA Savannah/Macon/Athens, IN Fort Wayne/
Evansville, MI Grand Rapids, NJ Jersey City, WV Morgantown/
Parkersburg/Wheeling, then 4 WI verification pins after the
structural fix landed. All cross-checked against the state DOR
publications before pinning. Other probes turned up real
discrepancies needing follow-up: SD Sioux Falls/Rapid City
rate-finder discrepancy (ended up being my outdated DOR estimate;
6.2% is correct); ND Fargo/Bismarck rate drift; UT SLC and AR
Little Rock both still suspect.

**iter-63 WI structural fix** -- WI module previously had a
hand-rolled `parse_boundaries` that emitted only state + county
bindings, dropped `4` (ZIP+4) records, did no ZIP5 range
expansion, and skipped the cross-border filter. Switched to
inheriting :class:`SstStateModule` (commit `133240c`). After
re-load on prod (`docker compose exec api python -m
opensalestax.cli.main data load --state WI --version
2026Q2FEB18`), the WI engine now picks up:

- Milwaukee City's 2% sales tax (WI Act 12, in the SST file
  since 2024-01-01 but unreachable because the boundary parser
  never linked ZIP -> city). Milwaukee 53202: 5.9% -> 7.9%.
- County overlays carried by `4` records: Eau Claire / Rock /
  Columbia / etc. previously returned state-only despite each
  county having adopted the 0.5% county tax. Janesville 53545,
  Eau Claire 54701, Portage 53901: 5.0% -> 5.5%.
- Boundary count for WI: ~50K -> ~528K.

Lesson: when a state module DOESN'T inherit `SstStateModule`,
audit the standalone parser for missing capabilities --
especially city / district binding emit. AL / FL / IL / etc. are
the next candidates worth checking.

**iter-64 audit pin batches** (424 -> 444 entries): TN Nashville
37203 (with IMPROVE Act transit), OK Broken Arrow, GA Columbus
(after rate-stack inspection corrected my outdated DOR estimates),
plus KY Bowling Green / KY Owensboro / GA Albany / GA Marietta /
AR Conway / NC Greensboro/Durham/Winston-Salem/Asheville /
NV Henderson/North Las Vegas / UT Provo / RI Warwick/Cranston /
SD Pierre / AR Hot Springs/Jonesboro.

**iter-64 wi_names.py** (commits `d4805d5` + `b1f2022`) -- new
20-entry friendly-name table for WI cities. Each code verified
two ways: probe the live API for a known-city ZIP, then
cross-check against the US Census FIPS Place code (state-FIPS +
place-FIPS scheme: Milwaukee FIPS Place 5553000 -> SST code
53000). Entries: Appleton / Eau Claire / Elkhorn / Fitchburg /
Grand Chute / Green Bay / Janesville / Kenosha / Madison /
Milwaukee / Neenah / New Berlin / Oak Creek / Oshkosh / Portage /
Racine / Stoughton / Sturgeon Bay / Waukesha / West Allis. After
the WI re-load on prod, all 20 cities surface with friendly names
instead of `WI-city-NNNNN` placeholders.

**iter-65/66 audit pin batches** (440 -> 463 entries): more
AL/MS/SC/CT/VA/HI/NM/MD/MA/KY/OR/MT cities pinned after live
probe verified each matched the published DOR rate. AL Auburn /
Florence / Prattville rates that initially looked like
discrepancies were confirmed as the AL-DOR-correct intentional
values per al_data.py docstring.

**iter-67 AK borough-stacks-with-city fix** (commit `01d7d65`,
deployed + re-loaded). The AK module's parse_boundaries
previously suppressed the borough binding for city ZIPs on the
mistaken assumption that "borough rates are NOT collected inside
city limits per ARSSTC." The actual KPB ordinance (KPB Code
5.18.430-440) and ARSSTC's tax-rate look-up both confirm the
borough sales tax IS collected throughout the borough including
inside city limits. Fix emits the borough binding for city ZIPs
too. Six AK ZIPs corrected on prod after the AK reload:

- Homer 99603:    4.85% -> 7.85% (KPB 3 + Homer 4.85)
- Kenai 99611:    3.00% -> 6.00% (KPB 3 + Kenai 3)
- Seldovia 99663: 6.50% -> 9.50%
- Seward 99664:   4.00% -> 7.00%
- Soldotna 99669: 3.00% -> 6.00%
- Ketchikan 99901: 5.50% -> 8.00% (KGB 2.5 + city 5.5)

**iter-68/69 USPS PO-box ZCTA supplement** (commits `f270314` +
`2416c1d`, deployed + ZCTA reloaded). Discovery: PO-box-only ZIPs
aren't in Census ZCTA (no physical delivery boundary) so the
ZCTA loader -- the sole source of state-level ZIP bindings for
self-seeded flat-rate states (MA / MD / CT) and a fallback for
SST flat-rate states -- silently dropped them. Result: any GET
/v1/calculate for a PO-box-only ZIP returned
combined_rate_pct=0. New `usps_po_box_zips.py` module supplies
hand-curated ZIP -> state mappings appended by
parse_zcta_state_rows. Currently 29 entries covering Springfield
/ Boston / Worcester (MA), Newark / Jersey City / Paterson /
Camden / Trenton (NJ), Providence (RI), Hartford / New Haven
(CT), Baltimore (MD). Scope intentionally narrow: only
flat-rate states -- PO-box ZIPs in states with locals
(NY/CA/TX/etc.) need SubJurisdiction Protocol work since
they could land in many counties. Easy to grow as new PO-box
ZIPs are discovered via /loop probes.

**iter-70/71 audit pin batches** (488 -> 516 entries): probed
the lowest-coverage states (1-5 pin entries) and pinned the
matches:

- ID Twin Falls / Idaho Falls / Coeur d'Alene = 6%
- IA Davenport / Sioux City / Waterloo = 7%
- MI Lansing / Ann Arbor / Flint = 6%
- ND Minot = 7.5%
- IN Bloomington / South Bend / Carmel / Fishers = 7%
- NV Sparks 8.265% / Carson City 7.6% / Elko 7.1%
- UT St George 6.75%
- WY Sheridan 6.0% / Gillette 5.0%
- HI Pearl City / Kaneohe / Waipahu / Kailua-Kona = 4.5%
- PR Ponce / Caguas / Arecibo = 11.5%
- OK Bartlesville 8.9%

Discrepancies surfaced for follow-up:
- ID Sun Valley / Ketchum: resort city tax 3% not modeled
- IA Iowa City Johnson Co LOST may be missing
- ND Williston Williams Co 0.5% may be missing
- WA Tacoma/Spokane/Vancouver: small 0.1-0.2% drift since last
  WA quarterly load
- KS Hays/Dodge City and OK Stillwater: county rates may have
  shifted; need DOR confirmation
- SD Brookings/Watertown/Mitchell 6.2%: correct general retail
  per SD DOT (the 0.3% MGRT only applies to lodging/alcohol/
  prepared food)
- AL Madison +1% Madison Co Sp district: acknowledged gap in
  al_data.py

**iter-72/73 audit pin batches** (516 -> 525 entries): FL
Pensacola, NY Albany, NY Long Island (Huntington/Smithtown),
CA Berkeley, MN Twin Cities suburbs (St Paul/Eden Prairie/
Minnetonka/Plymouth). Notable MN finding: the Twin Cities pins
capture 2 metro-wide taxes effective Oct 1 2023 -- Metro Area
Transportation Sales Tax 0.75% + Metro Area Sales and Use Tax
for Housing 0.25% -- adding 1.0% to every 7-county metro
retailer. The live engine correctly stacks these per MN Sec
297A.99; my mental DOR estimates were 1.5% low.

**iter-74 AL Madison Co Sp fold-in** (commit `851ca18`,
deployed). Closed the acknowledged 1.0% under-collection gap
documented in al_data.py: Madison City had a +1.0% "Madison Co
Sp" special district that wasn't modeled. Folded the +1% into
the Madison city portion (3.5% -> 4.5%) using the same trick
iter-63 used for the MO Jackson + KCZD fold-in. After AL
reload, Madison ZIPs 35756 / 35757 / 35758 corrected from 8.0%
-> 9.0%, matching ALDOR / Avalara exactly. Birmingham BSD
examined and confirmed not applicable to general retail (BSD
applies to specific categories like lodging/alcohol; Birmingham
10.0% is correct as-is, no fold needed).

**iter-75/76 ID resort cities feature** (commits `661aa88` +
`a56bd9a`, deployed). Closed the deferred gap noted in idaho.py
docstring since v0.6 (resort-city local-option taxes under
Idaho Code section 50-1044). New `id_data.py` with 12 cities
total: 6 highest-population at 3% (Sun Valley / Ketchum / McCall
/ Stanley / Donnelly / Cascade -> combined 9.0%), 5 mid-tier at
1% (Sandpoint / Driggs / Riggins / Lava Hot Springs / Crouch ->
combined 7.0%), 1 low-tier at 0.5% (Salmon -> combined 6.5%).
Pattern matches alaska.py: per-city table + idaho.py emits state
+ city RateRows + (state, city) BoundaryRows per ZIP. Verified
all 12 live on prod. Outstanding: Sun Valley 83353 lodging
0.5% / by-the-drink 1% rates aren't modeled (only general
sales); a future ratchet can split per-category.

**iter-77 IA Johnson Co LOST friendly-name fix** (commit
`1fe1b4e`, deployed). Initial assumption (iter-77) that the IA
SST file omitted Johnson County's 1% LOST proved wrong: the SST
data DOES include it as district code 98103, just unfriendly
named. Adding 98103 -> "Johnson County Local Option Sales Tax"
to ia_names resolved Iowa City 52240 from 6% -> 7%. Lesson:
when a rate stack shows a placeholder authority name like
`IA-district-NNNNN`, check the per-state names file before
assuming the data is missing. iter-81 expanded ia_names from 4
to 19 districts via the same ZIP probe + FIPS Place chain
pattern (98XXX = county FIPS 19XXX last 3 digits).

**iter-78 MN city attribution picker bug logged** (no fix yet).
The `_pick_one_city_county_per_zip5` picker prefers
higher-row-count cities, so Edina ZIPs return city='Bloomington'
(both have 0.5% city tax). Combined RATE is correct because
those cities share the same rate, but per-jurisdiction
attribution is wrong. Fix would require either USPS PCITY-aware
tiebreaker or per-state city-anchor tables (like CA's
CA_CITIES city_county_for_zip).

**iter-79..86 names-table expansions across 10 states** (8
commits, all deployed). Pattern: probe city ZIPs against the
live API, identify placeholder codes like `WI-city-53000`,
cross-check against US Census FIPS Place codes (state-FIPS +
place-FIPS scheme), add to per-state names file, reload state
data on prod. Each entry verified two ways before pinning.

  WI: 0  -> 31 cities (Appleton, Beaver Dam, ... Whitewater)
  IA:  4 -> 19 districts (Adair Co LOST, ... Woodbury Co LOST)
  WV: 3  -> 16 cities (Beckley, Bluefield, ... Wheeling)
  KS: 8  -> 12 cities (+ Dodge City, Emporia, Hays, Newton)
  OK: 20 -> 23 cities (+ Durant, Guthrie, Woodward)
  TN: 6  -> 10 cities (+ Brentwood, Cleveland, Franklin, Winchester)
  SD: 3  -> 8 cities (+ Brookings, Mitchell, Pierre, Watertown, Yankton)
  UT: 7  -> 8 cities (+ Tooele)
  WA: 17 -> 18 cities (+ Sedro-Woolley)
  ND: 6  -> 7 cities (+ Valley City)

Total: **86 new friendly authority names** across 10 states.
Receipts and the per-jurisdiction breakdown in the API response
no longer surface placeholder codes for any of those cities.

NC and GA require no city-name table because their local sales
tax is purely county-level (no city authorities). NE, OH, AR
were probed clean (existing names tables already cover the
major cities).

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
