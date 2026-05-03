# Research — Consolidated External References

> Every external source we've consulted to build OpenSalesTax,
> organized so a state-research agent can find prior work without
> re-discovering it.

**Status:** Compiled 2026-05-03 from the v0.1.0 → v0.5.0 build
session. Subsequent state-research agents are **required** to
append their references here (per
`specs/agent-briefs/per-state-research-brief.md` Step 5).

## How to use this file

- Looking for "what does Sovos say about my state?" → §1
- Looking for "what's MN's official rate file?" → §2 SST sources
- Looking for "what statute did we cite for clothing in TX?" →
  §3 Per-state references
- Adding a new state → append a §3 subsection following the
  template at the bottom

## §1. Cross-state aggregator sources

### 1.1 Sovos State-by-State Guide to Sales Tax

- **URL:** https://sovos.com/content-library/sut/state-by-state-guide-to-sales-tax/
- **Captured:** 2026-05-02 (manually transcribed; the page is
  JS-rendered)
- **Local:** `specs/research/sovos-state-summary.tsv` +
  `sovos-state-summary.md`
- **What's there:** 50 states + DC; nexus thresholds, marketplace
  rules, base rates, filing thresholds + due dates
- **Known defects:** 7 documented in the companion `.md` file
  (wrong-state copy-paste in AL, CT, ME; "Pennsylvani" typo;
  column drift in HI/MO/MS/SD/TN multi-line cells). **DO NOT
  TRUST without cross-checking the state DOR.**
- **License:** Sovos's content. Used here as **research-only
  cross-reference**; explicitly excluded as an ingestion source
  per `constitution.md` §3. Do not redistribute as data.

### 1.2 Streamlined Sales Tax Project (SST)

- **URL:** https://www.streamlinedsalestax.org
- **Membership list:** `specs/research/state-coverage.md` table
  (cross-checked against SST member roster)
- **License:** Public-domain government data. Free to ingest.
- **What's there:**
  - 24 member states publish quarterly rate + boundary files
  - Per-state taxability matrices (HTML; no public structured
    download — must be scraped or transcribed by agents
    promoting tier-2 → tier-1)
- **Empirical format research:** `specs/research/sst-file-format.md`
  documents the column layouts (rate file = 9 cols, boundary
  file = 89 cols, two record types `z` + `4`)
- **NO public layout spec located** — the SST Governing Board
  may have one for members. Our format docs are reverse-
  engineered from MN + WI 2026Q2 files.

### 1.3 US Census TIGER/Line shapefiles (boundary data, future use)

- **URL:** https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
- **Status:** Not yet ingested. Planned for v1.0+ when PostGIS
  address-level resolution lands.
- **License:** US public domain.

### 1.4 Sales Tax Institute (alternative cross-reference, not used yet)

- **URL:** https://www.salestaxinstitute.com/resources/rates
- **Status:** Mentioned in `sovos-state-summary.md` "follow-ups"
  section as an alternative to Sovos if/when our research scales.
- **License:** Industry association content; same caveats as
  Sovos.

## §2. SST quarterly data (rates + boundaries)

