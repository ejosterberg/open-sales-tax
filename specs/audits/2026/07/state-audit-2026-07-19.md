# Daily state sales tax audit — 2026-07-19 (day 19: OK + OR)

## TL;DR
- 2 jurisdictions audited. **0 real-world rate changes** requiring a data
  fix — the live engine matches the DOR/Avalara-published rate for **every**
  OK tier-1 city and returns 0% for every OR ZIP.
- **2 stale/incorrect DOR-validation pins corrected** (Bixby, Edmond) — both
  cases the *engine* was already right and the *pin* was stale (Bixby) or
  based on a false premise (Edmond). Committed directly (liveapi grid; not in
  default CI).
- **1 SST refresh chipped**: OK prod is a full quarter behind (Q2, now expired
  past Jul-1) — latest `OKR2026Q3MAY29` / `OKB2026Q3JUN10`.
- **2 engine/labelling issues written to a finding + chipped** (Bixby dual
  city-code / missing friendly name; Edmond Logan-County side drops the city
  tax). Neither is rate drift.

---

## OK (Oklahoma) — SST member

- **Source:** OK is an SST member; the engine loads its per-jurisdiction
  rates from the SST quarterly rate file. Cross-checked live engine
  (`https://api.opensalestax.org/v1/calculate`, browser UA) against Avalara
  per-city breakdowns (per the standing OK audit lesson: cross-check Avalara,
  don't trust SalesTaxHandbook alone).
- **Last loaded on prod:** `OKR2026Q2FEB17` (rate) / `OKB2026Q2APR01`
  (boundary) — Q2 2026.
- **Latest available (SST Governing Board):** `OKR2026Q3MAY29` (posted
  2026-05-29, eff Jul 1 2026) / `OKB2026Q3JUN10`.
- **Drift summary:** No real-world drift. All 14 tier-1 cities match the live
  engine and the DOR/Avalara-published combined rate. Two pins were stale/wrong
  and were corrected to match reality (engine was already correct).
- **Recommended action:** (1) chip the Q3 SST refresh (currency hygiene —
  prod is on the expired Q2 file); (2) chip the Bixby/Edmond labelling +
  Logan-side engine investigation (finding written). No data fix needed for
  correctness — the engine is current.

### Tier-1 city cross-check (live engine vs Avalara/OK DOR)

| City | ZIP(+4) | Expected (DOR/Avalara) | Engine | Match |
|---|---|---|---|---|
| Tulsa | 74103+3804 | 8.517 | 8.517 | ✓ |
| Oklahoma City | 73102+6107 | 8.625 | 8.625 | ✓ |
| Norman | 73069+6107 | 8.750 | 8.750 | ✓ |
| Moore | 73160+2306 | 8.500 | 8.500 | ✓ |
| Broken Arrow | 74012+2417 | 8.417 | 8.417 | ✓ |
| Lawton | 73505+1306 | 9.000 | 9.000 | ✓ |
| Bixby | 74008 | **8.917** (was pinned 8.417) | 8.917 | ✓ (pin fixed) |
| Sand Springs | 74063 | 8.917 | 8.917 | ✓ |
| Sapulpa | 74066 | 9.667 | 9.667 | ✓ |
| Glenpool | 74033 | 9.967 | 9.967 | ✓ |
| Edmond | 73034 | **8.250** (was pinned 9.000) | 8.250 | ✓ (pin fixed) |
| Stillwater | 74074 | 9.313 | 9.313 | ✓ |
| Enid | 73701 | 9.100 | 9.100 | ✓ |
| Shawnee | 74801 | 9.995 | 9.995 | ✓ |

### Bixby — pin was stale (engine correct)
Bixby raised its **city** rate **3.55% → 4.05%** (combined **8.417 → 8.917**),
already reflected in the engine (the Q2 SST file carries 4.05% under city code
`06400`). Verified vs Avalara (Bixby city 4.05%, combined 8.917%). The
DOR-validation pin (8.417) was stale → **bumped to 8.917**. The engine labels
the 4.05% authority as the unnamed placeholder `OK-city-06400` while
`ok_names` maps a *different* code (`37800`) to "Bixby" at the OLD 3.55% — a
friendly-name/dual-code issue (finding + chip; **not** drift).

### Edmond — pin premise was false (engine correct on the dominant side)
The old pin expected **9.000** on the claim "+4 1234 is in Logan County".
`+4 1234` of 73034 is actually the **Oklahoma-County** side of Edmond
(Oklahoma County levies 0% county tax) → state 4.5% + Edmond 3.75% =
**8.250%**, which matches Avalara's published Edmond rate and the engine. Pin
**corrected to 8.250**. A genuine engine issue *does* exist on the real
Logan-County +4 ranges (e.g. 0022/0600 return **5.25%** — Logan 0.75% + state,
**dropping the Edmond city 3.75%**, vs an expected 9.0% if those ranges are
inside Edmond city limits). Written to the finding + chipped; **not** masked
by re-pinning a Logan +4.

---

## OR (Oregon) — no statewide sales tax

- **Source:** Oregon levies **no statewide sales tax** and no local *general*
  sales taxes (only narrow meals / lodging / motor-vehicle-rental excises,
  documented as a Phase-1 deferral in `src/opensalestax/states/no_tax.py`).
  Handled by the generic `NoTaxState` instance registered for OR.
- **Last loaded on prod:** n/a (no rate/boundary files — `NoTaxState` returns
  empty iterators).
- **Latest available:** n/a.
- **Drift summary:** None. The live engine returns **0.000%** with zero
  jurisdictions for every OR ZIP probed.
- **Recommended action:** None.

### Spot-check (live engine)

| City | ZIP | Engine rate | Jurisdictions |
|---|---|---|---|
| Portland | 97201 | 0 | 0 |
| Salem | 97301 | 0 | 0 |
| Eugene | 97401 | 0 | 0 |
| Bend | 97701 | 0 | 0 |
| Pendleton | 97801 | 0 | 0 |
| Gresham | 97030 | 0 | 0 |

---

## Actions taken
1. **Committed (mechanical, liveapi grid):** Bixby pin 8.417→8.917; Edmond pin
   9.000→8.250, each with an explanatory comment + finding reference.
2. **Finding written:** `specs/findings/ok-bixby-dualcode-edmond-logan-2026-07.md`
   (Bixby dual code / missing friendly name; Edmond Logan-side city-drop).
3. **Chips (for Eric's review):**
   - Refresh OK SST quarterly to `OKR2026Q3MAY29` / `OKB2026Q3JUN10`.
   - Investigate the OK Bixby/Edmond labelling + Logan-side engine issue.
4. **handoff.md:** open follow-up added.

## Method notes
- Live engine: `POST /v1/calculate` with
  `{"address":{"zip5","zip4"},"line_items":[{"amount":"100.00","category":"general"}]}`,
  browser User-Agent (Cloudflare 403s bare python-urllib). Effective rate read
  from `lines[0].rate_pct`; jurisdiction breakdown from `lines[0].jurisdictions`.
- Prod DB probed read-only for authority/rate/boundary bindings
  (`boundaries` ⋈ `tax_authorities` ⋈ `rates`).
- Rate ground truth cross-checked against Avalara per-city pages (OK audit
  lesson: avoid SalesTaxHandbook-only).
