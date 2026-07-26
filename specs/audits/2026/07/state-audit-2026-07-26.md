# Daily state sales tax audit — 2026-07-26 (day 26: WV + WY)

## TL;DR
- 2 jurisdictions audited (both SST member states).
- **0 rate changes found in either state's top cities — the live
  engine matches the authoritative sources exactly.** No code/test
  updates required.
- **Both states are still running stale SST quarterly files on prod
  (unchanged since the 2026-06-26 audit — the Q3 refresh chips were
  never applied):**
  - WV is **two quarters behind** (prod = 2026 Q1; latest = **Q3**).
  - WY is **one quarter behind** (prod = 2026 Q2; latest = **Q3**).
- **No Q4 2026 SST files exist yet** — Q3 2026 remains the newest
  published rate/boundary set for both states (verified today against
  the SST Governing Board rate + boundary directory listings).
- Both Q3-refresh chips **re-opened** for Eric to apply (SST files are
  not auto-pulled per audit policy). Same pattern as the SD/TN
  2026-07-22 re-chip.
- ⚠️ **Availability incident (see "Operational note"):** the entire
  prod stack (`open-sales-tax-api-1` + `open-sales-tax-postgres-1`) was
  **down for ~2 days** — both containers `Exited (0)`, and the public
  API `https://api.opensalestax.org` was returning **HTTP 502**. This
  run brought the stack back up. Root cause + a `restart:` policy fix
  are chipped for Eric.

## WV (West Virginia) — SST member
- Source: SST Governing Board rate/boundary directory listings
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/ ,
  .../Boundary/); cross-checked against WV Tax Division "Municipalities
  Imposing Sales and Use Taxes" (6% state + 1% municipal model).
- Last loaded on prod: `WVR2026Q1AUG14.csv` / `WVB2026Q1SEP02.csv`
  (unchanged since the 2026-06-26 audit).
- Latest available from SST: **`WVR2026Q3FEB25.csv` /
  `WVB2026Q3APR29.csv`** — two quarters newer than prod. **No Q4 file
  is posted yet** (confirmed today).