| State | Latest captured | Local fixtures | Format |
|---|---|---|---|
| MN | 2026Q2FEB18 | `src/opensalestax/data/fixtures/mn/MNR2026Q2FEB18.csv` + `.zip`, `MNB2026Q2FEB18-sample.csv` | Rates: 9-col CSV, type codes 00/01/45/63 |
| WI | 2026Q2FEB18 | `src/opensalestax/data/fixtures/wi/WIR2026Q2FEB18.csv` | Rates: same 9-col layout; uses `99991231` open-end sentinel (vs MN's `29991231`) |
| Other 22 SST states | Not yet captured | -- | Use same 9-col layout per `sst-file-format.md` |

The `download_sst_file()` helper in `src/opensalestax/data/sst.py`
fetches any SST file by name; bundle as fixture if you need it
for tests.

## §3. Per-state references (built up over time)

Format for each state:

> ### XX -- State Name
>
> - **Statewide rate:** X.XXX% effective YYYY-MM-DD
> - **Tax model:** sales tax | TPT | GET | GRT | none
> - **Local jurisdictions:** counties / cities / parishes / districts / none / home-rule
> - **Sales-tax holidays:** N annual holidays / none
> - **Threshold rules:** clothing under $X / none
> - **DOR URL:** https://...
> - **Statutes consulted:** [citation, citation, ...]
> - **Module file:** `src/opensalestax/states/<name>.py`
> - **Last verified:** YYYY-MM-DD by [agent name or "orchestrator"]

### MN — Minnesota

- **Statewide rate:** 6.875% effective 2009-07-01
- **Tax model:** sales tax (SST member)
- **Local jurisdictions:** counties + cities + special districts
  (Twin Cities transit)
- **Sales-tax holidays:** none
- **Threshold rules:** none
- **DOR URL:** https://www.revenue.state.mn.us
- **Statutes consulted:**
  - Minn. Stat. 297A.61 subd 31 (groceries)
  - Minn. Stat. 297A.67 subd 7 (prescription drugs)
  - Minn. Stat. 297A.67 subd 8 (clothing)
- **Module file:** `src/opensalestax/states/minnesota.py`
- **Last verified:** 2026-05-03

### WI — Wisconsin

- **Statewide rate:** 5.0% effective 1980-01-01
- **Tax model:** sales tax (SST member)
- **Local jurisdictions:** counties (most add 0.5%) + stadium districts
- **Sales-tax holidays:** none
- **Threshold rules:** none
- **DOR URL:** https://www.revenue.wi.gov
- **Statutes consulted:**
  - Wis. Stat. 77.54(20n) (food and food ingredients)
- **Module file:** `src/opensalestax/states/wisconsin.py`
- **Last verified:** 2026-05-03

### CA — California

- **Statewide rate:** 7.25% effective 2017-01-01
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** ~1,700 districts (CDTFA-published);
  not yet loaded in v0.5
- **Sales-tax holidays:** none
- **Threshold rules:** none
- **DOR URL:** https://www.cdtfa.ca.gov
- **Statutes consulted:**
  - Cal. Rev. & Tax Code §6359 (food products for human
    consumption)
  - Cal. Rev. & Tax Code §6369 (prescription drugs)
  - AB 147 (2019) -- digital goods taxability
- **Module file:** `src/opensalestax/states/california.py`
- **Last verified:** 2026-05-03

### TX — Texas

- **Statewide rate:** 6.25% effective 1990-07-01
- **Tax model:** sales tax (NOT SST); origin-based sourcing
  for in-state sellers
- **Local jurisdictions:** cities + counties + transit + SPDs
  (combined cap 8.25%); not yet loaded
- **Sales-tax holidays:** 3 annual (Emergency Prep April,
  Energy Star May, Back-to-School August $100 cap)
- **Threshold rules:** none year-round; holidays apply per-item caps
- **DOR URL:** https://comptroller.texas.gov
- **Statutes consulted:**
  - Tex. Tax Code §151.313 (prescription drugs)
  - Tex. Tax Code §151.314 (food products)
  - Comptroller publications: 98-1017 (emergency prep),
    98-1018 (Energy Star), 98-490 (back-to-school)
- **Module file:** `src/opensalestax/states/texas.py`
- **Last verified:** 2026-05-03

### NY — New York

- **Statewide rate:** 4.0% effective 2005-06-01
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** ~57 counties + ~18 cities + MTA
  surcharge (0.375% in NYC + 7 counties); not yet loaded
- **Sales-tax holidays:** none
- **Threshold rules:** clothing/footwear under **$110/item**
  exempt at the state level (DEFERRED to v0.6+ threshold
  feature; v0.5 module marks clothing taxable with caveat)
- **DOR URL:** https://www.tax.ny.gov
- **Statutes consulted:**
  - N.Y. Tax Law §1115(a)(1) (food and food products)
  - N.Y. Tax Law §1101(b)(6) (prewritten software)
  - DTF Publication 718-C (clothing-exemption details)
- **Module file:** `src/opensalestax/states/new_york.py`
- **Last verified:** 2026-05-03

### FL — Florida

- **Statewide rate:** 6.0% effective 1988-02-01
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** counties (DR-15DSS surtax 0.5%-2.5%);
  not yet loaded
- **Sales-tax holidays:** 4 annual (Disaster Prep Jun, Freedom
  Month Jul, Back-to-School Aug, Tool Time Sep)
- **Threshold rules:** none year-round; holidays apply per-item caps
- **DOR URL:** https://floridarevenue.com
- **Statutes consulted:**
  - Fla. Stat. 212.08(1) (groceries exemption)
- **Module file:** `src/opensalestax/states/florida.py`
- **Last verified:** 2026-05-03

### PA — Pennsylvania

- **Statewide rate:** 6.0% effective 1968-03-01
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** Allegheny County (+1%), Philadelphia
  (+2%); not yet loaded
- **Sales-tax holidays:** none
- **Threshold rules:** none
- **DOR URL:** https://www.revenue.pa.gov
- **Statutes consulted:**
  - 72 P.S. Article II (general); broad clothing exemption
- **Module file:** `src/opensalestax/states/pennsylvania.py`
- **Last verified:** 2026-05-03
- **Note:** PA is one of the major clothing-exemption states.
  Footwear exemption has more nuance; consult PA Retailer's
  Information Guide for athletic/formal cases.

### IL — Illinois

- **Statewide rate:** 6.25% effective 1990-01-01 (Retailer's
  Occupation Tax)
- **Tax model:** Retailer's Occupation Tax (functionally a sales
  tax; legally on the seller); NOT SST
- **Local jurisdictions:** many home-rule cities; not yet loaded
- **Sales-tax holidays:** no recurring annual holiday in current
  law
- **Threshold rules:** none
- **DOR URL:** https://tax.illinois.gov
- **Statutes consulted:**
  - IL Retailer's Occupation Tax Act
