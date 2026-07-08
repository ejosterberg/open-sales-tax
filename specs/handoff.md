# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

**v0.59.0 is the latest release (2026-05-17, first-class shipping
field).** Untagged main is at iter-212 (MN district leak xfail
regression test). 10 unreleased iters of overnight work since
v0.59.0 — see "Overnight 2026-05-19" below for the punch list.

Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax)
and prod API at the Cloudflare-fronted public URL
[api.opensalestax.org](https://api.opensalestax.org/v1/docs).
All 52 jurisdictions tier-1. The SST loader/lookup engine matches
every published DOR rate within 0.05% across **781 sampled
ZIP+4s** on the live engine (every US jurisdiction covered).

## Overnight 2026-05-19 (iter-200..231, since v0.59.0)

**Session totals:** 29 substantive iters, 28 commits, all CI green.
Two deep-research workflow runs (wqptxor1k MN, wh43sz09n IA+NC).
Three states now at major progress milestones:

| State | Before | After | Method |
|---|---|---|---|
| **WV** | 22/98 (22%) | **98/98 (100%)** | iter-203..210 ZIP-probe pattern; iter-224 cols[14] discovery |
| **UT** | 21 entries | 120 entries | iter-226..230 Census Gazetteer FIPS Place 49-XXXXX |
| **WI** | 56 entries | 68 entries (kick-off) | iter-231 Census Gazetteer FIPS Place 55-XXXXX |
| MN | 10 district entries | 52 entries (re-derived) | iter-220 MN DOR xlsx |
| IA | 19 entries (3 wrong) | 20 entries (corrected) | iter-221 FIPS pattern via revenue.iowa.gov |
| NC | 5 entries (1 wrong) | 4 entries (corrected) | iter-221 NCDOR SST page |

**Major artifacts shipped this session:**
- `scripts/audit_district_code_bindings.py` (iter-216..218) — diagnostic
  tool for any state's SST-code → ZIP-prefix coverage
- `tests/unit/test_state_names_invariants.py` (iter-222) — FIPS-pattern
  regression guard catches mislabelings at CI time
- `specs/findings/mn-transit-district-cross-county-leak.md` (iter-211..221)
  — full investigation history including retractions and 3-tier
  hand-curation strategy
- `specs/findings/sst-source-file-quirks.md` (iter-225) — cross-state
  SST CSV column convention survey
- Scheduled monthly state-rate audit task (`monthly-state-tax-audit`,
  first run 2026-06-01)

**WV labelled-city coverage 22 → 88 (+66 entries, ~90% of WV
placeholders).** Used a DB-driven single-ZIP-bound probe pattern:
query `tax_authorities` for placeholders bound to a single ZIP,
WebFetch zip-codes.com for that ZIP's primary city, label the
code. Multi-ZIP placeholders (mostly likely county-level or
special-district authorities mislabelled as 'city' by the loader)
left for a different pattern. See `src/opensalestax/states/
wv_names.py` for the full table.

| iter | added | running coverage |
|---|---|---|
| 203 | 11 | 33/98 (34%) |
| 204 | 8  | 41/98 (42%) |
| 205 | 8  | 49/98 (50%) |
| 206 | 8  | 57/98 (58%) |
| 207 | 8  | 65/98 (66%) |
| 208 | 8  | 73/98 (74%) |
| 209 | 8  | 81/98 (83%) |
| 210 | 7  | 88/98 (90%) |

10 WV placeholders remain: 5 multi-ZIP (likely county/district
authorities) and 5 duplicate-bound (probably sales-tax + use-tax
authority pairs that share a ZIP — see iter-210 commit). Deferred
until a different pattern handles them.

**MN/IA/NC district name corrections (iter-211..222, CLOSED):**
The original iter-211 hypothesis (loader bug causing cross-county
"leak") was retracted in iter-215; the real issue was wrong
hand-curated friendly-name mappings in `mn_names.py`, `ia_names.py`,
and `nc_names.py`. Closed across two deep-research workflows and
14 commits:

- **iter-220 — MN:** MN_DISTRICT_NAMES re-derived from MN DOR's
  authoritative "Tax Type Codes" xlsx
  (revenue.state.mn.us/media/document/58036). 10 entries → 52,
  7 wrong labels corrected (e.g. 80001 "Cook Co Transp" → "St.
  Cloud Area Sales/Use", 80012 "Anoka Co Transp" → "Stearns Co
  Sales/Use"). Plus 42 newly-added codes covering Cannabis Gross
  Receipts, Retail Delivery Fee, Liquor, Car Rental, lodging
  taxes for 15 cities, etc.
- **iter-221 — IA:** off-by-one in IA_DISTRICT_NAMES: 98175 was
  "Taylor" → "Union" (FIPS 19175); 98181 "Union" → "Warren"
  (FIPS 19181); 98173 "Taylor" added (was missing). Source:
  revenue.iowa.gov SST page.
- **iter-221 — NC:** removed 99055 (NCDOR doesn't list it; was
  wrongly duplicating "Durham" alongside 99063). Renamed 4
  remaining codes to NCDOR's exact wording "Public Transportation
  Tax" (was "...Sales Tax"). Source: NCDOR SST participants page.
- **iter-222:** new unit test
  `test_state_names_invariants.test_fips_derived_codes_match_county_name`
  enforces the FIPS-pattern invariant for IA + NC at every CI run.
  Smoke-verified it catches all 3 known-bug labels.

The 6-row xfail regression in `tests/integration/test_sst_dor_validation.py`
(`MN_DISTRICT_LABEL_GRID`) will flip to xpass after the next prod
data reload. Mechanical follow-up:

```bash
# Hot-deploy iter-220/221 mn_names/ia_names/nc_names to prod,
# then refresh per-state data versions to apply the new friendly
# names in tax_authorities.name. Boundaries don't need refresh
# (only friendly names changed; ZIP↔authority bindings unchanged).
ssh opensalestax-01 "cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api"
# Then re-run loader for the three states:
for s in MN IA NC; do
  ssh opensalestax-01 "docker exec open-sales-tax-api-1 \
    python -m opensalestax data load -s $s -v <latest-version>"
done
```

See `specs/findings/mn-transit-district-cross-county-leak.md`
for the full investigation history including iter-211's wrong
"loader bug" hypothesis, iter-215's retraction, the audit script
in `scripts/audit_district_code_bindings.py` (iter-216..218),
and both deep-research workflow IDs.

## Standing processes (recurring scheduled tasks)

Two scheduled Claude tasks keep the project actively maintained
without Eric having to drive every cadence step. Both are stored
under `C:\Users\ejosterberg\.claude\scheduled-tasks\` and run when
the Claude Code app is open (or on next launch if it was closed
when the cron fired).

### Daily state-tax audit (`monthly-state-tax-audit` taskId)

**Schedule:** 7am local, every day. Cycles through 2 jurisdictions
per day; 26 days covers all 52 (50 states + DC + PR). Days 27-31
are buffer.

| Day | Pair | Day | Pair |
|----:|------|----:|------|
|  1 | AK, AL |  14 | MT, NC |
|  2 | AR, AZ |  15 | ND, NE |
|  3 | CA, CO |  16 | NH, NJ |
|  4 | CT, DC |  17 | NM, NV |
|  5 | DE, FL |  18 | NY, OH |
|  6 | GA, HI |  19 | OK, OR |
|  7 | IA, ID |  20 | PA, PR |
|  8 | IL, IN |  21 | RI, SC |
|  9 | KS, KY |  22 | SD, TN |
| 10 | LA, MA |  23 | TX, UT |
| 11 | MD, ME |  24 | VA, VT |
| 12 | MI, MN |  25 | WA, WI |
| 13 | MO, MS |  26 | WV, WY |

Per-state procedure compares the state's authoritative DOR (or
SST Governing Board for SST members) rate publication against
the live engine, writes findings to `specs/audits/YYYY/MM/state-
audit-YYYY-MM-DD.md`, auto-commits trivial fixes, chips larger
refreshes for Eric's review.

Set up in iter-219 as monthly; reshaped to daily-rotation in
iter-233 per Eric's feedback that monthly-as-one-big-batch was
too coarse.

### Weekly software improvement (`weekly-software-improvement` taskId)

**Schedule:** 8am local, every Monday. Looks for the highest-yield
improvement to ship that week. 7-tier decision tree:

1. Real bugs / correctness / security issues open right now
2. Open items in handoff.md's "what to start on next"
3. Sales-tax-legislation discoveries worth converting to public
   `docs/legislation/<topic>.md` explainers
4. Documentation gaps (TODOs, missing examples, stale docstrings)
5. Test coverage gaps (modules below 80%)
6. Performance / code-smell wins (audit script, profiling)
7. Community signal (issues, PRs, external mentions)

Last resort: improve a state module's docstring to read better
for a contributor. Set up in iter-233.

### Invoking ad-hoc

To run either task immediately rather than waiting for the
schedule, use the "Scheduled" sidebar → "Run now" on the task,
or list via `mcp__scheduled-tasks__list_scheduled_tasks`.

### MANDATORY security gate (iter-234)

Per Eric's standing directive ("security scans run with any change
before it is posted"), BOTH scheduled tasks were updated to require
a SonarQube scan + the `quality-gate` skill before any `git push`.
Push must be blocked if either:

1. `quality-gate` reports any FAIL (ruff format/check, mypy strict,
   pytest, pip-audit).
2. SonarQube scan introduces ANY new BLOCKER or CRITICAL finding
   vs. the previous baseline.

OWASP self-review is also required on the diff (SQL injection,
path traversal, credential exposure, auth bypass, info leakage).

**Baseline established iter-234 (2026-05-19):**
- 0 bugs / 0 vulnerabilities / 0 security hotspots
- Reliability A / Security A / Maintainability A
- 29 CRITICAL code smells (pre-existing — all dated 2026-05-04..06
  or 2026-05-17, none from the iter-203..233 session)
- 4 MAJOR code smells
- Dashboard: http://10.32.161.205:9000/dashboard?id=opensalestax

Any scheduled-task run that introduces a 30th CRITICAL finding (or
any new BLOCKER) blocks itself before push.

## What to start on next

**The obvious next move is deploying iter-220/221 to prod + a
data reload for MN/IA/NC** so the corrected friendly names
surface in the live engine. The mechanical sequence is in the
"MN/IA/NC district name corrections" section above.

After the reload:

1. Verify the 6 xfail rows in `MN_DISTRICT_LABEL_GRID` now xpass
   (`pytest -m liveapi tests/integration/test_sst_dor_validation.py
   -k test_mn_district_label_correct`).
2. Remove the xfail decorator and rename the grid constant from
   `MN_DISTRICT_LABEL_GRID` to something neutral like
   `DISTRICT_LABEL_REGRESSION_GRID` (it now covers IA + NC too).
3. Tag a release (v0.60.0 candidate) and update `CHANGELOG.md`.

If Eric wants something different, the next-obvious-thing menu:

- **Finish the last 10 WV placeholders** (5 multi-ZIP + 5
  duplicate-bound). The remaining cases are likely county-level
  or special-district authorities mis-classified as 'city' by
  the loader — they need a different pattern than the iter-203..210
  ZIP-probe approach.
- **UT/WI hand-curation sweep**. UT codes follow the FIPS Place
  scheme (49-NNNNN) so they can be bulk-resolved via Census
  TIGER/Line gazetteer data; needs offline FIPS Place data. WI
  has the same FIPS Place pattern (55-NNNNN) and a far larger
  pool (~1850 placeholders).
- **Resume captain-tier work** on the error-envelope migration
  investigation (`specs/captain-requests/error-envelope-migration-investigation.md`)
  — that gates v0.60.0 per the iter-197 captain brief.
- **Hand-request IA DOR for the 98201+ multi-county-city
  mapping** that IA DOR documents the existence of but doesn't
  publish in tabular form (102 codes covering 45 cities × 2
  counties + 4 cities × 3 counties).

If Eric wants none of the above, ask before pivoting.

### Latest session continuation hooks

- **UT 97xxx-series codes (~60 remaining)** don't match Census FIPS
  Place — need UT State Tax Commission "Tax Rate Charts"
  cross-check. Possibly CDPs not in standard gazetteer or special-
  purpose tax districts.
- **UT 57080 vs 57300** both bind to Orem-area ZIPs. Census says
  57080 is Orem; iter-180 has 57300 as Orem. Possibly a sales/use
  pair or alternate-code convention -- needs disambiguation.
- **WI long tail (~1782 placeholders)** mostly Wisconsin Towns (a
  township-level government), not in Census Place gazetteer. Use
  `2024_gaz_cousub_55.txt` (Census County Subdivision file) to
  cover Towns. Mechanical batch through 100+ iters wasn't appropriate
  for the autonomous loop; better as a one-time script that downloads
  the cousub file once and processes the whole pool offline.

### Open follow-ups from daily state-tax audits

- **IA West Des Moines LOST dedup over-collect — FIXED in repo, prod
  redeploy PENDING (audit 2026-07-07, finding written, deploy chipped).**
  West Des Moines cross-county ZIPs over-collected: **50265 → 9.0%** (Iowa
  6% + Polk LOST 1% + *Union LOST 1%* + IA-district-98199 1%) and **50266 →
  10.0%** (adds Dallas district 98049 1%). Correct rate is **7.0%** — Iowa's
  LOST is capped at 1% (Iowa Code ch. 423B). **Fixed in the engine** (not
  data): `core/lookup.py` now runs `_dedup_single_local_districts` on both
  the strict + loose lookup paths — for `_SINGLE_LOCAL_DISTRICT_STATES`
  (`{"IA"}`) it keeps only the dominant district (most rows for the ZIP) and
  drops the multi-county stack. Rate-neutral: every IA district is a 1% LOST
  (verified on prod), so collapsing never changes the rate. Covered by new
  unit tests + two DB-backed end-to-end tests (both paths, run in CI) + live
  grid pins for 50265/50266. **The live engine still returns 9%/10% until
  prod is redeployed** (engine-only, NO data reload needed) — chip "Deploy
  IA West Des Moines LOST fix to prod (redeploy api)" carries the sequence;
  until then the two `-m liveapi` pins fail (expected). Rate file
  `IAR2025Q3MAY30` + boundary `IAB2026Q1DEC09` on prod are current (match
  latest SST posting); no IA data refresh needed. Cosmetic follow-up: give
  `IA-district-98049` (Dallas Co LOST) a friendly name in `ia_names.py`.
  Idaho audited same day — no drift. See
  `specs/findings/ia-west-des-moines-lost-dedup-2026-07.md` and
  `specs/audits/2026/07/state-audit-2026-07-07.md`.
- **HI Maui County GET surcharge FIXED in repo, prod reload PENDING
  (audit 2026-07-06, commit f68fe40, chipped).** The engine had
  under-collected the **Maui County 0.5% GET surcharge on every
  Maui-County transaction since 2024-01-01**: `hi_data.py` recorded
  Maui at 0.000% (combined 4.0%) with a wrong "not enacted" comment.
  The surcharge was in fact enacted by County Ordinance 5511 (signed
  2023-07-19), effective 2024-01-01 → 2030-12-31 — confirmed vs the HI
  DOTAX county-surcharge schedule + Maui County Council notice. This
  resolves the long-standing iter-158/159 open item. Fixed: Maui
  0.000→0.500%, all HI docstrings/notes, **HI removed from
  `STATE_COVERAGE_WARNINGS`** (gap now closed — all 4 inhabited
  counties correct at 4.5%), stale "HI Maui dispute" refs cleaned from
  api schemas/handlers, and tests (incl. Kahului 96732 pin 4.000→4.500,
  `test_hawaii_combined_rate_maui_is_4_5`). **The live engine still
  returns 4.0% for Maui until prod is redeployed + HI reloaded** — chip
  "Deploy HI Maui GET fix to prod (reload HI)" carries the sequence.
  Until then the Kahului pin fails under `-m liveapi`. Flag for CY2030:
  all current HI county surcharges sunset 2030-12-31. See
  `specs/findings/hi-maui-county-surcharge-2026-07.md` and
  `specs/audits/2026/07/state-audit-2026-07-06.md`.
- **GA SST rate file 1 quarter behind (audit 2026-07-06, chipped).**
  Prod caches `GAR2026Q2FEB19` / `GAB2026Q2FEB16` (Q2 2026); latest SST
  rate file is `GAR2026Q3JUN05` (posted 2026-06-08). No real-world drift
  — all 10 GA tier-1 cities match the engine + GA DOR published rates.
  Routine currency refresh; chip "Refresh GA SST quarterly to
  GAR2026Q3JUN05" carries the load sequence. See
  `specs/audits/2026/07/state-audit-2026-07-06.md`.
- **FL Collier + Palm Beach over-collect FIXED in repo, prod reload
  PENDING (audit 2026-07-05, commit 32a61f6, chipped).** The CY2026
  DR-15DSS (R.11/25) cross-check caught two stale FL county surtaxes
  from the 2026-05-04 module build: **Collier** was 1.0% but is "None"
  (its 1% infra surtax hit its $490M/7yr cap and ended → Naples 6.0%),
  and **Palm Beach** was 1.0% but is 0.5% eff Jan 1 2026 (old 1% ended;
  new 0.5% runs 2026–2035 → WPB/Boca 6.5%). Both confirmed vs
  Avalara/SalesTaxHandbook. `fl_data.py` + 3 live pins + FL unit test
  fixed and pushed (CI green). **The live engine still returns the old
  too-high rates until prod is redeployed + FL data reloaded** — chip
  "Deploy FL rate fix to prod (Collier/Palm Beach reload)" carries the
  exact sequence. Until then the 3 pins (Naples 34102, WPB 33401, Boca
  33432) fail under `-m liveapi`. Also flag for CY2027: Brevard +
  Charlotte are 1.0% now but their components expire Dec 31 2026. See
  `specs/audits/2026/07/state-audit-2026-07-05.md`.
- **Pre-existing dep CVE: asyncmy 0.2.11 PYSEC-2026-286 (surfaced by
  pip-audit during the 2026-07-05 gate, chipped).** No fix version
  published; unrelated to any rate change. asyncmy is the optional
  MariaDB driver, so PostgreSQL self-hosters are unaffected. Triage
  chip "Triage asyncmy PYSEC-2026-286" filed.
- **WV SST refresh Q1 → Q3 (audit 2026-06-26, chipped).** Prod caches
  `WVR2026Q1AUG14` / `WVB2026Q1SEP02`; latest SST is
  `WVR2026Q3FEB25` / `WVB2026Q3APR29`. No drift in the top-5 cities
  (all correctly 7%), but several new 2026 municipalities adopted the
  1% municipal tax (Bramwell, Glenville, Hinton, Marlinton, Pineville,
  Anmoore, Bath) + increases (Richwood, Westover) that only surface
  after the Q3 load. See `specs/audits/2026/06/state-audit-2026-06-26.md`.
- **WY SST refresh Q2 → Q3 (audit 2026-06-26, chipped).** Prod caches
  `WYR2026Q2APR1` / `WYB2026Q2FEB23`; latest SST is `WYR2026Q3JUN2` /
  `WYB2026Q3MAY18`. No drift in the top-7 county/city stacks (all match
  the WY Excise Division chart). Routine currency refresh; also worth
  checking whether Teton Village (83025) / Alta (83414) resolve to WY's
  9% resort-overlay max (Jackson proper 83001 correctly 7%).
- **6 SST states need Q3 refresh (buffer-day catch-up audit 2026-06-29,
  chipped).** Days 22–25 of the rotation were missed (app not open), so
  SD/TN/UT/VT/WA/WI were audited together on the day-29 buffer. No
  real-world rate drift in any of them, but all 6 are 1+ quarters behind
  on prod. **SD and TN are badly behind on their RATE files** (SD prod =
  `SDR2024Q1DEC12`, TN prod = `TNR2025Q1MAR07`). Latest Q3 2026 files:
  SD `SDR2026Q3JUN02`/`SDB2026Q3JUN04`, TN `TNR2026Q3JUN11`/
  `TNB2026Q3MAY22`, UT `UTR2026Q3MAY11`/`UTB2026Q3MAY11`, VT
  `VTR2026Q3MAY20`/`VTB2026Q3MAY20`, WA `WAR2026Q3MAY27`/`WAB2026Q3MAY27`,
  WI `WIR2026Q3MAY22`/`WIB2026Q3MAY22`. See
  `specs/audits/2026/06/state-audit-2026-06-29.md`.
- **UT `-0001` placeholder ZIP+4 drops county for some ZIPs (audit
  2026-06-29, chipped).** Calling `/v1/calculate` with the synthetic
  `-0001` ZIP+4 under-collects the county rate for Provo (84601), St
  George (84770), Clearfield (84015) — bare-ZIP5 and real-+4 lookups are
  correct, so real-world impact is low, but two UT DOR_GRID pins now fail
  under `-m liveapi`. Full write-up + investigation steps in
  `specs/findings/ut-zip4-0001-county-drop-2026-06.md`. Do NOT mask it by
  swapping the pins' ZIP+4 — fix the engine/loader resolution first.
- **WI Milwaukee stale DOR_GRID pin — FIXED (audit 2026-06-29).** The
  `53202-2402` pin expected 5.900% (pre-Act-12, county only); engine
  correctly returns 7.900% (Milwaukee city 2% per WI Act 12). Pin bumped
  to 7.900 with an explanatory comment. No engine change.

## Recent improvements (weekly sweeps)

- **2026-07-06 — No-code contributor on-ramp (Tier 4 doc gap, driven
  by Tier 7 community signal).** The weekly sweep responded to open
  issue [#38](https://github.com/ejosterberg/open-sales-tax/issues/38)
  ("How are you finding state-module contributors?" — a genuine
  maintainer question from a fellow founder, unanswered since
  2026-05-21). The durable answer to "how do you find people with tax-
  domain knowledge" is to *lower the barrier so domain experts can
  contribute without Python*, which was previously impossible: every
  contributor doc (`CONTRIBUTING.md`, `docs/state-modules.md`) assumed
  the reader writes Python, ran Poetry, and could pytest against two DB
  engines. Shipped: (1) the project's **first GitHub issue forms** under
  `.github/ISSUE_TEMPLATE/` — a structured **rate-correction** form (a
  tax preparer / accountant / business owner can report a wrong or
  missing rate with a DOR citation, no code), an **adopt-a-state** form
  (become a state maintainer, "Python comfort: none" is a valid answer),
  and a `config.yml` chooser linking the no-code guide; (2)
  `docs/contributing-without-code.md` — "Help your state without writing
  Python," covering the primary-source rule (no commercial-vendor data
  per constitution §2), the three no-code paths, and how to check a
  rate via the demo site / `/v1/rates`; (3) two triage labels
  (`rate-report`, `state-adoption`); (4) prominent links to the no-code
  guide from `README.md`, `CONTRIBUTING.md` (above the dev-setup wall),
  and `docs/state-modules.md`. Docs + GitHub-config only — no code or
  dependency surface. **Issue #38 itself is a founder-to-founder
  question best answered personally by Eric** (it asks "have *you*
  found a reliable way…"); left open for his reply, but the durable
  artifact it prompted now serves every future would-be contributor.
  Gate: ruff format/check + mypy + pytest all green; SonarQube delta
  recorded below. Commit on `main`.

- **2026-07-04 — Public SST file-format field guide (Tier 3).** The
  weekly software-improvement sweep converted the project's
  accumulated SST-format knowledge — previously scattered across
  `specs/research/sst-file-format.md` and
  `specs/findings/sst-source-file-quirks.md` — into a public,
  contributor-facing explainer at
  [`docs/legislation/sst-file-format.md`](../docs/legislation/sst-file-format.md).
  It walks a cold contributor through the filename/version convention,
  the 9-column rate file (and the non-standardized col-2
  jurisdiction-type code), the 89/90-column boundary file with its
  `z`/`4`/`a` records and repeating district triplets, and every
  format gotcha that cost real debugging time (VT BOM, single-digit
  days, csv↔zip migration, the two no-end-date sentinels, phantom
  type-45 location codes, ZIP+4 zero-padding, the 90th-column
  widening) — each grounded in the actual parser source. Added
  `docs/legislation/README.md` as an index for future explainers and
  linked the guide from `README.md` + `docs/state-modules.md` so it's
  the first thing a new-state contributor finds. Docs-only, no
  code/dependency surface. Gate: ruff format/check + mypy (134 files)
  + pytest (1560 passed) all green; **SonarQube 0 new BLOCKER/CRITICAL**
  (baseline 0, current 0). Commit `7bd82f2` on `main`.

## Recent releases (latest first)

- **v0.59.0** (2026-05-17, iter-198): **First-class shipping field
  for /v1/calculate.** Closes connector-tier captain Ask 3;
  unblocks OpenCart O-3. New `ShippingInput`/`ShippingOutput`
  schema; every state module's `shipping_rule_set()` returns one
  of 5 rules (CONDITIONAL×27, EXEMPT_IF_SEPARATELY_STATED×19,
  NONE×5, ALWAYS_TAXABLE×1 HI, MIXED×1 MD) with primary
  DOR/statute citations from
  `specs/research/shipping-taxability.md`. `shipping_first_class`
  capability flag flipped True. Decisions ratified in
  `specs/phase-shipping-p1/plan.md`. Iter-199 added 5 live-API
  shipping pins to the DOR grid for drift detection.

- **v0.58.0** (2026-05-15): `coverage_warning` field (iter-189)
  +`/v1/capabilities` endpoint (iter-197) + 7 more TX/AZ cities
  (iter-188/190/191/192/193/194/195/196). Coverage warning fires
  for CO/LA/AL/HI when those state-only responses understate the
  true rate.

- **v0.57.0** (2026-05-15): Overnight quality ratchet (16 iters
  iter-172..187). NM TRD rate refresh: all 17 NM tier-1+tier-2
  cities re-verified against published 2026 TRD rates. **130
  city friendly names added across 10 states** (WA+15, TN+14,
  AR+9, KS+16, SD+8, UT+12, ND+9, OK+21, WI+20, WV+6). 6 TX DFW
  satellites added.

- **v0.56.0** (2026-05-14): Major correctness ratchet (191
  commits, iter-117..171). MN/SD cross-state ZIP RESOLVED
  (iter-165..168); OH COTA multi-district fix (iter-169); MO
  KCMO multi-county fix (iter-170/171); CA/TX/AZ/FL/SC data
  expansion.

## Overnight 2026-05-14..05-15 (iter-172..183, since v0.56.0)

**NM TRD rate refresh — 17 cities re-verified (iter-172..175):**

| City | Drift | New combined |
|---|---|---|
| Albuquerque | -0.25% over | 7.625% |
| Santa Fe | -0.25% over | 8.1875% |
| Las Cruces | **+0.39% under** (Jul 2025) | 8.390% |
| Rio Rancho | +0.1875% under | 7.875% |
| Roswell | **+0.71% under** (Jul 2025) | 8.2708% |
| Farmington | +0.0625% under | 8.1875% |
| Hobbs | clean | 6.5625% |
| Carlsbad | -0.4375% over | 7.3958% |
| Clovis | -0.125% over | 7.9375% |
| Alamogordo | +0.0625% under | 8.1875% |
| Los Lunas | +0.30% under | 8.425% |
| Las Vegas NM | -0.3334% over | 8.1458% |
| Sunland Park | -0.185% over | 8.19% |
| Deming | +0.125% under | 8.25% |
| Lovington | **-0.5625% over** (rate cut) | 7.000% |
| Artesia | +0.125% under | 7.6458% |
| Portales | **+0.4875% under** (Jul 2025) | 8.55% |
| Espanola | -0.0625% over | 8.8125% |
| Grants | -0.0625% over | 8.000% |
| Anthony | +0.2525% under | 8.3775% |
| Bernalillo | **-0.5% over** (rate cut) | 7.4375% |
| Silver City | -0.0125% (noise) | 8.125% (unchanged) |

Only Gallup (87301) remains unverified — Navajo Nation Reservation
overlay needs sub-ZIP precision modeling.

**Receipt-quality: 124 city friendly names added across 9 states
(iter-176..183):**

| State | Module | Was | Now | Added |
|---|---|---:|---:|---:|
| WA | wa_names.py | 18 | 33 | +15 |
| TN | tn_names.py | 10 | 24 | +14 |
| AR | ar_names.py | 18 | 27 | +9 |
| KS | ks_names.py | 12 | 28 | +16 |
| SD | sd_names.py | 8 | 16 | +8 |
| UT | ut_names.py | 8 | 20 | +12 |
| ND | nd_names.py | 7 | 16 | +9 |
| OK | ok_names.py | 23 | 44 | +21 |
| WI | wi_names.py | 39 | 59 | +20 |
| **Total** | | **143** | **267** | **+124** |

Every entry verified via the standard two-way protocol: probe live
engine for a ZIP known to lie in that city + cross-check the SST
jurisdiction code against the FIPS Place 5-digit suffix.

## Overnight 2026-05-15 rate-audit findings (RETRACTED — false alarm)

**iter-186 OK city rate audit, RETRACTED**: Initial probe vs
SalesTaxHandbook surfaced 3 OK cities looking like they had drift
(Catoosa under 0.80%, Guthrie under 0.25%, Bethany under
0.125%). Cross-verified by inspecting the OK SST quarterly file
directly (``OKR2026Q2FEB17.zip``) AND Avalara's per-city
breakdown:

- OK SST file rates: Catoosa 3.25% city, Bethany 4.0% city,
  Guthrie 3.75% city — these are the authoritative SST-published
  rates effective through 2078-12-31.
- Avalara confirms: Catoosa 3.25% city / 9.25% combined, Bethany
  4.0% city / 8.5% combined — both match our engine exactly.
- SalesTaxHandbook's per-city OK pages were the unreliable
  source. No engine drift.

**Lesson for future audits**: when verifying OK rates,
cross-check Avalara before trusting SalesTaxHandbook. Their
listed "combined rate" for OK cities can be inflated by including
phantom overlays. Verified against multiple sources is the new
default for non-NM rate audits.

States probed clean (no placeholder city names surfaced):
- IN / GA / NC / KY: state or county-only tax models, no city
  layer in our schema
- NV: no city sales tax (state + county only)
- MO / IL / MS / AZ / AL: all curated names already populated

States deferred:
- MN, VT, WV: module docstrings explicitly warn FIPS-pattern
  guessing is unreliable — codes don't follow Census FIPS Place
  scheme. Hand-curation only.
- NE: probed several placeholders but FIPS Place mappings
  uncertain; hand-curation recommended.

## Pre-overnight highlights (iter-117..171, in v0.56.0)

Headline highlights:
- CA reconciliation (50 cities) iter-63
- WI structural rewrite iter-63 (Milwaukee 2% etc)
- AK borough-stacks-with-city iter-67
- USPS PO-box ZCTA supplement iter-68/69 (29 ZIPs)
- AL Madison Co Sp fold-in iter-74
- IA Johnson Co LOST friendly-name fix iter-77/80
- ID resort cities feature iter-75/76 (12 cities)
- wi_names.py (39 cities), 11 names tables expanded with
  99+ friendly names total
- **iter-93..104 CA-cities expansion: 19 cities added**
  (Burbank/Walnut Creek/San Mateo/El Cerrito/Burlingame/Richmond/
  Antioch/Pittsburg/Redwood City/Mill Valley/Sausalito/Larkspur/
  San Anselmo/San Bruno/Pacifica/Belmont/Rocklin/San Carlos/
  San Ramon + Folsom + Palo Alto + East Palo Alto county
  anchors). Total under-collection closed: ~16% across 19 CA
  cities, 50+ ZIPs.
- **iter-105..116 CA-cities continued expansion: 58 more cities
  added (CA_CITIES grew 50 → 127)**, batched per region:
  - iter-105/106/107/108/110: LA Co cluster (Novato + Corte Madera
    + Culver City + El Segundo + Whittier + La Habra OC anchor +
    Gardena + Lawndale + Hawthorne + Cerritos + Santa Monica +
    West Hollywood + Alhambra + Monterey Park) — 14 cities
  - iter-111/112: SD Co + Santa Clara Co (National City + Vista +
    San Marcos + Cupertino + Milpitas) — 5 cities
  - iter-113: Auburn (Placer Co cross-county fix from El Dorado)
    + Loomis + Davis (Yolo Co cross-county fix from Solano) +
    5 SLO Co cities (San Luis Obispo / Atascadero / Paso Robles /
    Arroyo Grande / Morro Bay) — 8 cities
  - iter-114: Sonoma Co (Petaluma cross-county from Marin + Sonoma
    cross-county from Napa + Sebastopol + Healdsburg + Rohnert
    Park + Cotati) + Napa Co (Napa + American Canyon + Calistoga)
    — 9 cities
  - iter-115: Riverside Co single-iter sweep (Hemet + Temecula +
    Murrieta + Lake Elsinore + Menifee + Indio + Coachella +
    Palm Desert + La Quinta + Cathedral City + Palm Springs) +
    Porterville (Tulare Co) — 12 cities
  - iter-116: SD Co (El Cajon + La Mesa + Imperial Beach + Lemon
    Grove + Del Mar + Solana Beach) + Westminster (OC Co) — 7 cities
  Cross-county misattribution pattern (Census ZCTA-vs-USPS) hit
  five times in this stretch (Folsom iter-103, Auburn iter-113,
  Davis iter-113, Petaluma iter-114, Sonoma iter-114). Each fix
  uses the city anchor in CA_CITIES to force the correct county
  bind. Verified live + pinned to test_sst_dor_validation grid
  for every iter (~75 new pins added 596 → 671). Total combined
  CA under-collection closed across iter-93..116: ~50% across
  ~75 cities.
- **iter-147..153 CA + AZ probe sweep**: 17 more fixes across 7
  iters, mixing new-city adds with existing-rate updates:
  - **iter-147 CA Imperial+Kern**: 4 cities (El Centro/Calexico
    +0.5; Brawley +1.0; Ridgecrest +1.0). CA_CITIES 210 → 214.
  - **iter-150 AZ Sahuarita rate**: city tax 2.0 → 5.0 (raised
    2024 per SalesTaxHandbook).
  - **iter-151 AZ Sun City + Vail + Bisbee**: 3 city additions.
  - **iter-152 AZ 8 fixes**: 6 new (Cave Creek which was 0%-
    unbound, Fountain Hills, Paradise Valley, Youngtown, Eagar,
    Springerville) + 2 rate updates (Tolleson 2.5 → 2.8,
    Litchfield Park 2.8 → 3.0). **3rd missing-binding bug**
    fixed (CA Mariposa → FL Paxton → AZ Cave Creek).
  - **iter-153 AZ Parker + Quartzsite**: La Paz Co cities; Parker
    includes Oct-2025 special tax (+4.0 city brings to 10.6%).
  Notable: this stretch survived a ~7-minute GitHub Internal
  Server Error outage on 2026-05-11 14:01-14:09 UTC; iter-153
  push retried via a Monitor until GitHub recovered. One CI
  rerun was needed (the pin CI run hit the same checkout
  failure mid-build and was re-triggered cleanly).

  **AZ session total: 14 city/rate fixes** (Sahuarita rate
  update + 13 new/updated city anchors).
- **iter-170 follow-up GA Dunwoody Fulton TSPLOST stray bind**
  (logged not fixed): ZIP 30338 (Dunwoody, DeKalb Co) returns
  8.75% but Avalara says 8.00%. Engine emits Fulton County
  TSPLOST (0.75%) AND DeKalb MARTA (1.0%) districts. Dunwoody is
  fully in DeKalb -- Fulton TSPLOST shouldn't apply. SQL shows
  Fulton TSPLOST has 24 type-4 boundary rows + 1 stray typez row
  at 30338, vs DeKalb MARTA's 29 type-4 + 0 typez. The typez row
  triggers the engine's "typez district always applies"
  classification. Fix requires linking districts to their parent
  county and dropping districts whose county wasn't picked --
  structural change. Likely affects similar metro-Atlanta /
  metro-Macon / metro-Augusta ZIPs that straddle county lines.
- **iter-169 follow-up MO KC multi-county under-collect** (logged
  not fixed): Kansas City MO's city tax (3.25%) is bound only to
  Jackson Co ZIPs in MO_CITIES. The KC city limits extend into
  Clay Co (64117-64119), Platte Co (64150-64158), and Cass Co.
  64117/64118/64119 return 5.475% (state + Clay only) instead of
  ~8.725%. North Kansas City (64116) is also missing — separate
  municipality with its own ~2.625% city rate. The MO module's
  ``MO_CITIES`` comment block already flags this: "A future
  ratchet should add Clay-side / Platte-side KCMO entries as
  separate 'Kansas City (Clay)' rows." Adding two new
  ``MO_CITIES`` entries (``Kansas City (Clay)`` and
  ``North Kansas City``) and a Platte-side entry would fix it.
  Each entry takes a county_name + city_rate + tuple of ZIPs;
  the parser already supports cross-county anchors. Defer
  pending bandwidth.
- **iter-169 OH COTA transit under-collect — RESOLVED**:
  Probed OH cities, found that Dublin 43017 returned 7.0%
  instead of 8.0% — the 1% COTA transit was missing. Root cause:
  the engine's "lone type-4-only district" rule (iter-62 / v0.47)
  only included a type-4-only district if it was THE ONLY one.
  Dublin 43017 has 3 type-4-only districts (COTA 260 rows + 2
  placeholder special districts at 71 and 28 rows), so the
  picker dropped them all.

  **Fix** (commit a44ae05 src/opensalestax/core/lookup.py): when
  multiple type-4-only districts compete, pick the dominant
  CURATED one (i.e. has a friendly name in the state's *_names.py
  table) if it has >= _MIN_LONE_DISTRICT_ROWS (20) rows AND
  dominates the runner-up by 2x+. The curated-name filter
  naturally excludes the KS/OK/TN competing-CID case (placeholder
  TIF/CID names) while letting OH transit authorities through.

  Verified affected ZIPs: 43017 / 43215 / 43004 (Dublin /
  Columbus / Reynoldsburg) all moved from 7.0/7.5/7.5 -> 8.0.
  Verified unaffected: KS Wichita / OK OKC / OK Tulsa (all
  multi-CID ZIPs with placeholder names; correctly drop all
  type-4-only districts as before).

  **Pin** (commit pending): tests/integration/test_sst_dor_validation.py
  with Dublin 43017 + Reynoldsburg 43004 entries.
- **iter-165..168 MN/SD cross-state ZIP bug — RESOLVED**
  (was iter-163/164 logged, iter-165 partial, iter-166 mis-fix,
  iter-167 right idea wrong filter, iter-168 ships):

  **Symptom**: Pipestone-area ZIPs returned 11-13% combined
  because the engine emitted AND SUMMED jurisdictions from BOTH
  states for ZIPs straddling the MN/SD border:
  - 56144 (MN side) = 11.075% (MN 6.875 + SD 4.2)
  - 56164 (Pipestone) = 11.075%
  - 57068 (SD side) = 13.075% (SD 6.2 + MN 6.875)

  **Root cause**: Both states' SST quarterly files independently
  bound the same border ZIPs to their own state authorities. The
  Census ZCTA loader (iter-165 pre-fix) ALSO emitted one row per
  (ZIP, state) intersection, doubling the binding. Lookup engine
  returned both states' authorities and rate calculator summed.

  **Fix lineage**:
  - **iter-165** (commit c3382de): ZCTA loader collapsed multi-
    state ZIPs to one row by row-count majority. Right shape,
    but didn't fix the bug alone — the SST files still bound
    both sides.
  - **iter-166** (commit b2f89f0): Added engine-level dedup
    using authority-count majority. Helped 56164, broke 56144
    (SD's SST file bound more rows than MN's, count picked SD
    wrongly).
  - **iter-167** (commits 6e31889, a980f43): Refactored engine
    to defer to the ZCTA-sourced boundary as canonical-state
    truth (DataVersion.source LIKE 'zcta%'). Right idea — but
    the underlying ZCTA loader's row-count majority STILL
    picked the wrong state for 57068 (one MN county + one SD
    county = 1:1 row tie, alphabetical picked MN despite SD
    having 13.5x more land area).
  - **iter-168** (commit 378290f): ZCTA loader now picks the
    **area-majority state** per ZIP using AREALAND_PART (sq m
    summed per state). Reloaded the 33,801 ZCTA boundaries.
    All three cross-state ZIPs now resolve correctly:
    56144 → MN 6.875%, 56164 → MN 6.875%, 57068 → SD 6.200%.

  **Tests pinned** (commit 1c560dc):
  - tests/integration/test_sst_dor_validation.py: 3 live-grid
    entries for 56144 / 56164 / 57068.
  - tests/unit/test_zcta_loader.py: 2 pins (tied-row-count area
    decides + majority-on-both-signals).

  **Architectural note**: The engine-level filter
  (`_filter_to_canonical_state` in lookup.py) remains a
  defense-in-depth layer. If a future Census refresh has a
  malformed AREALAND_PART or the ZCTA load is skipped for a
  state, the engine falls back to authority-count majority. The
  combo of "ZCTA loader picks one state per ZIP" + "engine
  defers to ZCTA's pick when available" cleanly handles both
  ZCTA-tracked and ZCTA-missing ZIPs.
- **iter-160 WI Premier Resort Area Tax** (logged not fixed):
  Wisconsin's "Premier Resort Area Tax" (Wis. Stat. 77.994) is a
  special tax of 0.5-1.25% that certain resort municipalities can
  adopt on top of the standard state + county rates. Engine
  currently returns 5.5% for Wisconsin Dells 53965 (should be
  6.75% per SalesTaxHandbook: +1.25% PRAT) and 5.5% for
  Rhinelander 54501 (should be 6.0%: +0.5% PRAT). Other PRAT-
  enabled cities: Bayfield, Lake Delton, Eagle River, Sister Bay,
  Stockholm. SST file provides the city authority slot at 0%; the
  PRAT must be modeled as a special district or city overlay.
  Fix requires WI-specific code-79 district handling similar to
  TN/IL.
- **iter-158/159 HI Maui Co surcharge uncertain** (logged not
  fixed): SalesTaxHandbook reports 0.5% Maui County surcharge for
  Kahului/Kihei/Lahaina/Wailuku ZIPs as of May 2026, but our
  hi_data.py has Maui Co at 0.000% with comment "Maui Bill No. 30
  (2023) authorized but did not enact a 0.5% surcharge." Engine
  returns 4.0% for these ZIPs; SalesTaxHandbook says 4.5%. The
  effective date of the Maui surcharge appears to be in dispute --
  need authoritative cross-check against HI DOTAX Tax Facts 31-1
  before updating. Conservative stance: leave at 0.0% pending
  verification.
- **iter-148 TN IMPROVE Act over-collect** (logged not fixed):
  multiple TN cities in Davidson + Williamson + Sumner Co
  over-collect by 0.5-1.0% due to multiple IMPROVE Act district
  codes (91950/91955/91958) emitting for the same ZIP when only
  one should apply per the v0.44 dedup logic. Examples found:
  Goodlettsville 37072 returns 10.75% (3 districts stacked) vs
  9.75% expected; Brentwood 37027 returns 10.25% (Davidson IMPROVE
  Act 91950 wrongly applies to Williamson Co ZIP) vs 9.25%
  expected. The v0.44 fix solved a different cross-county pattern;
  this is a same-ZIP stacking issue. Same family as iter-128 IA
  West Des Moines LOST dedup bug -- both need per-state dedup
  logic that filters non-applicable district codes.
- **iter-117 cross-state probe**: validated MN, WI, OH, MI, IN,
  TN, NV, UT, WV, NE, NJ, NM, NC, FL, TX, IL, PA, MA, VA, MD
  major cities against SalesTaxHandbook. Most match exactly --
  the engine is well-calibrated for non-CA states. **Two open
  bugs**: NM Albuquerque + Santa Fe over-collect by 0.25% each
  (city tax 0.25% high vs current TRD published rate). NM module
  data is from Jan 2026; needs refresh. Other one-off finding:
  IL Naperville under by 1.0% (mixed-rate-per-ZIP boundary --
  engine picks the Downtown F&B district 7.75% rather than the
  main Naperville rate 8.75%). TN Nashville may have +0.5% over
  due to IMPROVE Act transit district that voters approved Nov
  2024 but SalesTaxHandbook hasn't updated -- engine likely
  correct, SalesTaxHandbook stale.
- **iter-118..125 CA-cities continued (CA_CITIES → 200 milestone)**:
  73 more cities added across 8 iters, with 5 more cross-county
  Census ZCTA misattribution fixes (Davis/Turlock/Dinuba/Watsonville
  /Rio Vista) + 1 missing CA county (Mariposa).
  - iter-118: Rancho Cordova + Galt + Highland + Norco + Calimesa
    (5 cities, Sac/SBd/Riverside Co)
  - iter-119: 11 Central Valley + SJ Co cities (Tracy/Manteca/Lodi
    + 5 Fresno Co + Dinuba cross-county rebind from Fresno→Tulare)
  - iter-120: 9 Northern + Central CA (Mariposa fixes missing
    county + 0%-jurisdictions bug; Turlock cross-county Merced→
    Stanislaus; Ceres + Eureka + Arcata + Chico + Oroville +
    Paradise + Fort Bragg)
  - iter-121: 8 Central Coast + Sierra (Truckee TBID +0.125;
    Hollister; Watsonville cross-county Monterey→Santa Cruz +
    4 more Monterey + Santa Maria)
  - iter-122: 7 Solano + Yolo Co cities (Fairfield/Benicia/Suisun
    City/Dixon + Rio Vista cross-county Sacramento→Solano +
    West Sacramento + Winters)
  - iter-123: 8 Contra Costa Co cities (Brentwood/Martinez/
    Pleasant Hill/Lafayette/Moraga/Hercules/Pinole/Orinda)
  - iter-124: 13 LA Co cities (Beverly Hills/Downey/Norwalk/
    Bellflower/Carson/El Monte + Inglewood + Compton/Lynwood/
    Paramount/South Gate/Pico Rivera/Montebello) -- biggest
    single-iter LA Co batch this session
  - iter-125: 12 more LA Co cities (SGV + east-LA suburbs).
    CA_CITIES hits **200** -- 4x the original 50-city seed.

Cumulative impact since iter-93: **150 CA cities added** (CA_CITIES
50 → 200), 9 cross-county Census ZCTA misattribution fixes, 1
missing CA county (Mariposa) added, ~250 new live-grid pins.
~70% of historical CA under-collection closed.

- **iter-126 LA Co beach + west + southeast**: 10 more LA Co cities
  added (Manhattan/Hermosa/Redondo Beach + Malibu + La Verne +
  Sierra Madre + La Cañada Flintridge + Maywood + Signal Hill +
  Huntington Park). **CA_CITIES → 210**.
- **iter-127 SC Myrtle Beach**: closed a docstring-acknowledged
  gap (sc_data.py line 122-124 noted Myrtle Beach 1% Tourism
  Development tax should be modeled, but the city was never added
  to SC_CITIES). Myrtle Beach 8.0 → 9.0 across 6 ZIPs.
- **iter-128..131 TX expansion (65 cities total this session)**:
  - iter-128: Waco + Galveston (2 cities at 8.25% local cap)
  - iter-129: 15 Austin satellites + Hill Country + San Antonio
    edges (San Marcos / Georgetown / Pflugerville / Leander / Kyle
    / Buda / Hutto / Dripping Springs / Wimberley / Schertz /
    Cibolo / Boerne / Fredericksburg / Kerrville / Marble Falls)
  - iter-130: 23 regional TX cities (East TX / Gulf Coast / Border /
    West TX / Panhandle): Texarkana / Nacogdoches / Lufkin / Paris /
    Sherman / Denison / Greenville / Athens / Palestine / Brenham /
    Huntsville / Rockport / Port Arthur / Orange / Victoria /
    Del Rio / Eagle Pass / Brownwood / Stephenville / San Angelo /
    Big Spring / Andrews / Pampa
  - iter-131: 25 more (DFW satellites / Brazoria-Galveston Co /
    Panhandle / South Plains): Weatherford / Granbury / Burleson /
    Cleburne / Mansfield / Crowley / Cleveland / Liberty / Texas
    City / Friendswood / Dickinson / Alvin / Angleton / Lake
    Jackson / Freeport / El Campo / Cuero / Yoakum / Hereford /
    Borger / Dumas / Plainview / Levelland / Snyder / Sweetwater
  - iter-132: 27 more (North TX small-mid + East TX + Brazos
    Valley + Central TX + South TX): Mineral Wells / Decatur /
    Gainesville / Bonham / Mount Pleasant / Henderson / Marshall /
    Carthage / Center / Crockett / Livingston / Madisonville /
    Navasota / Caldwell / Giddings / La Grange / Bastrop /
    Smithville / Lockhart / Luling / Seguin / Gonzales / Beeville
    / Alice / Kingsville / Sinton / Mathis
  - iter-134: 26 more (SE TX Hardin/Jefferson + Brazos Valley
    west + South TX): Vidor / Groves / Nederland / Port Neches /
    Silsbee / Jasper / Newton / Kountze / Hempstead / Sealy /
    Bellville / Columbus / Schulenburg / Hallettsville / Edna /
    Goliad / Refugio / Karnes City / Pleasanton / Floresville /
    Jourdanton / Pearsall / Cotulla / Carrizo Springs / Crystal
    City / Hondo
  - iter-136: 24 more (NE TX + East TX + Brazos Valley + Central
    TX): Sulphur Springs/Mount Vernon/Pittsburg/Linden/Daingerfield/
    Atlanta/Jefferson/Diboll/Trinity/Groveton/Mexia/Teague/Fairfield/
    Buffalo/Hearne/Franklin/Cameron/Rockdale/Taylor/Elgin/Bartlett/
    Salado/Belton/Kennedale
  - iter-137: 27 panhandle + west TX (Vernon/Quanah/Childress/
    Memphis/Clarendon/Wellington/Shamrock/Wheeler/Canadian/Spearman/
    Perryton/Stratford/Dalhart/Tulia + South Plains + Permian Basin
    + Trans-Pecos). Marfa 79843 logged as 8.0% (city tax 1.75%
    unique, not modeled in this batch).
  - iter-140: 21 Rio Grande Valley + Coastal Bend (Donna/Mercedes/
    Weslaco/Alamo/San Juan/San Benito/Harlingen/La Feria/
    Raymondville/Roma/Rio Grande City/Zapata/Falfurrias/Hebbronville/
    Freer/Three Rivers/George West/Aransas Pass/Portland/Robstown/
    Ingleside)
  **Cumulative TX session total: 190 cities** added across
  iter-128..140. All hit TX's 8.25% local-cap max per
  SalesTaxHandbook + Texas Comptroller. TX module was previously
  the next-most under-modeled big state behind CA; this is a
  major closure (engine now properly returns city rates for the
  190 most-populous TX incorporated places beyond the original
  49-city seed). Sampling ~5 cities per iter against
  SalesTaxHandbook (instead of all) caught no errors; the
  systemic "8.25% local cap" pattern is very reliable for TX.
- **iter-138..145 FL probe sweep**: 8 distinct FL data bugs
  surfaced and fixed across 6 iters, evenly split between cross-
  county misattribution and county-rate/missing-binding issues:
  - **Cross-county Census ZCTA fixes (5)**: Brooksville
    Citrus→Hernando (iter-138); Dade City Hernando→Pasco +
    Winter Garden Lake→Orange (iter-139); Chipley Bay→Washington
    (iter-143); White Springs Columbia→Hamilton (iter-145).
  - **County-rate updates (2)**: Okeechobee Co 1.0 → 1.5
    (iter-142, +School Capital Outlay surtax); Hamilton Co
    1.0 → 2.0 (iter-145, effective Jan 2025 per
    SalesTaxHandbook -- pushed past historic 1.5% surtax cap,
    test relaxed to 2.0% allowable in commit 19a3500).
  - **Missing-binding (0%-jurisdictions) fix (1)**: Paxton 32538
    was unbound -- Census ZCTA didn't ship that ZIP. Added
    Walton Co city anchor (iter-144). Same bug pattern as CA
    Mariposa 95338 from iter-120.
  FL_CITIES grew 30 → 37 (Brooksville, Dade City, Winter Garden,
  Chipley, Paxton, White Springs, Jasper).
  **Cross-county fix total this session: 14** (Auburn, Davis,
  Petaluma, Sonoma, Dinuba, Turlock, Watsonville, Rio Vista,
  Folsom + Brooksville, Dade City, Winter Garden, Chipley,
  White Springs).
- **iter-135 broad probe** (no fixes shipped): verified
  MN/WI/TN/GA/NC/VA/MO/CT/RI/MD/DE major + mid cities mostly
  correct. Marietta GA 6.0%, Charlottesville VA 5.3%, Topeka KS
  9.35%, Kansas City KS 9.125% all match SalesTaxHandbook exactly.

**Open follow-ups (overnight 2026-05-15 batch):**

- **Demo site coverage_warning rendering**: The API now returns
  ``coverage_warning`` for CO / LA / AL / HI (iter-189, v0.58.0).
  Demo site at ``demo.opensalestax.org`` does NOT render this field
  yet -- the Astro/JS calculator at
  ``ejosterberg/open-sales-tax-website`` needs a small update to:
  1. Read ``data.coverage_warning`` from the API response
  2. Render it as a yellow banner above the rate table when present
  Eric: a 5-line JS change in the calculator partial. Until that
  ships, CO addresses on the demo still look like 2.9% without
  context. The API contract is correct; only the demo presentation
  lags.

- **CA El Dorado County 1.0% over-collect** (real bug, audit
  required): Engine returns 8.25% for unincorporated El Dorado Co
  ZIPs (e.g. El Dorado Hills 95762); Avalara confirms 7.25%
  truth. Fix: drop El Dorado Co rate from 1.000 to 0.000 AND add
  Placerville as an explicit city entry (Placerville has its own
  ~0.5% Measure L) so it doesn't get under-collected by the same
  change. ~20 El Dorado Co ZIPs affected.

**Older open follow-ups discovered during iter-117..131:**
- ~~**NM TRD over-collect 0.25%**~~ **RESOLVED** in iter-172..175
  (overnight 2026-05-14..05-15) — all 17 tier-1+tier-2 NM cities
  re-verified against TRD. See overnight summary at top of file.
- ~~**IL Naperville mixed-rate-per-ZIP**~~ **RETRACTED 2026-05-15**:
  Avalara confirms 60540 combined is 7.75% (state 6.25 + RTA 0.75
  + Naperville city 0.75 + DuPage 0) — matching our engine
  exactly. SalesTaxHandbook's reported 8.75% was wrong. Same
  pattern as the iter-186 OK rate audit retraction. **Lesson**:
  cross-check Avalara before trusting SalesTaxHandbook for IL
  city rates too.
- **IA West Des Moines LOST dedup bug**: ZIP 50265 over-collects
  2.0% (Polk Co LOST + Union Co LOST + IA-district-98199 all
  emitted) and ZIP 50266 over 3.0% (adds IA-district-98049). Fix
  requires per-state cross-county LOST dedup similar to TN's
  IMPROVE Act fix in v0.44.
- **CA El Dorado County over-collect 0.5%**: El Dorado Hills
  95762 returns 8.25% vs SalesTaxHandbook 7.75%. Engine has El
  Dorado Co at 1.0% but actual is 0% (the 1.5% special is baked
  into CA's 7.25% baseline). Fix needs careful audit because
  Placerville/Cameron Park/Pollock Pines also bind to El Dorado.
- **CA San Pablo 94806 mixed-rate**: ZIP shared with Richmond;
  engine picks Richmond's 1.0% city tax instead of San Pablo's
  1.5%; 0.5% under-collect for ZIP 94806.
- **CA 90201 cluster**: Bell + Bell Gardens + Cudahy all share
  ZIP 90201; picker would pick one ambiguously. Not modeled.

Next release should bump significantly for these.

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
