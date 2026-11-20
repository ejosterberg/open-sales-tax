# Daily state sales tax audit — 2026-11-20 (day 20: PA + PR)

## TL;DR
- 2 states audited. **No general-rate drift.** All 22 live-engine probes match
  exactly: 14 PA and 8 PR.
- **1 finding needs code: PR back-to-school IVU-free days.** Hacienda's CC RI
  26-11 (2026-06-02) sets the days at 2026-07-17..18 (passed) and
  **2027-01-08..09 (upcoming)**. `puerto_rico.py` still says the 2026 holiday is
  "not yet confirmed", and a test pins "no holiday" for 2024–2030. The
  2026-11-01 audit missed this. Written up in
  `specs/findings/pr-back-to-school-ivu-holiday-2026-11.md` and chipped.

## PA
- Source: PA Department of Revenue, Sales, Use and Hotel Occupancy Tax page.
  `revenue.pa.gov/TaxTypes/SUT/Pages/default.aspx` now redirects (302) to
  `pa.gov/en/agencies/revenue/resources/tax-types-and-information/sales-use-and-hotel-occupancy-tax.html`.
  It states 6% state, 1% Allegheny County and 2% Philadelphia. That page was
  only partly readable by the fetch tool, so treat this as a summary-level
  confirmation. DOR newsroom items through "October 2026 Collections" contain
  no rate announcement.
- Last loaded on prod: self-seeded (`PA_COUNTY_RATE_PCT`); unchanged since the
  2026-11-01 audit. No PA module commits in the last 35 days.
- Latest available: n/a (non-SST; statutory rates, 72 P.S. § 7202).
- County rates: only Allegheny (1%) and Philadelphia (2%) levy one. Every
  non-Allegheny/Philadelphia ZIP probed returned the state rate only, with no
  stray county layer.
- Drift summary: none.
- Recommended action: none. Not reviewed this run: the DOR "Local Sales Tax
  Rules" document and the Tax Update newsletter.
- Details (prod `/v1/calculate`, ZIP+4 `-0001`, $100 general):

  | City | ZIP | Expected | Actual (engine) | Delta |
  |---|---|---:|---:|---:|
  | Philadelphia | 19102 | 8.000 | 8.000 | 0 |
  | Philadelphia (Center City) | 19103 | 8.000 | 8.000 | 0 |
  | Pittsburgh | 15222 | 7.000 | 7.000 | 0 |
  | Gibsonia (Allegheny) | 15044 | 7.000 | 7.000 | 0 |
  | Bethel Park | 15102 | 7.000 | 7.000 | 0 |
  | Monroeville | 15146 | 7.000 | 7.000 | 0 |
  | McKeesport | 15132 | 7.000 | 7.000 | 0 |
  | Allentown | 18101 | 6.000 | 6.000 | 0 |
  | Erie | 16501 | 6.000 | 6.000 | 0 |
  | Reading | 19601 | 6.000 | 6.000 | 0 |
  | Scranton | 18503 | 6.000 | 6.000 | 0 |
  | Lancaster | 17602 | 6.000 | 6.000 | 0 |
  | Lancaster (edge) | 17601 | 6.000 | 6.000 | 0 |
  | Harrisburg | 17101 | 6.000 | 6.000 | 0 |

## PR
- Source: Departamento de Hacienda, `hacienda.pr.gov`: the IVU page, the press
  room (first page only of 983 items), CC RI 26-11 and CC RI 26-13.
- Last loaded on prod: self-seeded (`PR-SST-V0.32-MUNICIPAL`, 2026-05-05).
- Latest available: n/a.
- County rates: n/a. The 1% municipal IVU is uniform, confirmed by CC RI 26-13
  ("IVU Municipal de uno (1) por ciento"). The 10.5% state component was not
  restated on any page read this run. No change to it was found, and it stays
  as last confirmed (13 L.P.R.A. § 32021).
- Drift summary: general rate none. **Holiday data missing (see TL;DR).**
- Also noted, not drift: from July/August 2026, 73 municipios file the
  municipal IVU through SURI (Ley 72-2025). The rate is unchanged.
- Recommended action: encode the 2026-27 back-to-school windows before
  2027-01-08 (chip).
- Details:

  | Municipio | ZIP | Expected | Actual (engine) | Delta |
  |---|---|---:|---:|---:|
  | San Juan | 00901 | 11.500 | 11.500 | 0 |
  | Adjuntas | 00601 | 11.500 | 11.500 | 0 |
  | Bayamón | 00956 | 11.500 | 11.500 | 0 |
  | Carolina | 00979 | 11.500 | 11.500 | 0 |
  | Ponce | 00731 | 11.500 | 11.500 | 0 |
  | Caguas | 00725 | 11.500 | 11.500 | 0 |
  | Arecibo | 00612 | 11.500 | 11.500 | 0 |
  | Mayagüez | 00680 | 11.500 | 11.500 | 0 |

## Actions
- No code or pin changes. Of the two windows, the July 2026 one was already
  missed. The January 2027 one is still preventable.
- Finding file written and chipped. `specs/handoff.md` open follow-ups updated.
- Uncommitted NY changes (`new_york.py`, `ny_data.py`) were already in the
  working tree before this run. They were not touched or committed.
