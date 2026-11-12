# Daily state sales tax audit — 2026-11-12 (day 12: MI + MN)

## TL;DR
- 2 states audited (both SST members). **0 live rate drift.** 24 of 24
  pinned MI/MN rows in `tests/integration/test_sst_dor_validation.py`
  match the live engine exactly.
- MN was refreshed on prod since the last audit: `MN-SST-2026Q4AUG18`
  loaded 2026-11-08 (Q2 label purged, no double-stacking). Upstream SST has
  no newer MN file yet. MI pin equals upstream (perpetual 2023 file).
- The 6-row `test_mn_district_label_correct` xfail now xpasses in full
  (MN + the IA/NC parallels). Per the marker's own instruction, the xfail
  marker is **removed** in this commit.
- **One upcoming change to watch:** MN DOR lists **Grand Rapids** local
  sales tax **ending 2026-12-31**. Prod (correctly, for today) still
  charges 0.5% city on 55744. The 2027Q1 SST file that removes it is not
  posted yet — next MN refresh must happen on/just after 2027-01-01.

## MI
- Source: SST Governing Board, `streamlinedsalestax.org/ratesandboundry/{Rates,Boundary}/`
- Last loaded on prod: `MI-SST-2023Q1DEC22` (fetched 2026-05-04); cached
  `MIR2023Q1DEC22.csv` / `MIB2023Q1DEC15.csv`
- Latest available: `MIR2023Q1DEC22.csv` / `MIB2023Q1DEC15.csv` — **pin = upstream**
- Drift summary: none. 6.0% flat, constitutionally fixed (Mich. Const. Art. IX §8); no local sales tax.
- Recommended action: none.
- Details:

  | City | ZIP+4 | Expected | Actual (engine) | Delta |
  |---|---|---:|---:|---:|
  | Ann Arbor | 48104-0001 | 6.000 | 6.000 | 0 |
  | Detroit | 48201-0001 | 6.000 | 6.000 | 0 |
  | Detroit | 48226-3614 | 6.000 | 6.000 | 0 |
  | Flint | 48502-0001 | 6.000 | 6.000 | 0 |
  | Grand Rapids | 49503-0001 | 6.000 | 6.000 | 0 |
  | Lansing | 48933-0001 | 6.000 | 6.000 | 0 |

## MN
- Source: SST Governing Board (rates/boundaries); MN DOR
  `revenue.state.mn.us/local-sales-tax-notices` (page last updated 2026-10-22)
  for announced starts/ends. SST quarterly files carry county + district
  rates, so the county check is covered by the SST pin comparison.
- Last loaded on prod: `MN-SST-2026Q4AUG18` (fetched **2026-11-08**);
  cached `MNR2026Q4AUG18.zip` / `MNB2026Q4AUG18.zip` (old Q2 zips still in
  the cache dir, harmless).
- Latest available: `MNR2026Q4AUG18.zip` / `MNB2026Q4AUG18.zip` — **pin = upstream**
- Drift summary: none on 24 pinned rows; the 2026-09-30 endings are honoured.
- Recommended action: refresh MN to the 2027Q1 SST file once posted, effective
  2027-01-01 (Grand Rapids ending). Flagged in handoff; no chip today because
  the file does not exist yet.
- Details (pinned rows):

  | City | ZIP+4 | Expected | Actual (engine) | Delta |
  |---|---|---:|---:|---:|
  | Bloomington | 55425-1234 | 9.025 | 9.025 | 0 |
  | Duluth | 55802-0001 | 8.875 | 8.875 | 0 |
  | Eagan | 55121-1234 | 8.125 | 8.125 | 0 |
  | Eden Prairie | 55344-0001 | 9.025 | 9.025 | 0 |
  | Edina | 55435-0001 | 9.025 | 9.025 | 0 |
  | Hopkins | 55305-1234 | 8.525 | 8.525 | 0 |
  | Lake Wilson (Murray Co) | 56144-0001 | 6.875 | 6.875 | 0 |
  | Mankato | 56001-0001 | 7.875 | 7.875 | 0 |
  | Maple Grove | 55369-0001 | 9.025 | 9.025 | 0 |
  | Minneapolis | 55401-1024 | 9.025 | 9.025 | 0 |
  | Minnetonka | 55345-0001 | 8.525 | 8.525 | 0 |
  | Pipestone | 56164-0001 | 6.875 | 6.875 | 0 |
  | Plymouth | 55441-0001 | 8.525 | 8.525 | 0 |
  | Rochester | 55901-0001 | 8.125 | 8.125 | 0 |
  | St Louis Park | 55416-0001 | 9.025 | 9.025 | 0 |
  | St. Louis Park | 55416-1234 | 8.525 | 8.525 | 0 |
  | St Paul | 55102-0001 | 9.875 | 9.875 | 0 |
  | St. Paul | 55101-1014 | 9.875 | 9.875 | 0 |

- MN DOR notices with effect on/after 2026-10-01 (primary source):
  - **Grand Rapids — End, 2026-12-31** (`/sites/default/files/2026-10/grand-rapids-ending-general-notice.pdf`).
    Tax type is not stated in the table; read as the general local sales
    tax from the filename and because Grand Rapids Lodging is a separate
    listing. The notice PDF itself was not parsed this run.
  - Northfield Lodging — Start, 2026-10-01 (lodging; out of scope).
  - No 2027-01-01 starts or changes listed.
- Spot checks on recent endings (verify the Q4 reload took effect):

  | Place | ZIP | Engine | Components | Note |
  |---|---|---:|---|---|
  | Albert Lea (ended 2026-09-30) | 56007 | 7.375 | state 6.875 + Freeborn Co 0.5 | city tax gone ✓ |
  | Blackduck (ended 2026-09-30) | 56630 | 7.375 | state 6.875 + Beltrami Co 0.5 | city tax gone ✓ |
  | Grand Rapids (ends 2026-12-31) | 55744 | 8.375 | state 6.875 + city 0.5 + Itasca Co 1.0 | correct until 12-31 |

- Cosmetic: Grand Rapids' city row is labelled `MN-city-25118` (raw code,
  no friendly name). Rate-neutral; it disappears after the 2027Q1 reload.

## Test change in this commit
- `test_mn_district_label_correct`: all 6 rows XPASS against live (run
  2026-11-12, `pytest -k test_mn_district_label_correct`: 6 xpassed). The
  xfail marker said "When all 6 rows xpass, remove the xfail marker" —
  done. The grid name `MN_DISTRICT_LABEL_GRID` is kept (rename is
  cosmetic; left for a later cleanup).

## Status
**CLEAN — one dated follow-up (MN 2027Q1 refresh for Grand Rapids end).**