- Drift summary: **none in the engine's 8 probed tier-1 cities** — all
  return the correct 6% state + 1% municipal = 7.000%. The stale file
  does NOT cause drift in existing cities (WV's 6% state rate is fixed
  and the major municipalities' 1% rates are unchanged); it causes
  *missing coverage* of municipalities that newly adopted the tax in
  2026.
- Recommended action: **REFRESH NEEDED** — load WV Q3 SST files on prod
  (re-chipped). Picks up the new 2026 municipalities.
- Details (live engine, `GET /v1/rates`):
  | City (ZIP) | Expected (WV DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Charleston (25301)  | 7.000% | 7.000% | 0.000 |
  | Huntington (25701)  | 7.000% | 7.000% | 0.000 |
  | Morgantown (26505)  | 7.000% | 7.000% | 0.000 |
  | Parkersburg (26101) | 7.000% | 7.000% | 0.000 |
  | Wheeling (26003)    | 7.000% | 7.000% | 0.000 |
  | Beckley (25801)     | 7.000% | 7.000% | 0.000 |
  | Clarksburg (26301)  | 7.000% | 7.000% | 0.000 |
  | Martinsburg (25401) | 7.000% | 7.000% | 0.000 |
- New 2026 WV municipalities that will surface after the Q3 refresh
  (state 6% + 1% municipal = 7%): Bramwell (Mercer), Glenville
  (Gilmer), Hinton (Summers), Marlinton (Pocahontas), Pineville
  (Wyoming Co), Anmoore (Harrison), Bath/Berkeley Springs (Morgan).
  Plus rate increases: Richwood, Westover. (Carried from the
  2026-06-26 audit — still pending the Q3 load.)

## WY (Wyoming) — SST member
- Source: SST Governing Board rate/boundary directory listings;
  cross-checked against WY Excise Tax Division rate charts (state 4% +
  county local-option stacks).
- Last loaded on prod: `WYR2026Q2APR1.csv` / `WYB2026Q2FEB23.csv`
  (unchanged since the 2026-06-26 audit).
- Latest available from SST: **`WYR2026Q3JUN2.CSV` /
  `WYB2026Q3MAY18.CSV`** — one quarter newer than prod. **No Q4 file is
  posted yet** (confirmed today).
- Drift summary: **none.** All 7 probed county/city stacks match the
  authoritative WY chart. No county rate change took effect at the Q3
  (July 1 2026) boundary for the major counties.
- Recommended action: **REFRESH NEEDED** — load WY Q3 SST files on prod
  (re-chipped) to stay current and catch any smaller-jurisdiction
  specific-purpose-tax sunsets/renewals the top-7 probe doesn't cover.
- Details (live engine, `GET /v1/rates`):
  | City (county, ZIP) | Expected (WY DOR/handbook) | Actual (engine) | Delta |
  |---|---|---|---|
  | Cheyenne (Laramie, 82001)     | 5.000% | 5.000% | 0.000 |
  | Casper (Natrona, 82601)       | 6.000% | 6.000% | 0.000 |
  | Jackson (Teton, 83001)        | 7.000% | 7.000% | 0.000 |
  | Sheridan (Sheridan, 82801)    | 6.000% | 6.000% | 0.000 |
  | Gillette (Campbell, 82716)    | 5.000% | 5.000% | 0.000 |
  | Laramie city (Albany, 82070)  | 6.000% | 6.000% | 0.000 |
  | Rock Springs (Sweetwater, 82901) | 6.000% | 6.000% | 0.000 |
- Minor coverage note (not drift, carried from 2026-06-26): Teton
  Village (83025) / Alta (83414) carry WY's highest combined rate (9%)
  via a resort-district overlay on Teton County's 3%. Jackson proper
  (83001) is correctly 7%. The resort-district-ZIP resolution is a
  long-standing coverage question, not a Q3 rate change.

## Operational note — prod stack was down ~2 days (availability incident)
- When this audit started, both prod containers were stopped:
  - `open-sales-tax-api-1` — `Exited (0)` ~2 days ago
  - `open-sales-tax-postgres-1` — `Exited (0)` ~2 days ago
  - Public API `https://api.opensalestax.org/v1/*` was returning
    **HTTP 502** (Cloudflare origin down).
- Both exited with status 0 (clean shutdown, not a crash-loop), and
  neither restarted on its own — indicating the compose services do
  **not** carry a `restart: unless-stopped` / `restart: always` policy,
  so a host reboot or `docker compose down` leaves prod dark until
  someone manually brings it back.
- Recovery performed by this run (needed the live engine for the
  cross-check): `docker compose up -d postgres` then
  `docker restart open-sales-tax-api-1`. Verified healthy
  (`/v1/rates?zip5=82001` → 200 with full jurisdiction breakdown)
  before probing.
- **Chipped** for Eric: add a restart policy to the compose services so
  the stack self-heals across reboots, and confirm what took it down
  ~2 days ago (host reboot? OOM? manual `down`?). This is the real
  reliability finding of the day — not a rate issue, but higher-impact.

## Actions taken
- No code changes (no rate drift in either jurisdiction's covered
  cities).
- Recovered the down prod stack (see Operational note).
- 3 background-task chips opened:
  1. Refresh WV SST quarterly Q1 → Q3 (`WVR2026Q3FEB25` /
     `WVB2026Q3APR29`).
  2. Refresh WY SST quarterly Q2 → Q3 (`WYR2026Q3JUN2` /
     `WYB2026Q3MAY18`).
  3. Add a `restart:` policy to the prod compose services + root-cause
     the ~2-day outage.
- `specs/handoff.md` open follow-ups updated (WV/WY Q3 refresh still
  pending; prod-outage note added).
- Report committed + pushed only after the mandatory quality-gate +
  SonarQube scan pass with zero new BLOCKER/CRITICAL, then CI watched
  green.