- **Module file:** `src/opensalestax/states/illinois.py`
- **Last verified:** 2026-05-03
- **Note:** Groceries + prescription drugs taxed at REDUCED 1%
  rate. v0.5 stores `rate_modifier=Decimal("1.000")` in the
  TaxabilityRule but the engine doesn't yet apply it (v0.6+).

### MD — Maryland

- **Statewide rate:** 6.0% effective 2008-01-03
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** none for sales tax (some local meals
  taxes administered separately)
- **Sales-tax holidays:** 2 annual (Shop Maryland Energy Feb,
  Shop Maryland Tax-Free Week Aug)
- **Threshold rules:** none year-round; holidays apply per-item caps
- **DOR URL:** https://www.marylandtaxes.gov (Maryland Comptroller)
- **Statutes consulted:**
  - Md. Code Ann., Tax-General §11-206 (food for human consumption)
  - HB 932 (2021) -- digital goods taxability
- **Module file:** `src/opensalestax/states/maryland.py`
- **Last verified:** 2026-05-03

### MA — Massachusetts

- **Statewide rate:** 6.25% effective 2009-08-01
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** none for sales tax (some local 0.75%
  meals taxes administered separately)
- **Sales-tax holidays:** 1 annual (sales tax holiday weekend
  in August, $2500 per-item cap)
- **Threshold rules:** clothing under **$175/item** exempt
  (DEFERRED to v0.6+ threshold feature; v0.5 module marks
  clothing taxable with caveat)
- **DOR URL:** https://www.mass.gov/dor
- **Statutes consulted:**
  - M.G.L. c. 64H (Massachusetts sales tax)
  - M.G.L. c. 64H §6(k) (clothing exemption)
- **Module file:** `src/opensalestax/states/massachusetts.py`
- **Last verified:** 2026-05-03

### AZ — Arizona

- **Statewide rate:** 5.6% effective 2013-06-01 (TPT base rate)
- **Tax model:** Transaction Privilege Tax (NOT a sales tax
  legally; same math; imposed on the seller)
- **Local jurisdictions:** counties + cities (combined 6.6%-11.2%);
  not yet loaded
- **Sales-tax holidays:** none
- **Threshold rules:** none
- **DOR URL:** https://azdor.gov
- **Statutes consulted:**
  - Ariz. Rev. Stat. §42-5061 (TPT)
- **Module file:** `src/opensalestax/states/arizona.py`
- **Last verified:** 2026-05-03
- **Note:** Some cities (e.g. Tucson) tax groceries at the local
  level even though the state TPT exempts them. Verify per-city
  when loading district rates.

### CT — Connecticut

- **Statewide rate:** 6.35% effective 2011-07-01 (raised from 6.0% by P.A. 11-6)
- **Tax model:** sales tax (NOT SST -- verified against the SST member
  roster on 2026-05-03; CT does not appear among the 23 full members
  or the lone associate member, TN)
- **Local jurisdictions:** none -- CT is state-only for sales tax. The
  Mashantucket Pequot Tribal Nation reservation is a separate regime
  not modeled in v0.6.
- **Sales-tax holidays:** 1 annual (Sales Tax Free Week, third Sunday
  in August through following Saturday; under-$100 clothing/footwear)
- **Threshold rules:** 7.75% luxury rate on motor vehicles > $50,000,
  jewelry > $5,000, and clothing/footwear/handbag/luggage/umbrella/
  wallet/watch > $1,000 (Conn. Gen. Stat. 12-408(1)(H)). Modeling
  these requires the threshold-rule engine work scheduled for v0.6+;
  v0.6 module documents the rule in `notes` but applies the 6.35%
  general rate.
- **Category-specific rates not yet modeled:**
  - 7.35% on meals/beverages (12-408(1)(I) -- 6.35% + additional 1%)
  - 15% on hotel/lodging-house occupancy (12-408(1)(B)(i))
  - 11% on bed & breakfast occupancy (12-408(1)(B)(ii))
  - 9.35% on short-term passenger-vehicle rental (12-408(1)(G))
  - 1% on computer and data processing services (12-408(1)(D)(i))
  - 2.99% on vessels and vessel motors (12-408(1)(E)(ii))
- **DOR URL:** https://portal.ct.gov/drs *(retrieved 2026-05-03)*
- **Statutes consulted (Connecticut General Statutes title 12, chapter 219):**
  - Conn. Gen. Stat. section 12-407(a)(13) -- "tangible personal
    property" defined to include digital goods + canned/prewritten
    software accessed electronically (added by P.A. 19-117 effective
    2019-10-01)
  - Conn. Gen. Stat. section 12-407e -- annual Sales Tax Free Week
    (under-$100 threshold effective 2015-07-01 per P.A. 15-244)
  - Conn. Gen. Stat. section 12-408(1)(A) -- general 6.35% rate
  - Conn. Gen. Stat. section 12-408(1)(B) -- 15% / 11% lodging rates
  - Conn. Gen. Stat. section 12-408(1)(D) -- 1% computer/data services
  - Conn. Gen. Stat. section 12-408(1)(E) -- 2.99% vessel rate
  - Conn. Gen. Stat. section 12-408(1)(G) -- 9.35% short-term rental
  - Conn. Gen. Stat. section 12-408(1)(H) -- 7.75% luxury rate
  - Conn. Gen. Stat. section 12-408(1)(I) -- additional 1% meals
  - Conn. Gen. Stat. section 12-412(4) -- prescription medicine
    exemption
  - Conn. Gen. Stat. section 12-412(13) -- food products for human
    consumption exemption
  - Public Acts: P.A. 11-6 (2011 rate increase); P.A. 15-244 (2015
    holiday-threshold reduction); P.A. 19-117 (2019 digital-goods
    inclusion); P.A. 04-218 (2004 holiday establishment)
