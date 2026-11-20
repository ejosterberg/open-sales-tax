# Daily state sales tax audit — 2026-11-19 (day 19: OK + OR)

## TL;DR
- 2 states audited. **0 live rate drift; 0 code/test updates needed.**
- OK: the Q2 → Q4 SST refresh flagged on 2026-11-01 has been applied
  (`OK-SST-2026Q4AUG17` loaded 2026-11-08, single SST label, no double-stacking).
  Prod now equals upstream. All 17 pinned OK rows match the live engine exactly.
- The row diff the 2026-11-01 audit deferred (Q4 vs Q2 rate file) was done
  this run: **15 local rate changes** (11 effective 2026-07-01, 4 effective
  2026-10-01). None touch a pinned city. All 12 city changes were probed on
  the live engine and apply the new rate with no stacking of the old row.
- OR: no sales tax; engine returns 0.000% on both pinned Portland rows.

## OK
- Source: SST Governing Board listings
  `streamlinedsalestax.org/ratesandboundry/Rates/` and `/Boundary/`
  (the `/state-tax-files` index returned HTTP 404 this run — use the two
  listing URLs directly).
- Last loaded on prod: `OK-SST-2026Q4AUG17` (fetched 2026-11-08); cached
  `OKR2026Q4AUG17.zip` / `OKB2026Q4AUG28.zip` (Q2 zips still in the cache, harmless).
- Latest available: `OKR2026Q4AUG17.zip` / `OKB2026Q4AUG28.zip` — **pin = upstream**.
  No 2027Q1 OK file posted yet.
- County rates: carried in the SST rate file; no county rows changed Q2 → Q4.
- Drift summary: none.
- Recommended action: none. Next check: 2027Q1 file once posted.
- Pinned rows (`tests/integration/test_sst_dor_validation.py`):

  | City | ZIP+4 | Expected | Actual (engine) | Delta |
  |---|---|---:|---:|---:|
  | Tulsa | 74103-3804 | 8.517 | 8.517 | 0 |
  | Oklahoma City | 73102-6107 | 8.625 | 8.625 | 0 |
  | Norman | 73069-6107 | 8.750 | 8.750 | 0 |
  | Moore | 73160-2306 | 8.500 | 8.500 | 0 |
  | Broken Arrow | 74012-2417 | 8.417 | 8.417 | 0 |
  | Broken Arrow | 74012-0001 | 8.417 | 8.417 | 0 |
  | Lawton | 73505-1306 | 9.000 | 9.000 | 0 |
  | Bixby | 74008-1234 | 8.917 | 8.917 | 0 |
  | Sand Springs | 74063-1234 | 8.917 | 8.917 | 0 |
  | Sapulpa | 74066-1234 | 9.667 | 9.667 | 0 |
  | Glenpool | 74033-1234 | 9.967 | 9.967 | 0 |
  | Edmond | 73034-1234 | 8.250 | 8.250 | 0 |
  | Stillwater | 74074-1234 | 9.313 | 9.313 | 0 |
  | Enid | 73701-1234 | 9.100 | 9.100 | 0 |
  | Shawnee | 74801-1234 | 9.995 | 9.995 | 0 |
  | Newcastle | 73072-1015 | 9.000 | 9.000 | 0 |
  | Bartlesville | 74003-0001 | 8.900 | 8.900 | 0 |

- Wholesale diff `OKR2026Q2FEB17` → `OKR2026Q4AUG17` (full-row set diff; codes
  are FIPS Place codes, unnamed in `ok_names.py`). Engine probe = combined
  rate at one bound ZIP+4, city component shown in the breakdown:

  | Authority | Old | New | Effective | Probe ZIP+4 | Engine combined (city part) |
  |---|---:|---:|---|---|---|
  | city 12000 | 3.000 | 3.500 | 2026-07-01 | 73726-0002 | 10.000 (3.500) |
  | city 15250 | 2.000 (0 on two cols) | 2.000 all cols | 2026-07-01 | 74331-5557 | 8.200 (2.000) |
  | city 15800 | 3.000 | 4.000 | 2026-07-01 | 74538-0001 | 10.500 (4.000) |
  | city 35850 | 3.500 | 3.000 | 2026-07-01 | 74035-0001 | 8.750 (3.000) |
  | city 41700 | 3.250 | 3.000 | 2026-10-01 | 73848-0001 | 9.500 (3.000) |
  | city 55450 | 1.000 | 3.000 | 2026-07-01 | 73560-0001 | 8.625 (3.000) |
  | city 62550 | 3.000 | 3.750 | 2026-07-01 | 74563-0001 | 9.500 (3.750) |
  | city 64950 | 4.000 | 5.000 | 2026-10-01 | 74361-7444 | 10.875 (5.000) |
  | city 66275 | — (new) | 4.000 | 2026-10-01 | 73072-0015 | 9.000 (4.000) |
  | city 68600 | 2.000 | 3.500 | 2026-07-01 | 74072-0001 | 10.000 (3.500) |
  | city 76500 | 3.000 | 4.500 | 2026-07-01 | 73129-3640 | 9.000 (4.500) |
  | city 79900 | 4.000 | 3.500 | 2026-10-01 | 74881-4602 | 9.000 (3.500) |
  | district 98243 | 4.500 | 1.500 | 2026-07-01 | (no ZIP+4 binding found) | loaded in DB at 1.500 |
  | district 98364 | 3.000 | 4.125 | 2026-07-01 | (no ZIP+4 binding found) | loaded in DB at 4.125 |
  | district 98373 | 3.000 | 4.125 | 2026-07-01 | (no ZIP+4 binding found) | loaded in DB at 4.125 |

  The three districts have rate rows in the DB but no ZIP+4-ranged boundary,
  so they could not be probed this way. Not treated as drift (they are
  outside the pin set, and the Q2 data behaved the same way).

## OR
- Source: no statewide or local general sales tax (encoded as `NoTaxState`
  in `src/opensalestax/states/no_tax.py`). Unchanged since the 2026-11-01 audit.
- Last loaded on prod: `OR-ZCTA-2020` only (boundaries); nothing to refresh.
- Latest available: n/a.
- Drift summary: none.
- Recommended action: none.
- Details:

  | City | ZIP+4 | Expected | Actual (engine) | Delta |
  |---|---|---:|---:|---:|
  | Portland | 97201-0001 | 0.000 | 0.000 | 0 |
  | Portland | 97204-0001 | 0.000 | 0.000 | 0 |

## Actions
- No code or pin changes. No chips. `specs/handoff.md` not updated (no drift).
- Closes the 2026-11-01 OK follow-up ("diff Q4 vs Q2 after reload").
