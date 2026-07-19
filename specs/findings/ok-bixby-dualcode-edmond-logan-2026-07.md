# OK — Bixby dual city-code + Edmond Logan-County city-drop (daily-audit 2026-07-19)

**Status:** OPEN — needs human review. Neither is real-world rate drift
(the engine returns the DOR-correct rate for the *dominant* portion of both
ZIPs); both are data-labelling / +4-resolution issues surfaced during the
first OK daily audit.

**Audit:** `specs/audits/2026/07/state-audit-2026-07-19.md`
**Engine data on prod:** `OKR2026Q2FEB17` / `OKB2026Q2APR01` (Q2 2026; now
one quarter stale — Q3 refresh separately chipped).

---

## 1. Bixby (ZIP 74008) — dual city code, one stale, one unlabelled

### What the engine does
`POST /v1/calculate {zip5:74008}` → **8.917%**
= Oklahoma 4.5% + Tulsa County 0.367% + **`OK-city-06400` 4.05%**.

This is **correct** — Avalara confirms Bixby city = 4.05%, combined 8.917%.
Bixby raised its city sales tax from **3.55% → 4.05%** at some point before
the Q2-2026 SST file (the file already carries 4.05%). The DOR-validation
pin was stale (8.417%); corrected to 8.917% in
`tests/integration/test_sst_dor_validation.py` on 2026-07-19.

### The labelling problem
The prod DB has **two** Bixby-area city authorities bound to ZIP 74008:

| DB name | Rate(s) | Bound ZIPs |
|---|---|---|
| `Bixby` (from `ok_names` code **37800**) | 3.55% (+3.00% use) | 74008, 74033, 74037, 74066, 74132 |
| `OK-city-06400` (unlabelled placeholder) | 4.05% (+3.50 +3.00) | 74008, 74011, 74133 |

`src/opensalestax/states/ok_names.py` maps **`37800` → "Bixby"** at the OLD
3.55% rate, while the code carrying the CURRENT 4.05% rate (**`06400`**) has
**no friendly name**. So the engine returns the correct number but labels the
authority `OK-city-06400` instead of "Bixby", and the `ok_names` "Bixby"
entry points at the superseded 3.55% code.

Hypotheses (need confirmation against an authoritative OTC↔code table):
- **`06400` is Bixby's current OTC code**; `37800`→"Bixby" in `ok_names` is a
  wrong/obsolete mapping (Bixby recoded, or 37800 is a different jurisdiction).
- Or Bixby appears under two codes in the SST file (old + new) and the engine
  correctly prefers the 4.05% one at 74008.

### Recommended action (human/next-maintainer)
1. Confirm what OTC/SST codes 06400 and 37800 actually are (OK Tax Commission
   rate/code listing, or the OK SST file's own jurisdiction table).
2. If 06400 is Bixby: add `"06400": "Bixby"` to `ok_names.py` and remove or
   correct the `37800` entry (root-cause the mislabel — see the "wrong
   friendly-name mapping" pattern already fixed for MN/IA/NC, handoff
   iter-220/221).
3. Do **not** treat this as drift — no rate is wrong; only the label is.

---

## 2. Edmond (ZIP 73034) — Logan-County sliver drops the Edmond city tax

Edmond straddles **Oklahoma County** (0% county tax) and **Logan County**
(0.75% county tax).

| Query | Engine | Jurisdictions returned |
|---|---|---|
| `73034` (bare) | **8.250%** | Oklahoma County 0% + Edmond 3.75% + state 4.5% |
| `73034+1234` | 8.250% | (same — 1234 is the Oklahoma-County side) |
| `73034+0022` | **5.250%** | **Logan County 0.75% + state 4.5% — NO Edmond city** |
| `73034+0600` | 5.250% | (same) |

- The **8.250%** answer is **correct** for the Oklahoma-County side and
  matches Avalara's published Edmond rate (min combined 8.25%). The old pin
  (9.000%, "+4 1234 is in Logan") was based on a **false premise** — 1234 is
  Oklahoma County, not Logan. Pin corrected to 8.250% on 2026-07-19.
- The **5.250%** answer on the real Logan-County +4 ranges is **suspect**: it
  binds Logan County but **drops the Edmond city 3.75%**. If those +4 ranges
  are inside Edmond *city* limits (Edmond-in-Logan), the correct rate is
  **9.0%** (4.5 + 3.75 + 0.75) and the engine is under-collecting by 3.75%.
  If those ranges are *unincorporated* Logan County, 5.25% is correct.

This is the same class of multi-jurisdiction +4 mis-resolution seen in the
UT `-0001` county-drop (handoff open item) — a city binding lost when a ZIP's
+4 spans two counties.

### Recommended action (human/next-maintainer)
1. Determine whether 73034 +4 ranges 0022-0025 / 0600-0613 / … are inside
   Edmond city limits (OK Tax Commission address lookup on a street in those
   ranges, or the OK SST boundary file's city binding for those +4s).
2. If Edmond-in-Logan: fix the engine/loader so the Edmond city authority is
   retained alongside Logan County on those +4s (expected 9.0%). Add a
   liveapi pin at a confirmed Logan-side Edmond +4 once it returns 9.0%.
3. If unincorporated Logan: 5.25% is correct; document and add a pin.
4. Per handoff discipline: do **not** paper over by re-pinning a passing +4.

---

## Not affected
All other 12 OK tier-1 cities (Tulsa, Oklahoma City, Norman, Moore, Broken
Arrow, Lawton, Sand Springs, Sapulpa, Glenpool, Stillwater, Enid, Shawnee)
match the live engine and Avalara/OK DOR exactly. Oregon (audited same day)
is fully clean — no statewide or local general sales tax, engine returns 0%
for every OR ZIP.