- **External sources retrieved 2026-05-03:**
  - Connecticut General Statutes Chapter 219, raw text via
    https://www.cga.ct.gov/current/pub/chap_219.htm (the live source
    of truth for 12-407, 12-407e, 12-408, and 12-412)
  - https://portal.ct.gov/drs/sales-tax (DRS landing page; confirmed
    Sales Tax Free Week page link layout)
  - https://portal.ct.gov/drs/sales-tax/sales-tax-free-week (2025
    DRS announcement: "Sunday, August 17, through Saturday, August 23,
    2025"; confirms third-Sunday-in-August window pattern + $100 cap
    + athletic/jewelry/handbag/luggage/umbrella/wallet/watch
    exclusions)
  - https://en.wikipedia.org/wiki/Streamlined_Sales_Tax_Project
    (cross-check that CT is not a member; member list verified to
    contain 23 full members + Tennessee associate, no CT)
  - https://en.wikipedia.org/wiki/Sales_taxes_in_the_United_States
    (cross-reference for the 6.35% rate effective 2011-07-01 and the
    7.35% meals rate)
- **Module file:** `src/opensalestax/states/connecticut.py`
- **Last verified:** 2026-05-03 by orchestrator (agent: state-ct)
- **Notes:**
  - 2026 Sales Tax Free Week dates: August 16 (Sunday) - August 22
    (Saturday). Third Sunday of August 2026 is the 16th.
  - The Mashantucket Pequot Tribal Nation reservation (in Ledyard,
    CT) operates outside CT's sales-tax regime under federal
    settlement and tribal-state compact -- documented as a future
    SpecialCase rather than modeled in v0.6.
  - Until rate-modifier and threshold-rule engine support lands,
    consumers calculating CT tax on meals (7.35%), luxury items
    (7.75%), or hotel stays (15%) should expect the engine to apply
    only the 6.35% general rate.
  - DRS publishes individual page URLs that 404 frequently when the
    department reorganizes. The cga.ct.gov statute repository is the
    more durable primary source.

### DC — District of Columbia

- **Statewide rate:** 6.000% effective through 2026-09-30; 7.000%
  effective 2026-10-01 (scheduled increase)
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** none -- DC is a single jurisdiction.
  No sub-District counties or cities levy their own sales tax.
- **Sales-tax holidays:** none (back-to-school holiday repealed by
  D.C. Law 18-111, FY 2010 Budget Support Act of 2009)
- **Threshold rules:** none
- **DOR URL:** https://otr.cfo.dc.gov *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - DC Code Sec. 47-2001 (definitions, including (n) "retail sale",
    (n)(2)(E) food exclusion, (d-1) digital goods definition,
    (n)(1)(BB) digital goods imposition, (g)/(g-1) food vs.
    food-for-immediate-consumption)
  - DC Code Sec. 47-2002 (imposition of tax on sales)
  - DC Code Sec. 47-2002.02 (rates on transient lodgings, food
    for immediate consumption, on-premises spirits, rental
    vehicles)
  - DC Code Sec. 47-2005(14) (prescription drugs exemption)
  - DC Code Sec. 47-2005(15) (medical devices exemption)
  - DC Code Sec. 47-2005(23) (food-stamp eligible foods)
  - DC Code Sec. 47-2005(24) (residential utilities)
  - D.C. Law 18-111 (FY 2010 BSA -- repealed sales-tax holiday)
  - Sec. 337 of FY 2019 Budget Support Act (digital goods expansion)
- *Sources for rate / taxability:*
  - OTR "Notice of Oct. 1, 2025 Tax Changes"
    (https://otr.cfo.dc.gov/release/notice-oct-1-2025-tax-changes,
    retrieved 2026-05-03) -- confirms 6% through 9/30/2026, 7%
    from 10/1/2026, hotel 15.95% through 9/30/2027, commercial
    bingo 7.5% from 10/1/2025
  - OCFO "Tax Rates and Revenues, Sales and Use Taxes"
    (https://cfo.dc.gov/page/tax-rates-and-revenues-sales-and-use-taxes-alcoholic-beverage-taxes-and-tobacco-taxes,
    retrieved 2026-05-03) -- full special-rate table (6%/8%/10%/
    10.25%/14.95%-15.95%/18%)
  - OTR "Taxable and Non-Taxable Services"
    (https://otr.cfo.dc.gov/page/taxable-and-non-taxable-services,
    retrieved 2026-05-03) -- 10% prepared-food, 10.25% rentals
  - OTR "Sales Tax Holiday Repealed"
    (https://otr.cfo.dc.gov/page/sales-tax-holiday-repealed,
    retrieved 2026-05-03)
  - DC Council Code, Title 47 Chapter 20 (primary source for all
    statutory citations above) via
    https://code.dccouncil.gov/us/dc/council/code/titles/47/chapters/20
  - Sales Tax Institute, "DC Repeals Back-to-School Tax Holiday"
    (cross-reference for repeal context)
