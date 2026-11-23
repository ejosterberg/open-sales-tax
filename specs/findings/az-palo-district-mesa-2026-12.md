# AZ — new "Palo District" special taxing district in Mesa (effective 2026-12-01)

**Found:** all-state audit 2026-11-22.
**Status:** OPEN — not encoded; needs a design decision.

## What the source says

AZ DOR `TPT_RATETABLE_12012026.pdf` ("Effective December 1, 2026
(Revised)"), first page, "Rate Change(s) Effective December 1, 2026":
Palo District, Camp Verde, Winslow. The Palo District is new in the
December table (absent from `TPT_RATETABLE_11012026.pdf`).

Its own table (page 4 of the PDF) lists, among others:

| Business | Code | Rate |
|---|---|---|
| Retail | 017 | 7.30% |
| Restaurants and Bars | 011 | 9.30% |
| Amusements | 012 | 15.30% |
| Marketplace Facilitated or Remote Retail | 605 | 7.30% |

Boundary (DOR wording, summarized): roughly South Longmore on the west,
West Southern Ave. on the north, South Alma School Rd. on the east and
the Superstition Freeway (US 60) on the south, excluding outparcels
fronting Southern, Longmore and Alma School (with some exceptions on
Alma School). DOR adds: "When reporting activity in this region, City of
Mesa rate will also apply."

## Open questions

1. Whether the 7.30% retail figure is the district's combined state +
   county + district rate (5.6% + Maricopa 0.7% + 1.0% district) with
   Mesa's 2.0% added on top, or something else. Confirm from the DOR
   table notes or Mesa's ordinance before encoding.
2. The district is parcel-level inside one or two Mesa ZIPs (likely
   85202 / 85210). A ZIP5 lookup cannot isolate it, and charging the
   district rate to the whole ZIP would over-collect everywhere else in
   it. Options: leave ZIP-level lookups at the Mesa rate and document
   the gap, or support it only for address/ZIP+4 lookups.

## Recommended action

Leave the engine as is (Mesa rate for the whole ZIP) until the questions
above are answered; record the gap in the AZ module's docstring.