- **Module file:** `src/opensalestax/states/district_of_columbia.py`
- **Last verified:** 2026-05-03 by per-state agent
- *Notes:*
  - DC has multiple **special-category rates** (10% restaurant,
    10% on-premises liquor, 10.25% off-premises liquor, 10.25%
    rental vehicles, 8% soft drinks, 15.95% hotel, 18% commercial
    parking, 7.5% commercial bingo). The current OpenSalesTax
    engine resolves one rate per authority per category; encoding
    these as separate per-category rates needs either multiple
    authority rows OR a future category-aware authority feature.
    **v0.6 ships only the general 6%/7% statewide rate** -- the
    `prepared_food` taxability rule still marks the line item as
    taxable, so a restaurant meal IS taxed, just at the general
    rate (under-collection until the special-rate feature lands).
  - The 6%-to-7% rate change on 2026-10-01 is encoded as two
    `RateRow`s with non-overlapping `effective_from` /
    `effective_to` so the engine picks the right rate per
    transaction date.

### SC — South Carolina

- **Statewide rate:** 6.0% effective 2007-06-01
  (S.C. Code Ann. section 12-36-910(A) imposes the 5% base rate;
  section 12-36-1110 added the 1% additional surcharge effective
  June 1, 2007 -- combined statewide rate has been 6% since)
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** counties may stack Local Option (1%),
  Capital Project (1%), School District / Education Capital
  Improvement (up to 1%), Transportation (1%); some
  municipalities (e.g., Myrtle Beach) impose a separate 1%
  Tourism Development Fee. Combined rates currently span 6% -- 9%.
  **Per-county rates NOT loaded in v0.6** (no SST file; no public
  machine-readable per-ZIP feed comparable to TX Comptroller's).
  Deferred until SC-specific data ingestion lands.
- **Sales-tax holidays:** 1 annual (Tax Free Weekend, first
  Friday-Sunday of August, no per-item cap; 2026 dates Aug 7-9)
- **Threshold rules:** none
- **DOR URL:** https://dor.sc.gov *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - S.C. Code Ann. section 12-36-60 (definition of tangible
    personal property; basis for SC Revenue Ruling 03-5's
    treatment of electronically delivered software)
  - S.C. Code Ann. section 12-36-910(A) (imposition of the 6%
    sales tax)
  - S.C. Code Ann. section 12-36-1110 (1% surcharge effective
    2007-06-01 that brought the rate to 6%)
  - S.C. Code Ann. section 12-36-2120(28) (prescription drug
    exemption)
  - S.C. Code Ann. section 12-36-2120(57) (annual August Tax
    Free Weekend exemption -- 72 hours, no per-item cap)
  - S.C. Code Ann. section 12-36-2120(75) (unprepared food
    exemption from STATE 6% only; local taxes may still apply)
  - SC Revenue Ruling 03-5 (electronically delivered software /
    digital downloads NOT subject to sales tax; physical-media
    delivery IS taxable)
- *Sources for rate/taxability:*
  - SC DOR Tax Free Weekend page
    (https://dor.sc.gov/communications/tax-free-weekend),
    retrieved 2026-05-03
  - SC DOR Chapter 9 (Exemptions) policy manual,
    retrieved 2026-05-03
  - SC DOR Chapter 21 (Unprepared Food Exemption) policy manual,
    retrieved 2026-05-03
  - SC Revenue Ruling 03-5 (electronic software delivery),
    retrieved 2026-05-03
  - SC Statehouse Title 12 Chapter 36 archive,
    retrieved 2026-05-03
- **Module file:** `src/opensalestax/states/south_carolina.py`
- **Last verified:** 2026-05-03 by per-state agent
- *Notes:*
  - **Digital goods are NOT taxable** when delivered purely
    electronically -- this is unusual relative to most peer
    states (CA, TX, FL, MD all tax digital goods). Per SC RR 03-5;
    track legislative bills (e.g., 2017-2018 Bill 214 attempted
    to add digital goods to the tax base) for any change.
  - **Groceries (unprepared food) state-level exempt** but
    local-level taxes may still apply. Until OpenSalesTax models
    per-jurisdiction taxability overrides, the engine treats
    groceries as fully exempt; document this caveat in any
    SC-facing API documentation.
  - **Pending 2025-2026 Bill 728** ("Tax Free Month") would
    extend the August holiday to the entire month. Not enacted as
    of 2026-05-03; v0.6 encodes the existing 72-hour holiday.
  - **Myrtle Beach Tourism Development Fee (1%)** is separately
    imposed under S.C. Code Title 12 Chapter 4 (NOT under the
    sales tax act); collected differently. Deferred to v1.0+
    when per-municipality fees can be modeled distinctly from
    sales taxes.

### AK — Alaska, DE — Delaware, MT — Montana, NH — New Hampshire, OR — Oregon

- **Statewide rate:** none (no state-level sales tax)
- **Tax model:** none
- **Local jurisdictions:** AK has ~110 boroughs/cities (many via
  the Alaska Remote Seller Sales Tax Commission, https://arsstc.org).
  MT has resort taxes (Whitefish, Big Sky). OR has some meals/MV
  rental taxes. Phase 1 doesn't model any of these.
- **DOR URLs:** state DORs; not authoritative for these states
- **Module file:** `src/opensalestax/states/no_tax.py` (all 5 share)
- **Last verified:** 2026-05-03

### VA -- Virginia

- **Statewide rate:** **5.300% effective 2013-07-01** (the
  combined statewide minimum: 4.3% state portion + 1% mandatory
  local option)
- **Tax model:** sales tax (NOT SST; layered "state + mandatory
  local + optional regional" structure)
- **Local jurisdictions:** every locality imposes the 1% local
  option (mandatory, so it functions as a statewide floor).
  Regional add-ons:
  - Central Virginia, Hampton Roads, Northern Virginia: **+0.7%**
    regional transportation tax -> combined **6.0%**
  - Historic Triangle (Williamsburg, James City County, York
    County): **+1.0%** regional + Historic Triangle tax ->
    combined **7.0%**
  - Selected Southside localities (Charlotte, Danville,
    Gloucester, Halifax, Henry, Northampton, Patrick,
    Pittsylvania): **+1.0%** additional local -> combined **6.3%**
  - All other localities: combined **5.3%** (the statewide minimum)

  Per-region/per-locality rates are NOT modeled in v0.6; the
  module ships the 5.3% statewide minimum only (similar to how
  CA defers its ~1,700 CDTFA districts and SC defers local rates).
- **Sales-tax holidays:** 1 statutory holiday (combined 3-day
  August Sales Tax Holiday covering 4 scopes: school supplies,
  clothing/footwear, Energy Star/WaterSense, hurricane
  preparedness). Encoded as 4 separate ``HolidayWindow`` instances
  to allow per-scope category matching. Per Va. Code 58.1-639.1
  the holiday is set to **sunset July 1, 2030** unless renewed.
- **Threshold rules:** the August holiday has tiered per-item
  caps ($20 / $100 / $2,500 / $60-$350-$1,000); the lowest cap
  in the hurricane scope is encoded today, with higher tiers
  documented in ``HolidayWindow.notes`` for v0.6+ threshold-rule
  enforcement.
- **DOR URL:** **https://www.tax.virginia.gov** *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - Va. Code section 58.1-603 -- imposition of state sales tax
    (4.3% state portion); retrieved
    https://law.lis.virginia.gov/vacode/title58.1/chapter6/section58.1-603/
    on 2026-05-03
  - Va. Code section 58.1-605, 58.1-606 -- 1% mandatory local
    option (cited via tax.virginia.gov rate breakdown)
  - Va. Code section 58.1-609.10 -- miscellaneous exemptions
    including subdivisions 9, 14, 22 (prescription drugs,
    nonprescription drugs, veterinary prescriptions); retrieved
    https://law.lis.virginia.gov/vacode/title58.1/chapter6/section58.1-609.10/
    on 2026-05-03
  - Va. Code section 58.1-611.1 -- exemption for food purchased
    for human consumption and essential personal hygiene products
    (state portion eliminated effective 2023-01-01; only 1% local
    still applies); retrieved
    https://law.lis.virginia.gov/vacode/title58.1/chapter6/section58.1-611.1/
    on 2026-05-03
  - Va. Code section 58.1-639.1 -- annual retail sales and use
    tax holiday (effective until July 1, 2030); first Friday in
    August through following Sunday; per-item caps for school
    supplies $20, clothing/footwear $100, Energy Star/WaterSense
    $2,500, generators $1,000, chainsaws $350, other hurricane
    prep $60; retrieved
    https://law.lis.virginia.gov/vacode/title58.1/chapter6/section58.1-639.1/
    on 2026-05-03
  - Virginia Tax Commissioner rulings 05-44, 14-178, 16-135 --
    long-standing policy treating electronically-delivered
    prewritten software as not constituting tangible personal
    property under Va. Code 58.1-602 (digital goods non-taxable
    when no tangible medium is involved). Cross-referenced via
    the Virginia Tax website search results 2026-05-03.
- *Sources for rate/taxability:* Virginia Department of Taxation
  rate breakdown page (combined rates by locality) + Virginia
  General Assembly online code (law.lis.virginia.gov) + Virginia
  Tax Commissioner rulings (digital goods).
- **Module file:** `src/opensalestax/states/virginia.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (Phase 6 Batch B)
- *Notes:*
  - VA's grocery rate is encoded with ``rate_modifier=1.000``
    mirroring the IL pattern. The state 4.3% portion was
    eliminated effective 2023-01-01; only the mandatory 1% local
    survives, giving an effective 1% rate on food and personal
    hygiene products. The engine doesn't yet wire rate_modifier
    through (deferred to v0.6+); until then, retailers should
    verify with the Virginia Department of Taxation.
  - VA is one of the few states where digital downloads of
    prewritten software are NOT taxable (when no tangible medium
    is delivered). This contrasts with CA, TX, FL, MD, and NY,
    all of which tax digital goods.
  - The August holiday's hurricane scope has three tiered caps
    ($60 / $350 / $1,000). The conservative $60 cap is encoded
    today; the higher chainsaw and generator tiers are documented
    in ``HolidayWindow.notes`` for v0.6+ threshold-rule work.
  - Most Virginia localities also impose a separate **meals tax**
    that is administered locally and not modeled here; the
    "prepared_food" rule notes this for downstream callers.

### ID — Idaho

- **Statewide rate:** **6.000% effective 2006-10-01** (raised from 5%
  by HB 82 of the 2006 First Extraordinary Legislative Session;
  Idaho Code section 63-3619 as amended by Chapter 1, Section 18 of
  the 2006 1st Extra. Sess.)
- **Tax model:** sales tax (NOT SST -- verified 2026-05-03 against
  the SST member roster on streamlinedsalestax.org)
- **Local jurisdictions:** **No county-level sales tax.** A small
  number of "resort cities" (population <= 10,000 with primary
  economy from tourism/recreation) may impose 1-3% local-option
  non-property taxes, including a sales tax, by 60% voter approval
  under Idaho Code section 50-1044 (and the related municipal-finance
  statute section 50-1046). Examples: Sun Valley, Ketchum, McCall,
  Stanley, Donnelly, Cascade. **Per-resort-city rates are NOT loaded
  in v0.7** -- deferred until a resort-city loader lands.
- **Sales-tax holidays:** **NONE.** Idaho has never enacted a
  recurring sales-tax holiday; confirmed 2026-05-03 against Idaho
  State Tax Commission filing/holiday pages and multiple
  cross-references. The module's ``holidays_for(year)`` returns an
  empty iterator for every year, with a regression test in
  ``test_state_idaho.py`` that exercises 2024-2030.
- **Threshold rules:** none.
- **DOR URL:** **https://tax.idaho.gov** *(retrieved 2026-05-03)*
- **Statutes consulted (Idaho Code Title 63, Chapter 36 unless noted):**
  - Idaho Code section 63-3612 -- definition of "sale" (includes
    furnishing of meals)
  - Idaho Code section 63-3616 -- definition of "tangible personal
    property"; subsection (b) classifies prewritten/canned computer
    software AND digital music/books/videos/games sold with a
    permanent right to use as TPP, while EXCLUDING custom programs,
    SaaS / remotely accessed software, "load and leave" delivery
    without tangible media, and digital media without a permanent
    right to use
  - Idaho Code section 63-3619 -- imposition and rate (6%)
  - Idaho Code section 63-3622N -- prescription/medical-products
    exemption (drugs, hypodermic syringes, insulin, artificial eyes,
    eyeglasses/components, contact lenses, hearing aids and parts;
    practitioner administered or by prescription; humans only)
  - Idaho Code section 50-1044 (Title 50, Chapter 10) -- resort-city
    local-option non-property tax authority
  - Idaho Code section 50-1046 -- city local-option non-property
    taxes by 60% majority vote
  - HB 82, 2006 First Extraordinary Session -- enacted the 5% to 6%
    rate increase effective 2006-10-01
  - IDAPA 35.01.02.041 -- regulation, "FOOD, MEALS, OR DRINKS"
    (confirms taxability of meal sales and service charges)
  - IDAPA 35.01.02.027 -- regulation, "COMPUTER EQUIPMENT, SOFTWARE,
    AND DATA SERVICES" (cross-reference for 63-3616(b) software
    treatment)
- *Sources for rate/taxability:*
  - Idaho State Legislature statute repository
    (https://legislature.idaho.gov/statutesrules/idstat/title63/t63ch36/)
    retrieved 2026-05-03 -- primary source for sections 63-3612,
    63-3616, 63-3619, 63-3622N
  - Idaho State Tax Commission, "Sales and Use Taxes: Basics Guide"
    (https://tax.idaho.gov/taxes/sales-use/online-guide/) retrieved
    2026-05-03 -- confirmed 6% rate, prepared-food taxability,
    digital-goods permanent-right rule
  - Idaho State Tax Commission, "Idaho Food Tax Credit"
    (https://tax.idaho.gov/taxes/income-tax/individual-income/popular-credits-and-deductions/idaho-grocery-credit/)
    retrieved 2026-05-03 -- confirms groceries are FULLY TAXED at
    the 6% sales-tax rate; the "grocery credit" is a separate
    non-refundable INCOME-TAX credit, not a sales-tax reduction
  - Idaho State Tax Commission, "Sales Tax: Filing and Paying"
    (https://tax.idaho.gov/taxes/sales-use/stfiling/) retrieved
    2026-05-03 -- no holiday entries
  - Idaho State Tax Commission, "Introduction to Medical Products
    Exemption" (https://tax.idaho.gov/taxes/sales-use/exemptions/medical-products/introduction/)
    retrieved 2026-05-03 -- 63-3622N exemption scope
  - Justia codification of Title 63 Chapter 36
    (https://law.justia.com/codes/idaho/title-63/chapter-36/)
    retrieved 2026-05-03 -- cross-reference
  - Idaho State Tax Commission, "City Sales Taxes"
    (https://tax.idaho.gov/taxes/sales-use/sales-tax/local-sales-tax/city-sales-tax/)
    retrieved 2026-05-03 -- resort-city local-option tax overview
- **Module file:** `src/opensalestax/states/idaho.py`
- **Last verified:** 2026-05-03 by per-state agent (Phase 6 Batch B)
- *Notes:*
  - Idaho is one of the small group of states (with HI, MS, SD, AL,
    OK, KS, AR among others depending on year) that fully tax
    groceries at the state sales-tax rate. The "Idaho grocery
    credit" is a non-refundable INCOME-TAX credit administered under
    the income-tax statutes -- it is NOT a reduction of the sales
    tax owed at the register. The module's grocery taxability rule
    explicitly documents this in the ``notes`` field, and the test
    suite has a regression test asserting the notes mention both
    "grocery credit" and "income-tax credit" so an integrator
    skimming the rule cannot miss the distinction.
  - The per-state research brief's initial sketch said "ID taxes
    remotely accessed software (SaaS) per Idaho Code section
    63-3616(b)" -- this is **incorrect**. Section 63-3616(b)
    expressly EXCLUDES remotely accessed software / SaaS from the
    TPP definition. The implementation here encodes the dominant
    taxable case (downloaded canned software + permanent-right
    digital media) and documents the SaaS exclusion in notes for
    callers; a future sub-category split between "downloaded
    digital media / canned software" and "SaaS / subscription
    digital media" would let the engine distinguish them precisely.
  - The Idaho State Tax Commission provides industry-specific guides
    (food, medical, schools, computers, etc.) at
    https://tax.idaho.gov/taxes/sales-use/online-guide/ -- valuable
    follow-up reading for the next maintainer.
  - Resort-city local-option taxes vary by city (typical 1-3%) and
    by what the city ordinance taxes (some tax the full state-tax
    base, some limit to lodging + restaurants + alcohol). When the
    v0.7+ resort-city loader lands, encoding will need per-city
    ordinance research; Stanley and Donnelly publish their own
    ordinances online which are good starting points.

### Tier-2 SST states (rate-only, default taxability)

22 states load via the generic `SstStateModule` in
`src/opensalestax/states/_tier2.py`:

AR, GA, IA, IN, KS, KY, MI, NE, NV, NJ, NC, ND, OH, OK, RI, SD,
TN, UT, VT, WA, WV, WY

Each has a one-class entry there with state_abbrev + state_name +
state_fips. They use the SST quarterly data files for rates and
default taxability (everything taxable except groceries). To
**promote one to tier 1**, follow `per-state-research-brief.md`:

- Look up the state's actual taxability matrix from the state DOR
- Cite statutes
- Add a dedicated module under `src/opensalestax/states/<name>.py`
- Remove the entry from `_tier2.py`

## §4. Per-state references — TEMPLATE for new entries

Copy this when adding a new state's section. **Mandatory fields**
are bold; optional fields are italicized.

> ### **XX -- State Name**
>
> - **Statewide rate:** **X.XXX% effective YYYY-MM-DD**
> - **Tax model:** sales tax | TPT | GET | GRT | none
> - **Local jurisdictions:** [counties / cities / parishes /
>   districts / none / home-rule]
> - **Sales-tax holidays:** N annual holidays / none
> - **Threshold rules:** [description] / none
> - **DOR URL:** **https://...** *(retrieved YYYY-MM-DD)*
> - **Statutes consulted:**
>   - [citation -- subject]
>   - [citation -- subject]
> - *Sources for rate/taxability:* [Sovos summary | DOR
>   publication X | press release | etc.]
> - **Module file:** `src/opensalestax/states/<name>.py`
> - **Last verified:** YYYY-MM-DD by [agent name | "orchestrator"]
> - *Notes:* [any state-specific quirks worth flagging for the
>   next maintainer]

## §5. References-of-references (places we should look but haven't)

For agents researching tier-0 states with complex local-tax landscapes:

- **Avalara compliance docs** -- public, useful for cross-checking
  but DO NOT scrape or copy schemas (see constitution §2 patent
  posture; we don't reverse-engineer commercial APIs)
- **TaxJar state guides** -- same caveat as Avalara
- **Tax Foundation state-by-state reports** -- think-tank, public,
  good for historical-rate research
- **State Bar Association tax sections** -- state-specific
  practitioner guides; useful for edge-case research
- **State CPA Society publications** -- excellent practitioner
  resources for understanding local-tax topology

When citing any of these, cite the URL + date + your assessment
("treated as one input among many; primary source is the state
DOR").
