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

### MO -- Missouri

- **Statewide rate:** **4.225% effective ~1984-01-01** (composed of
  3.000% general revenue + 1.000% Proposition C education + 0.125%
  parks/soils + 0.100% conservation; the current composition has
  been stable since the parks/soils tax took effect 1984)
- **Tax model:** sales tax (NOT SST -- verified against the SST
  member roster on 2026-05-03; MO does not appear among the 23 full
  members or the lone associate member, Tennessee)
- **Local jurisdictions:** counties, cities, fire districts,
  ambulance districts, transit authorities, and tourism community
  enhancement districts (TCEDs) may each levy their own sales tax.
  Combined rates range 4.225% to 11.0%+ (Branson area is among the
  highest). **Per-jurisdiction local rates NOT loaded in v0.7** --
  no SST file (MO is non-SST) and no public per-ZIP machine-
  readable feed comparable to TX Comptroller's. MO DOR publishes a
  quarterly Sales/Use Tax Rate Tables PDF + Excel download but
  ingesting / normalizing requires a custom MO loader, deferred to
  a future state-data-loader phase.
- **Sales-tax holidays:** **2 annual** holidays codified in
  Chapter 144:
  - Show-Me Green Sales Tax Holiday (April 19-25 each year, fixed
    calendar dates) -- Energy Star certified appliances $1,500/less
    per item
  - Back-to-School Sales Tax Holiday (first Friday of August
    through following Sunday) -- clothing $100/less, school supplies
    $50/purchase, computers $1,500/less, computer peripherals
    $1,500/less, computer software $350/less
- **Threshold rules:** none year-round; both holidays apply per-item
  caps. Back-to-school school-supply cap is per-PURCHASE (not strictly
  per-item) under the statute -- documented in the holiday's notes
  pending purchase-level threshold-rule support.
- **DOR URL:** **https://dor.mo.gov** *(retrieved 2026-05-03)*
- **Statutes consulted (Mo. Rev. Stat. Title X, Chapter 144 --
  sales/use tax):**
  - Mo. Rev. Stat. section 144.014 -- reduced 1.225% state rate on
    food for home consumption (the 3.0% general-revenue portion is
    excluded; the 1.0% education + 0.125% parks/soils + 0.1%
    conservation portions still apply, totaling 1.225%)
  - Mo. Rev. Stat. section 144.020 -- imposition of the sales tax
    on tangible personal property
  - Mo. Rev. Stat. section 144.030.2(18) -- prescription drug and
    medical-equipment exemption
  - Mo. Rev. Stat. section 144.049 -- annual Back-to-School Sales
    Tax Holiday (first Friday of August through following Sunday;
    HB 154 of 2021 made the holiday mandatory at all jurisdiction
    levels via subdivision .10)
  - Mo. Rev. Stat. section 144.526 -- annual Show-Me Green Sales
    Tax Holiday (April 19-25 each year; cities/counties may opt out)
  - Mo. Rev. Stat. section 144.605 -- remote-seller economic-nexus
    threshold (SB 153, 2021; effective 2023-01-01)
  - Mo. Rev. Stat. section 144.701 -- Proposition C 1% education tax
  - Mo. Rev. Stat. section 144.752 -- marketplace-facilitator
    collection requirement (SB 153, 2021; effective 2023-01-01)
  - Mo. Const. art. IV section 43(a) -- 0.100% Conservation Sales Tax
  - Mo. Const. art. IV section 47(a) -- 0.125% Parks and Soils Sales Tax
- *Sources for rate/taxability:*
  - Missouri Department of Revenue Sales/Use Tax page
    (https://dor.mo.gov/taxation/business/tax-types/sales-use/),
    retrieved 2026-05-03 -- confirms the 4.225% composition
  - MO DOR Show-Me Green Sales Tax Holiday page
    (https://dor.mo.gov/taxation/business/tax-types/sales-use/holidays/show-me-green/),
    retrieved 2026-05-03 -- confirms April 19-25 fixed-date window
    and $1,500 Energy Star cap
  - MO DOR Back-to-School Sales Tax Holiday page
    (https://dor.mo.gov/taxation/business/tax-types/sales-use/holidays/back-to-school/),
    retrieved 2026-05-03 -- confirms first-Friday-of-August window
    + clothing $100 / supplies $50 / computers $1,500 / peripherals
    $1,500 / software $350 caps + post-2023 mandatory-jurisdiction
    rule
  - Missouri Revisor of Statutes (Title X Chapter 144) at
    https://revisor.mo.gov/main/OneChapter.aspx?chapter=144,
    retrieved 2026-05-03 -- primary source for every statutory
    citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Missouri is NOT a member
- **Module file:** `src/opensalestax/states/missouri.py`
- **Last verified:** 2026-05-03 by per-state research agent (Phase
  6 Batch B)
- *Notes:*
  - **Reduced grocery rate caveat:** the 1.225% rate per section
    144.014 applies to the STATE portion only. City, county, and
    other local sales taxes apply to qualifying food at the FULL
    local rate. Encoded with ``rate_modifier=Decimal("1.225")``
    mirroring IL/VA; engine support for rate_modifier is deferred
    to v0.6+. Until then, retailers selling groceries in MO should
    verify with the Missouri Department of Revenue.
  - **Digital goods are NOT taxable** when delivered electronically.
    Missouri sales tax applies to "tangible personal property"
    per section 144.020; downloaded software, music, ebooks, and
    streaming services have historically been treated as non-
    tangible by the Missouri DOR. SB 153 (2021) added economic-
    nexus + marketplace-facilitator collection requirements but did
    NOT change the underlying tangibility-based scope. Tangible-
    media sales (boxed CD, etc.) remain taxable. This contrasts
    with CA, TX, FL, MD, NY, IL (all of which tax digital goods).
  - **Show-Me Green local opt-out:** under section 144.526, cities
    and counties may opt out of the Show-Me Green holiday, in
    which case their local sales tax still applies to qualifying
    Energy Star purchases. The state portion is exempt regardless.
    Per-jurisdiction opt-out tracking is deferred to a future
    SpecialCase implementation.
  - **Back-to-School holiday is now mandatory** at all jurisdiction
    levels per HB 154 (2021), codified at section 144.049.10.
    Prior-year analyses that allowed local opt-out are stale.
  - **School-supply cap is PER PURCHASE** under the statute (not
    strictly per item). The HolidayWindow encodes it as a per-item
    cap pending purchase-level threshold-rule support; documented
    in the window's ``notes`` field.
  - **Statewide effective date:** the current 4.225% composition
    has been stable since 1984; encoded as 1984-01-01 in
    parse_rates. Earlier composition history (3.0% only pre-1977,
    3.1% with conservation 1977-1982, 4.1% with Prop C 1982-1984)
    is documented here for completeness but not modeled as
    historical RateRows in v0.7.

### MS -- Mississippi

- **Statewide rate:** **7.000% effective 1992-07-01** (the highest
  single statewide sales tax rate in the country; stable since the
  1992 increase from 6%)
- **Tax model:** sales tax (NOT SST)
- **Local jurisdictions:** very limited -- a small handful of
  cities have local "tourism" or "infrastructure" taxes (Tupelo,
  Jackson, etc.) authorized by individual local-and-private-laws
  acts; the Tunica County Tourism Tax is administered separately.
  No general local-option statute. **Per-municipality rates NOT
  loaded in v0.7** (deferred -- mirrors the SC and CA decisions).
- **Sales-tax holidays:** **2 annual holidays**:
  1. Back-to-School (second Friday in July through Sunday;
     clothing/footwear/school supplies < $100/item; 2026 dates:
     **July 10-12, 2026**)
  2. Second Amendment / MSAW (last Friday in August through
     Sunday; firearms, ammunition, statutorily-defined hunting
     supplies; no per-item cap; 2026 dates: **August 28-30, 2026**)
- **Threshold rules:** $100 per-item cap on the back-to-school
  holiday; no year-round thresholds
- **Special rates:** REDUCED 5% rate on SNAP-eligible groceries
  effective 2025-07-01 per H.B. 1, Laws 2025 (encoded as
  ``rate_modifier=Decimal("5.000")`` on the groceries TaxabilityRule;
  the engine does not yet apply rate_modifier so the 7% general
  rate is over-collected on grocery line items until v0.6+
  rate_modifier wiring lands)
- **DOR URL:** **https://www.dor.ms.gov** *(retrieved 2026-05-03;
  the DOR's TLS configuration trips some HTTP clients with strict
  certificate validation -- legacy intermediates -- so research
  agents may need to fall back to legislative or aggregator
  sources for primary text)*
- **Statutes consulted (Miss. Code Ann., Title 27, Chapter 65 --
  sales tax):**
  - Miss. Code Ann. section 27-65-17 -- general 7% rate imposition
    on tangible personal property (amended by H.B. 1, Laws 2025 to
    add the reduced 5% rate on SNAP-eligible food effective
    2025-07-01)
  - Miss. Code Ann. section 27-65-26 -- imposition of tax on
    selling, renting, or leasing specified digital products (added
    by S.B. 2449, Laws 2023, effective 2023-07-01)
  - Miss. Code Ann. section 27-65-111(h) -- prescription drug /
    medicine exemption (drugs prescribed for human treatment by
    an authorized prescriber and dispensed by a registered
    pharmacist, OR furnished by a licensed
    physician/surgeon/dentist/podiatrist; excludes prosthetics,
    ophthalmic devices, dentures, artificial limbs, splints,
    bandages, etc.)
  - Miss. Code Ann. section 27-65-111(bb) -- annual back-to-school
    sales tax holiday (clothing/footwear/school supplies < $100;
    moved from "last Friday/Saturday in July" to "second Friday in
    July through Sunday" by S.B. 2470, Laws 2024)
  - Miss. Code Ann. section 27-65-111(af) -- annual Mississippi
    Second Amendment Sales Tax Holiday (firearms, ammunition,
    statutorily-defined "hunting supplies"; last Friday in August
    through following Sunday; no per-item cap)
  - **Session laws of note:**
    - H.B. 1, Laws 2025 -- grocery rate reduction 7% -> 5%
      effective 2025-07-01
    - S.B. 2449, Laws 2023 -- specified digital products /
      computer software taxability effective 2023-07-01
    - S.B. 2470, Laws 2024 -- back-to-school holiday moved to
      second weekend in July, extended from 2 days to 3 days
      (signed 2024-04-22)
- *Sources for rate / taxability / holiday verification (retrieved
  2026-05-03):*
  - Mississippi Department of Revenue -- "Reduced Sales Tax on
    Groceries Begins July 1" press release at
    https://www.dor.ms.gov/news/reduced-sales-tax-groceries-begins-july-1
    (DOR site requires lenient TLS validation; cross-referenced
    via Sales Tax Institute summary at
    https://www.salestaxinstitute.com/resources/mississippi-grocery-sales-tax-cut)
  - Mississippi Department of Revenue -- 2025 Second Amendment
    Sales Tax Holiday official guide at
    https://www.dor.ms.gov/sites/default/files/2025-05/2025%20Second%20Amendment%20Sales%20Tax%20Holiday%20Updated%205-13-2025.pdf
    (cross-referenced via VATupdate guide at
    https://www.vatupdate.com/2025/05/15/guide-to-mississippi-second-amendment-sales-tax-holiday-dates-eligibility-and-guidelines/
    -- confirms 2025 dates Aug 29-31, statutory pattern of "last
    Friday in August", and the eligible items list)
  - Mississippi Legislature billstatus archive --
    https://billstatus.ls.state.ms.us/documents/2023/html/SB/2400-2499/SB2449SG.htm
    (S.B. 2449 enrolled text, digital products / software);
    https://billstatus.ls.state.ms.us/documents/2024/html/SB/2400-2499/SB2470SG.htm
    (S.B. 2470 enrolled text, holiday rescheduling)
  - Mississippi Code on Justia --
    https://law.justia.com/codes/mississippi/title-27/chapter-65/in-general/section-27-65-26/
    (specified digital products) and the 27-65-111 search results
    referenced in agent research notes (Justia returned 403 to the
    automated fetcher; a manual visit confirms subsections (h),
    (bb), and (af) cited above)
  - Sales Tax Institute, "Mississippi Changes and Extends Dates
    for Annual Back to School Sales Tax Holiday" --
    https://www.salestaxinstitute.com/resources/mississippi-changes-and-extends-dates-for-annual-back-to-school-sales-tax-holiday
    (confirms S.B. 2470 effect: second Friday in July, $100 cap on
    clothing AND school supplies)
  - Avalara 2026 sales tax holiday calendar --
    https://www.avalara.com/blog/en/north-america/2026/01/sales-tax-holidays.html
    (cross-reference for 2026 date confirmation: back-to-school
    July 10-12; Second Amendment August 28-30 -- consistent with
    the "second Friday of July" and "last Friday of August"
    statutory rules and the 2026 calendar; cited as a secondary
    cross-check, not as authoritative; primary authority is the
    Mississippi Code)
- **Module file:** `src/opensalestax/states/mississippi.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (Phase 6 Batch B)
- *Notes:*
  - Pre-2025-07-01 Mississippi was one of the few states that
    taxed groceries at the FULL state rate (7%). H.B. 1, Laws 2025
    cut the grocery rate to 5%; the saving statute references SNAP
    eligibility as the qualifying definition. This historical
    "groceries fully taxable" fact is the most-cited MS-vs-peers
    distinction even though it is no longer the current law -- the
    module docstring documents both the historical and current
    treatment so future maintainers do not silently re-introduce a
    stale assumption.
  - The 5% reduced grocery rate is encoded as
    ``rate_modifier=Decimal("5.000")`` on the TaxabilityRule
    (mirrors IL's reduced grocery rate handling). The engine does
    not yet apply rate_modifier through to the calculation
    (deferred to v0.6+); until that lands, the engine over-collects
    by 2 percentage points on SNAP-eligible food and the API
    disclaimer should reflect this.
  - The Second Amendment Sales Tax Holiday's "hunting supplies"
    definition is statutorily LIMITED to: archery equipment,
    firearm and archery cases, firearm and archery accessories,
    hearing protection, holsters, belts, and slings. General
    hunting clothing, decoys, calls, and live animals are NOT
    eligible -- a common point of confusion at retail.
  - Two 2026-session bills (HB 281 and HB 437) propose to expand
    the back-to-school holiday's eligible items list (e.g., adding
    computers) or raise the cap. Status to verify in subsequent
    legislative-session reviews.
  - The Tunica County Tourism Tax and the small set of
    municipality tourism / infrastructure taxes are NOT modeled in
    v0.7. They are imposed under local-and-private-laws acts
    rather than a general local-option statute, so each requires
    its own authorizing-bill review and effective-date research.

### CO -- Colorado

- **Statewide rate:** **2.900% effective 2001-01-01** -- one of the
  lowest state-level rates of any taxing US state. Combined rates
  inside home-rule cities reach **11%+**.
- **Tax model:** sales tax (NOT SST). Three concurrent regimes:
  state-administered state tax, state-collected local taxes
  (counties + special districts + non-home-rule cities), and
  ~70 home-rule self-collecting cities.
- **Local jurisdictions:** **HOME-RULE CITIES** (~70) self-administer
  under Article XX of the Colorado Constitution -- Denver, Aurora,
  Boulder, Colorado Springs, Fort Collins, Lakewood, Thornton,
  Arvada, Pueblo, Greeley, Westminster, Centennial, and ~58 others.
  Each defines its own rate, base, and exemptions (notably:
  most home-rule cities tax groceries even though the state exempts
  them). State-collected counties + special districts (RTD, SCFD,
  Football Stadium District) layer on additional rates that CDOR
  collects on the locality's behalf. **None modeled in v0.7** -- see
  the "Notes" section and ``specs/decisions/04-colorado-home-rule.md``.
- **Sales-tax holidays:** **NONE** at the state level (some
  home-rule cities have local holidays; not modeled).
- **Threshold rules:** none.
- **DOR URL:** **https://tax.colorado.gov** *(retrieved 2026-05-03)*
- **Statutes consulted (Colorado Revised Statutes Title 39 Article 26):**
  - Colo. Rev. Stat. section 39-26-104 -- imposition (taxable
    property and services definitions)
  - Colo. Rev. Stat. section 39-26-106(1)(a)(II) -- 2.9% rate
    effective 2001-01-01
  - Colo. Rev. Stat. section 39-26-102(15)(b.5) -- "tangible
    personal property" expanded to include "digital goods"
    regardless of method of delivery (added by **HB 21-1312**,
    signed 2021-06-23, effective 2021-07-01)
  - Colo. Rev. Stat. section 39-26-707(1)(e) -- food for home
    consumption exemption, effective 1980-01-01
  - Colo. Rev. Stat. section 39-26-707(1.5) -- candy and soft
    drinks carved out of the food exemption (taxable), effective
    2010-05-01
  - Colo. Rev. Stat. section 39-26-717 -- drugs and medical and
    therapeutic devices exemption (prescription drugs, insulin,
    oxygen-delivery equipment, prescription-dispensed medical
    supplies)
  - **HB 21-1312** -- digital goods (cited above)
  - **HB 21-1162** -- separate bill addressing destination-sourcing
    transition rules (NOT digital goods; the orchestrator brief's
    mention of "1162 affected sourcing" is correct -- both are real
    bills with different scopes)
- **External sources retrieved 2026-05-03:**
  - https://law.justia.com/codes/colorado/title-39/specific-taxes/sales-and-use-tax/article-26/part-1/section-39-26-106/
    -- C.R.S. section 39-26-106 (state rate)
  - https://colorado.public.law/statutes/crs_39-26-707
    -- C.R.S. section 39-26-707 (food exemption + candy/soft drink carve-outs)
  - https://law.justia.com/codes/colorado/title-39/specific-taxes/sales-and-use-tax/article-26/part-7/section-39-26-717/
    -- C.R.S. section 39-26-717 (drugs and medical exemptions)
  - https://www.stateandlocaltax.com/digital-economy/colorado-defines-digital-goods-as-taxable-tangible-personal-property-regardless-of-the-means-of-delivery/
    -- HB 21-1312 digital-goods analysis (Eversheds Sutherland SALT Shaker, 2021)
  - https://tax.colorado.gov/DR1002 -- CDOR rate publication landing
    page (DR 1002 is the canonical state+local rate schedule and
    home-rule contact directory)
  - https://tax.colorado.gov/local-government-sales-tax -- CDOR
    overview page describing state-collected vs. self-collecting
    distinction
  - https://www.salestaxcolorado.com/2022/10/06/which-towns-cities-in-colorado-are-self-collecting-home-rule-jurisdictions/
    -- third-party roster of CO home-rule self-collecting cities
    (cites "68 towns and cities" as of 2022; CDOR cites
    "approximately 70" in current materials)
  - https://www.cml.org/docs/default-source/uploadedfiles/legislative/position-papers/2021-position-papers/hb-1162-position-paper.pdf?sfvrsn=10477b4a_0
    -- Colorado Municipal League position paper on HB 21-1162
    (confirms it addressed destination sourcing, not digital goods)
  - https://taxcloud.com/sales-tax/colorado/ -- combined-rate
    cross-reference for the 12 most populous home-rule cities
    (used only as a cross-check; not authoritative)
- *Sources for rate/taxability:* Colorado Revised Statutes via
  Justia + colorado.public.law (the statute repositories) + CDOR
  rate publications + the Eversheds Sutherland SALT Shaker analysis
  of HB 21-1312.
- **Module file:** `src/opensalestax/states/colorado.py`
- **Last verified:** 2026-05-03 by per-state research agent (state-co)
- **Decision document:** `specs/decisions/04-colorado-home-rule.md`
  -- the canonical rationale for the v0.7 state-portion-only scope
  and the three options considered.
- *Notes:*
  - **HOME-RULE WARNING.** This is the most important caveat for any
    Colorado integrator. Approximately 70 home-rule cities
    self-administer their own sales taxes under Article XX of the
    Colorado Constitution. Their rates, bases, and exemptions differ
    from the state, and CDOR does not collect on their behalf. The
    OpenSalesTax v0.7 module ships the **state portion only** -- a
    transaction inside a home-rule city will be **under-collected**
    (the city portion is missing entirely, and the taxability matrix
    may be wrong, notably for groceries). See the decision document
    for the path to correctness.
  - **Most home-rule cities tax groceries** (Denver, Boulder,
    Colorado Springs, Fort Collins, etc.) even though the state
    exempts them under section 39-26-707(1)(e). The module's
    ``groceries`` taxability rule warns about this in its ``notes``
    field but cannot model it precisely until per-jurisdiction
    taxability overrides land.
  - **Combined rates** in CO range from 2.9% (an unincorporated area
    with no county or special-district add-on) up to **~11.2%** in
    some home-rule cities. The state portion alone is one of the
    lowest in the country; the combined rate ranks among the highest.
  - **Digital goods are taxable** in Colorado as of 2021-07-01 per
    HB 21-1312, which expanded the C.R.S. section 39-26-102(15)(b.5)
    definition of "tangible personal property" to include digital
    goods regardless of delivery method (downloads + streaming).
  - **Candy and soft drinks** are statutorily carved out of the food
    exemption (taxable) per section 39-26-707(1.5) effective
    2010-05-01. The current six-category taxability matrix doesn't
    distinguish candy/soft-drinks from groceries; encoding that
    distinction is a future refinement that ties into per-subcategory
    item codes.
  - **No state-level holidays.** Some home-rule cities have local
    sales-tax holidays; not modeled.

### **LA -- Louisiana**

> **HEADS UP:** Louisiana's local tax landscape is uniquely
> fragmented. **v0.7 ships the state portion only and does NOT
> model the 64 parishes' independent local sales taxes.** See
> `specs/decisions/05-louisiana-parishes.md` for the full
> trade-off analysis (Options A / B / C considered; Option A --
> state-only with prominent deferral -- chosen). A v0.7 caller
> calculating tax for a LA address will under-collect by
> ~5-7 percentage points for typical inhabited parishes (which
> stack their own 4-7% on top of the state 5%).

- **Statewide rate:** **5.000%** effective **2025-01-01** through
  **2029-12-31** (Act 11 of 2024 3rd Extraordinary Session;
  scheduled to step down to 4.75% on 2030-01-01 absent further
  legislative action). The 5% rate is the sum of statutory layers
  under La. R.S. 47:302, 47:321, 47:321.1, 47:331, and 47:332;
  LDR publishes the combined rate as the headline figure.
- **Tax model:** sales and use tax (standard).
- **Local jurisdictions:** **64 parishes**, each with its own Sales
  and Use Tax Commission (or comparable body) administering parish
  + sub-municipal + special-district taxes under La. R.S. 47:337.1
  et seq. ("Uniform Local Sales Tax Code"). Combined rates exceed
  12% in some inhabited corners. Partial consolidation: the
  Louisiana Sales and Use Tax Commission for Remote Sellers (R.S.
  47:339.1, established 2018) collects state + local on
  remote-seller transactions only; Parish E-File offers a unified
  filing portal but rates remain parish-specific. **Not modeled in
  v0.7.**
- **Sales-tax holidays:** 1 active annual holiday (Second Amendment
  Weekend, R.S. 47:305.62, first consecutive Friday-Sunday of
  September; 2026 dates Sept 4-6). Two historical holidays --
  back-to-school (R.S. 47:305.54) and hurricane preparedness (R.S.
  47:305.58) -- have been **suspended** since 2018 and were NOT
  reauthorized in the 2025 Regular Session (HB 551 died on
  2025-06-12).
- **Threshold rules:** none (the Second Amendment Weekend Holiday
  has no per-item dollar cap).
- **DOR URL:** **https://revenue.louisiana.gov** *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - **Act 11 of 2024 3rd Extraordinary Session (HB 10)** -- raised
    state rate from 4.45% to 5.0% effective 2025-01-01, sunset
    2029-12-31, scheduled step-down to 4.75% on 2030-01-01. Full
    enrolled text retrieved
    https://www.legis.la.gov/legis/ViewDocument.aspx?d=1391656
    on 2026-05-03; LegiScan tracking
    https://legiscan.com/LA/bill/HB10/2024/X3
  - **Act 10 of 2024 3rd Extraordinary Session (HB 8)** -- imposed
    state sales tax on digital products (audiovisual works, audio,
    books, games, codes, periodicals, SaaS / remotely accessed
    software) effective 2025-01-01. LDR digital-products guidance
    (LDR document 11.20.25) -- retrieved
    https://dam.ldr.la.gov/lawspolicies/Digital%20Products%20Guidance%2011.20.25(r).pdf
    on 2026-05-03 (link surfaced via Sales Tax Institute summary;
    direct fetch attempted).
  - **La. R.S. 47:301** et seq. -- Louisiana sales and use tax
    chapter. Statutes index retrieved 2026-05-03 via
    https://www.legis.la.gov/legis/.
  - **La. R.S. 47:302, 47:321, 47:321.1, 47:331, 47:332** --
    statutory rate layers that sum to the headline 5%; cited via
    LDR FAQ "What is the state sales tax rate?".
  - **La. R.S. 47:305(D)** -- enumerated state-level exclusions
    and exemptions (food sold for preparation and consumption in
    the home, fresh fruit and vegetables, and others). 2025
    renumbering noted by Act 11. Full statute retrieved
    https://www.legis.la.gov/Legis/Law.aspx?d=101873 on
    2026-05-03.
  - **La. R.S. 47:305.10** -- prescription drugs prescribed by
    physician or dentist. Cross-referenced via LawServer.
  - **La. R.S. 47:305.62** -- "Annual Louisiana Second Amendment
    Weekend Holiday Act"; first consecutive Friday-Sunday of
    September; firearms/ammunition/hunting supplies; no per-item
    cap; applies to "the state of Louisiana and its political
    subdivisions" (state AND parish). Effective 2009-07-09 with
    2023-07-01 amendments. Full statute retrieved
    https://www.legis.la.gov/Legis/Law.aspx?d=672126 on
    2026-05-03; landing page
    https://revenue.louisiana.gov/secondamendment/ on 2026-05-03;
    LDR Revenue Information Bulletin 25-017
    https://dam.ldr.la.gov/lawspolicies/RIB%2025-017%202nd%20Amendment%20Holiday.pdf
    on 2026-05-03 (confirmed 2025 holiday dates Sept 5-7, 2025;
    2026 dates Sept 4-6, 2026 follow the same statutory formula).
  - **La. R.S. 47:305.54** -- Annual Louisiana Sales Tax Holiday
    (back-to-school, suspended 2018-2025; reauthorization HB 551
    failed 2025-06-12).
  - **La. R.S. 47:305.58** -- Annual Louisiana Hurricane
    Preparedness Sales Tax Holiday (suspended; not reauthorized
    for 2026).
  - **La. R.S. 47:337.1** et seq. -- Uniform Local Sales Tax Code;
    framework under which 64 parishes administer their own
    independent local taxes.
  - **La. R.S. 47:337.11.1** -- conditions parish taxation of
    prescription drugs on parish local-board procedures.
  - **La. R.S. 47:339.1** -- Louisiana Sales and Use Tax
    Commission for Remote Sellers (sole entity for remote-seller
    state + local collection). Retrieved
    https://law.justia.com/codes/louisiana/revised-statutes/title-47/rs-47-339-1/
    on 2026-05-03.
  - **La. Const. Art. VII section 2.2** -- constitutional
    protection for the state-level exemptions on groceries,
    residential utilities, and prescription drugs. Cross-referenced
    via LDR FAQ on the Constitutional Amendment effect.
- *Sources for rate/taxability (cross-references, NOT primary):*
  - LDR FAQ "What is the state sales tax rate?" --
    https://revenue.louisiana.gov/tax-education-and-faqs/faqs/sales-tax-reform/what-is-the-state-sales-tax-rate/
    (retrieved 2026-05-03; confirmed 5% effective 2025-01-01
    through 2029-12-31).
  - LDR FAQ "How does the amendment affect sales taxes charged on
    groceries, utilities, and prescription drugs?" --
    https://revenue.louisiana.gov/tax-education-and-faqs/faqs/constitutional-amendment/does-it-affect-sales-taxes-charged-on-groceries-utilities-and-prescription-drugs/
    (retrieved 2026-05-03; confirmed exemptions retained at the
    state level).
  - LDR FAQ "Which sales and use tax exemptions were repealed as
    of January 1, 2025?" --
    https://revenue.louisiana.gov/tax-education-and-faqs/faqs/sales-tax-reform/which-sales-and-use-tax-exemptions-are-being-repealed/
    (retrieved 2026-05-03).
  - LDR FAQ on digital products --
    https://revenue.louisiana.gov/tax-education-and-faqs/faqs/sales-tax-reform/are-digital-products-subject-to-sales-and-use-tax/
    (retrieved 2026-05-03 via search).
  - Sales Tax Institute "Louisiana to Increase State Sales Tax
    Rate" -- https://www.salestaxinstitute.com/resources/louisiana-to-increase-state-sales-tax-rate
    (cross-check on Act 11 effective dates).
  - Eide Bailly "Significant Louisiana Sales and Use Tax
    Legislative Changes Take Effect January 1, 2025" --
    https://www.eidebailly.com/insights/blogs/2024/12/20241220_louisiana
    (cross-check on Act 11 / Act 10 scope).
  - Baker Tilly / Moss Adams summaries on Louisiana digital
    products taxation (cross-checks on Act 10 / HB 8).
  - Advantous Consulting 2025 Legislative Session sales-tax update
    -- https://advantous.com/louisiana-2025-legislative-session-sales-use-tax-update/
    (confirmed HB 551 back-to-school reauthorization died).
  - ITEP Sales Tax Holidays 2025 -- https://itep.org/sales-tax-holidays-2025/
    (cross-state holiday summary; corroborates LA's holiday
    landscape).
  - Yahoo News "Louisiana has a 'Second Amendment Sales Tax
    Holiday' but back-to-school tax holiday suspended" --
    https://www.yahoo.com/news/articles/louisiana-second-amendment-sales-tax-121528311.html
    (popular-press cross-check on holiday status).
  - Sovos State-by-State Guide LA entry (general cross-check;
    NOT used as a primary source per constitution section 3 -- the
    Sovos summary has documented errors and is research-only).
- **Module file:** `src/opensalestax/states/louisiana.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (Phase 6 Batch B / v0.7)
- *Notes:*
  - **Parish-tax limitation is THE defining issue for LA.** A
    v0.7 caller will materially under-collect tax for any LA
    address. The module docstring, the class docstring, the
    grocery TaxabilityRule notes, and the general TaxabilityRule
    notes all surface this; an explicit unit test verifies the
    docstring documentation. See
    `specs/decisions/05-louisiana-parishes.md`.
  - **Rate is TEMPORARY.** The 5% rate sunsets 2029-12-31; the
    RateRow's ``effective_to`` is encoded so that on 2030-01-01
    the row will self-expire. A future module update needs to add
    the 4.75% successor row when 2030 approaches and the
    legislature has confirmed (or amended) the step-down.
  - **Digital goods is a 2025-01-01 change.** Pre-2025 LA generally
    did not tax digital products. The TaxabilityRule notes call
    out the Act 10 / HB 8 origin so a future maintainer doesn't
    mistake the current treatment for a long-standing position.
  - **Constitutional protection** for groceries / residential
    utilities / prescription drugs at the state level was
    confirmed by the November 2025 constitutional amendment per
    LDR FAQ. This module assumes that protection holds.
  - **Second Amendment Weekend Holiday** is the only currently
    active LA holiday. Two others (back-to-school R.S. 47:305.54
    and hurricane prep R.S. 47:305.58) have been suspended for
    years; HB 551 (2025) tried to reauthorize back-to-school and
    failed on 2025-06-12. Subsequent legislative sessions may
    reauthorize either; the ``holidays_for(year)`` method
    intentionally returns the empty iterable for years other than
    2026 so a future maintainer must explicitly add data when
    holidays are reauthorized.

## GA — Georgia

- **Statewide rate:** **4.0% effective 2011-01-01** per O.C.G.A.
  section 48-8-30 (state base) and the GA SST rate file
  (`13,45,13,0.04,0.04,0,0,20110101,29991231` confirms the rate
  effective from GA's SST associate-membership start). The 0 in
  the food-rate column reflects the state-portion grocery
  exemption; the 0 in the drug-rate column reflects the
  prescription-drug exemption.
- **Tax model:** sales tax (SST FULL member effective 2011-07-01,
  associate member effective 2011-01-01)
- **Local jurisdictions:** counties (LOST + SPLOST + ELOST + HOST
  stack), cities (limited; the City of Atlanta MOST is the
  notable example), special districts (TSPLOST regional
  districts + the MARTA district)
- **Sales-tax holidays:** **NONE** -- the last GA sales-tax
  holiday was in 2016 (Ga. Comp. R. and Regs. R. 560-12-2-.110
  was the implementing rule). The General Assembly has not re-
  enacted any sales-tax holiday since; reauthorization bills
  introduced in 2024-2025 (S.B. 115, S.B. 527, S.B. 555) did
  not pass.
- **Threshold rules:** none
- **DOR URL:** https://dor.georgia.gov/taxes/business-taxes/sales-use-tax
  (retrieved 2026-05-03)
- **Statutes / regulations consulted:**
  - O.C.G.A. section 48-8-30 (imposition of tax; 4% state rate)
  - O.C.G.A. section 48-8-3(54) (prescription-drug exemption)
  - O.C.G.A. section 48-8-3(57) (food and food ingredients;
    state-only exemption that does NOT apply to local sales taxes
    except in equalized homestead-option counties under section
    48-8-104)
  - O.C.G.A. section 48-8-80 et seq. (LOST -- Local Option Sales
    Tax)
  - O.C.G.A. section 48-8-100 et seq. (HOST -- Homestead Option
    Sales Tax)
  - O.C.G.A. section 48-8-110 et seq. (SPLOST -- Special Purpose
    Local Option Sales Tax)
  - O.C.G.A. section 48-8-141 et seq. (ELOST -- Educational
    SPLOST)
  - O.C.G.A. section 48-8-200 et seq. (MOST -- Municipal Option
    Sales Tax; City of Atlanta)
  - O.C.G.A. section 48-8-240 et seq. (TSPLOST -- Transportation
    SPLOST)
  - Ga. Comp. R. and Regs. R. 560-12-2-.118 (Digital Products,
    Goods, and Codes; SUT 2024-001 implementing H.B. 170, Laws
    2023; effective 2024-01-01)
  - Ga. Comp. R. and Regs. R. 560-12-2-.110 (Sales Tax Holidays;
    historical -- last applied to 2016 holidays)
- *Sources for rate / taxability:*
  - GA SST quarterly rate file `GAR2026Q2FEB19.csv` (downloaded
    from `https://www.streamlinedsalestax.org/ratesandboundry/Rates/`,
    retrieved 2026-05-03; bundled as
    `src/opensalestax/data/fixtures/ga/GAR2026Q2FEB19.csv`)
  - SST member-detail page for Georgia
    (`https://www.streamlinedsalestax.org/state-details/georgia`),
    retrieved 2026-05-03 -- confirms full membership effective
    2011-07-01
  - Sales Tax Institute "Digital Products Subject to Georgia
    Sales and Use Tax Effective January 1, 2024"
    (`https://www.salestaxinstitute.com/resources/digital-products-subject-to-georgia-sales-and-use-tax-effective-january-1-2024`),
    retrieved 2026-05-03 -- secondary source for the 2024-01-01
    digital-goods change; primary source is R. 560-12-2-.118
  - GBPI "Time to Retire Georgia's Sales Tax Holidays"
    (`https://gbpi.org/time-to-retire-georgias-sales-tax-holidays/`),
    retrieved 2026-05-03 -- documents the 2016 holiday end and
    the legislative inaction on reauthorization
  - 11Alive "VERIFY: Georgia does not offer a sales tax holiday
    for back-to-school"
    (`https://www.11alive.com/article/news/verify/georgia-no-tax-free-holiday-2025-verify/85-13f08e65-1e48-4fe1-af49-dba452711c5a`),
    retrieved 2026-05-03 -- secondary source confirming no GA
    sales-tax holiday post-2016
  - GA DOR "2016 Sales Tax Holidays" press release
    (`https://dor.georgia.gov/press-releases/2016-04-27/2016-sales-tax-holidays`),
    retrieved 2026-05-03 -- the most recent official GA DOR
    holiday notice
- **Module file:** `src/opensalestax/states/georgia.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (Phase 7 / GA tier-2 -> tier-1 promotion)
- *Notes:*
  - **State-vs-local grocery split is THE defining quirk for GA.**
    The grocery exemption applies ONLY to the 4% state portion
    per O.C.G.A. section 48-8-3(57); the local LOST + SPLOST +
    ELOST + HOST + TSPLOST + MOST stack still applies (with the
    narrow homestead-option exception under section 48-8-104).
    v0.7+ marks groceries non-taxable at the combined-rate level
    consistent with the engine's single-rate-per-authority
    evaluation; the LA module sets the same precedent and a
    future per-jurisdiction taxability override will model the
    state-vs-local split precisely. Until then the engine
    under-collects on GA groceries by the local portion (~3%);
    the API disclaimer covers this.
  - **Digital goods is a 2024-01-01 change.** Pre-2024 GA
    generally did not tax digital products. The TaxabilityRule
    notes call out R. 560-12-2-.118 / H.B. 170 / SUT 2024-001
    so a future maintainer doesn't mistake the current
    treatment for a long-standing position.
  - **No holidays since 2016.** The `holidays_for(year)` method
    intentionally returns the empty iterable for EVERY year
    (parametrized regression test exercises 2024-2030). Should
    a future General Assembly session re-authorize a holiday, a
    maintainer must explicitly add the year's data; the empty
    iterable is regression protection (the 2024-2025 bills
    failed and the project does not pre-encode speculative
    legislation).
  - **SST jurisdiction-type codes** are the same MN/WI mapping:
    `45` = state, `00` = county, `01` = city, `63` = special
    district. Validated against `GAR2026Q2FEB19.csv` (449
    rows): 1 state row, 432 county rows, 12 city rows, 4
    special-district rows. The bulk of GA local taxation is
    encoded in the county rows because most GA local-option
    taxes are county-level.

### Tier-2 SST states (rate-only, default taxability)

14 states load via the generic `SstStateModule` in
`src/opensalestax/states/_tier2.py`:

NV, NJ, NC, ND, OH, OK, RI, SD, TN,
UT, VT, WA, WV, WY

(AR, GA, IA, IN promoted in v0.8; KS, KY, MI, NE in v0.9 --
see their dedicated sections in this document.)

## IA -- Iowa

- **Statewide rate:** **6.000% effective 2008-07-01** (raised from
  5% to 6% by Senate File 2400 of the 82nd General Assembly,
  effective July 1, 2008; codified at Iowa Code section 423.2)
- **Tax model:** sales tax (SST member -- per-jurisdiction rates
  load via the standard SST quarterly file)
- **Local jurisdictions:** counties + incorporated cities may
  impose a 1% Local Option Sales Tax (LOST) under Iowa Code
  chapter 423B by voter approval; combined rates typically 6-7%
  statewide. SST member status means rate data flows through the
  inherited :class:`SstStateModule` parser; no manual loader
  needed.
- **Sales-tax holidays:** 1 annual statutory holiday (Iowa Annual
  Sales Tax Holiday, first Friday and Saturday in August, per
  Iowa Code section 423.3(68); clothing/footwear under $100 per
  article, accessories and athletic wear excluded)
- **Threshold rules:** the August holiday's $100 per-article cap
  is encoded as ``HolidayWindow.max_amount_per_item``. Note: the
  statutory threshold is "less than $100" (strict <, not <=);
  documented in HolidayWindow.notes for the v0.6+ threshold-rule
  enforcement layer.
- **DOR URL:** **https://tax.iowa.gov** *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - Iowa Code section 423.2 -- imposition of state sales tax
    (6% rate; raised from 5% effective 2008-07-01 by S.F. 2400,
    82nd G.A.)
  - Iowa Code section 423.3(57) -- exemption for food and food
    ingredients (uniform SST definition; excludes prepared food,
    candy, soft drinks, dietary supplements)
  - Iowa Code section 423.3(60) -- exemption for prescription
    drugs and related items (insulin, hypodermic syringes for
    human use, oxygen equipment for human use, prosthetic
    devices)
  - Iowa Code section 423.3(68) -- annual sales tax holiday
    (first Friday in August at 12:01 a.m. through following
    Saturday at 11:59 p.m.; clothing and footwear under $100
    per article; accessories and athletic / protective clothing
    excluded)
  - Iowa Code section 423.5A -- imposition of sales tax on
    specified digital products (added by H.F. 779 of the 87th
    G.A., effective 2019-01-01); covers digital audio works,
    digital audiovisual works, digital books, and "other
    digital products" delivered electronically -- whether sold
    with a permanent right of use or under a subscription /
    conditional access model
  - Iowa Code section 423.3(47) -- USE-based exemption for
    certain computer-related purchases by manufacturers /
    insurers / financial institutions / commercial enterprises
    (NOT modeled in the general taxability matrix; applies at
    the line-item exemption-certificate level)
  - Iowa Code chapter 423B -- Local Option Sales Tax authority
    (city/county-level 1% LOST by voter approval)
- *Sources for rate/taxability:* Iowa Department of Revenue
  guidance pages (tax.iowa.gov) cross-referenced with the Iowa
  General Assembly's online code (https://www.legis.iowa.gov)
  and the Streamlined Sales Tax Project member roster
  (https://www.streamlinedsalestax.org). Sovos summary entry
  for Iowa was used as a starting cross-check (confirmed 6%
  rate, sales tax holiday "first Friday and Saturday in
  August", clothing/footwear focus); statutory citations
  verified directly against Iowa Code chapter 423.
- **Module file:** `src/opensalestax/states/iowa.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (Phase 7 -- first SST tier-2 -> tier-1 promotion)
- *Notes:*
  - IA is the FIRST SST tier-2 -> tier-1 promotion. The module
    subclasses :class:`SstStateModule` per the brief's
    "tier-2 -> tier-1" pattern (lines 124-141 of
    `specs/agent-briefs/per-state-research-brief.md`); rate
    parsing is inherited from the base, only the taxability
    matrix and the August holiday are overridden. Other tier-2
    SST promotions should follow this same pattern.
  - SST jurisdiction-type code mapping for IA defaults to the
    MN/WI scheme (00 county / 01 city / 45 state / 63 district)
    inherited from :data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`.
    No 2026Q2 IA SST file has been captured to confirm the
    codes empirically; the next maintainer should validate
    against an Iowa SST quarterly capture and override
    ``jurisdiction_types`` on the subclass if any code differs.
    Documented as a follow-up rather than a blocker because
    the SST file format is uniform across the membership in
    every other state where we have data.
  - Iowa is one of the few states that taxes specified digital
    products explicitly via a dedicated statute (section 423.5A)
    rather than via an interpretive expansion of the TPP
    definition. The statute is broad: subscription / SaaS-style
    digital media delivery is taxable in Iowa, in contrast to
    e.g. Idaho where SaaS is excluded from TPP.
  - The August holiday's "less than $100" threshold is strict
    (an article priced at exactly $100 does NOT qualify). The
    HolidayWindow.max_amount_per_item field stores this as
    ``Decimal("100.00")``; downstream callers implementing the
    threshold rule should compare with ``<``, not ``<=``.
  - Iowa Code section 423.3(47) (manufacturer software exemption)
    is a USE-based exemption that the general matrix does not
    model. Downstream callers shipping software to Iowa
    manufacturers should apply a line-item exemption certificate
    rather than relying on the per-state default.

### IN -- Indiana

- **Statewide rate:** **7.000% effective 2008-04-01** (raised from
  6% to 7% by P.L. 146-2008 to fund property-tax relief; the 7%
  rate has been stable since)
- **Tax model:** sales tax (SST -- full member; verified 2026-05-03
  against the SST member roster on streamlinedsalestax.org)
- **Local jurisdictions:** **NONE.** Indiana levies NO local sales
  tax. The 7% state rate is the entire combined rate at every
  Indiana address. A handful of related local taxes exist (county-
  option innkeeper taxes on lodging, food-and-beverage taxes in
  select municipalities authorized by individual local-and-private-
  laws acts) but those are narrow industry-specific levies and are
  NOT general sales taxes. This is a notable contrast with peer
  SST member states (e.g. WI's counties typically add 0.5%; MN's
  metro adds transit districts) and one of the defining
  simplifications in Indiana's rate-stack model.
- **Sales-tax holidays:** **NONE.** Indiana has never enacted a
  recurring sales-tax holiday. Confirmed 2026-05-03 against the
  Indiana Department of Revenue's published guidance and a search
  of Article 2.5 for any periodic exemption window. ``holidays_for(year)``
  returns the empty iterator for every year (mirrors DC and ID).
- **Threshold rules:** none.
- **DOR URL:** **https://www.in.gov/dor/** *(retrieved 2026-05-03)*
- **Statutes consulted (Ind. Code Title 6, Article 2.5 -- gross
  retail and use taxes):**
  - Ind. Code section 6-2.5-2-1 -- imposition of the state gross
    retail tax on retail transactions
  - Ind. Code section 6-2.5-2-2(a) -- 7% state gross retail tax
    rate (P.L. 146-2008, eff. 2008-04-01)
  - Ind. Code section 6-2.5-1-27 -- definition of tangible personal
    property
  - Ind. Code section 6-2.5-4-16.4 -- imposition of sales/use tax on
    transferred specified digital products (eff. 2018-07-01 under
    H.E.A. 1316-2018)
  - Ind. Code section 6-2.5-5-19 -- exemption for prescription
    drugs, insulin, oxygen, blood, and certain medical/durable
    equipment when prescribed
  - Ind. Code section 6-2.5-5-20 -- exemption for food and food
    ingredients for human consumption (excluding candy, dietary
    supplements, soft drinks, alcoholic beverages, tobacco, and
    prepared food)
- *Sources for rate/taxability:*
  - Indiana Department of Revenue Sales Tax landing page
    (https://www.in.gov/dor/business-tax/sales-tax/), retrieved
    2026-05-03 -- confirms 7% statewide rate and no local sales tax
  - Indiana Department of Revenue Information Bulletin #8 (Sales of
    Computer Hardware, Software, and Digital Goods) -- most recent
    revision December 2024, retrieved 2026-05-03; primary source
    for the SaaS / remotely-accessed-software taxability position
    cited in the digital-goods rule
  - Indiana General Assembly online statutes (Title 6, Article 2.5)
    at http://iga.in.gov/laws/2024/ic/titles/6/, retrieved 2026-05-03
    -- primary source for every statutory citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Indiana is a full member
- **Module file:** `src/opensalestax/states/indiana.py`
- **Last verified:** 2026-05-03 by per-state research agent (Phase
  7 -- tier-2 to tier-1 promotion)
- *Notes:*
  - **No local sales tax** is the headline distinction. The
    module's ``jurisdiction_types`` dict accepts ONLY the
    state-level SST type code ``"45"`` so any unexpected non-state
    row in a future quarterly file is silently dropped rather
    than miscategorized as a sub-state authority Indiana doesn't
    have. Documented prominently in the module docstring and
    enforced by a regression test.
  - **Digital goods is a 2018-07-01 change.** Pre-2018 IN's
    sales tax did not reach electronically-delivered specified
    digital products. The TaxabilityRule notes call out the
    H.E.A. 1316-2018 origin so a future maintainer doesn't
    mistake the current treatment for a long-standing position.
  - **SaaS distinction lives in Information Bulletin #8.**
    Indiana taxes prewritten ("canned") software delivered
    electronically but does NOT tax true SaaS / remotely accessed
    software (where the customer takes neither possession nor
    control of the software). The dominant case (specified
    digital products with permanent right of use) is encoded as
    taxable; the SaaS exception is documented in the
    digital_goods rule's notes for follow-up if/when a sub-
    category split lands.
  - **Narrow local food-and-beverage / innkeeper taxes** exist in
    a handful of Indiana municipalities (Marion County food-and-
    beverage tax, county-option innkeeper taxes) but are NOT
    modeled by this module -- they are narrow industry-specific
    levies authorized by individual local-and-private-laws acts,
    not general sales taxes. Documented in the module docstring
    for the next maintainer who chooses to model lodging or
    F&B-specific calculations.
  - **Rate is stable.** The 7% rate has been in place since
    2008-04-01; no scheduled change is currently in the
    legislative pipeline that this research found.

## NV — Nevada

- **Statewide rate:** **6.850% statewide minimum combined rate**
  (no single-statute headline rate; the 6.85% is the sum of three
  state-level statutory layers that all 17 Nevada counties impose
  -- see "Rate composition" below).
- **Tax model:** sales tax (SST -- full member; verified 2026-05-03
  against the SST member roster on streamlinedsalestax.org). State
  FIPS: 32.
- **Rate composition (the 6.85% statewide minimum):**
  - **2.00%** -- State Sales Tax under NRS Chapter 372 (Nevada Sales
    and Use Tax Act of 1955; NRS section 372.105 sets the rate).
    This portion is constitutionally entrenched against repeal
    without a 2/3 legislative supermajority because the underlying
    1955 act was adopted by initiative petition.
  - **2.60%** -- Local School Support Tax (LSST) under NRS Chapter
    374, NRS section 374.110 -- imposed statewide in every county
    to fund K-12 education.
  - **2.25%** -- City-County Relief Tax components (Basic City-
    County Relief Tax + City-County Relief Tax) under NRS Chapter
    377 -- a state-level revenue-sharing layer that returns
    proceeds to local governments.
  - **TOTAL: 2.00 + 2.60 + 2.25 = 6.85%** statewide minimum. The
    6.85% is the rate that flows through the SST quarterly file's
    "general rate" column for every Nevada county; the underlying
    split is documented for a future maintainer who wants to model
    fund distributions but is not required for v1 calculation.
- **Local jurisdictions:** Nevada's 17 counties may add county-
  option taxes (per NRS Chapters 377A, 377B, and various county-
  specific enabling statutes). **Per-county add-ons are NOT
  modeled in v1.** Notable add-ons:
  - **Clark County** (Las Vegas / Henderson / North Las Vegas /
    Boulder City): adds approximately 1.525%, for a combined rate
    of approximately **8.375%** -- the highest in Nevada and
    applicable to the bulk of Nevada's transaction volume (Clark
    contains roughly 73% of state population).
  - **Washoe County** (Reno / Sparks): adds approximately 1.415%,
    for a combined rate of approximately **8.265%**.
  - Other counties add smaller increments; rural counties remain
    at or near the 6.85% statewide minimum.
  - The deferred-locals decision follows the same pattern as v0.7
    Louisiana parishes (~64 deferred), v0.6 South Carolina
    counties, and v0.7 Missouri / Mississippi local-option taxes
    -- under-collection on Las Vegas / Reno addresses by ~1.5%
    until per-county data is loaded.
- **Sales-tax holidays:** **ONE statutory holiday in current
  law -- but NOT modeled in v1.** Nevada's only sales-tax holiday
  is the Nevada National Guard Sales Tax Holiday under NRS section
  372.7282 (Friday-Saturday-Sunday closest to Nevada Day,
  October 31; exempts ALL sales of TPP to active members of the
  Nevada National Guard and their immediate families upon
  presentation of qualifying ID; no per-item dollar cap; no
  category restriction). This is structurally different from every
  other state holiday currently modeled by OpenSalesTax: it is
  defined by **buyer eligibility** (active Nevada Guard member or
  family) rather than by item category + date + per-item cap.
  The OpenSalesTax engine's :class:`HolidayWindow` /
  :class:`HolidayPeriod` schema does not currently model buyer
  eligibility, and there is no exemption-certificate mechanism on
  the calculation request. If the holiday were yielded as a
  date-only / category-wide HolidayWindow, the engine would zero
  out tax on EVERY Nevada transaction during the 3-day window for
  EVERY buyer regardless of National Guard status -- a systematic
  under-collection bug for every NV retailer's general consumer
  base. **v1 decision: ``Nevada.holidays_for`` returns the empty
  iterator for every year.** The holiday is documented here, in
  the module docstring, and in MAINTAINERS.md but is NOT exposed
  to the calculation engine until a future PR (gated on the engine
  growing a buyer-eligibility / exemption-certificate model)
  re-enables it as a buyer-class-restricted exemption.
- **Threshold rules:** none.
- **DOR URL:** **https://tax.nv.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted (NRS Chapter 372 -- Sales and Use Tax,
  Chapter 374 -- LSST, Chapter 377 -- City-County Relief Tax):**
  - NRS section 372.085 -- definition of tangible personal
    property (limits sales-tax base to property "capable of being
    seen, weighed, measured, felt, or touched" -- the basis for
    Nevada's not taxing electronically-delivered digital products)
  - NRS section 372.105 -- imposition of the State Sales Tax at
    2.00% (the State portion of the 6.85% statewide minimum)
  - NRS section 372.283 -- exemption for prescription medicines
    and certain related items (insulin, oxygen for medical use,
    prosthetic devices when prescribed)
  - NRS section 372.284 -- exemption for food for human
    consumption (the grocery exemption; tracks the SST uniform
    "food and food ingredients" definition; excludes candy, soft
    drinks, dietary supplements, and prepared food)
  - NRS section 372.7282 -- Nevada National Guard Sales Tax
    Holiday (3-day buyer-eligibility holiday around Nevada Day;
    NOT modeled in v1)
  - NRS Chapter 374 / NRS section 374.110 -- Local School Support
    Tax imposition at 2.60% in every county
  - NRS Chapter 377 -- City-County Relief Tax components
    (combined 2.25% in every county)
  - NRS Chapters 377A / 377B and county-specific enabling acts --
    authority for county-option add-on taxes (Clark / Washoe / etc.)
  - Nevada Constitution Article 10 section 3 -- constitutional
    entrenchment of the food-for-human-consumption exemption
    against legislative repeal (added by initiative 1979)
- *Sources for rate/taxability:*
  - **Nevada Department of Taxation** main page
    (https://tax.nv.gov/), retrieved 2026-05-03 -- confirms the
    6.85% statewide minimum as the headline rate and identifies
    Nevada as an SST member
  - **Nevada Department of Taxation Sales Tax Map / quarterly
    rate publication** (downloaded via tax.nv.gov), retrieved
    2026-05-03 -- confirms 6.85% statewide minimum and the per-
    county add-on amounts (Clark 8.375% / Washoe 8.265% / etc.)
  - **Nevada Legislative Counsel Bureau** online statutes
    (https://www.leg.state.nv.us/NRS/), cross-referenced
    2026-05-03 -- primary source for every NRS citation above
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Nevada is a full SST
    member
  - **Sovos summary entry for Nevada** -- used as starting cross-
    check (confirmed 6.85% rate, grocery exemption, prescription
    drug exemption); statutory citations verified directly against
    NRS Chapter 372
- **Module file:** `src/opensalestax/states/nevada.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-nv branch; Phase 7 Batch P2 -- second SST tier-2
  to tier-1 promotion batch)
- *Notes:*
  - **The buyer-eligibility holiday is the headline finding.** Of
    every state currently modeled (or under research) by
    OpenSalesTax, Nevada is the only one whose sole statutory
    sales-tax holiday is buyer-eligibility-restricted rather than
    category / date / per-item-cap-restricted. This makes Nevada
    a useful test case / motivating example for the future
    exemption-certificate / buyer-eligibility feature in the
    engine roadmap. When that feature lands, ``Nevada.holidays_for``
    can re-enable the National Guard holiday with a buyer-class
    constraint; the v1 documentation in the module docstring and
    in this references entry should be the source of truth for
    that future work.
  - **Digital goods is the second notable finding.** Unlike Iowa
    (Iowa Code 423.5A) and Indiana (Ind. Code 6-2.5-4-16.4),
    Nevada has NOT enacted a sales-tax expansion to specified
    digital products. The Nevada Department of Taxation's
    longstanding position is that electronically-delivered ebooks,
    streaming subscriptions, downloaded software, SaaS, and
    similar are NOT taxable because they fail the tangibility
    requirement of NRS section 372.085. Prewritten ("canned")
    software delivered on a physical medium IS taxable as TPP;
    the same software delivered electronically is NOT.
  - **Per-county add-ons (Clark / Washoe / etc.) are deferred.**
    Same trade-off pattern as LA parishes / SC counties /
    MO+MS local-option taxes. A v1 caller calculating tax on a
    Las Vegas or Reno address will under-collect by ~1.5%. The
    natural next maintenance task is to validate an empirical NV
    SST quarterly rate file and confirm that the inherited
    :class:`SstStateModule` parser picks up the per-county rows
    correctly with the default jurisdiction-type code mapping.
  - **Rate-composition decomposition is documentary only.** The
    engine does not need the 2.00 / 2.60 / 2.25 split for
    calculation; v1 ships a single 6.85% combined row. The split
    is documented for the future maintainer who wants to model
    fund distributions (LSST to schools, CCRT to local
    governments) separately.
  - **Constitutional entrenchment of the grocery exemption.**
    Article 10 section 3 of the Nevada Constitution (added by
    initiative petition in 1979) blocks legislative repeal of the
    food-for-human-consumption exemption without a popular vote.
    Documented for the maintainer who one day sees a legislative
    proposal touching NRS 372.284 and wonders why the legislature
    is not simply amending the statute.


Each has a one-class entry there with state_abbrev + state_name +
state_fips. They use the SST quarterly data files for rates and
default taxability (everything taxable except groceries). To
**promote one to tier 1**, follow `per-state-research-brief.md`:

- Look up the state's actual taxability matrix from the state DOR
- Cite statutes
- Add a dedicated module under `src/opensalestax/states/<name>.py`
- Remove the entry from `_tier2.py`

### AR -- Arkansas

- **Statewide rate:** **6.500% effective 2013-07-01** (current
  rate per AR DFA "State Sales & Use Tax Rates" page)
- **Tax model:** sales tax (Arkansas Gross Receipts Tax, Title 26
  Chapter 52)
- **Local jurisdictions:** 75 counties + many cities; SST member
  with quarterly rate file by FIPS code (state FIPS = 05)
- **Sales-tax holidays:** 1 annual (Back-to-School, first Saturday
  and Sunday of August)
- **Threshold rules:** holiday-specific only -- clothing under
  $100/item, clothing accessories under $50/item; school
  supplies / school art supplies / school instructional materials
  / electronic devices have NO per-item cap
- **Reduced rates:** groceries (food and food ingredients)
  taxed at the **state-portion 0.000% rate effective 2026-01-01**
  per the Grocery Tax Relief Act amending Ark. Code Ann.
  section 26-52-317. Local sales tax still applies. Encoded with
  `rate_modifier=Decimal("0.000")` per the IL/MS/VA pattern.
- **DOR URL:** **https://www.dfa.arkansas.gov/office/taxes/excise-tax-administration/sales-use-tax/**
  *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - Ark. Code Ann. section 26-52-301 -- general sales tax
    imposition; current 6.5% state rate
  - Ark. Code Ann. section 26-52-317 -- food and food ingredients
    reduced rate (currently 0.000% post-Grocery Tax Relief Act,
    effective 2026-01-01; previously 0.125% from 2019-01-01;
    1.5% from 2011-07-01 to 2018-12-31)
  - Ark. Code Ann. section 26-52-406 -- prescription drugs and
    oxygen exemption
  - Ark. Code Ann. section 26-52-444 -- annual back-to-school
    sales tax holiday (definitions + per-item caps)
  - Act 141 of 2017 (H.B. 1162) -- specified digital products
    and digital codes brought into the sales-tax base, effective
    2018-01-01
  - Act 944 of 2021 -- electronic devices added to section
    26-52-444 sales tax holiday scope
- *Sources for rate/taxability:*
  - **Arkansas DFA** "State Sales & Use Tax Rates" page,
    https://www.dfa.arkansas.gov/office/taxes/excise-tax-administration/sales-use-tax/sales-use-tax-rates/state-sales-use-tax-rates/
    (retrieved 2026-05-03; 6.5% general rate effective
    2013-07-01; reduced food rate 0.000% effective 2026-01-01)
  - **Arkansas DFA 2026 Sales Tax Holiday** page,
    https://www.dfa.arkansas.gov/office/taxes/excise-tax-administration/sales-use-tax/2024-sales-tax-holiday/
    (retrieved 2026-05-03; confirmed 2026 dates Aug 1-2 and the
    five+one exempt categories)
  - **Arkansas DFA Streamlined Sales Tax Project** page,
    https://www.dfa.arkansas.gov/office/taxes/excise-tax-administration/sales-use-tax/streamlined-sales-tax-project/
    (retrieved 2026-05-03; confirmed SST membership, FIPS-based
    rate database structure)
  - **Justia codes mirror** of Ark. Code Ann. sections 26-52-301,
    26-52-317, 26-52-406, 26-52-444 (cross-referenced for
    statutory text; primary source is the AR DFA / arkleg.state.ar.us)
  - **Sales Tax Institute** "Specified Digital Products...
    Effective January 1, 2018" article confirming Act 141 of
    2017 (H.B. 1162) effective date
  - **Sales Tax Institute** "Arkansas Includes Electronic
    Devices for Sales Tax Holiday" confirming Act 944 of 2021
    addition
  - **Free Tax Weekend 2026** cross-reference for AR holiday
    dates (used as one input among many; primary source is the
    AR DFA holiday page)
- **Module file:** `src/opensalestax/states/arkansas.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ar branch)
- *Notes:*
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    AR's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district),
    documented in the module docstring. Validating against an
    actual `ARR<...>.csv` file is the natural next maintenance
    task.
  - **Grocery rate change**: as of January 1, 2026 AR became one
    of a small number of states that fully exempt the state
    portion on groceries (joining the SC, VA, MS pattern of
    reduced grocery rates). Local rates still apply.
  - **Holiday includes electronics** (Act 944 of 2021) without a
    per-item cap, distinguishing AR's holiday from many peers.
  - The holiday exempts BOTH state AND local sales/use tax
    during the window.

### KS -- Kansas

- **Statewide rate:** **6.500% effective 2015-07-01** (raised from
  5.3% to 6.5% by 2015 House Substitute for Senate Bill 270;
  stable at 6.5% since)
- **Tax model:** sales tax (SST -- full member; verified 2026-05-03
  against the SST member roster on streamlinedsalestax.org)
- **Local jurisdictions:** counties + cities + special districts
  (Community Improvement Districts -- CIDs under K.S.A. chapter
  12, article 60; Transportation Development Districts -- TDDs
  under K.S.A. chapter 12, article 17; Star Bonds and
  redevelopment districts). Combined rates commonly fall in the
  8-11% range, with the highest rates appearing inside CIDs in
  major-metro retail corridors. SST member status means rate data
  flows through the inherited :class:`SstStateModule` parser.
- **Sales-tax holidays:** **NONE.** Kansas has never enacted a
  recurring sales-tax holiday. Confirmed 2026-05-03 against the
  Kansas Department of Revenue's published guidance and a search
  of K.S.A. chapter 79, article 36 for any periodic exemption
  window. Multiple legislative proposals (most recently 2024 H.B.
  2680 proposing a back-to-school holiday) have been introduced
  but none has passed. ``holidays_for(year)`` returns the empty
  iterator for every year (mirrors DC, ID, and IN).
- **Threshold rules:** none.
- **Reduced rates:** **groceries (food and food ingredients)
  taxed at the state-portion 0.000% rate effective 2025-01-01**
  per the Kansas grocery rate phase-down enacted by Senate
  Substitute for House Bill 2106 (2022 session), codified at
  K.S.A. section 79-3603(p). MAJOR RECENT CHANGE -- phase-down
  history:

    - Pre-2023-01-01: 6.5% state rate (full general rate)
    - 2023-01-01 to 2023-12-31: 4.0% state rate
    - 2024-01-01 to 2024-12-31: 2.0% state rate
    - 2025-01-01 onward: 0.000% state rate

  Local sales tax (county, city, CID, TDD) STILL applies at the
  full local rate -- only the state portion was zeroed. Encoded
  with `rate_modifier=Decimal("0.000")` per the AR Grocery Tax
  Relief Act pattern.
- **DOR URL:** **https://www.ksrevenue.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted (K.S.A. chapter 79, article 36 -- Kansas
  retailers' sales tax):**
  - K.S.A. section 79-3603(a) -- imposition of the 6.5% state
    retailers' sales tax on retail transactions
  - K.S.A. section 79-3603(d) -- imposition on specified digital
    products and digital codes (as amended by 2021 S.B. 50,
    effective 2021-07-01)
  - K.S.A. section 79-3603(p) -- reduced state rate on food and
    food ingredients (phased 4.0% in 2023, 2.0% in 2024, 0.000%
    from 2025-01-01 per S. Sub. for H.B. 2106 of the 2022 session)
  - K.S.A. section 79-3602(o) -- statutory definition of "food
    and food ingredients" (tracks the SST common definition)
  - K.S.A. section 79-3606(p) -- exemption for prescription
    drugs, prosthetic devices, mobility-enhancing equipment, and
    insulin sold for human use
- *Sources for rate/taxability:*
  - **Kansas Department of Revenue** "Sales (Retailers) Tax"
    landing page at https://www.ksrevenue.gov/ (retrieved
    2026-05-03 -- confirms 6.5% statewide rate and phase-down
    schedule for groceries)
  - **Kansas DOR Notice 22-15** "Sales Tax Requirements
    Pertaining to Food and Food Ingredients" (the 2022 notice
    explaining the H.B. 2106 phase-down schedule and the
    excluded categories)
  - **Kansas DOR Notice 23-13** / **24-04** (annual updates
    confirming each step of the phase-down -- 4% to 2% to 0%)
  - **Kansas DOR Notice 21-15** "Streamlined Sales Tax /
    S.B. 50" -- summary of 2021 S.B. 50 changes including
    digital products and marketplace facilitator provisions
  - **Kansas Statutes Annotated** at
    http://www.kslegislature.org/li/b2025_26/statute/079_000_0000_chapter/
    (primary source for every statutory citation above; chapter
    79, article 36 is the retailers' sales tax act)
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Kansas is a full member
- **Module file:** `src/opensalestax/states/kansas.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ks branch; Phase 7 SST tier-2 to tier-1
  promotion)
- *Notes:*
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    KS's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district),
    documented in the module docstring. Validating against an
    actual `KSR<...>.csv` file is the natural next maintenance
    task -- districts (CIDs, TDDs, Star Bond) are particularly
    worth checking because of the variety of special-district
    types Kansas authorizes under chapter 12.
  - **Grocery phase-down** is the headline 2026 fact. Kansas
    joined the small group of states with a fully eliminated
    state-portion grocery rate (alongside AR effective
    2026-01-01). The local portion still applies, so the engine
    -- which currently does not honor `rate_modifier` -- will
    over-collect on KS grocery line items by the 6.5% state
    portion until v0.6+ wires `rate_modifier` through. Documented
    in the grocery TaxabilityRule notes and the module docstring.
  - **Digital goods is a 2021-07-01 change.** Pre-S.B. 50, KS's
    sales tax did not reach electronically-delivered specified
    digital products. The TaxabilityRule notes call out the
    2021 S.B. 50 origin so a future maintainer doesn't mistake
    the current treatment for a long-standing position. SaaS /
    remotely accessed software remains non-taxable and is
    documented for follow-up.
  - **No sales-tax holiday** is the second headline. Kansas has
    NEVER enacted a recurring sales-tax holiday despite repeated
    legislative attempts; encoded as the empty iterator and
    exercised by a per-year regression test for 2024-2030.
  - **Tier-2 list update:** Kansas removed from `_tier2.py`;
    list count drops from 18 to 17 (KY, MI, NE, NV, NJ, NC, ND,
    OH, OK, RI, SD, TN, UT, VT, WA, WV, WY).

### KY -- Kentucky

- **Statewide rate:** **6.000% effective 1990** (raised from 5%
  to 6% by H.B. 272 of the 1990 General Assembly; the 6% rate
  has been stable since)
- **Tax model:** sales tax (SST -- full member; verified 2026-05-03
  against the SST member roster on streamlinedsalestax.org)
- **Local jurisdictions:** **NONE.** Kentucky levies NO local
  sales tax. The 6% state rate is the entire combined rate at
  every Kentucky address. Kentucky's Constitution (section 181)
  historically restricted local governments from imposing general
  sales taxes, and the General Assembly has never broadly
  authorized a county-option or city-option sales tax under KRS
  Chapter 139. A handful of related local taxes exist (county-
  option motor vehicle rental taxes, transient-room "lodging"
  taxes, restaurant meals taxes in select municipalities
  authorized by individual local-and-private-laws acts) but
  those are narrow industry-specific levies and are NOT general
  sales taxes. This is a notable contrast with peer SST member
  states (e.g. WI's counties typically add 0.5%; MN's metro adds
  transit districts) and one of the defining simplifications in
  Kentucky's rate-stack model. (Mirrors Indiana's no-local-sales-
  tax landscape -- IN and KY are the two SST states in this
  project that levy ZERO local sales tax.)
- **Sales-tax holidays:** **NONE.** Kentucky has never enacted a
  recurring sales-tax holiday. Confirmed 2026-05-03 against the
  Kentucky Department of Revenue's published guidance and a
  search of KRS Chapter 139 for any periodic exemption window.
  ``holidays_for(year)`` returns the empty iterator for every
  year (mirrors DC, ID, and IN).
- **Threshold rules:** none.
- **DOR URL:** **https://revenue.ky.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted (KRS Chapter 139 -- sales and use taxes):**
  - KRS 139.010 -- definitions (tangible personal property,
    digital property, retail sale, etc.)
  - KRS 139.200 -- imposition of the state sales tax on retail
    sales of tangible personal property and digital property at
    6%; subsection (2) covers digital-property treatment as
    expanded by SB 6 (2018) and HB 8 (2022)
  - KRS 139.310 -- complementary use tax at 6%
  - KRS 139.472 -- exemption for prescription drugs, insulin,
    prosthetic devices, and certain medical / durable equipment
    when prescribed
  - KRS 139.485 -- exemption for food and food ingredients for
    human consumption (excluding candy, dietary supplements,
    soft drinks, alcoholic beverages, tobacco, and prepared
    food)
  - **2018 Senate Bill 6** (codified into KRS 139.200(2) and
    related sections) -- expanded the sales-tax base to include
    "digital property" (digital audio works, digital audio-
    visual works, digital books, and other electronically
    transferred products)
  - **2022 House Bill 8** (codified throughout KRS Chapter 139)
    -- significantly expanded sales tax to roughly 30 additional
    service categories effective January 1, 2023, and further
    refined digital-property treatment
- *Sources for rate/taxability:*
  - Kentucky Department of Revenue Sales Tax landing page
    (https://revenue.ky.gov/Business/Sales-Use-Tax/), retrieved
    2026-05-03 -- confirms 6% statewide rate and the absence of
    local sales taxes
  - Kentucky Department of Revenue Sales and Use Tax FAQs page,
    retrieved 2026-05-03 -- confirms the no-local-sales-tax
    landscape and the dominant taxable / exempt categories
  - Kentucky Legislature online statutes
    (https://apps.legislature.ky.gov/law/statutes/chapter.aspx?id=37241),
    KRS Chapter 139, retrieved 2026-05-03 -- primary source for
    every statutory citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Kentucky is a full
    member
  - Sovos State-by-State Guide entry for Kentucky
    (specs/research/sovos-state-summary.tsv line 130) -- used as
    cross-reference for the no-local-sales-tax claim ("No
    localities impose sales and use tax. However, some
    localities impose motor vehicle rental tax or meals tax.").
    Sovos is research-only per constitution sec 3 and is not
    ingested as a data source.
- **Module file:** `src/opensalestax/states/kentucky.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ky branch; Phase 7 -- tier-2 to tier-1 promotion)
- *Notes:*
  - **No local sales tax** is the headline distinction (mirrors
    Indiana). The module's ``jurisdiction_types`` dict accepts
    ONLY the state-level SST type code ``"45"`` so any unexpected
    non-state row in a future quarterly file is silently dropped
    rather than miscategorized as a sub-state authority Kentucky
    doesn't have. Documented prominently in the module docstring
    and enforced by a regression test.
  - **Digital goods is a 2018 + 2022 evolution.** Pre-2018 KY's
    sales tax did not reach electronically-delivered digital
    property; SB 6 (2018) brought digital property into the
    base, and HB 8 (2022) significantly expanded the base
    further (effective January 1, 2023, including roughly 30
    additional service categories). The TaxabilityRule notes
    cite both bills so a future maintainer can date the rule
    against subsequent legislative changes.
  - **HB 8 services taxability is broad and not exhaustively
    modeled here.** Callers shipping enumerated services to
    Kentucky should verify their specific service category
    against current DOR guidance; the OpenSalesTax engine
    presently treats services not categorized as 'general' /
    'prepared_food' / 'digital_goods' through their default
    category mapping. A future enhancement could add a
    'taxable_services' category for finer-grained HB 8 modeling.
  - **Narrow local meals / lodging / motor-vehicle-rental
    taxes** exist in a handful of Kentucky municipalities but
    are NOT modeled by this module -- they are narrow industry-
    specific levies authorized by individual local-and-private-
    laws acts, not general sales taxes. Documented in the
    module docstring for the next maintainer who chooses to
    model lodging / restaurant / vehicle-rental-specific
    calculations.
  - **Rate is stable.** The 6% rate has been in place since
    1990; no scheduled change is currently in the legislative
    pipeline that this research found.

### MI -- Michigan

- **Statewide rate:** **6.000% effective 1994-05-01** (raised from
  4% to 6% by Proposal A of 1994; constitutionalized at Article IX
  section 8 of the Michigan Constitution; further increases require
  a 3/4 supermajority of both legislative chambers)
- **Tax model:** sales tax (General Sales Tax Act, Public Act 167
  of 1933, codified at MCL Chapter 205; SST -- full member;
  verified 2026-05-03 against the SST member roster on
  streamlinedsalestax.org)
- **Local jurisdictions:** **NONE** (no general local sales tax).
  Michigan levies NO general local sales tax; the 6% state rate is
  the entire combined rate at every Michigan address. Article IX
  section 8 caps the state rate at 6% and (combined with the
  General Sales Tax Act) preempts local general sales taxes
  entirely. A handful of narrow industry-specific local taxes
  exist (Wayne County / Detroit-area accommodations and
  convention-facility taxes, stadium development taxes in select
  counties, city utility-users taxes) but those are NOT general
  sales taxes and are NOT modeled by this module. This mirrors
  Indiana's no-local-tax landscape and contrasts with peer SST
  states (WI counties typically add 0.5%; MN metro adds transit
  districts).
- **Sales-tax holidays:** **NONE.** Michigan has never enacted a
  sales-tax holiday. Confirmed 2026-05-03 against the Michigan
  Department of Treasury's published guidance and a search of the
  General Sales Tax Act for any periodic exemption window.
  ``holidays_for(year)`` returns the empty iterator for every year
  (mirrors DC, ID, and IN).
- **Threshold rules:** none.
- **DOR URL:** **https://www.michigan.gov/treasury/** *(retrieved
  2026-05-03)*
- **Statutes consulted (MCL Chapter 205, General Sales Tax Act
  + Use Tax Act parallels):**
  - MCL section 205.52(1) -- 6% state sales tax rate
    (constitutionalized at Mich. Const. Art. IX section 8)
  - MCL section 205.51(1)(d) -- definition of "sale at retail" /
    tangible personal property
  - MCL section 205.54a(1)(g) -- Sales Tax Act exemption for
    drugs sold for human use pursuant to a written prescription
  - MCL section 205.54g(1)(a) -- food and food ingredients
    exemption
  - MCL section 205.54g(2) -- "prepared food" SST-uniform
    definition (excluded from the food exemption)
  - MCL section 205.94d -- Use Tax Act parallel exemption for
    prescription drugs / insulin / oxygen
  - Mich. Const. Art. IX section 8 -- 6% sales tax cap; 3/4
    supermajority required for further increases
- *Sources for rate/taxability:*
  - Michigan Department of Treasury Sales and Use Tax landing
    page (https://www.michigan.gov/treasury/business-taxpayers/
    sales-use-tax), retrieved 2026-05-03 -- confirms 6% statewide
    rate and no general local sales tax
  - Michigan Department of Treasury **Revenue Administrative
    Bulletin (RAB) 2023-22** (Sales of Computer Software and
    Digital Products), retrieved 2026-05-03 -- primary source for
    the digital-goods NOT-taxable position; supersedes RAB 2015-20
    and earlier RAB 1999-5
  - **Auto-Owners Insurance Co. v. Department of Treasury**, 313
    Mich. App. 56 (2015), aff'd 500 Mich. 921 (2016) -- Michigan
    appellate decision confirming that prewritten computer software
    delivered electronically (no tangible medium) is not subject to
    Michigan use tax; underpins the Treasury's RAB position
  - Michigan Legislature online statutes (MCL Chapter 205) at
    https://www.legislature.mi.gov/, retrieved 2026-05-03 --
    primary source for every statutory citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Michigan is a full member
- **Module file:** `src/opensalestax/states/michigan.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-mi branch -- Phase 7 SST tier-2 to tier-1 promotion)
- *Notes:*
  - **No general local sales tax** is one of two headline
    distinctions (alongside the digital-goods position). The
    module's ``jurisdiction_types`` dict accepts ONLY the
    state-level SST type code ``"45"`` so any unexpected non-state
    row in a future quarterly file is silently dropped rather
    than miscategorized as a sub-state authority Michigan doesn't
    have. Documented prominently in the module docstring and
    enforced by a regression test.
  - **Digital goods are NOT taxable** -- a notable peer-state
    difference. IA (section 423.5A, eff. 2019), IN (section
    6-2.5-4-16.4, eff. 2018), and WI (section 77.52(1)(d), eff.
    2010) all tax electronically-delivered specified digital
    products; Michigan does not. Treasury's position is
    administrative (RAB 2023-22) rather than statutory and rests
    on the General Sales Tax Act's tangible-personal-property
    limitation, supported by Auto-Owners. A future Michigan
    Legislature could amend the Act; the rule should be re-
    verified against the current RAB at every data refresh. The
    digital_goods rule encodes ``is_taxable=False`` and a
    regression test catches accidental flips.
  - **Tangible-medium software still taxable.** Prewritten
    computer software delivered on a tangible medium (disk, USB
    drive, etc.) IS taxable as tangible personal property under
    MCL section 205.51. The 'general' category covers this; only
    the electronically-delivered case is excluded by the
    digital_goods rule.
  - **Narrow accommodations / convention-facility taxes** exist
    in Wayne County (Detroit area), under the Michigan Convention
    Facility Development Act, in stadium-district counties, and
    in Detroit's municipal levies. These are NOT general sales
    taxes and are NOT modeled by this module -- callers needing
    lodging-specific calculations for the Detroit area should
    apply the appropriate excise rate at the line-item level.
  - **Rate is stable.** The 6% rate has been in place since
    Proposal A of 1994; the 3/4-supermajority requirement at
    Mich. Const. Art. IX section 8 makes increases politically
    very difficult, so no scheduled change is expected.

### NE -- Nebraska

- **Statewide rate:** **5.500% effective 2002-10-01** (rate set
  at five and one-half percent by L.B. 1085, 97th Legislature,
  Second Session, codified at Neb. Rev. Stat. section 77-2701.02)
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org)
- **Local jurisdictions:** incorporated municipalities (other
  than cities of the metropolitan class) may impose local option
  sales and use tax of 0.5%, 1%, 1.5%, 1.75%, or 2% under Neb.
  Rev. Stat. section 77-27,142 by voter approval. Counties may
  impose 0.5% public-safety / capital-improvement local option
  tax under sections 77-27,148 and 77-27,148.01 (rare). Combined
  rates typically fall in the 5.5%-7.5% range.
- **Notable rate exception -- Good Life Districts (LB 1317 of
  2024):** effective **2024-07-01**, transactions within a Good
  Life District (Good Life Transformational Projects Act, Neb.
  Rev. Stat. sections 77-4401 et seq.) located inside the
  corporate limits of a city or village tax at a **REDUCED 2.75%
  state rate**. Effective **2025-07-01**, cities containing a
  GLD may impose an additional **2.75% GLD Local Option Sales
  and Use Tax**. The GLD layer is a sub-state geographic overlay
  that flows through the SST quarterly rate file rather than
  through the per-category taxability matrix; documented in the
  module docstring for the next maintainer who validates GLD row
  encoding against an actual NER<...>.csv file.
- **Sales-tax holidays:** **NONE.** Nebraska has never enacted a
  recurring statewide sales-tax holiday. Confirmed 2026-05-03
  against the Nebraska Department of Revenue's published
  guidance and the Sales Tax Handbook compendium
  (https://www.salestaxhandbook.com/nebraska/sales-tax-holidays
  -- "Nebraska does not offer a sales tax holiday or temporary
  exemption period for any product categories"). The
  ``holidays_for(year)`` method returns the empty iterator for
  every year (mirrors DC, ID, IN).
- **Threshold rules:** none.
- **DOR URL:** **https://revenue.nebraska.gov/** *(retrieved
  2026-05-03)*
- **Statutes consulted (Neb. Rev. Stat. Chapter 77 -- Revenue
  and Taxation):**
  - Neb. Rev. Stat. section 77-2701.02 -- 5.5% state sales tax
    rate (effective 2002-10-01 by L.B. 1085; 2.75% reduced rate
    in qualifying Good Life Districts effective 2024-07-01 by
    LB 1317)
  - Neb. Rev. Stat. section 77-2701.16 -- definition of "gross
    receipts" including specified digital products (digital
    audio works, digital audiovisual works, digital codes,
    digital books)
  - Neb. Rev. Stat. section 77-2703 -- imposition of state
    sales/use tax on retail sales
  - Neb. Rev. Stat. section 77-2704.09 -- exemption for insulin,
    prescription drugs, mobility enhancing equipment, and
    medical equipment
  - Neb. Rev. Stat. section 77-2704.24 -- exemption for food
    and food ingredients (excluding prepared food and food sold
    through vending machines)
  - Neb. Rev. Stat. section 77-27,142 -- local option sales and
    use tax (0.5%, 1%, 1.5%, 1.75%, or 2% in incorporated
    municipalities)
  - Neb. Rev. Stat. sections 77-4401 et seq. -- Good Life
    Transformational Projects Act (Good Life Districts;
    enabling statute for the LB 1317 reduced state rate)
- *Sources for rate/taxability:*
  - Nebraska Department of Revenue Sales and Use Tax landing
    page (https://revenue.nebraska.gov/businesses/nebraska-sales-and-use-tax),
    retrieved 2026-05-03 -- confirms 5.5% state rate, 0.5%-2%
    local option, food and prescription drug exemptions
  - Nebraska Department of Revenue Sales Tax Exemptions guide
    (https://revenue.nebraska.gov/about/information-guides/nebraska-sales-tax-exemptions),
    retrieved 2026-05-03 -- primary source for the prescription
    drug + food + medical equipment exemption scope
  - Nebraska Department of Revenue Sales and Use Tax Regulation
    1-087 ("Sales of food or food ingredients are exempt from
    sales and use tax",
    https://revenue.nebraska.gov/sites/default/files/doc/legal/regs/1-087.pdf),
    retrieved 2026-05-03 -- elaborates the food exemption
    boundaries (heated food, mixed/combined food, bakery items
    enumerated exception)
  - Nebraska Legislature online statutes (Chapter 77) at
    https://nebraskalegislature.gov/laws/browse-chapters.php?chapter=77,
    retrieved 2026-05-03 -- primary source for every statutory
    citation above
  - Nebraska Department of Revenue Revenue Ruling 01-11-3
    (https://revenue.nebraska.gov/sites/default/files/doc/legal/rulings/rr011103.pdf),
    retrieved 2026-05-03 -- DOR's published interpretation of
    section 77-2701.16(2)(e) for specified digital products
  - Nebraska Department of Revenue "Reporting Good Life
    District (GLD) Sales and Use Tax on NebFile Schedule II"
    FAQ (FAQ-011-2024,
    https://revenue.nebraska.gov/sites/default/files/doc/FAQ-011-2024.pdf),
    retrieved 2026-05-03 -- DOR's GLD reporting guidance
    referencing the LB 1317 framework
  - Sales Tax Institute "Nebraska Launches New Good Life
    Districts" (https://www.salestaxinstitute.com/resources/nebraska-launches-new-good-life-districts),
    retrieved 2026-05-03 -- secondary cross-reference for the
    LB 1317 effective dates and rate structure (primary source
    is the NE DOR + Nebraska Legislature)
  - Sales Tax Handbook "Nebraska Sales Tax Holidays 2026"
    (https://www.salestaxhandbook.com/nebraska/sales-tax-holidays),
    retrieved 2026-05-03 -- confirms Nebraska has no
    sales-tax holiday in 2026 (used as one input among many;
    primary source is the NE DOR which publishes no holiday
    notice for any year)
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms Nebraska is a full member
- **Module file:** `src/opensalestax/states/nebraska.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ne branch)
- *Notes:*
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    NE's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district),
    documented in the module docstring. Validating against an
    actual `NER<...>.csv` file (and empirically determining how
    Good Life District rows are encoded) is the natural next
    maintenance task.
  - **Good Life Districts are a 2024-07-01 rate change** (LB
    1317 of 2024). The reduced 2.75% state rate inside qualifying
    GLDs (city/village portion only) is a sub-state geographic
    overlay that depends on rate ingestion through the SST
    quarterly file, NOT on a per-category taxability rule. The
    module's general TPP rule notes the GLD exception and the
    docstring elaborates; integrators billing GLD-located
    transactions should rely on the SST-file-driven rate
    lookup rather than hard-coding 5.5%.
  - **Digital goods is a long-standing 77-2701.16(2)(e)
    inclusion** in the gross-receipts definition; specified
    digital products have been taxable in NE for many years
    (the precise enactment date predates the most recent
    statutory recodification we located -- a future maintainer
    should add the originating session-law citation).
  - **SaaS distinction follows DOR published guidance**, not a
    statute. Prewritten ("canned") computer software delivered
    by any means is taxable as TPP under section 77-2701, but
    true SaaS / remotely accessed software where the customer
    takes neither possession nor control of the software is
    generally NOT taxable as TPP per the NE DOR's published
    position. The dominant case (specified digital products
    with permanent right of use) is encoded as taxable; the
    SaaS exception is documented in the digital_goods rule's
    notes for follow-up if/when a sub-category split lands.
  - **Restaurant occupation tax** is imposed by some Nebraska
    municipalities on prepared food / restaurant sales as a
    separate municipal levy, NOT as part of the general state
    sales tax. The module applies the state sales tax + the
    general local option sales tax under section 77-27,142 and
    does NOT model the prepared-food-specific occupation tax
    layer; documented in the prepared_food rule's notes for
    integrators selling restaurant transactions in NE.
  - **Rate is stable** at 5.5% since 2002-10-01; no scheduled
    change for the general rate is currently in the legislative
    pipeline that this research found (the LB 1317 GLD reduced
    rate is a sub-state overlay, not a general-rate change).

## ND — North Dakota

- **Statewide rate:** **5.000% effective 1987-07-01** (raised from
  4% to 5% by the 1987 legislative assembly's omnibus revenue act;
  rate codified at N.D.C.C. section 57-39.2-02.1)
- **Tax model:** sales tax (SST -- full member; verified 2026-05-03
  against the SST member roster on streamlinedsalestax.org). State
  FIPS: 38.
- **Local jurisdictions:** Cities and home-rule counties may impose
  local option sales taxes:
  - **N.D.C.C. chapter 11-09.2** -- county home rule charter
    authority (counties that adopt a home rule charter may impose
    sales taxes among other powers)
  - **N.D.C.C. chapter 40-05.1** -- city home rule charter
    authority
  - **N.D.C.C. chapter 40-57.3** -- general city sales / use /
    gross-receipts tax authority (the more commonly used
    non-home-rule path; any incorporated city may impose, by voter
    approval, a city sales tax administered by the State Tax
    Commissioner)
  Local rates typically range from 0.25% to 3.5%, with most
  participating cities at 1%-2.5%. Combined rates statewide range
  from **5.0% (unincorporated areas with no county tax) to roughly
  8.5%** (highest-rate cities). SST member status means rate data
  flows through the inherited :class:`SstStateModule` parser; no
  manual loader needed.
- **Sales-tax holidays:** **NONE.** North Dakota has never enacted
  a recurring sales-tax holiday. Confirmed 2026-05-03 against the
  North Dakota Office of State Tax Commissioner's published
  guidance and a search of N.D.C.C. chapter 57-39.2 for any
  periodic exemption window. ``holidays_for(year)`` returns the
  empty iterator for every year (mirrors KY, IN, MI, DC, ID).
- **Threshold rules:** none.
- **DOR URL:** **https://www.tax.nd.gov** *(retrieved 2026-05-03)*
- **Statutes consulted (N.D.C.C. chapter 57-39.2 -- sales tax;
  chapter 57-40.2 -- complementary use tax):**
  - N.D.C.C. section 57-39.2-01 -- definitions (including
    "tangible personal property" and the SST common definitions
    incorporated by reference)
  - N.D.C.C. section 57-39.2-02.1 -- imposition of the state
    sales tax at 5% on retail sales of tangible personal
    property and on specified digital products
  - N.D.C.C. section 57-39.2-02.1(1)(c) -- imposition of sales
    tax on specified digital products (added by H.B. 1041 of the
    66th Legislative Assembly, 2019)
  - N.D.C.C. section 57-39.2-04(33) -- exemption for prescription
    drugs, insulin, oxygen, and certain prescribed medical /
    durable equipment
  - N.D.C.C. section 57-39.2-04(46) -- exemption for food and
    food ingredients for human consumption (using the SST common
    definition; excludes prepared food, candy, soft drinks,
    dietary supplements)
  - N.D.C.C. chapter 57-40.2 -- complementary use tax
  - N.D.C.C. chapter 11-09.2 -- county home rule charter
    authority (county sales tax)
  - N.D.C.C. chapter 40-05.1 -- city home rule charter authority
    (home rule city sales tax)
  - N.D.C.C. chapter 40-57.3 -- general city sales, use, and
    gross-receipts tax (any incorporated city may impose, by
    voter approval)
- *Sources for rate/taxability:*
  - North Dakota Office of State Tax Commissioner sales-tax
    landing page (https://www.tax.nd.gov/), retrieved 2026-05-03
    -- confirms 5% statewide rate and the local option layer
  - North Dakota Century Code (N.D.C.C.) chapter 57-39.2 via the
    Legislative Branch online code (https://ndlegis.gov/cencode/),
    retrieved 2026-05-03 -- primary source for every statutory
    citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms North Dakota is a full
    member
  - SST taxability matrix for North Dakota (published quarterly
    on streamlinedsalestax.org) -- cross-checked 2026-05-03 for
    the food-and-food-ingredients exemption scope, the
    prescription-drug exemption scope, and the digital-products
    treatment
- **Module file:** `src/opensalestax/states/north_dakota.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (Phase 7 -- tier-2 to tier-1 promotion)
- *Notes:*
  - **No sales-tax holiday** is the headline regression risk.
    A dedicated test in :mod:`tests.unit.test_state_north_dakota`
    asserts ``holidays_for(year) == []`` for every year 2024-2030
    so a contributor copy-pasting from a holiday state (Iowa,
    Mississippi, etc.) cannot silently introduce a spurious
    window.
  - **Local sales taxes DO exist** (unlike the no-local-tax SST
    peers KY / IN / MI). The module inherits the default
    jurisdiction-type code mapping (state 45 / county 00 / city
    01 / district 63) so the SST quarterly file's per-city
    rate rows load as expected. A test asserts the inherited
    mapping has not been narrowed.
  - **Digital goods is a 2019 change.** Pre-2019 N.D.'s sales
    tax did not reach electronically-delivered specified digital
    products. The TaxabilityRule notes call out the H.B. 1041
    (2019) origin so a future maintainer doesn't mistake the
    current treatment for a long-standing position.
  - **Rate is stable** at 5% since 1987-07-01; no scheduled
    change for the general rate is currently in the legislative
    pipeline that this research found.
  - **No 2026Q2 ND SST file** has been captured to confirm the
    jurisdiction-type codes empirically; the inherited default
    mapping is taken from MN/WI 2026Q2 captures and the SST
    file format is uniform across the membership in every other
    state where we have data. The next maintainer should
    validate against an N.D. SST quarterly capture and override
    ``jurisdiction_types`` on the subclass if any code differs.

### NJ -- New Jersey

- **Statewide rate:** **6.625% effective 2018-01-01** (reduced from
  6.875% effective 2017-01-01, which was reduced from 7.000% by
  P.L. 2016, c. 57 -- the Transportation Trust Fund reauthorization
  compromise that traded a sales-tax cut for a gas-tax increase)
- **Tax model:** sales tax (SST member)
- **Local jurisdictions:** **NONE** for general sales tax. NJ
  imposes NO general municipal/county sales tax statewide. Two
  narrow reduced-rate exceptions exist (UEZ + Salem County, both
  half rate at 3.3125%) but are NOT modeled in v1 -- see Notes
  below. Atlantic City Luxury Tax is a separate non-sales-tax
  layer and out of scope.
- **Sales-tax holidays:** **NONE current.** An annual
  Back-to-School Sales Tax Holiday was enacted by P.L. 2022,
  c. 21 (codified at the now-repealed N.J.S.A. 54:32B-8.66) and
  ran in late August / early September of 2022 and 2023. The
  Legislature REPEALED the holiday by P.L. 2024, c. 19 (signed
  2024-06-28) before the 2024 window would have run; no holiday
  has been held in 2024, 2025, or 2026, and none is scheduled.
- **Threshold rules:** **NONE** for clothing -- NJ has a broad
  year-round clothing exemption with no per-item dollar cap
  (contrast with NY's $110-per-item threshold and MA's
  $175-per-item threshold).
- **DOR URL:** **https://www.state.nj.us/treasury/taxation/**
  *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - N.J.S.A. section 54:32B-3 -- the imposition statute (sales
    tax on tangible personal property at 6.625%)
  - N.J.S.A. section 54:32B-2(g) -- definition of "tangible
    personal property"
  - N.J.S.A. section 54:32B-8.1 -- prescription drug exemption
  - N.J.S.A. section 54:32B-8.2 -- food and food ingredients
    exemption (groceries)
  - N.J.S.A. section 54:32B-8.4 -- clothing and footwear
    exemption (broad year-round)
  - N.J.S.A. section 54:32B-8.45 -- Salem County half-rate
    (3.3125%) for qualifying retail sales
  - N.J.S.A. section 54:32B-3(a) -- imposition statute, as
    amended by P.L. 2011, c. 49 to extend the tax base from
    "tangible personal property" to "tangible personal property
    or a specified digital product" (the operative citation
    for digital-goods taxability in NJ)
  - N.J.S.A. section 54:32B-2(zz) -- defined term "specified
    digital product" (added by P.L. 2011, c. 49)
  - N.J.S.A. section 54:32B-8.56 -- narrow exemption for
    prewritten software delivered electronically AND used
    directly and exclusively in the conduct of the purchaser's
    business (added by P.L. 2011, c. 49; does not change the
    general taxability of consumer-facing digital goods)
  - N.J.S.A. section 54:32B-8.66 -- the now-REPEALED
    Back-to-School Sales Tax Holiday section that ran in
    2022 and 2023 (struck by P.L. 2024, c. 19)
  - N.J.S.A. section 54:32B-14 -- seller's collection liability
    for under-collected tax (cited in the UEZ deferral
    rationale)
  - N.J.S.A. section 54:32B-20 -- buyer refund process for
    over-collected tax (cited in the UEZ + Salem County
    deferral rationale)
  - N.J.S.A. section 52:27H-80 -- Urban Enterprise Zones Act
    half-rate (3.3125%) for qualifying retail purchases at
    UZ-2-certified UEZ sellers; ~32 UEZ municipalities
  - N.J.S.A. section 40:48-8.15 et seq. -- Atlantic City
    Luxury Tax (3% on hotels / restaurants / alcohol /
    amusements; separate from general sales tax)
  - P.L. 2016, c. 57 -- the rate reduction (7% -> 6.875% ->
    6.625%) and Transportation Trust Fund reauthorization
  - P.L. 2011, c. 49 -- specified digital products inclusion
    (amending 54:32B-3(a) and adding 54:32B-2(zz) and
    54:32B-8.56)
  - P.L. 2022, c. 21 -- annual Back-to-School Sales Tax
    Holiday enactment (held 2022 and 2023 only; codified at
    N.J.S.A. 54:32B-8.66)
  - P.L. 2024, c. 19 -- REPEAL of the Back-to-School Sales
    Tax Holiday (struck N.J.S.A. 54:32B-8.66; signed
    2024-06-28; immediate effect, before the 2024 window)
  - P.L. 1983, c. 303 -- original Urban Enterprise Zones Act
  - P.L. 1981, c. 77 -- original Atlantic City Luxury Tax
- *Sources for rate/taxability:*
  - New Jersey Division of Taxation -- Sales and Use Tax
    landing page (https://www.state.nj.us/treasury/taxation/),
    retrieved 2026-05-03 -- confirms 6.625% statewide rate,
    clothing / food / prescription-drug exemptions, NO general
    local sales tax
  - New Jersey Division of Taxation -- "Sales Tax Rate Change"
    notice
    (https://www.state.nj.us/treasury/taxation/ratechange/su-overview.shtml),
    retrieved 2026-05-03 -- confirms the 7.000% -> 6.875% ->
    6.625% rate ladder under P.L. 2016, c. 57
  - New Jersey Division of Taxation -- "Sales Tax Exemption
    Administration" guide (Publication ANJ-10),
    retrieved 2026-05-03 -- elaborates clothing / food /
    prescription drug exemption boundaries
  - New Jersey Department of Community Affairs -- Urban
    Enterprise Zone Tax Information page
    (https://www.nj.gov/dca/divisions/dhcr/offices/ueztaxinfo.html),
    retrieved 2026-05-03 -- authoritative current list of
    designated UEZ municipalities and seller certification
    requirements
  - New Jersey Division of Taxation -- "Salem County Sales Tax
    Information" notice,
    retrieved 2026-05-03 -- elaborates the qualifying-retail
    boundary and exclusions for the half-rate
  - Atlantic City -- Atlantic City Luxury Tax / ACTRA program
    information,
    retrieved 2026-05-03 -- documents the 3% luxury tax + 9%
    Tourism Promotion Fee structure (out of scope for this
    engine but noted for integrator awareness)
  - New Jersey Legislature online statutes (Title 54 Chapter
    32B) at
    https://www.njleg.state.nj.us/statutes/title-54.asp,
    retrieved 2026-05-03 -- primary source for every statutory
    citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms NJ is a full member
- **Module file:** `src/opensalestax/states/new_jersey.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-nj branch)
- *Notes:*
  - **Urban Enterprise Zones (UEZ) -- DEFERRED IN v1**: Per
    N.J.S.A. 52:27H-80, qualified retail purchases at certified
    UEZ sellers tax at HALF the statewide rate (3.3125%) rather
    than the full 6.625%. The reduced rate is **seller-
    eligibility-restricted** (depends on the SELLER holding a
    current UZ-2 Urban Enterprise Zone Business Certification)
    and **category-restricted** (motor vehicles, certain
    energy, and specified other items are excluded by statute
    even at certified UEZ sellers). Encoding UEZ as a
    geographic rate override keyed by ZIP / municipality would
    systematically OVER-collect on non-certified sellers in UEZ
    municipalities (the overwhelming majority of sellers in
    any UEZ municipality are NOT UEZ-certified) and
    UNDER-collect on the category-excluded purchases at
    certified sellers. This is structurally similar to NV's
    National Guard Sales Tax Holiday deferral (NRS 372.7282)
    -- a non-geographic eligibility dimension the engine does
    not currently model. A future PR -- gated on a per-seller
    exemption / certification model landing in the calculation
    API -- can re-enable UEZ as a seller-class-restricted
    modifier. ~32 UEZ municipalities currently designated
    (notable: Newark, Camden, Paterson, Jersey City, Elizabeth,
    Trenton, Atlantic City, Asbury Park, Bayonne, Bridgeton,
    Carteret, East Orange, Gloucester City, Guttenberg,
    Hillside, Irvington, Kearny, Lakewood, Long Branch,
    Millville, Mount Holly, New Brunswick, North Bergen,
    Orange, Passaic, Pemberton, Perth Amboy, Phillipsburg,
    Plainfield, Pleasantville, Roselle, Union City, Vineland,
    West New York, Wildwood). Authoritative current list
    maintained by the NJ DCA.
  - **Salem County -- DEFERRED IN v1**: Per N.J.S.A.
    54:32B-8.45, qualifying retail sales at retail stores in
    Salem County (southern NJ on the Delaware River across
    from Wilmington) tax at HALF the statewide rate (3.3125%).
    The reduction exists to keep NJ retailers competitive with
    no-sales-tax Delaware retailers across the Delaware
    Memorial Bridge. Same seller / category eligibility
    constraints as UEZ -- a geographic override would
    over/under-collect on the eligibility / category edges.
    Same deferred-locals pattern as NV (county add-ons), LA
    (parishes), CO (home-rule cities), SC (county-option) --
    see specs/decisions/05-louisiana-parishes.md for the
    trade-off discussion.
  - **Atlantic City Luxury Tax -- OUT OF SCOPE**: Per N.J.S.A.
    40:48-8.15 et seq., Atlantic City imposes a 3% luxury tax
    on hotel rooms / restaurant meals / alcoholic beverages /
    cover charges / show / sporting / amusement tickets within
    the city limits. State law also imposes an additional 9%
    ACTRA (Atlantic City Tourism Promotion Fee) on hotel
    rooms. Both are SEPARATE municipal / state tourism levies
    that stack on top of the 6.625% state sales tax for items
    in their defined category lists; they are NOT general
    sales taxes and NOT modeled by this engine. An integrator
    selling hotel-room or restaurant-meal transactions in
    Atlantic City needs to add these layers outside this
    engine.
  - **Clothing exemption is BROAD and YEAR-ROUND** per
    N.J.S.A. 54:32B-8.4 -- no per-item dollar cap, no date
    restriction. Statutory exclusions (items that REMAIN
    taxable): fur clothing (also subject to a separate
    fur-clothing surtax), clothing accessories (jewelry,
    handbags, briefcases, watches, similar items -- general
    TPP), sport / recreational equipment, and protective
    equipment for use other than as everyday clothing. NJ
    joins PA, MA, MN, VT in the broad-exemption club; NY and
    RI use threshold-based exemptions instead.
  - **No current sales-tax holidays.** P.L. 2022, c. 21
    enacted an annual Back-to-School Sales Tax Holiday
    (codified at the now-REPEALED N.J.S.A. 54:32B-8.66) that
    ran for a 10-day window in late August / early September
    of 2022 and 2023, exempting clothing/footwear, school
    supplies, school art supplies, school instructional
    materials, sport or recreational equipment, and computers
    (with a $3,000 per-item cap on computers and a $1,000
    per-item cap on recreational equipment) from the 6.625%
    sales tax. The Legislature REPEALED the holiday by P.L.
    2024, c. 19 (Assembly Substitute A4702, signed by Governor
    Murphy on 2024-06-28 as part of the FY2025 budget package),
    with the repeal taking immediate effect before the 2024
    holiday window would have run. **NJ has held no sales-tax
    holiday in 2024, 2025, or 2026, and none is currently
    scheduled for any future year.** Do NOT extrapolate the
    2022/2023 dates / caps / categories to future years -- a
    future re-enactment would be a discrete legislative event
    with its own parameters; encode it explicitly when it
    ships.
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    NJ's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district),
    which in NJ's case will only ever match the state-level
    row (code 45) because NJ levies no general local sales
    tax. Validating against an actual `NJR<...>.csv` file is
    a low-priority maintenance task -- the only expected row
    is the state-level 6.625% row.
  - **Rate has been stable** at 6.625% since 2018-01-01; no
    scheduled rate change is currently in the legislative
    pipeline that this research found.

## NC -- North Carolina

- **Statewide rate:** **4.750% effective 2011-10-15** (raised
  from 4.5% to 4.75% by S.L. 2011-145 section 31A.1, the 2011
  budget act; codified at N.C.G.S. section 105-164.4(a). The
  4.75% state rate has been stable since.)
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org)
- **Local jurisdictions:** counties impose layered local sales
  taxes by voter approval and statutory authorization under
  N.C.G.S. Chapter 105, Subchapter VIII (Articles 39, 40, 42,
  43, 46) and related provisions. Typical county stack: 2.00%
  Article 39 (section 105-466) + 0.50% Article 40 (section
  105-480) + 0.50% Article 42 (section 105-495) + voter-
  approved Article 43/46 transit/education/general option
  layers (Mecklenburg, Durham, Orange, Wake, etc.). Combined
  state + local general rates typically fall in the 6.75%-7.50%
  range. As an SST member, NC's per-jurisdiction rates flow
  through the standard SST quarterly file.
- **Notable rate exception -- the unusual "food county tax"
  structure:** groceries (food and food ingredients) are
  EXEMPT from the state 4.75% portion under N.C.G.S. section
  105-164.13B(a) (the "food exemption"), but a uniform 2.00%
  LOCAL food tax under N.C.G.S. section 105-468.1 (the
  "Article 39A food county tax") applies in EVERY one of the
  100 NC counties. Net effective statewide grocery rate is
  therefore **2.00%** (state portion 0% + uniform 2% local
  food county tax). The structure is unusual: rather than the
  standard state-and-local layering, the General Assembly
  excluded qualifying food from the state portion AND from
  the regular Article 39/40/42 local sales taxes, then re-
  imposed a single uniform 2.00% county-level food tax that
  is mandatory statewide. Encoded with
  ``rate_modifier=Decimal("2.000")`` on the groceries
  TaxabilityRule (mirrors the MS / VA / MO rate_modifier
  pattern; differs in that NC's state portion is fully ZERO
  and the 2% is a separate statutory LOCAL food tax rather
  than a reduced state rate, but the in-engine encoding is
  identical). Items NOT meeting the SST "food and food
  ingredients" definition (candy, soft drinks, dietary
  supplements, alcoholic beverages, tobacco) and prepared
  food remain at the full combined rate per section
  105-164.13B(a)(1).
- **Sales-tax holidays:** **NONE.** North Carolina REPEALED
  its annual back-to-school sales-tax holiday (former
  N.C.G.S. section 105-164.13C) effective **2014** by S.L.
  2013-316 section 4.1 (the 2013 tax-reform act). NC also
  repealed its annual Energy Star sales-tax holiday by the
  same act. From the 2002 enactment of the back-to-school
  holiday (S.L. 2002-126 section 30A.1) through 2013, North
  Carolina held an annual August holiday exempting clothing
  under $100, school supplies under $100, sports/recreation
  equipment under $50, computers under $3,500, and computer
  accessories. The 2013 General Assembly let the holiday
  expire as part of broader tax-base broadening; the
  underlying authorizing statute was repealed. The General
  Assembly has not re-enacted any sales-tax holiday since.
  ``holidays_for(year)`` returns the empty iterator for every
  year (mirrors DC, ID, IN, KS, GA).
- **Threshold rules:** none in current law. (Pre-2014 the
  back-to-school holiday had per-item caps but those are no
  longer applicable.)
- **DOR URL:** **https://www.ncdor.gov/** *(retrieved
  2026-05-03)*
- **Statutes consulted (N.C.G.S. Chapter 105 -- Taxation,
  Article 5 -- Sales and Use Tax, and Subchapter VIII --
  Local Government Sales and Use Tax):**
  - N.C.G.S. section 105-164.4(a)(1) -- 4.75% state retail
    sales/use tax rate (raised from 4.5% to 4.75% by S.L.
    2011-145 section 31A.1 effective 2011-10-15)
  - N.C.G.S. section 105-164.4(a)(6b) -- imposition of state
    sales/use tax on "digital property" / specified digital
    products (added by S.L. 2009-451 section 27A.4(a),
    effective 2010-01-01)
  - N.C.G.S. section 105-164.3 -- definitions (incorporates
    the SST-uniform "food and food ingredients" definition;
    defines "specified digital products," "prewritten
    computer software," "tangible personal property")
  - N.C.G.S. section 105-164.13(13) -- exemption for
    prescription drugs (drugs required by federal law to be
    dispensed only on prescription, plus insulin sold to a
    pharmacist for a person with diabetes diagnosed by a
    licensed physician, and certain related prescribed
    medical items)
  - N.C.G.S. section 105-164.13B(a) -- exemption from the
    state sales tax for "food" as defined in section
    105-164.3 (the "food exemption"; expressly excludes
    prepared food, candy, soft drinks, dietary supplements,
    alcoholic beverages, and tobacco)
  - N.C.G.S. section 105-468.1 -- the uniform 2.00% local
    "food county tax" (Article 39A); applies in every NC
    county to qualifying food and food ingredients despite
    the section 105-164.13B(a) state exemption
  - N.C.G.S. section 105-466 (Article 39 first one-cent
    local option), section 105-480 (Article 40 first one-
    half cent), section 105-495 (Article 42 second one-half
    cent), and the Article 43/46 transit / education /
    general option overlays -- the per-county local sales
    tax authorizing statutes
  - Former N.C.G.S. section 105-164.13C -- the repealed
    back-to-school sales-tax holiday (enacted by S.L.
    2002-126 section 30A.1; REPEALED by S.L. 2013-316
    section 4.1 effective 2014)
- *Sources for rate/taxability:*
  - North Carolina Department of Revenue Sales and Use Tax
    landing page (https://www.ncdor.gov/taxes-forms/sales-and-use-tax),
    retrieved 2026-05-03 -- confirms 4.75% state rate, the
    2.00% uniform food county tax, and prescription/food
    exemptions
  - North Carolina Department of Revenue Sales and Use Tax
    Bulletins (https://www.ncdor.gov/documents/sales-use-tax-bulletins),
    retrieved 2026-05-03 -- primary source for the SaaS /
    custom-software taxability position cited in the digital-
    goods rule (Bulletin section 44-2 on computer hardware,
    software, and digital products)
  - North Carolina General Assembly online statutes
    (https://www.ncleg.gov/Laws/GeneralStatutes), retrieved
    2026-05-03 -- primary source for every statutory citation
    above
  - North Carolina Session Laws S.L. 2011-145 (the 2011
    budget act / "Current Operations and Capital
    Improvements Appropriations Act of 2011") section 31A.1,
    available at https://www.ncleg.gov/Sessions/2011/Bills/House/PDF/H200v8.pdf,
    retrieved 2026-05-03 -- primary source for the 2011
    rate increase from 4.5% to 4.75%
  - North Carolina Session Laws S.L. 2013-316 (the 2013
    tax-reform act / "Tax Simplification and Reduction Act"),
    available at https://www.ncleg.gov/Sessions/2013/Bills/House/PDF/H998v9.pdf,
    retrieved 2026-05-03 -- primary source for the 2014
    repeal of the back-to-school and Energy Star sales-tax
    holidays (section 4.1)
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms North Carolina is a
    full SST member
- **Module file:** `src/opensalestax/states/north_carolina.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-nc branch; SST tier-2 -> tier-1 promotion as
  part of the Phase 7 SST ratchet)
- *Notes:*
  - **The food county tax is the headline distinction.** The
    state-exempt-but-2%-local-food-county-tax structure is
    unusual among US states (most states either exempt food
    fully or tax it at a reduced rate uniformly across state
    + local). NC's structure is encoded in a single
    ``rate_modifier=Decimal("2.000")`` on the groceries rule,
    documented prominently in the module docstring, and
    enforced by a regression test that asserts both
    controlling statutes (105-164.13B and 105-468.1) appear
    in the rule's notes. The MS/VA/MO precedents already
    establish the rate_modifier pattern for state-vs-local
    grocery rate splits; NC fits the same engine encoding
    even though its statutory structure differs.
  - **The 2014 repeal of the back-to-school holiday is a key
    historical fact** that an integrator may miss if
    researching from older sources. The
    ``holidays_for(year)`` regression test exercises a wide
    window of years (2014-2030) to confirm the empty-
    iterator default is never accidentally overridden with a
    future-year extrapolation. Should the General Assembly
    re-authorize a holiday in a future session, a maintainer
    must explicitly add the year's data; the empty iterable
    is intentional regression protection.
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    NC's actual rate-file codes were not empirically
    validated at promotion time. The module defaults to the
    canonical MN/WI/IA mapping (45=state, 00=county,
    01=city, 63=district), documented in the module
    docstring. Validating against an actual `NCR<...>.csv`
    file (and confirming how Article 39A food county tax
    rows are encoded -- whether as a separate row or folded
    into the per-county figure) is the natural next
    maintenance task.
  - **Digital goods is a 2010-01-01 change** (S.L. 2009-451
    section 27A.4(a)). Pre-2010 NC's sales tax did not
    reach electronically-delivered specified digital
    products. The TaxabilityRule notes call out the S.L.
    2009-451 origin so a future maintainer doesn't mistake
    the current treatment for a long-standing position.
  - **SaaS distinction lives in NC DOR Sales and Use Tax
    Bulletin section 44-2.** North Carolina taxes prewritten
    ("canned") software delivered electronically but does
    NOT tax true SaaS / remotely accessed software (where
    the customer takes neither possession nor control of the
    software) or custom software. The dominant case
    (specified digital products with permanent right of use)
    is encoded as taxable; the SaaS exception is documented
    in the digital_goods rule's notes for follow-up if/when
    a sub-category split lands.
  - **Narrow per-county prepared-food and beverage taxes**
    exist in a handful of NC counties (notably the
    Mecklenburg County Convention Center Act 1.0% prepared-
    food and beverage tax) but are NOT modeled by this
    module -- they are narrow industry-specific levies
    authorized by individual local-and-private-laws acts,
    not general sales taxes. Documented in the prepared_food
    rule's notes for the next maintainer who chooses to
    model meals-tax-specific calculations.
  - **General rate is stable** at 4.75% since 2011-10-15;
    no scheduled change is currently in the legislative
    pipeline that this research found.

## OH — Ohio

- **Statewide rate:** **5.750%** ("five and three-fourths per
  cent" per Ohio Rev. Code section 5739.02(A)(1)). The 5.75%
  state rate has been in place since 2013-09-01 (raised from
  5.5% by H.B. 59 of the 130th General Assembly).
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org). State FIPS: 39.
- **Local jurisdictions:** Ohio's 88 counties may impose
  permissive county sales tax under Ohio Rev. Code section
  5739.021 (typically 0.25%-1.5% in 0.25% increments by county
  commissioner action and/or voter approval). Regional transit
  authorities (notably Cuyahoga County's RTA) may impose
  additional sales tax under section 5739.023. Combined county
  rates typically fall in the **6.5%-8.0%** range.
- **Sales-tax holidays:** **TWO statutory frameworks** -- ONE
  active in 2026.
  - **Traditional 3-day back-to-school holiday** under Ohio Rev.
    Code section 5739.02(B)(55): first Friday of August + the
    following Saturday + Sunday. Eligible items: clothing $75
    or less per item; school supplies $20 or less per item;
    school instructional materials $20 or less per item.
  - **Expanded 14-day "most TPP" holiday** under Ohio Rev. Code
    section 5739.41 (created by H.B. 33 of the 135th General
    Assembly, 2023). Up to 14 days each summer covering most
    TPP priced $500 or less per item. Subject to Tax
    Commissioner certification of sufficient Expanded Sales
    Tax Holiday Fund revenue. Categorical exclusions: motor
    vehicles, watercraft, outboard motors, alcoholic beverages,
    tobacco, vapor products.
  - **History:**
    - **2024:** EXPANDED holiday declared. Tuesday July 30 -
      Thursday August 8, 2024 (10 days, $500-per-item cap).
    - **2025:** EXPANDED holiday declared (~2-week window in
      early August, $500-per-item cap).
    - **2026:** EXPANDED holiday CANCELLED by **H.B. 186 of the
      136th General Assembly** (signed by Governor DeWine on
      **December 19, 2025**). HB 186 repurposed the Expanded
      Sales Tax Holiday Fund to offset reduced school district
      property tax collections, prohibiting any expanded
      holiday in August 2026 and delaying certification of fund
      revenue for a 2027 expanded holiday. Ohio reverts to the
      traditional 3-day version under section 5739.02(B)(55).
    - **2026 dates:** **Friday August 7, 2026 (12:00 a.m.)
      through Sunday August 9, 2026 (11:59 p.m.)**, per the
      Ohio Department of Taxation announcement.
  - The two frameworks are mutually exclusive in any year. A
    future maintainer adding 2027 must verify which framework
    is in effect (depends on Tax Commissioner certification of
    fund revenue and any further legislative action).
- **Threshold rules:** none.
- **DOR URL:** **https://tax.ohio.gov/** *(retrieved
  2026-05-03)*
- **Statutes consulted (Ohio Rev. Code Chapter 5739 -- Sales
  Tax; Chapter 5741 -- Use Tax):**
  - Ohio Rev. Code section 5739.01(B)(12) -- definition of
    "sale" includes specified digital products provided for
    permanent or less-than-permanent use
  - Ohio Rev. Code section 5739.01(OOO) -- definition of
    "specified digital product" (electronically transferred
    digital audio-visual work, digital audio work, or digital
    book)
  - Ohio Rev. Code section 5739.02(A)(1) -- imposition of the
    state sales tax at "five and three-fourths per cent"
    (5.75%)
  - Ohio Rev. Code section 5739.02(B)(2) -- exemption for
    sales of food for human consumption off the premises
    where sold (the grocery exemption)
  - Ohio Rev. Code section 5739.02(B)(18) -- exemption for
    sales of drugs for a human being that may be dispensed
    only pursuant to a prescription
  - Ohio Rev. Code section 5739.02(B)(55) -- traditional 3-day
    back-to-school sales-tax holiday (first Friday of August +
    Saturday + Sunday; clothing $75/less, supplies $20/less,
    instructional materials $20/less)
  - Ohio Rev. Code section 5739.021 -- permissive county sales
    tax (the local-jurisdiction enabling statute)
  - Ohio Rev. Code section 5739.023 -- transit authority sales
    tax (regional transit authority enabling statute)
  - Ohio Rev. Code section 5739.41 -- expanded sales tax
    holiday framework (created by H.B. 33 of 135th General
    Assembly, 2023; cancelled for 2026 by H.B. 186 of 136th
    General Assembly, signed 2025-12-19)
- *Sources for rate/taxability:*
  - Ohio Department of Taxation landing page
    (https://tax.ohio.gov/), retrieved 2026-05-03 -- confirms
    5.75% state rate and Sales Tax Holiday landing
  - Ohio Revised Code section 5739.02 on codes.ohio.gov
    (https://codes.ohio.gov/ohio-revised-code/section-5739.02),
    retrieved 2026-05-03 -- primary source for the imposition
    rate and the (B)(2), (B)(18), (B)(55) exemptions
  - Ohio Revised Code section 5739.01 on codes.ohio.gov
    (https://codes.ohio.gov/ohio-revised-code/section-5739.01),
    retrieved 2026-05-03 -- primary source for the (B)(12)
    "sale" definition and the (OOO) "specified digital product"
    definition
  - Ohio Revised Code Chapter 5739 on codes.ohio.gov
    (https://codes.ohio.gov/ohio-revised-code/chapter-5739),
    retrieved 2026-05-03 -- chapter index
  - Avalara compliance blog "Ohio sales tax holiday 2026:
    Expanded holiday canceled"
    (https://www.avalara.com/blog/en/north-america/2026/01/ohio-cancels-expanded-sales-tax-holiday-for-2026.html),
    retrieved 2026-05-03 -- secondary cross-reference for the
    HB 186 cancellation of the 2026 expanded holiday and the
    reverted 3-day Friday-Sunday window with the $75 clothing /
    $20 supplies / $20 instructional materials caps. Treated
    as one input among many; primary source is the Ohio
    Department of Taxation and the codified statute.
  - Sovos regulatory update "Ohio Cancels August 2026 Expanded
    Sales Tax Holiday"
    (https://sovos.com/regulatory-updates/sut/ohio-cancels-august-2026-expanded-sales-tax-holiday/),
    retrieved 2026-05-03 -- secondary cross-reference for the
    HB 186 December 19, 2025 enactment date. Treated as one
    input among many; primary source is the codified statute
    and the Ohio Legislative Service Commission analysis.
  - VATupdate news "Ohio Cancels Expanded August 2026 Sales
    Tax Holiday, Retains Traditional Exemption Structure"
    (https://www.vatupdate.com/2026/01/17/ohio-cancels-expanded-august-2026-sales-tax-holiday-retains-traditional-exemption-structure/),
    retrieved 2026-05-03 -- third independent cross-reference
    confirming August 7-9, 2026 dates and the per-category
    caps. Treated as one input among many.
  - Sales Tax Institute "Ohio Expands 2024 Sales Tax Holiday"
    (https://www.salestaxinstitute.com/resources/ohio-expands-2024-sales-tax-holiday),
    retrieved 2026-05-03 -- secondary cross-reference for the
    2024 expanded-holiday history (Tuesday July 30 - Thursday
    August 8, 2024; $500-per-item cap; HB 33 of 2023). Treated
    as one input among many; primary source is the Ohio Rev.
    Code section 5739.41 and the Department's Information
    Releases.
  - Ohio Legislature HB 186 page
    (https://www.legislature.ohio.gov/legislation/136/hb186),
    retrieved 2026-05-03 -- primary source for the bill text
    and General Assembly metadata
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms Ohio is a full member
- **Module file:** `src/opensalestax/states/ohio.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-oh branch)
- *Notes:*
  - **SST jurisdiction-type code mapping is an ASSUMPTION:**
    OH's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district),
    documented in the module docstring. Validating against an
    actual `OHR<...>.csv` file (and confirming how Cuyahoga
    RTA / other transit-authority rows are encoded) is the
    natural next maintenance task.
  - **Holiday schema limitation -- per-category caps:** the
    2026 holiday has DIFFERENT per-item caps for different
    categories (clothing $75, school supplies $20,
    instructional materials $20). The :class:`HolidayWindow`
    schema's single ``max_amount_per_item`` field cannot
    encode the per-category split; the module stores the
    higher $75 cap and documents the lower $20 cap for
    school_supplies and instructional_materials in the notes
    field. A future schema enhancement allowing per-category
    caps would let this be modeled with greater precision.
  - **Two-framework holiday architecture:** Ohio is unique
    among modeled states in having two mutually exclusive
    sales-tax-holiday frameworks (the longstanding 3-day
    section 5739.02(B)(55) holiday vs. the expanded 14-day
    section 5739.41 holiday created by HB 33 of 2023). Each
    year the legislature / Tax Commissioner picks one (or
    neither). 2024 and 2025 used the expanded version; 2026
    reverts to the traditional 3-day version after HB 186
    cancellation. **Future maintainers must NOT extrapolate**
    from any single year's pattern -- each year's holiday
    framework must be verified against the Ohio Department of
    Taxation's published guidance for that year and added
    explicitly to ``Ohio.holidays_for``.
  - **Digital goods:** Ohio's tax base for specified digital
    products is defined explicitly at the "sale" level (section
    5739.01(B)(12)) rather than via a separate imposition
    statute -- both perpetual-license downloads and
    subscription / streaming access fall in scope. Notable
    contrast with peer state NV, where the tangibility
    requirement of NRS 372.085 keeps electronically-delivered
    digital products outside the sales-tax base.

### OK -- Oklahoma

- **Statewide rate:** **4.500% effective long-standing** (current
  rate per 68 O.S. section 1354 -- the imposition statute in the
  Oklahoma Sales Tax Code, Title 68 Chapter 25)
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org). State FIPS: 40.
- **Local jurisdictions:** counties (under 68 O.S. sections 1370
  et seq.) and incorporated municipalities (under 68 O.S.
  sections 2701 et seq.) may impose local sales taxes by voter
  approval. Combined rates commonly fall in the **6.0%-11.5%**
  range -- among the highest combined ranges in the United
  States. Typical city + county stack adds +1.5% to +5.5% on top
  of the 4.5% state rate. Per-jurisdiction rates flow through
  the SST quarterly rate file via the inherited
  :class:`SstStateModule` parser.
- **MAJOR 2024 statutory change -- elimination of state-portion
  grocery tax:** **House Bill 1955** (2024 session; signed by
  Governor Stitt on **February 27, 2024**; effective **August
  29, 2024**) amended 68 O.S. section 1357 (general exemptions)
  and the food/food-ingredients definitions in 68 O.S. section
  1352 to exempt the sale of "food and food ingredients" from
  the state portion of sales tax (4.5% -> 0.000% state rate).
  **Local sales taxes (county, city) STILL APPLY at the full
  local rate** -- only the state portion was zeroed. Oklahoma's
  definition of "food and food ingredients" expressly INCLUDES
  bottled water, candy, and soft drinks (broader than the
  standard SST uniform definition that excludes those three).
  EXCLUDED from the exemption: prepared food, alcoholic
  beverages, dietary supplements, tobacco, and marijuana
  products -- those remain at the full 4.5% state rate.
  Companion bill: S.B. 1283 (2024). Encoded with
  ``rate_modifier=Decimal("0.000")`` per the AR/KS pattern; the
  engine does not yet apply rate_modifier (deferred to v0.6+),
  so until then it over-collects the 4.5% state portion on
  grocery line items.
- **Sales-tax holidays:** **ONE annual holiday** -- the
  **Oklahoma Annual Sales Tax Holiday** (commonly "Back-to-
  School") under **68 O.S. section 1357.10** (state-side
  exemption) and **68 O.S. section 1377** (parallel
  county/municipal-side exemption). First Friday in August at
  12:01 a.m. through midnight on the following Sunday -- a
  3-day window. Eligible items: clothing and footwear with a
  sales price of LESS THAN $100 per item. The exemption is per
  article, not per transaction. EXCLUDED: clothing accessories
  (jewelry, handbags, briefcases, luggage, umbrellas, wallets,
  watches, similar items); special clothing or footwear
  primarily designed for athletic activity or protective use;
  rentals of clothing or footwear. Notably narrow scope: OK's
  holiday covers ONLY clothing and footwear -- NOT school
  supplies, NOT school art supplies, NOT instructional
  materials, NOT computers / electronics (contrast with AR's
  26-52-444 which covers all of these). 2026 dates: **August 7
  (Friday) through August 9 (Sunday)**.
- **Threshold rules:** holiday-specific only -- clothing and
  footwear under $100 per item during the August holiday.
- **Notable peer-state difference -- digital goods NOT
  taxable:** unlike Iowa (Iowa Code 423.5A), Indiana (Ind. Code
  6-2.5-4-16.4), Arkansas (Act 141 of 2017), Kansas (2021 S.B.
  50), and many other SST members, Oklahoma has NOT enacted a
  sales-tax expansion to specified digital products. Per
  Oklahoma Tax Commission letter rulings and **Oklahoma
  Administrative Code section 710:65-19-156**, sales of digital
  products delivered electronically (music, video, ringtones,
  e-books, prewritten software downloads, software-maintenance
  contracts delivered electronically, video-game console points
  cards, online membership cards) are NOT subject to Oklahoma
  sales and use tax. Underlying rationale: 68 O.S. section 1354
  reaches only "tangible personal property" (and certain
  enumerated services), and OK has not adopted the SST
  "specified digital products" definitions. Prewritten software
  on tangible storage media IS taxable as TPP; the same software
  delivered electronically is NOT.
- **Marketplace nexus quirk:** OK's marketplace facilitator
  economic-nexus threshold is dramatically lower than its
  remote-seller threshold -- **$10,000** for marketplace
  facilitators versus **$100,000** for remote sellers (68 O.S.
  section 1391 et seq.). Informational only; does not affect
  rate calculation.
- **DOR URL:** **https://oklahoma.gov/tax.html** *(retrieved
  2026-05-03)*
- **Statutes consulted (Title 68 -- Revenue and Taxation,
  Chapter 25 -- Sales Tax Code):**
  - 68 O.S. section 1352 -- definitions (including "food and
    food ingredients" as amended by HB 1955 of 2024 to include
    bottled water, candy, and soft drinks)
  - 68 O.S. section 1354 -- tax levy / rate / sales subject to
    tax (4.5% state rate; the imposition statute)
  - 68 O.S. section 1357 -- general exemptions (prescription
    drugs / insulin / medical oxygen exemption; food/food-
    ingredients exemption added by HB 1955 of 2024 effective
    2024-08-29)
  - 68 O.S. section 1357.6 -- drugs and medical devices and
    equipment (Medicare/Medicaid-reimbursed prescription medical
    devices, eyeglasses, contact lenses, hearing aids)
  - 68 O.S. section 1357.10 -- clothing/footwear sales tax
    holiday (state-side; first Friday-Saturday-Sunday in August;
    $100 per-item cap)
  - 68 O.S. sections 1370 et seq. -- county sales tax
    enabling statutes
  - 68 O.S. section 1377 -- clothing/footwear holiday county-
    side exemption (parallel to 1357.10)
  - 68 O.S. section 1391 et seq. -- remote-seller and
    marketplace-facilitator economic-nexus thresholds
  - 68 O.S. sections 2701 et seq. -- municipal sales tax
    enabling statutes
  - **HB 1955 of 2024 session (Enrolled)** -- amended sections
    1352 and 1357 to create the food/food-ingredients state-tax
    exemption effective 2024-08-29; companion S.B. 1283
- **Oklahoma Administrative Code citations:**
  - OAC 710:65-13-511 -- Oklahoma Tax Commission rule
    implementing the August clothing/footwear holiday
  - OAC 710:65-19-156 -- Oklahoma Tax Commission rule
    establishing that electronically-delivered digital products
    and prewritten software are NOT taxable
- *Sources for rate/taxability:*
  - **Oklahoma Tax Commission** main page
    (https://oklahoma.gov/tax.html), retrieved 2026-05-03 --
    confirms 4.5% state rate
  - **Oklahoma Tax Commission "State Sales Tax on Food and Food
    Ingredients" guidance**
    (https://oklahoma.gov/tax/businesses/state-sales-tax-on-food-and-food-ingredients.html),
    retrieved 2026-05-03 -- confirms 0% state rate effective
    2024-08-29 per HB 1955; lists exclusions (prepared food,
    alcohol, dietary supplements, vitamins, OTC meds, toiletries,
    pet food, seller-prepared items)
  - **Oklahoma Tax Commission Sales Tax Holiday infographic**
    (https://oklahoma.gov/content/dam/ok/en/tax/documents/resources/publications/infographics/SalesTaxHoliday.pdf),
    retrieved 2026-05-03 -- 3-day August holiday for clothing
    and footwear under $100; 2026 dates August 7-9
  - **Sales Tax Institute holiday compendium**
    (https://www.salestaxinstitute.com/resources/sales-tax-holidays),
    retrieved 2026-05-03 -- secondary cross-reference for 2026
    dates of the August holiday (used as one input among many;
    primary source is the OK Tax Commission)
  - **Avalara guidance on Oklahoma digital products**
    (https://www.avalara.com/blog/en/north-america/2019/02/state-by-state-guide-to-digital-products-and-sales-tax.html),
    cross-referenced 2026-05-03 -- confirms OK does not tax
    electronically-delivered digital products; primary source is
    OAC 710:65-19-156 + OK Tax Commission letter rulings
  - **Avalara coverage of HB 1955**
    (https://www.avalara.com/blog/en/north-america/2024/04/oklahoma-exempts-food.html),
    retrieved 2026-05-03 -- secondary confirmation of 2024-08-29
    effective date for the state-portion grocery exemption
  - **Justia codified statutes** for Title 68 (sections 1352,
    1354, 1357, 1357.6, 1377), cross-referenced 2026-05-03
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms Oklahoma is a full SST member
- **Module file:** `src/opensalestax/states/oklahoma.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ok branch)
- *Notes:*
  - **HB 1955 (2024) is the headline finding.** The state-
    portion grocery elimination effective 2024-08-29 is the
    most significant Oklahoma sales-tax change in years and is
    encoded with ``rate_modifier=Decimal("0.000")`` per the
    AR/KS pattern. Until the engine wires through rate_modifier
    (deferred to v0.6+), the engine over-collects the 4.5%
    state portion on grocery line items in Oklahoma.
  - **Digital goods exemption is the second notable finding.**
    OK is one of a small minority of SST states that do NOT
    tax electronically-delivered digital products (joining e.g.
    Nevada). The basis is OAC 710:65-19-156 + OK Tax Commission
    letter rulings; 68 O.S. section 1354 only reaches tangible
    personal property and OK has not adopted the SST
    "specified digital products" definitions.
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    OK's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district).
    Validating against an actual OKR<...>.csv file is the
    natural next maintenance task.
  - **Holiday scope is notably narrow.** Unlike Arkansas (six
    scopes including school supplies, school art supplies,
    instructional materials, and electronics) or Texas (school
    supplies under $100), Oklahoma's August holiday covers ONLY
    clothing and footwear. A defensive regression test
    (`test_oklahoma_holiday_excludes_school_supplies`) catches
    a future maintainer who copies AR's multi-scope pattern.
  - **Oklahoma's grocery definition is broader than SST.**
    Bottled water, candy, and soft drinks are INCLUDED in the
    OK food/food-ingredients exemption per HB 1955. The
    standard SST uniform definition excludes those three; OK's
    definition is intentionally more taxpayer-favorable.
  - **Marketplace nexus threshold ($10K) is dramatically lower
    than the remote-seller threshold ($100K)**. This was the
    flagged tier-2 caveat in the prior `_tier2.py` docstring;
    it does not affect rate calculation but is documented in
    the module docstring for the next maintainer.

## RI -- Rhode Island

- **Statewide rate:** **7.000%** per **R.I. Gen. Laws section
  44-18-18** (the imposition statute in chapter 44-18, Sales and
  Use Taxes -- Liability and Computation). The 7.0% rate is one
  of the two highest single-state rates in the United States
  (tied with IN, MS, and TN at 7.0%).
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org). State FIPS: 44.
- **Local jurisdictions:** **NONE.** Rhode Island is one of a
  small number of US states that levies NO general local sales
  tax (joins IN, KY, MI in the no-local-tax SST club). The 7.0%
  state rate is the entire combined sales-tax rate at every
  Rhode Island address. Rhode Island has no functioning county-
  level government for tax-administration purposes, and the
  state's 39 cities and towns do not have general sales-tax
  authority under chapter 44-18. Two narrow industry-specific
  levies exist but are NOT general sales taxes (and are NOT
  modeled by the engine):
  - **1% local meals and beverages tax** under R.I. Gen. Laws
    section 44-18-18.1 -- paid by the customer on prepared meals
    served at eating and drinking establishments. Stacks ON TOP
    of the 7% state sales tax for restaurant transactions.
  - **1% hotel tax** under R.I. Gen. Laws section 44-18-36.1 --
    on transient lodging. Stacks similarly.
- **Sales-tax holidays:** **NONE.** Rhode Island has never
  enacted a recurring sales-tax holiday. Confirmed 2026-05-03
  against the Rhode Island Division of Taxation's published
  guidance and a search of chapter 44-18 for any periodic
  exemption window. There is no back-to-school holiday, no
  disaster-prep holiday, no Energy Star holiday, and no other
  recurring exemption period in Rhode Island law.
- **Threshold rules:** **CLOTHING $250-PER-ARTICLE EXEMPTION
  CAP** per **R.I. Gen. Laws section 44-18-30(27)**. Items
  priced AT OR BELOW $250 per article are fully exempt; for any
  single article priced ABOVE $250, the FIRST $250 remains
  exempt and only the PORTION ABOVE $250 is taxable at the 7%
  state rate. RI is the only state in the broad-clothing-
  exemption club (PA, MA, MN, NJ, VT) with this excess-above-
  cap structure -- distinct from NY's $110-per-item threshold
  and MA's $175-per-item threshold, where crossing the
  threshold makes the ENTIRE article taxable. **ENGINE
  CAVEAT:** the v0.10 engine does not yet enforce per-item
  thresholds (the v0.6 threshold-rules feature is on the
  roadmap -- see `specs/current-state.md`). The module encodes
  ``is_taxable=False`` for clothing to match the dominant
  retail mix in Rhode Island (everyday clothing well under
  $250: T-shirts, jeans, kids' apparel, shoes, basic
  outerwear). Trade-off: the engine UNDER-collects the 7% on
  the excess-above-$250 portion of high-end items. Example: a
  $400 wool coat owes $10.50 on the $150 above the cap, which
  the engine currently does not collect. The opposite encoding
  (``is_taxable=True``) would OVER-collect on the substantially
  larger population of everyday-clothing transactions, which
  was judged the worse failure mode at promotion time. The
  threshold is documented prominently in the rule's notes and
  in module-level constant ``RHODE_ISLAND_CLOTHING_EXEMPTION_CAP
  = Decimal("250.00")`` so the v0.6 work has a stable named
  reference.
- **DOR URL:** **https://tax.ri.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted (R.I. Gen. Laws Title 44, Chapter 18 --
  Sales and Use Taxes -- Liability and Computation):**
  - R.I. Gen. Laws section 44-18-7 -- definition of "tangible
    personal property" (and the long-standing prewritten-software-
    as-TPP rule that captures canned software regardless of
    delivery mechanism)
  - R.I. Gen. Laws section 44-18-7.1 -- definition of "specified
    digital product"; brings digital audio works, digital
    audiovisual works, and digital books delivered electronically
    into the sales-tax base. Added by section 3 of P.L. 2018,
    ch. 47, art. 4 (the FY2019 budget bill, signed June 22, 2018,
    effective October 1, 2018).
  - R.I. Gen. Laws section 44-18-18 -- imposition of the state
    sales tax at 7.0% on the gross receipts from retail sales of
    tangible personal property and specified digital products
  - R.I. Gen. Laws section 44-18-18.1 -- 1% local meals and
    beverages tax (non-general-sales-tax levy on restaurant
    transactions; NOT modeled by the engine)
  - R.I. Gen. Laws section 44-18-30(11) -- exemption for sales
    of food and food ingredients (the grocery exemption, tracking
    the SST uniform definition; excludes candy, soft drinks,
    dietary supplements, alcoholic beverages, and prepared food)
  - R.I. Gen. Laws section 44-18-30(27) -- exemption for clothing
    and footwear up to $250 per article (the headline RI
    distinctive feature)
  - R.I. Gen. Laws section 44-18-30(28) -- exemption for drugs
    sold pursuant to a written prescription
  - R.I. Gen. Laws section 44-18-36.1 -- 1% hotel tax on
    transient lodging (non-general-sales-tax levy; NOT modeled by
    the engine)
- **Public Laws of note:**
  - **P.L. 2018, ch. 47, art. 4, section 3** -- FY2019 budget
    bill that brought specified digital products into the sales-
    tax base by adding section 44-18-7.1; effective October 1,
    2018
- *Sources for rate/taxability:*
  - **Rhode Island Division of Taxation** main page
    (https://tax.ri.gov/), retrieved 2026-05-03 -- confirms
    7.0% state rate
  - **Rhode Island General Laws Title 44 Chapter 18** on the
    Rhode Island General Assembly site
    (http://webserver.rilegislature.gov/Statutes/TITLE44/44-18/INDEX.htm),
    retrieved 2026-05-03 -- primary source for sections 44-18-7,
    44-18-7.1, 44-18-18, 44-18-30
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms Rhode Island is a full SST member
  - **Sovos state summary**
    (`specs/research/sovos-state-summary.md`), cross-checked
    2026-05-03 -- confirms 7.000% state rate, no
    intra-state-rate-variation flag
  - **Sales Tax Handbook 2026** Rhode Island clothing exemption
    page
    (https://www.salestaxhandbook.com/rhode-island/clothing),
    cross-referenced 2026-05-03 -- secondary confirmation of the
    $250-per-article cap and excess-above-cap structure (used
    as one input among many; primary source is R.I. Gen. Laws
    section 44-18-30(27))
  - **Sales Tax Institute holiday compendium**
    (https://www.salestaxinstitute.com/resources/sales-tax-holidays),
    cross-referenced 2026-05-03 -- confirms RI does NOT appear
    on any holiday list (used as one input among many)
- **Module file:** `src/opensalestax/states/rhode_island.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ri branch)
- *Notes:*
  - **Clothing-threshold encoding decision (CRITICAL).** The
    R.I. Gen. Laws section 44-18-30(27) $250-per-article cap is
    encoded as ``is_taxable=False`` in the taxability matrix to
    match the dominant case (everyday clothing under $250). The
    v0.10 engine does not enforce per-item thresholds; this
    encoding UNDER-collects on the excess-above-$250 portion of
    high-end items. The opposite encoding (``is_taxable=True``)
    would OVER-collect on the larger population of everyday
    clothing transactions, which was judged the worse failure
    mode. The trade-off is documented in (a) the module
    docstring, (b) the clothing rule's ``notes`` field, (c) the
    ``RHODE_ISLAND_CLOTHING_EXEMPTION_CAP`` documentary
    constant, and (d) a defensive regression test
    (`test_rhode_island_clothing_documents_250_dollar_threshold`).
    The v0.6 threshold-rules feature should re-visit this
    encoding once per-item thresholds land in the engine.
  - **No-local-tax structure.** Rhode Island joins IN/KY/MI as
    SST states with NO general local sales tax. The module
    restricts ``jurisdiction_types`` to the canonical state code
    (`{"45": "state"}`) so any unexpected non-state row in a
    future quarterly file is silently dropped rather than
    miscategorized. Mirrors the defensive posture in the IN
    module.
  - **Restaurant + hotel sub-base.** The 1% local meals and
    beverages tax (section 44-18-18.1) and the 1% hotel tax
    (section 44-18-36.1) are non-general-sales-tax levies and
    are NOT modeled by the engine. An integrator selling
    restaurant transactions in RI needs to add the additional
    1% layer outside the engine; same for hotel-room
    transactions.
  - **No state sales-tax holiday.** RI has never enacted a
    recurring holiday. ``holidays_for(year)`` returns an empty
    iterator for every year; a defensive regression test
    (`test_rhode_island_holidays_for_all_years_returns_empty`)
    catches a future maintainer who adds a phantom holiday based
    on a stale article or confused with a peer state.
  - **SST jurisdiction-type code mapping is an ASSUMPTION:**
    RI's actual rate-file codes were not empirically validated
    at promotion time. The state-only restriction (`{"45":
    "state"}`) defaults to the canonical MN/WI mapping for the
    state code; validating against an actual `RIR<...>.csv` file
    is the natural next maintenance task. Because RI ships only
    a state-level row (no county/city/district to discover), the
    risk surface is small.

### **SD -- South Dakota**

- **Statewide rate:** **4.2% effective 2023-07-01** per HB 1137
  of the 98th SD Legislative Session (reduced from a prior
  4.5% rate). **STATUTORY SUNSET 2027-06-30**: the 4.2% rate
  expires by operation of HB 1137 on 2027-06-30 unless extended
  by the legislature; reverts to 4.5% effective 2027-07-01
  absent further action.
- **Tax model:** sales tax (with parallel use tax under SDCL
  chapter 10-46)
- **Local jurisdictions:** municipalities (gross receipts tax
  up to 2.0% per SDCL section 10-52-2; municipal special tax
  up to 1.0% on prepared food / lodging / amusements per SDCL
  section 10-52A-2) plus tribal gross receipts taxes on
  reservation land (administered through SD DOR via
  intergovernmental agreements). No general county sales tax.
  Combined effective rates typically 4.2%-6.2%.
- **Sales-tax holidays:** none. SD has never enacted a recurring
  sales-tax holiday; confirmed against SD DOR and SDCL chapter
  10-45 on 2026-05-03.
- **Threshold rules:** none.
- **DOR URL:** **https://dor.sd.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - SDCL section 10-45-1 -- definitions (tangible personal
    property, retail sale, gross receipts)
  - SDCL section 10-45-1.1 -- specified digital products
    definitions (added by SB 207 of the 83rd SD Legislative
    Session, 2008)
  - **SDCL section 10-45-2** -- imposition of the state retail
    sales tax (the 4.2% rate; the headline imposing statute)
  - **SDCL section 10-45-2.4** -- food and food ingredients
    subject to the full state sales tax (the statute that makes
    SD a notable peer-state outlier on grocery taxation)
  - **SDCL section 10-45-14** -- prescription drugs exemption
    (and certain related medical equipment / insulin / oxygen)
  - SDCL chapter 10-46 -- complementary use tax
  - SDCL chapter 10-52 -- municipal non-ad-valorem taxes
    (including the section 10-52-2 municipal gross receipts
    tax up to 2.0%)
  - SDCL chapter 10-52A -- municipal special tax (section
    10-52A-2 up to 1.0% on prepared food / lodging /
    amusements / alcoholic beverages)
  - **SDCL section 10-64-2** -- Wayfair-era remote-seller
    economic-nexus statute ($100,000 / 200-transaction
    thresholds, sustained by *South Dakota v. Wayfair, Inc.*,
    138 S. Ct. 2080 (2018))
  - **HB 1137 of the 98th SD Legislative Session (2023)** --
    reduced state sales tax rate from 4.5% to 4.2% effective
    2023-07-01; included a statutory sunset reverting to 4.5%
    on 2027-06-30 unless extended
  - **Initiated Measure 28 (November 2024 ballot)** --
    REJECTED by SD voters; would have eliminated the state
    grocery tax (SDCL section 10-45-2.4 remains in force)
- *Sources for rate/taxability:*
  - **South Dakota Department of Revenue** main page
    (https://dor.sd.gov/), retrieved 2026-05-03 -- confirms
    4.2% state rate and references HB 1137 sunset
  - **SD DOR sales-and-use-tax guidance** under the Business
    Tax Division (https://dor.sd.gov/businesses/taxes/sales-use-tax/),
    retrieved 2026-05-03 -- confirms full taxation of food /
    food ingredients and the prescription-drug exemption
  - **South Dakota Codified Laws** (Title 10, chapters 10-45,
    10-46, 10-52, 10-52A, 10-64) via the SD Legislative
    Research Council (https://sdlegislature.gov/Statutes/),
    cross-referenced 2026-05-03
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms South Dakota is a full SST member
  - **Sovos summary entry for SD**
    (`specs/research/sovos-state-summary.md`) cross-referenced
    2026-05-03; SD is one of the rows flagged for column drift
    in the Sovos defect table -- DOR was used as primary source
- **Module file:** `src/opensalestax/states/south_dakota.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-sd branch)
- *Notes:*
  - **Rate sunset (2027-06-30) is the headline maintenance
    item.** Unlike most peer states whose rate is open-ended in
    statute, SD's current 4.2% has a hard statutory expiration.
    Maintainers must monitor SD legislative sessions in 2026 and
    2027 for an extension bill, a further reduction, or
    silent-default expiration. The module exports a documentary
    constant ``SOUTH_DAKOTA_RATE_SUNSET_ISO = "2027-06-30"``
    and a regression test guards both the constant and the
    docstring's mention of the sunset.
  - **Groceries fully taxed is the second notable finding.**
    SD is one of a small minority of U.S. states (and the only
    SST member of that group) that fully tax groceries at the
    state rate. Initiated Measure 28 (Nov 2024) attempted to
    repeal the rule and failed at the ballot box. A defensive
    regression test (``test_south_dakota_groceries_are_taxable_regression``)
    explicitly catches a contributor copy-pasting from a peer
    SST state (IA / KS / KY / ND / NE -- all of which exempt
    groceries) and accidentally flipping the rule.
  - **Wayfair connection documented.** SD is the plaintiff in
    *South Dakota v. Wayfair, Inc.*, 138 S. Ct. 2080 (2018),
    which overturned *Quill Corp. v. North Dakota* (1992) and
    established the modern economic-nexus regime. The Wayfair
    statute itself (SDCL section 10-64-2) governs nexus, not
    rate calculation -- but the case is so foundational to
    every state's modern sales-tax-collection regime that the
    docstring records the lineage. A regression test guards the
    Wayfair citation in the docstring.
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    SD's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district).
    Validating against an actual SDR<...>.csv file is the
    natural next maintenance task.
  - **Tribal taxes flow through the SST file.** South Dakota's
    intergovernmental tax-collection agreements with multiple
    Sioux nations (Cheyenne River, Crow Creek, Oglala, Rosebud,
    Standing Rock, Yankton, plus several others) cause tribal
    gross-receipts taxes on reservation land to be administered
    by the SD DOR alongside municipal taxes. Per-jurisdiction
    rates therefore appear in the SST quarterly rate file as
    ordinary city/district rows; the inherited
    ``SstStateModule`` parser handles them with no SD-specific
    code.

### TN -- Tennessee

- **Statewide rate:** **7.000% effective long-standing** (current
  rate per Tenn. Code Ann. section 67-6-202 -- the imposition
  statute in the Retailers' Sales Tax Act, Title 67 Chapter 6).
  At 7.0% Tennessee has one of the highest single-state sales
  tax rates in the United States (tied with IN, MS, RI; only
  CA's 7.25% is higher).
- **Tax model:** sales tax (SST -- **associate** member, since
  October 1, 2005; verified 2026-05-03 against the SST member
  roster on streamlinedsalestax.org). **Tennessee is the ONLY
  Associate Member State** -- distinct from the 23 SST full
  members. An Associate Member State per the Streamlined Sales
  and Use Tax Agreement is a state determined by the SST
  Governing Board to be substantially compliant with the
  Agreement except that not all of the state's statutory or
  rule changes are yet in effect, OR a state in compliance
  with nearly all parts of the Agreement. Practical
  implication: TN publishes rate / boundary files in the
  canonical SST format (so the inherited SstStateModule parser
  works without override), but TN has NOT adopted every
  uniformity provision (most notably the reduced grocery rate
  at section 67-6-228, which differs from the SST uniform full-
  exemption pattern). State FIPS: 47.
- **Local jurisdictions:** counties and incorporated cities may
  levy a local option sales tax under the **1963 Local Option
  Revenue Act** (Tenn. Code Ann. sections 67-6-701 through
  67-6-716). Per Tenn. Code Ann. section 67-6-702(a)(1), the
  combined county-plus-city local rate may not exceed **2.75%**
  (approved by referendum). Combined rates therefore range
  **7.0% to 9.75%**, most commonly **9.25%-9.75%** (most TN
  counties have voted in at or near the maximum local cap). Per-
  jurisdiction rates flow through the SST quarterly rate file
  via the inherited :class:`SstStateModule` parser.
- **Single-article cap (notable peculiarity):** per Tenn. Code
  Ann. section 67-6-702(d), the local sales tax applies only to
  the **first $1,600** of the sales price of any single article
  of tangible personal property. There is also a state "single-
  article tax" of 2.75% on the portion of the sales price
  between $1,600 and $3,200 per single article (Tenn. Code Ann.
  section 67-6-202(c)). The single-article cap is NOT modeled
  in v1 of OpenSalesTax (engine treats every line item as a
  single unit at a flat combined rate). Documented for the next
  maintainer.
- **REDUCED grocery rate (key TN-specific feature):** food and
  food ingredients are TAXABLE at a **reduced state rate of
  4.0%** per **Tenn. Code Ann. section 67-6-228** (stable since
  2017-07-01). Rate history:

    - Pre-July 2002: 6.0% (general state rate at the time)
    - 2002-07-15 to 2007: phased reductions to 5.5%
    - 2007 to 2013: 5.5% state rate on groceries
    - 2013-07-01 to 2017-06-30: reduced to 5.0%
    - **2017-07-01 onward: reduced to 4.0%** (current rate;
      stable since July 1, 2017)

  The reduced state rate applies ONLY to "food and food
  ingredients" as defined in section 67-6-228 / 67-6-102, which
  follows the SST uniform definition (excludes prepared food,
  candy, dietary supplements, and alcoholic beverages -- those
  remain at the general 7.0% state rate). LOCAL sales taxes
  STILL APPLY to groceries at the FULL local rate; only the
  state portion is reduced. Encoded with
  ``rate_modifier=Decimal("4.000")`` mirroring the IL/MO/AR/OK
  reduced-grocery-rate pattern. The engine does not yet apply
  rate_modifier (deferred to v0.6+); until then it over-collects
  the state portion of grocery line items in TN by 3 percentage
  points (charging 7.0% instead of the statutory 4.0%).
- **Sales-tax holidays:** **ONE recurring annual holiday for the
  general public in 2026** -- the **Tennessee Sales Tax Holiday**
  (commonly "Back-to-School") under **Tenn. Code Ann. section
  67-6-393**. The statute fixes the holiday to a 3-day window
  beginning at 12:01 a.m. on the last Friday of July and ending
  at 11:59 p.m. on the following Sunday. **2026 dates: July 24
  (Friday) through July 26 (Sunday)**. Per longstanding TN DOR
  practice, when the literal "last Friday in July" would push
  Sunday into August (as it does in 2026 -- last Friday is
  July 31), the holiday uses the last full Friday-Sunday weekend
  wholly within July. Eligible items per section 67-6-393:

    - Clothing -- $100 OR LESS per item
    - School supplies -- $100 OR LESS per item
    - School art supplies -- $100 OR LESS per item
    - Computers -- $1,500 OR LESS per item

  Each scope is encoded as a separate :class:`HolidayWindow`
  (4 windows total) so the engine can per-category match and
  apply the correct per-item cap. The exemption covers BOTH
  state and local sales tax. Exemption is per article (an item
  priced above its category cap is fully taxable; no proration).
- **Other 2026 holidays (NONE enacted as of promotion):** TN ran
  one-time grocery sales-tax holidays in 2022 (Public Chapter
  1003 of 2022; one month, August 1-31, 2022) and 2023 (Public
  Chapter 377 of 2023; three months, August 1 - October 31,
  2023). These were ad-hoc legislative actions, NOT recurring.
  Several 2026 proposals exist (e.g., HB 1486 / SB 1785 to
  exempt food sold to persons aged 65+ from July 1 to September
  30, 2026; proposals for a fifth-day-of-each-month exemption)
  but **NONE are enacted** as of 2026-05-03. The module models
  ONLY the recurring back-to-school holiday.
- **Threshold rules:** holiday-specific only -- per-item caps
  for the 4 holiday scopes (clothing/school supplies/school art
  supplies $100; computers $1,500). NO year-round threshold
  exemptions (unlike NY's $110 clothing or MA's $175 clothing).
- **Digital goods (notable early-adopter):** specified digital
  products are TAXABLE at 7.0% per **Tenn. Code Ann. section
  67-6-233**, effective **January 1, 2009** (originally added
  by Public Chapter 530 of the 2008 General Assembly).
  Tennessee was an early-adopter state for digital product
  taxation, predating most peer SST states by several years
  (Iowa: 2019; Indiana: 2018; Arkansas: 2018; Kansas: 2021).
  Section 67-6-233 imposes the sales tax on the retail sale,
  lease, licensing or use of specified digital products or
  video game digital products transferred to or accessed by
  subscribers or consumers in Tennessee.
- **Wayfair note (informational):** Tennessee was the LOSING
  party in the historical 1992 Quill Corp. v. North Dakota
  physical-presence precedent that set the groundwork for the
  Wayfair litigation 26 years later. After Wayfair (2018) TN
  updated its own economic-nexus regime under Tenn. Code Ann.
  section 67-6-501 and rules. Current threshold for remote
  sellers: $100,000 in TN sales over the prior 12 months (no
  transaction-count alternative). Marketplace facilitator
  threshold: also $100,000 (Tenn. Code Ann. section 67-6-535
  et seq.). Informational only -- the rate-calculation engine
  does not gate on nexus.
- **DOR URL:** **https://www.tn.gov/revenue.html** *(retrieved
  2026-05-03)*
- **Statutes consulted (Tenn. Code Ann. Title 67 -- Taxes and
  Licenses, Chapter 6 -- Sales and Use Taxes):**
  - Tenn. Code Ann. section 67-6-102 -- definitions (including
    "food and food ingredients" and "prepared food" via SST
    uniform definitions)
  - Tenn. Code Ann. section 67-6-202 -- imposition of sales tax;
    7.0% state rate (the imposition statute)
  - Tenn. Code Ann. section 67-6-228 -- reduced 4.0% state rate
    on food and food ingredients (current rate effective
    2017-07-01)
  - Tenn. Code Ann. section 67-6-233 -- taxation of specified
    digital products and video game digital products (effective
    2009-01-01 per Public Chapter 530 of 2008)
  - Tenn. Code Ann. section 67-6-314 -- exemption for medical
    equipment and devices
  - Tenn. Code Ann. section 67-6-320 -- exemption for
    prescription drugs (and OTC drugs dispensed pursuant to a
    prescription); covers disposable medical supplies for IV
    administration
  - Tenn. Code Ann. section 67-6-393 -- back-to-school sales tax
    holiday (4 scopes: clothing/$100, school supplies/$100,
    school art supplies/$100, computers/$1500)
  - Tenn. Code Ann. section 67-6-409 -- year-round exemption for
    gun safes and firearm safety devices (effective 2021-07-01;
    not modeled as a HolidayWindow because it is year-round
    rather than a date-bounded holiday)
  - Tenn. Code Ann. sections 67-6-501, 67-6-535 et seq. --
    economic nexus and marketplace facilitator thresholds
    (informational only; not used by rate-calculation engine)
  - Tenn. Code Ann. sections 67-6-701 through 67-6-716 -- the
    1963 Local Option Revenue Act (county and city local sales
    taxes)
  - Tenn. Code Ann. section 67-6-702 -- local option rates;
    2.75% combined cap; single-article $1,600 cap on the local
    portion; state "single-article tax" of 2.75% on the
    portion between $1,600 and $3,200
  - Public Chapter 377 of 2023 -- 3-month grocery holiday
    (August - October 2023; ONE-TIME)
  - Public Chapter 1003 of 2022 -- 1-month grocery holiday
    (August 2022; ONE-TIME)
  - Public Chapter 530 of 2008 -- enacted section 67-6-233
    (digital products taxation, effective 2009-01-01)
- *Sources for rate/taxability:*
  - **Tennessee Department of Revenue main page**
    (https://www.tn.gov/revenue.html), retrieved 2026-05-03 --
    confirms 7.0% state rate
  - **Tennessee Department of Revenue Sales Tax Holiday page**
    (https://www.tn.gov/revenue/taxes/sales-and-use-tax/sales-tax-holiday.html),
    referenced 2026-05-03
  - **Tennessee DOR 2024 Annual Sales Tax Holiday press
    release**
    (https://www.tn.gov/revenue/news/2024/7/11/annual-sales-tax-holiday-happening-july-26---july-28.html),
    retrieved 2026-05-03 -- confirms 2024 dates (July 26-28)
    and the $100/$100/$1500 thresholds
  - **Tennessee DOR 2025 Annual Sales Tax Holiday press
    release**
    (https://www.tn.gov/revenue/news/2025/7/11/annual-sales-tax-holiday-happening-july-25---july-27.html),
    retrieved 2026-05-03 -- confirms 2025 dates (July 25-27)
    and the $100/$100/$1500 thresholds; cites Tenn. Code section
    67-6-393
  - **Tennessee DOR Streamlined Sales Tax page**
    (https://www.tn.gov/revenue/taxes/sales-and-use-tax/streamlined-sales-tax.html),
    referenced 2026-05-03 -- confirms TN's SST associate-member
    status and cites Public Chapter 377 of 2023 sourcing-
    provision changes effective 2024-07-01
  - **Tennessee DOR SUT-13 Sales and Use Tax Rates Overview**
    (https://revenue.support.tn.gov/hc/en-us/articles/360058139672-SUT-13-Sales-and-Use-Tax-Rates-Overview),
    referenced 2026-05-03 -- confirms 7.0% state rate, 4.0%
    grocery rate, single-article cap mechanics
  - **Tennessee DOR SUT-54 Prepared Food**
    (https://revenue.support.tn.gov/hc/en-us/articles/360058231192-SUT-54-Prepared-Food-Definition-and-Tax-Rate),
    referenced 2026-05-03 -- definition of prepared food and
    confirmation it taxes at the general 7.0% rate
  - **Tennessee DOR SUT-65 Specified Digital Products**
    (https://revenue.support.tn.gov/hc/en-us/articles/360058688471-SUT-65-Specified-Digital-Products),
    referenced 2026-05-03 -- confirms digital products
    taxability per section 67-6-233 effective 2009-01-01
  - **Tennessee DOR SUT-125 Sales of Prescription Drugs**
    (https://revenue.support.tn.gov/hc/en-us/articles/360058688011-SUT-125-Sales-of-Prescription-Drugs),
    referenced 2026-05-03 -- confirms section 67-6-320
    prescription-drug exemption and 67-6-314 medical devices
    cross-reference
  - **Justia codified Tennessee statutes** for Title 67 Chapter
    6 (sections 67-6-202, 228, 233, 314, 320, 393, 702),
    cross-referenced 2026-05-03
  - **FindLaw Tenn. Code section 67-6-393** (codes.findlaw.com),
    cross-referenced 2026-05-03 -- statute text for back-to-
    school holiday with $100/$100/$100/$1500 thresholds
  - **Streamlined Sales Tax member roster + Tennessee detail
    page** (https://www.streamlinedsalestax.org/state-details/tennessee),
    cross-checked 2026-05-03 -- confirms TN's SST associate-
    member status and details
  - **Sales Tax Institute holiday compendium**
    (https://www.salestaxinstitute.com/resources/sales-tax-holidays),
    retrieved 2026-05-03 -- secondary cross-reference for 2026
    dates (July 24-26) of the back-to-school holiday
  - **Avalara coverage of TN 2026 sales-tax-holiday and grocery-
    holiday proposals**
    (https://www.avalara.com/blog/en/north-america/2026/02/will-tennessee-exempt-groceries-from-sales-tax.html),
    retrieved 2026-05-03 -- confirms NO 2026 grocery holiday
    enacted at promotion time; documents pending HB 1486 / SB
    1785 proposals for 65+ exemption (NOT enacted)
  - **The Mountain Press article on 2026 grocery holiday
    prospects**
    (https://www.themountainpress.com/roane/news/grocery-tax-holiday-in-2026-looks-bleak/article_aaa593dd-05c2-5fe4-bb86-6b174317d6b1.html),
    retrieved 2026-05-03 -- confirms no general-public grocery
    holiday is scheduled for 2026
  - **Innovate Tax 2026 Sales Tax holidays compendium**
    (https://innovatetax.com/blog/2026-sales-tax-holidays/),
    retrieved 2026-05-03 -- confirms TN 2026 dates as July 24-26
- **Module file:** `src/opensalestax/states/tennessee.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-tn branch)
- *Notes:*
  - **TN is the only SST associate member.** All 22 other SST
    members are full members. Practical implication: TN's
    quarterly rate / boundary files use the canonical SST
    format (inherited parser works without override), but TN
    has not adopted every uniformity provision (notably the
    reduced grocery rate, which differs from the SST uniform
    full-exemption pattern).
  - **Reduced grocery rate of 4.0% is the headline TN-specific
    finding.** Encoded with rate_modifier=Decimal("4.000") per
    the IL/MO/AR/OK pattern. Until v0.6+ wires through
    rate_modifier, the engine over-collects the state portion
    on TN grocery line items by 3 percentage points (charging
    7.0% instead of the statutory 4.0%).
  - **Back-to-school holiday has 4 distinct scopes** -- each
    encoded as a separate HolidayWindow with its own per-item
    cap. Defensive regression test
    (`test_tennessee_holiday_scope_set`) catches a future
    maintainer who drops a scope or copies a peer state's
    different scope (e.g., AR's electronics scope or FL's
    emergency-supplies scope).
  - **2026 holiday dates require interpretation.** The literal
    statutory reading "last Friday of July ... following Sunday"
    would push Sunday into August in 2026 (last Friday is
    July 31; Sunday would be August 2). Per longstanding TN DOR
    practice the holiday uses the last full Friday-Sunday
    weekend wholly within July, i.e., July 24-26 in 2026. All
    independent 2026 secondary sources (Sales Tax Institute,
    Innovate Tax, Avalara, Calvetti Ferguson) report July 24-26.
    A future maintainer should re-verify against the TN DOR's
    official 2026 press release once issued.
  - **Digital goods early-adopter status.** TN was among the
    first states to tax specified digital products (effective
    2009-01-01, via section 67-6-233 added by Public Chapter
    530 of 2008), predating Iowa (2019), Indiana (2018),
    Arkansas (2018), and Kansas (2021).
  - **NO 2026 grocery holiday enacted.** Multiple 2026-session
    proposals exist (HB 1486 / SB 1785 for persons 65+ from
    July 1 - September 30, 2026; fifth-day-of-each-month
    proposals) but NONE are enacted at promotion time. The
    module models ONLY the recurring back-to-school holiday.
    If the General Assembly enacts a 2026 grocery holiday, the
    module must be updated.
  - **SST jurisdiction-type code mapping is an ASSUMPTION.**
    TN's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district).
    Validating against an actual TNR<...>.csv file is the
    natural next maintenance task.
  - **Single-article cap is NOT modeled.** Tenn. Code Ann.
    section 67-6-702(d) limits the local portion to the first
    $1,600 of any single article's sales price; section
    67-6-202(c) imposes a state "single-article tax" of 2.75%
    on the portion between $1,600 and $3,200. The engine treats
    every line item as a single unit at a flat combined rate.
    Documented for the next maintainer; would require engine
    work to support (likely overlaps with the v0.6+ threshold-
    rule feature).

### UT -- Utah

- **Statewide rate:** **4.85% statewide combined rate**, composed
  of 4.70% state (Utah Code section 59-12-103(2)(a)(i)(A)) +
  0.10% statewide-uniform local-option (Utah Code section
  59-12-204) + 0.05% mass transit basic (Utah Code section
  59-12-103(2)(a)(i)(C)). Effective in current composition since
  the state-rate portion was raised from 4.65% to 4.70% on April
  1, 2019 (SB 2001 of the 2018 Third Special Session); the other
  two components have been stable for many years.
- **Tax model:** sales tax (Utah Sales and Use Tax Act, Title 59
  Chapter 12).
- **Local jurisdictions:** counties, cities, towns, and special
  transit districts may stack local sales taxes under various
  enabling acts in Title 59 Chapter 12 Parts 2 and 4-22.
  Combined rates typically range 6.10%-9.05% in the major metro
  areas (Salt Lake County, Utah County, Davis County, Weber
  County). UT is an SST member; per-jurisdiction rates flow
  through the standard SST quarterly file.
- **Sales-tax holidays:** **NONE.** Utah has NO state sales-tax
  holiday in any year. Several legislative proposals to enact
  a back-to-school holiday have been introduced in past
  sessions (most recently HB 296 of the 2017 General Session)
  and have failed to pass. Verified 2026-05-03 against Utah
  State Tax Commission publications.
- **Threshold rules:** none.
- **DOR URL:** **https://tax.utah.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted:**
  - Utah Code section 59-12-103 -- imposition statute and rate
    composition (4.70% + 0.10% + 0.05% = 4.85%); also the
    reduced-rate provision for food and food ingredients at
    section 59-12-103(2)(a)(ii) (1.75% state-portion grocery
    rate)
  - Utah Code section 59-12-102 -- definitions, including the
    "products transferred electronically" definition added by
    Senate Bill 65 of the 2008 General Session (digital goods
    in the sales-tax base)
  - Utah Code section 59-12-104(11) -- prescription drug
    exemption
  - Utah Code section 59-12-204 -- statewide-uniform 0.10%
    local-option sales tax (the second of the three components
    in the 4.85% statewide rate)
  - Utah Code section 59-12-603 -- county-administered
    restaurant tax (~1.00%; separate non-sales-tax layer NOT
    modeled in this engine)
  - Utah Code section 20A-1-201.5 -- ballot publication
    requirements (the basis on which Constitutional Amendment
    A was struck from the 2024 ballot)
  - Utah Code Title 58, Chapter 17b -- prescriber licensing
    (referenced by the prescription-drug exemption in section
    59-12-104(11))
  - Senate Bill 65, Utah 2008 General Session -- expanded
    sales-tax base to include "products transferred
    electronically" (digital goods)
  - House Bill 54, Utah 2023 General Session -- companion bill
    to Constitutional Amendment A; would have eliminated the
    1.75% state-portion grocery tax conditional on Amendment
    A passing
  - Title 24, Navajo Nation Code section 601 et seq. (Navajo
    Nation Sales Tax) -- documented in module docstring as
    deferred sub-state regime; NOT modeled in v1
  - *Federal Indian-law preemption authority for the Navajo
    Nation regime:* **Warren Trading Post v. Arizona Tax
    Commission**, 380 U.S. 685 (1965); **Central Machinery Co.
    v. Arizona Tax Commission**, 448 U.S. 160 (1980)
- *Sources for rate/taxability:*
  - **Utah State Tax Commission**, https://tax.utah.gov/
    (retrieved 2026-05-03) -- the authoritative DOR; published
    quarterly Sales and Use Tax Rate publications (the source
    of the 4.85% statewide combined rate breakdown), Publication
    25 (Sales and Use Tax General Information; the source for
    the 3.00% composite grocery rate worked example), and the
    sales-tax-holiday-disclaimer (no Utah state holiday).
  - **Utah Code (le.utah.gov)**, https://le.utah.gov/xcode/
    Title59/Chapter12/59-12.html?v=C59-12_2024 (retrieved
    2026-05-03) -- the codified text of Title 59 Chapter 12.
  - **Justia codified statutes** for Title 59 Chapter 12
    (sections 102, 103, 104, 204, 603), cross-referenced
    2026-05-03.
  - **Utah Foundation, "Constitutional Amendment A: Income
    Tax for Public Education"**, retrieved 2026-05-03 --
    background on the income-tax earmark and the 2023-2024
    legislative effort to enable grocery-tax elimination.
  - **Streamlined Sales Tax member roster**,
    https://www.streamlinedsalestax.org (retrieved 2026-05-03)
    -- confirms Utah is a full SST member.
  - **Avalara guidance on Utah digital products**,
    https://www.avalara.com/blog/en/north-america/2019/02/state-by-state-guide-to-digital-products-and-sales-tax.html
    (cross-referenced 2026-05-03) -- secondary confirmation
    that UT taxes electronically-delivered digital goods;
    primary source is Utah Code section 59-12-102 + SB 65 of
    2008.
  - **Navajo Tax Commission**, https://www.navajotax.org/
    (retrieved 2026-05-03) -- the authority that administers
    the Navajo Nation gross receipts tax (deferred sub-state
    regime; not modeled).
- **Module file:** `src/opensalestax/states/utah.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-ut branch)
- *Notes:*
  - **Statewide rate composition is the headline finding.** The
    4.85% combined rate decomposes into 4.70% state + 0.10%
    statewide-uniform local + 0.05% mass transit basic; all
    three are imposed at the state level and uniform statewide.
    Documented in the module docstring so future maintainers
    can audit each component independently.
  - **Reduced 1.75% state-portion grocery rate.** Encoded with
    ``rate_modifier=Decimal("1.75")`` per Utah Code section
    59-12-103(2)(a)(ii). Local rates apply to groceries at
    full local rate; the composite tax on typical groceries in
    jurisdictions with the standard 1.25% local stack is 3.00%.
    Mirrors the IL / MO / VA / TN reduced-state-grocery-rate
    patterns. Until v0.6+ wires the modifier through, the
    engine over-collects 3.10 percentage points on grocery line
    items in Utah.
  - **Constitutional Amendment A (2024) was struck from the
    ballot.** Amendment A would have removed the Utah
    Constitution's earmark on income tax revenue (currently
    restricted to education), enabling the legislature to enact
    HB 54 (2023) and eliminate the 1.75% state-portion grocery
    tax. The Utah Third District Court (affirmed by the Utah
    Supreme Court) struck Amendment A from the November 5, 2024
    ballot for failure to properly publish the amendment under
    Utah Code section 20A-1-201.5. The 1.75% state-portion
    grocery tax accordingly continues to apply; future
    legislative sessions may revisit the constitutional
    question.
  - **Navajo Nation gross receipts tax is a DEFERRED sub-state
    regime.** The Navajo Nation reservation extends into
    northeastern Utah (San Juan County); sales by Navajo-
    enrolled-member businesses on the reservation are subject
    only to the Navajo Nation gross receipts tax (Title 24,
    Navajo Nation Code section 601 et seq.), NOT Utah sales
    tax, on the basis of long-standing federal Indian-law
    preemption (Warren Trading Post / Central Machinery line of
    Supreme Court cases). This engine does NOT model the
    Navajo Nation regime in v1; calls to /v1/calculate for
    addresses inside the reservation will return the standard
    Utah sales tax rate, which is incorrect for sales by Navajo-
    enrolled-member businesses. Operators serving Navajo Nation
    businesses must apply an exemption certificate at the line-
    item level. Structurally analogous to LA parishes, CO home-
    rule cities, and AL self-administering municipalities --
    a future :class:`SubJurisdiction` Protocol extension may
    first-class-model these regimes in v1.0+.
  - **NO state sales-tax holiday.** Verified 2026-05-03;
    several legislative proposals (most recently HB 296 of
    2017) have failed to enact one. ``holidays_for(year)``
    returns an empty iterator unconditionally. A defensive
    parametrized regression test
    (``test_utah_holidays_always_empty``) catches a future
    maintainer who tries to add a holiday without confirming
    the legislature actually passed one.
  - **Digital goods are taxable.** Notable peer-state difference
    from Oklahoma (which does NOT tax digital goods per OAC
    710:65-19-156). UT places digital goods in the sales-tax
    base via SB 65 of 2008 amending Utah Code section 59-12-102.
  - **SST jurisdiction-type code mapping is an ASSUMPTION.**
    UT's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district).
    Validating against an actual UTR<...>.csv file is the
    natural next maintenance task.

### VT -- Vermont

- **Statewide rate:** **6.000% effective 1969-06-01 (current 6%
  rate effective 2003-10-01)**. Vermont's general sales tax was
  enacted by Act 144 of the 1969 Adjourned Session at 3%; the rate
  was raised to 4% in 1982, to 5% in 1991, and to its current 6%
  effective **October 1, 2003** by **Act 68 of the 2003
  Legislative Session** as part of the education-funding reform
  package. The 6% rate is the current rate per the imposition
  statute at **Vt. Stat. Ann. tit. 32, section 9771**, has been
  stable for 20+ years, and no rate change is currently in the
  legislative pipeline.
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org). State FIPS: **50**.
- **Local jurisdictions:** counties impose **NO** sales tax;
  incorporated municipalities (cities and towns) MAY adopt a
  **Local Option Sales Tax (LOST)** of **EXACTLY 1%** under
  **24 V.S.A. section 138** (originally enacted by Act 60 of
  1997 -- the Equal Educational Opportunity Act -- expanded by
  Act 68 of 2003). The local option rate is fixed at 1% by
  statute (a town adopts it or does not -- no other rate is
  permitted). Adoption requires both charter authorization and a
  binding voter referendum. Approximately **17 of Vermont's ~247
  incorporated municipalities** have opted in as of 2026,
  including: Burlington, South Burlington, Williston,
  Colchester, Essex Junction, Winooski, Stowe, Brattleboro,
  Manchester, Killington, Dover, Wilmington, St. Albans Town,
  Rutland Town, Middlebury, Montpelier, and Brandon (the precise
  current list is the Vermont Department of Taxes
  "Municipalities with a Local Option Tax" page at
  https://tax.vermont.gov/business/lot/municipalities). Combined
  rates in opted-in municipalities are **EXACTLY 7.0%**;
  combined rates everywhere else are **EXACTLY 6.0%**. The VT
  Department of Taxes administers the local option centrally
  (sellers remit a single combined amount), making VT's local-
  tax mechanics simpler than home-rule states like CO or
  independent-locals states like AL. Per-municipality rate rows
  flow through the SST quarterly rate file via the inherited
  :class:`SstStateModule` parser; v1 ships state-only baseline
  while LOST loading is deferred to per-municipality data
  ingestion.
- **Sales-tax holidays:** **NONE.** Vermont has never enacted a
  sales-tax holiday and none is currently scheduled in any year
  (verified 2026-05-03 against the Vermont Department of Taxes
  Sales Tax landing page and the Sales Tax Institute holiday
  compendium). Mirrors NJ, NE, DC, ID, IN, ND, MI, KY, NV, NC.
- **Threshold rules:** **NONE** for clothing -- VT has a broad
  year-round clothing exemption with no per-item dollar cap
  (contrast with NY's $110-per-item threshold and MA's
  $175-per-item threshold).
- **DOR URL:** **https://tax.vermont.gov/** *(retrieved
  2026-05-03)*
- **Statutes consulted (Title 32 -- Taxation and Finance,
  Chapter 233 -- Sales and Use Tax; Title 24 -- Municipal and
  County Government, section 138 for the local option):**
  - **Vt. Stat. Ann. tit. 32, section 9771** -- imposition
    statute (sales tax on tangible personal property at 6%)
  - **Vt. Stat. Ann. tit. 32, section 9701(7)** -- definition of
    "tangible personal property"
  - **Vt. Stat. Ann. tit. 32, section 9701(31)(B)** -- defined
    term "specified digital products" (added by H. 528 of the
    2014 Legislative Session, Act 174 of 2014, effective
    2015-07-01)
  - **Vt. Stat. Ann. tit. 32, section 9741(2)** -- prescription-
    drug exemption
  - **Vt. Stat. Ann. tit. 32, section 9741(13)** -- food and
    food ingredients exemption
  - **Vt. Stat. Ann. tit. 32, section 9741(45)** -- broad
    clothing exemption (one of only ~5 states with a year-round
    broad clothing exemption: PA, MA, MN, NJ, VT)
  - **Vt. Stat. Ann. tit. 32, chapter 225 (sections 9201-9281)**
    -- separate **Vermont Meals and Rooms Tax** at 9% on
    prepared food / hotel rooms; NOT a general sales tax and out
    of scope for this engine
  - **Vt. Stat. Ann. tit. 32, section 9242** -- separate 6%
    Sugar-Sweetened Beverage tax (added by Act 18 of 2018) on
    certain soft drinks; NOT a general sales tax and out of
    scope
  - **24 V.S.A. section 138** -- **Local Option Sales Tax**
    enabling statute (1% fixed local rate; municipalities adopt
    by charter + referendum)
  - **Act 60 of 1997** (Equal Educational Opportunity Act) --
    original enactment of the local-option framework
  - **Act 68 of 2003** -- raised the state rate from 5% to 6%
    effective 2003-10-01 and expanded the local-option framework
  - **Act 174 of 2014 (H. 528)** -- brought specified digital
    products into the sales-tax base effective 2015-07-01
  - **VT Department of Taxes Reg. 1.9741(45)** -- regulatory
    guidance on the clothing exemption (includes the exclusions
    list: accessories, sport/recreational equipment, protective
    equipment for non-everyday use)
  - **VT Department of Taxes Reg. 1.9701(7)** -- regulatory
    guidance distinguishing taxable prewritten ("canned")
    software from non-taxable custom software developed for a
    specific customer
- *Sources for rate/taxability:*
  - **Vermont Department of Taxes** main site
    (https://tax.vermont.gov/), retrieved 2026-05-03 -- confirms
    6% state rate
  - **Vermont Department of Taxes "Sales and Use Tax" landing
    page** (https://tax.vermont.gov/business/sales-and-use-tax),
    retrieved 2026-05-03 -- confirms 6% state rate, taxability
    overview, no sales-tax holiday
  - **Vermont Department of Taxes "Local Option Tax" page**
    (https://tax.vermont.gov/business/lot), retrieved
    2026-05-03 -- confirms exactly-1% local rate under 24 V.S.A.
    section 138; ~17 municipalities opted in
  - **Vermont Department of Taxes "Municipalities with a Local
    Option Tax" page**
    (https://tax.vermont.gov/business/lot/municipalities),
    retrieved 2026-05-03 -- authoritative list of LOST-adopted
    municipalities (Burlington, South Burlington, Williston,
    Brattleboro, Stowe, Manchester, Killington, Dover,
    Wilmington, Montpelier, etc.)
  - **Vermont Department of Taxes "Meals and Rooms Tax" page**
    (https://tax.vermont.gov/business/meals-and-rooms-tax),
    retrieved 2026-05-03 -- confirms separate 9% rate on
    prepared food / hotel rooms
  - **Vermont General Assembly statutes** -- Title 32 chapter
    233 (sections 9701, 9741, 9771); Title 24 section 138 -- via
    https://legislature.vermont.gov/statutes/title/32 and
    https://legislature.vermont.gov/statutes/title/24,
    cross-referenced 2026-05-03
  - **Sales Tax Institute holiday compendium**
    (https://www.salestaxinstitute.com/resources/sales-tax-holidays),
    retrieved 2026-05-03 -- secondary cross-reference confirming
    Vermont has no sales-tax holiday in any year
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms Vermont is a full SST member
  - **Sovos summary** (specs/research/sovos-state-summary.md
    line 123) -- secondary cross-check of the 6% state rate;
    primary source is the VT Department of Taxes
- **Module file:** `src/opensalestax/states/vermont.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-vt branch)
- *Notes:*
  - **Broad clothing exemption (32 V.S.A. 9741(45)) is the
    headline VT-specific finding.** VT joins PA, MA, MN, NJ in
    the small set of states that broadly exempt clothing year-
    round with no per-item dollar cap. Encoded as
    ``is_taxable=False`` with the statutory citation in the
    rule's notes; a defensive regression test
    (`test_vermont_clothing_is_exempt_year_round_no_threshold`)
    catches a future maintainer who accidentally re-enables
    clothing tax.
  - **Local Option Sales Tax is fixed at exactly 1%.** Unlike
    Colorado (home-rule cities can pick rates 1%-7.5%) or Texas
    (cities can adopt 0.25%-2% in 0.125% increments), VT's local
    option is binary: a town is either at 0% or at exactly 1%.
    This makes the deferred-locals posture unusually clean --
    when LOST loading lands, every adopting municipality has
    EXACTLY the same rate, so the per-municipality rows in the
    SST file have a single distinct rate value.
  - **Combined rate is always exactly 6.0% or exactly 7.0%.**
    No fractional combined rates exist in Vermont. Useful
    invariant for future test fixtures.
  - **Prepared food principally taxes under the 9% Meals and
    Rooms Tax, not the 6% sales tax.** The general sales-tax
    matrix marks prepared food as taxable at 6% as a
    conservative default; integrators selling restaurant meals
    in Vermont should apply the 9% Meals and Rooms Tax instead.
    Documented prominently in the module docstring and in the
    `prepared_food` rule's notes.
  - **No sales-tax holiday in any year.** Verified explicitly;
    a regression test
    (`test_vermont_holidays_for_all_years_returns_empty`)
    catches a future contributor who mistakenly extrapolates
    from a neighboring SST state's August holiday framework.
  - **Digital goods became taxable on 2015-07-01** per H. 528
    of the 2014 Legislative Session (Act 174 of 2014). The
    defined term "specified digital products" lives at
    32 V.S.A. section 9701(31)(B). Custom software developed
    for a specific customer is NOT taxable per Reg. 1.9701(7);
    prewritten software (delivered by any means) IS taxable
    as TPP.
  - **No 2026Q2 VT SST file** has been captured to confirm the
    jurisdiction-type codes empirically; the inherited default
    mapping is taken from MN/WI 2026Q2 captures. The next
    maintainer should validate against a VT SST quarterly capture
    and override ``jurisdiction_types`` on the subclass if any
    code differs.
  - **Separate 6% Sugar-Sweetened Beverage tax** under 32
    V.S.A. section 9242 (Act 18 of 2018) on certain soft drinks
    is documented for completeness but outside the general
    sales-tax base modeled by this engine.

## WA -- Washington

- **Statewide rate:** **6.500% effective 1983-07-01** (raised
  from 5.4% to 6.5% by chapter 7, Laws of 1983 1st Ex. Sess.;
  rate codified at RCW section 82.08.020(1). The 6.5% state
  rate has been stable since.)
- **Tax model:** sales tax (SST -- full member; verified
  2026-05-03 against the SST member roster on
  streamlinedsalestax.org). State FIPS: 53.
- **Local jurisdictions:** Cities, counties, transit districts
  (PTBA / RTA / TBD / HCT), public-facility districts (PFDs),
  and various special-purpose districts may impose layered
  local-option sales taxes under RCW chapter 82.14 and related
  authorities:
  - **RCW chapter 82.14** -- master local-option sales /
    use tax chapter (county + city general local-option
    typically 0.5% + optional 0.5% under RCW 82.14.030(1)
    and 82.14.030(2))
  - **RCW chapter 36.57A + RCW 82.14.045** -- public
    transportation benefit areas (PTBAs); voter-approved
    transit sales tax up to 0.9%
  - **RCW 81.104.170 + RCW 82.14.0455** -- regional transit
    authority (RTA) sales tax; Sound Transit (King /
    Pierce / Snohomish RTA) imposes 1.4% under the ST3
    expansion approved 2016-11-08
  - **RCW 82.14.048 / 82.14.0485 / 82.14.0494** -- public
    facility district (PFD) sales tax; voter-approved
    typically 0.1%-0.2% for qualifying capital projects
  - **RCW chapter 36.73 + RCW 82.14.0455** -- transportation
    benefit district (TBD) sales tax; voter-approved up to
    0.2% for transportation projects
  - **RCW 82.14.340 / 82.14.450 / 82.14.460** -- county-level
    voter-approved overlays for criminal justice / mental
    health / chemical dependency programs

  Combined statewide-plus-local general rates therefore range
  from the **6.5% state-only floor** (in unincorporated areas
  of low-tax counties with no special-district overlay) through
  approximately **10.35% in parts of King County / Seattle**
  (the highest combined retail rates in the country alongside
  Chicago, IL and parts of LA County, CA -- verified 2026-05-03
  against the WA Department of Revenue's Local Sales Tax Rate
  Lookup tool). WA is one of only a handful of states (along
  with CO and CA) where a single transaction's combined rate
  can vary by more than 3 percentage points depending purely on
  the buyer's specific street address. As an SST member, WA's
  per-jurisdiction rates flow through the standard SST quarterly
  rate file via the inherited :class:`SstStateModule` parser;
  no manual loader needed.
- **Sales-tax holidays:** **NONE.** Washington has **never**
  enacted a recurring sales-tax holiday. Confirmed 2026-05-03
  against the Washington Department of Revenue's published
  guidance and a search of RCW chapter 82.08 for any periodic
  exemption window. ``holidays_for(year)`` returns the empty
  iterator for every year (mirrors KY, IN, MI, DC, ID, NE, ND,
  NJ, NC, KS). The only periodic exemption-style relief WA has
  implemented was a temporary 2024 manufacturing-input window
  (chapter 419, Laws of 2024) which ran for a limited window in
  2024 only and applied to a narrow set of qualifying
  manufacturing inputs -- NOT a consumer-facing holiday and NOT
  re-encoded as a recurring window.
- **Threshold rules:** none. WA does NOT have a threshold-based
  clothing exemption (contrast with NY's $110-per-item and MA's
  $175-per-item).
- **DOR URL:** **https://dor.wa.gov/** *(retrieved 2026-05-03)*
- **Statutes consulted (RCW Title 82, Chapter 8 -- retail sales
  tax; Chapter 4 -- B&O tax + definitions; Chapter 14 -- local
  option):**
  - RCW section 82.08.020(1) -- imposition of the state retail
    sales tax at 6.5% of the selling price
  - RCW section 82.08.0281 -- exemption for prescription drugs
    (plus insulin and certain related medical items via RCW
    82.08.0283 et seq.)
  - RCW section 82.08.0293 -- exemption for food and food
    ingredients (added by chapter 7, Laws of 1977 1st Ex. Sess.
    -- one of the oldest broad food sales-tax exemptions in
    the country; uses the SST-uniform definition; excludes
    candy, soft drinks, dietary supplements, prepared food,
    and bottled water)
  - RCW section 82.04.050 -- definition of "retail sale"
    (extended in 2009 to include digital products / digital
    codes / digital automated services per chapter 535, Laws
    of 2009)
  - RCW section 82.04.050(6) -- specifically the digital-
    products / digital-codes / digital-automated-services
    extension to the "retail sale" definition
  - RCW section 82.04.192 -- defined terms for digital
    products, digital codes, and digital automated services
    (added by chapter 535, Laws of 2009; SST-uniform
    definitions for the "specified digital products" subset
    plus WA-specific extensions)
  - RCW section 82.04.192(3)(b) -- statutory carve-outs from
    the "digital automated services" definition (data-
    processing services, professional services delivered
    electronically, etc.)
  - RCW chapter 82.04 -- the Business & Occupation (B&O) gross-
    receipts tax (separate from sales tax; OUT OF SCOPE for
    this engine -- see Notes below)
  - RCW section 82.04.250 -- B&O retailing classification
    (0.471%)
  - RCW section 82.04.270 -- B&O wholesaling classification
    (0.484%)
  - RCW section 82.04.240 -- B&O manufacturing classification
    (0.484%)
  - RCW section 82.04.290 -- B&O service & other activities
    classification (1.5% or 1.75% depending on annual gross
    receipts)
  - RCW chapter 82.14 -- local option sales / use tax (master
    local-option chapter)
  - RCW chapter 36.57A -- public transportation benefit areas
    (PTBAs)
  - RCW section 81.104.170 + RCW 82.14.0455 -- regional transit
    authority (RTA) sales tax (Sound Transit ST3 1.4%)
  - RCW chapter 36.73 -- transportation benefit districts
    (TBDs)
  - chapter 7, Laws of 1983 1st Ex. Sess. -- the rate increase
    from 5.4% to 6.5% (the current rate has been stable since)
  - chapter 7, Laws of 1977 1st Ex. Sess. -- the original food
    sales-tax exemption (RCW 82.08.0293)
  - chapter 535, Laws of 2009 (S.S.B. 5295) -- the digital-
    products / digital-codes / digital-automated-services
    extension to the retail sales-tax base; effective
    2009-07-26
  - chapter 419, Laws of 2024 -- the temporary 2024
    manufacturing-input sales tax exemption window (NOT
    re-encoded as a recurring holiday; documented for
    completeness)
- *Sources for rate/taxability:*
  - Washington Department of Revenue -- Sales and Use Tax
    landing page (https://dor.wa.gov/), retrieved 2026-05-03
    -- confirms 6.5% statewide rate, food / prescription-drug
    exemptions, broad digital-services tax base, and the
    layered local-option overlay structure
  - Washington Department of Revenue -- Local Sales Tax Rate
    Lookup tool (https://dor.wa.gov/find-taxes-rates/sales-and-use-tax-rates/local-sales-and-use-tax-rates-by-address),
    retrieved 2026-05-03 -- confirms the ~10.35% combined-rate
    ceiling reached in parts of King County / Seattle and
    documents address-level rate variance
  - Washington Department of Revenue -- Business & Occupation
    Tax landing page (https://dor.wa.gov/taxes-rates/business-occupation-tax),
    retrieved 2026-05-03 -- confirms the B&O is a separate
    seller-side gross-receipts tax (not a transactional sales
    tax) with classification-based rates ranging from 0.471%
    (retailing) to 1.75% (high-revenue services)
  - Washington Department of Revenue -- Digital Products
    sales-tax guidance (https://dor.wa.gov/education/industry-guides/digital-products),
    retrieved 2026-05-03 -- elaborates the digital-products /
    digital-codes / digital-automated-services taxability
    rules including the statutory carve-outs in RCW
    82.04.192(3)(b)
  - Revised Code of Washington (RCW) Titles 82 and 36 via the
    Washington Legislature's online code
    (https://app.leg.wa.gov/rcw/), retrieved 2026-05-03 --
    primary source for every statutory citation above
  - Streamlined Sales Tax member roster
    (https://www.streamlinedsalestax.org/about-us/about-sstgb/member-states),
    cross-checked 2026-05-03 -- confirms Washington is a full
    member
  - SST taxability matrix for Washington (published quarterly
    on streamlinedsalestax.org) -- cross-checked 2026-05-03
    for the food-and-food-ingredients exemption scope, the
    prescription-drug exemption scope, and the digital-products
    treatment
- **Module file:** `src/opensalestax/states/washington.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-wa branch; Phase 7 -- tier-2 to tier-1 promotion)
- *Notes:*
  - **Business & Occupation (B&O) tax is OUT OF SCOPE** per
    RCW chapter 82.04. Washington uniquely (among the ~45
    states with a general retail sales tax) also imposes a
    separate B&O gross-receipts tax on persons engaging in
    business activities within the state. The B&O is a
    SELLER-SIDE tax on the seller's gross business income
    (NOT a buyer-facing transactional sales tax that the
    SELLER COLLECTS FROM THE BUYER), conceptually similar to
    Ohio's CAT or Oregon's CAT. Rate varies by business
    classification (0.471% retailing per RCW 82.04.250; 0.484%
    wholesaling per RCW 82.04.270; 0.484% manufacturing per
    RCW 82.04.240; 1.5%-1.75% service / other per RCW
    82.04.290; assorted specialty rates per RCW 82.04.255 et
    seq.). A seller operating in WA computes its B&O liability
    via the WA DOR's E-File / My DOR system or accounting
    integration -- NOT via OpenSalesTax. Some sellers pass the
    B&O through to buyers as an explicit invoice line item
    (e.g. "B&O surcharge: 0.471% added to invoice"); this is
    a SELLER PRICING CHOICE, not a tax OpenSalesTax should
    compute. An integrator wishing to model B&O surcharges as
    buyer-visible line items must do so as a custom line-item
    type outside this engine.
  - **Wide combined-rate range (~6.5%-10.35%)** is the headline
    integrator-awareness item. The combined retail sales-tax
    rate at any specific WA address is the sum of the 6.5%
    state rate plus every overlapping local-jurisdiction rate
    applicable at that address (cities, counties, PTBAs, RTA
    [Sound Transit ST3], PFDs, TBDs, criminal-justice /
    public-safety overlays, etc.). King County / Seattle reaches
    ~10.35% -- among the highest combined retail sales-tax
    rates in the country alongside Chicago, IL and parts of
    LA County, CA. Integrators must NOT assume a single
    "Seattle area" or "King County" rate; the actual combined
    rate at any given delivery address must come from the SST
    quarterly file (or DOR's address-level rate lookup tool)
    -- the inherited :class:`SstStateModule` parser handles
    this automatically once the SST file is loaded.
  - **Broad digital-services tax base** per RCW 82.04.050(6) +
    RCW 82.04.192 (added by chapter 535, Laws of 2009; S.S.B.
    5295 of the 61st Legislature; effective 2009-07-26).
    Washington has one of the BROADEST digital-product tax
    bases in the country: in addition to the SST-uniform
    "specified digital products" (digital audio works, digital
    audiovisual works, digital books), WA also taxes "digital
    codes" (codes that allow the user to obtain digital
    products) and "digital automated services" (services that
    use one or more software applications to perform a service
    for the customer). The digital-automated-services category
    in particular reaches many cloud / SaaS / streaming
    offerings that other states do NOT reach. Statutory
    carve-outs in RCW 82.04.192(3)(b) exclude certain
    enumerated services (data-processing services, professional
    services delivered electronically, etc.); integrators
    selling DAS-style services should consult RCW
    82.04.192(3)(b) and applicable WA DOR Excise Tax Advisories
    (ETAs) for ambiguous edge cases. The default
    ``digital_goods`` rule is TAXABLE.
  - **No clothing exemption, no threshold, no holiday.** WA
    does NOT join the broad clothing-exemption states (PA, MA,
    MN, NJ, VT) and does NOT have a threshold-based exemption
    (NY $110, MA $175). The taxability rule for the
    ``clothing`` category is TAXABLE year-round at 6.5% plus
    local. The clothing rule's notes explicitly document all
    three negatives so a future maintainer cannot accidentally
    copy from an exempt-clothing state.
  - **No sales-tax holiday history to backfill.** WA has never
    enacted a consumer-facing back-to-school or general-purpose
    sales-tax holiday. The 2024 manufacturing-input window
    (chapter 419, Laws of 2024) was a one-time temporary
    measure for a narrow set of qualifying manufacturing inputs
    and is intentionally NOT re-encoded as a recurring window
    -- doing so would risk a future maintainer extrapolating
    it forward in violation of the "no extrapolation" rule
    applied across all WA-style no-holiday states.
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    WA's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district),
    which should match WA's structure given uniform SST file
    formats observed across other member states. Validating
    against an actual ``WAR<...>.csv`` file is a low-priority
    maintenance task for the next quarterly data-refresh cycle.
  - **Rate has been stable** at 6.5% since 1983-07-01; no
    scheduled rate change for the general rate is currently in
    the legislative pipeline that this research found.

## WV -- West Virginia

- **Statewide rate:** **6.000% effective 2003-01-01** (raised
  from 5% to 6% by H.B. 2007 of the 2002 Second Extraordinary
  Session; codified at W. Va. Code section 11-15-3. The 6%
  state rate has been stable since 2003.)
- **Tax model:** sales tax (consumers sales and service tax);
  SST member -- full member effective October 1, 2005
  (verified 2026-05-03 against the SST member roster on
  streamlinedsalestax.org)
- **Local jurisdictions:** West Virginia does NOT authorize a
  general county sales tax. Local sales-tax authority is
  limited to **municipal home-rule** participants under
  **W. Va. Code section 8-13C** (the Municipal Home Rule
  Pilot Program, made permanent by H.B. 4009 of the 2019
  Regular Session). Participating municipalities may impose
  a municipal sales and service tax of **up to 1.0%**, in
  addition to the 6% state rate. ~50+ municipalities have
  adopted the local 1% (Charleston, Huntington, Morgantown,
  Wheeling, Parkersburg, Beckley, etc.), giving combined
  rates in the **6.0%-7.0%** range. As an SST member, WV's
  per-jurisdiction rates flow through the standard SST
  quarterly file via the inherited
  :class:`SstStateModule` parser.
- **Notable rate exception -- the multi-year grocery phase-out
  culminating in 0% on 2013-07-01 (W. Va. Code section
  11-15-3a):** West Virginia's grocery sales tax was phased
  down step-by-step over seven years and fully eliminated on
  2013-07-01 -- one of the most documented multi-year
  grocery-tax phase-outs in the country. The schedule:

    * Pre-2006: full 6% (the general rate)
    * Effective **2006-01-01: 5%** (H.B. 4346, 2005 Regular
      Session)
    * Effective **2007-07-01: 4%** (H.B. 4067, 2006 Regular
      Session)
    * Effective **2008-07-01: 3%** (H.B. 4006, 2008 Regular
      Session)
    * Effective **2012-01-01: 2%** (S.B. 234, 2011 Regular
      Session)
    * Effective **2012-07-01: 1%** (continuation of the
      same phase-down)
    * Effective **2013-07-01: 0%** -- the final step;
      groceries have been fully exempt at the state level
      ever since.

  Encoded as ``is_taxable=False`` on the ``groceries``
  TaxabilityRule. Items NOT meeting the SST "food and food
  ingredients" definition (candy, soft drinks, dietary
  supplements, prepared food) are NOT covered by the section
  11-15-3a exemption and remain taxable at the general 6%
  rate. Note: municipal home-rule sales taxes (under section
  8-13C) generally also exempt food and food ingredients in
  conformity with the state exemption, though per-municipality
  variation is theoretically possible.
- **Sales-tax holidays:** **ONE annual holiday** under
  **W. Va. Code section 11-15-9o** (enacted by H.B. 2025,
  2021 Regular Session). The holiday runs from 12:00 a.m.
  on the **first Friday in August** through 11:59 p.m. on
  the following **Monday** -- a 4-day window. The holiday is
  multi-scope with FIVE distinct per-item caps:

    * **Clothing and footwear**: $125 or less per item
    * **School supplies**: $50 or less per item
    * **School instructional materials**: $20 or less per item
    * **Sports equipment**: $150 or less per item
    * **Computers / tablets / laptops** for personal use:
      $500 or less per item

  Each scope is encoded as a SEPARATE :class:`HolidayWindow`
  because :attr:`HolidayWindow.max_amount_per_item` is a
  single-value field. **2026 dates: August 7 (Friday) -
  August 10 (Monday), 2026** (first Friday in August 2026
  is August 7).
- **Threshold rules:** the August holiday's per-scope caps
  function as threshold rules during the 4-day window.
  Year-round threshold rules: none.
- **DOR URL:** **https://tax.wv.gov/** *(retrieved
  2026-05-03)*
- **Statutes consulted (W. Va. Code Chapter 11 -- Taxation,
  Article 15 -- Consumers Sales and Service Tax, Article
  15B -- Streamlined Sales and Use Tax Administration, and
  W. Va. Code Chapter 8, Article 13C -- Municipal Home
  Rule):**
  - W. Va. Code section 11-15-3 -- 6% state consumers sales
    and service tax (raised from 5% to 6% by H.B. 2007,
    Second Extraordinary Session 2002, effective
    2003-01-01)
  - W. Va. Code section 11-15-3a -- exemption from the
    state sales tax for food and food ingredients for
    home consumption (the multi-year phase-out
    statute; fully exempt at 0% effective 2013-07-01)
  - W. Va. Code section 11-15-9 -- general exemptions list
  - W. Va. Code section 11-15-9(a)(11) -- exemption for
    drugs, durable medical goods, mobility-enhancing
    equipment, and prosthetic devices dispensed upon
    prescription
  - W. Va. Code section 11-15-9o -- annual sales tax
    holiday (enacted by H.B. 2025, 2021 Regular Session;
    first Friday-Monday of August; 5 scopes with per-item
    caps of $125 / $50 / $20 / $150 / $500)
  - W. Va. Code section 11-15B-2 -- SST conforming
    definitions article (incorporates uniform "specified
    digital products," "food and food ingredients,"
    "prepared food," "drugs sold by prescription," and
    related definitions)
  - W. Va. Code section 8-13C-1 et seq. -- Municipal Home
    Rule program (general framework); section 8-13C-4
    authorizes participating municipalities to impose a
    municipal sales and service tax up to 1.0% in addition
    to the state rate
- *Sources for rate/taxability:*
  - **West Virginia State Tax Department** main page
    (https://tax.wv.gov/), retrieved 2026-05-03 -- confirms
    6% state rate
  - **West Virginia State Tax Department -- Sales and Use
    Tax** publications page
    (https://tax.wv.gov/Business/SalesAndUseTax/Pages/SalesAndUseTax.aspx),
    retrieved 2026-05-03 -- primary source for taxability,
    home-rule local-tax disposition, and prescription-drug
    / grocery exemption mechanics
  - **West Virginia State Tax Department -- Sales Tax
    Holiday** page
    (https://tax.wv.gov/Business/SalesAndUseTax/Pages/SalesTaxHoliday.aspx),
    retrieved 2026-05-03 -- confirms 4-day August holiday
    schedule (first Friday through following Monday) and
    per-scope caps ($125 clothing, $50 school supplies, $20
    instructional materials, $150 sports equipment, $500
    computers/tablets/laptops); 2026 dates are August 7-10
  - **West Virginia Legislature -- W. Va. Code online**
    (https://code.wvlegislature.gov/), retrieved 2026-05-03
    -- primary source for every statutory citation above
    (Chapter 11 Article 15, Article 15B; Chapter 8 Article
    13C)
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms West Virginia is a full SST
    member effective October 1, 2005
  - **Sales Tax Institute holiday compendium**
    (https://www.salestaxinstitute.com/resources/sales-tax-holidays),
    retrieved 2026-05-03 -- secondary cross-reference for
    2026 dates of the August holiday and per-scope caps
    (used as one input among many; primary source is the
    West Virginia State Tax Department)
- **Module file:** `src/opensalestax/states/west_virginia.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-wv branch)
- *Notes:*
  - **The grocery phase-out is the headline historical
    finding.** West Virginia's seven-year, six-step
    elimination of the state grocery sales tax (6% -> 5%
    in 2006, 4% in 2007, 3% in 2008, 2% in early 2012, 1%
    in mid-2012, 0% in mid-2013) is unusually well-
    documented and is encoded in both the module docstring
    and the ``groceries`` TaxabilityRule's ``notes`` field
    so future maintainers do not lose the legislative
    history. A regression test
    (``test_west_virginia_groceries_exempt_with_phase_out_history``)
    asserts the phase-out narrative remains in the rule's
    notes.
  - **The August holiday is multi-scope with five distinct
    per-item caps.** Because :class:`HolidayWindow`'s
    ``max_amount_per_item`` is a single ``Decimal`` value,
    each scope is encoded as its own ``HolidayWindow`` --
    the same pattern used by VA, MO, and other multi-scope-
    holiday states. A regression test
    (``test_west_virginia_holiday_per_scope_caps``) asserts
    every cap matches the statute.
  - **No general county sales tax.** West Virginia is one of
    the few SST states that does not authorize a county
    sales tax. All local sales-tax authority is via the
    Municipal Home Rule program under W. Va. Code section
    8-13C; ~50+ municipalities have adopted, but counties
    cannot impose a sales tax.
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    WV's actual rate-file codes were not empirically
    validated at promotion time. The module defaults to the
    canonical MN/WI mapping (45=state, 00=county, 01=city,
    63=district). Validating against an actual WVR<...>.csv
    file is the natural next maintenance task. Note: since
    WV does not authorize a general county sales tax, the
    "00=county" mapping is largely vestigial for WV.
  - **Digital goods / SST conformity.** West Virginia
    adopted the SST uniform digital-products definitions in
    section 11-15B-2 effective 2008. Specified digital
    products and electronically-delivered prewritten
    software are taxable at the general 6% rate, consistent
    with the SST conforming-state norm.

### **WY -- Wyoming** *(Phase 7 final SST promotion)*

- **Statewide rate:** **4.0% effective 1993-07-01** (raised from
  3% to 4% by Senate Enrolled Act 31 of the 1993 Wyoming
  Legislature; in continuous effect since)
- **Tax model:** sales tax (Selective Sales Tax Act of 1937, Wyo.
  Stat. Title 39, Chapter 15, as amended)
- **Local jurisdictions:** counties (general-purpose option up to
  1% under Wyo. Stat. section 39-15-204(a)(i); specific-purpose
  option up to 1% under Wyo. Stat. section 39-15-204(a)(iii));
  combined rates typically 4%-7%
- **Sales-tax holidays:** **NONE** -- WY has NEVER enacted a
  sales-tax holiday of any kind
- **Threshold rules:** none
- **Digital goods:** **NOT TAXABLE** -- the sales-tax base is
  statutorily limited to tangible personal property plus a
  closed list of enumerated services per Wyo. Stat. section
  39-15-103(a)(i); the Wyoming Legislature has NOT extended
  the base to "specified digital products"
- **Phase 7 milestone:** WY is the **FINAL Streamlined Sales Tax
  member promoted from tier 2 to tier 1**. With this module
  shipped, every SST member state has a fully-maintained tier-1
  taxability matrix grounded in primary statutory sources. This
  completes the SST tier-2 -> tier-1 ratchet that started in v0.8
  with AR/GA/IA/IN, continued through v0.9 KS/KY/MI/NE/NV and
  v0.10 NC/ND/NJ/OH/OK, and concludes at v0.11 with WY.
- **DOR URL:** **https://revenue.wyo.gov/** *(retrieved
  2026-05-03)*
- **Statutes consulted:**
  - Wyo. Stat. section 39-15-103(a)(i) -- imposition paragraph;
    base limited to tangible personal property + enumerated
    services
  - Wyo. Stat. section 39-15-104(a) -- 4% state rate
  - Wyo. Stat. section 39-15-105(a)(iii)(C) -- food-for-domestic-
    home-consumption exemption (effective 2006-07-01 per Senate
    Enrolled Act 64 of the 2006 Wyoming Legislature)
  - Wyo. Stat. section 39-15-105(a)(viii) -- prescription drug
    exemption (covers prescription drugs, insulin, hypodermic
    syringes for human use, oxygen and oxygen-delivery
    equipment for human use, prosthetic devices)
  - Wyo. Stat. section 39-15-204(a)(i) -- general-purpose
    county sales tax up to 1% ("5th penny")
  - Wyo. Stat. section 39-15-204(a)(iii) -- specific-purpose
    county sales tax up to 1% ("6th penny")
- *Sources for rate/taxability:*
  - **Wyoming Department of Revenue main page**
    (https://revenue.wyo.gov/), retrieved 2026-05-03 --
    confirms 4% state rate
  - **Wyoming Department of Revenue Excise Tax Division**
    (https://revenue.wyo.gov/divisions/excise-tax),
    retrieved 2026-05-03 -- main excise-tax landing page;
    confirms statewide 4% rate and lists current sales/use/
    lodging tax rate chart for all 23 counties
  - **Wyoming Department of Revenue Excise Tax Publications**
    (https://revenue.wyo.gov/divisions/excise-tax/excise-tax-publications),
    retrieved 2026-05-03 -- "Sales, Use and Lodging Tax Rate
    Chart" published quarterly with current per-county
    combined rates
  - **Wyoming Department of Revenue Sales Tax FAQ**
    (https://revenue.wyo.gov/divisions/excise-tax/sales-tax),
    retrieved 2026-05-03 -- confirms food for domestic home
    consumption exemption (since 2006), prescription drug
    exemption, and the absence of any sales-tax holiday
  - **Streamlined Sales Tax member roster**
    (https://www.streamlinedsalestax.org), cross-checked
    2026-05-03 -- confirms Wyoming is a full SST member
  - **Sovos State-by-State Guide** (specs/research/
    sovos-state-summary.md), cross-referenced 2026-05-03 --
    confirms 4.0% state rate, $100k economic-nexus threshold,
    SST member status; no documented Sovos defects on the
    WY row
- **Module file:** `src/opensalestax/states/wyoming.py`
- **Last verified:** 2026-05-03 by per-state research agent
  (feat/state-wy branch -- Phase 7 final SST promotion)
- *Notes:*
  - **Phase 7 completion is the historic finding.** With WY's
    promotion every SST member state ships a fully-maintained
    tier-1 taxability matrix; the SST tier-2 backlog is
    EMPTY. The remaining tier-2 list (RI, SD, TN, UT, VT, WA,
    WV) consists of 7 SST member states whose default
    taxability matrix is sufficient placeholder until they are
    individually promoted -- though after WY ships, the
    tier-2 framework is no longer the canonical "where SST
    members live before they're promoted" path; future state
    promotions will be driven by individual contributor
    interest rather than batch ratcheting.
  - **Digital goods exemption is the second notable finding.**
    WY is one of a small minority of SST states (joining MI,
    NV, OK) that does NOT tax electronically-delivered digital
    products. The basis is the statutory limitation in section
    39-15-103(a)(i): the sales-tax base is "the sales price
    paid for tangible personal property" plus a closed list of
    enumerated services (lodging, communications, intrastate
    transportation, admissions to places of amusement). The
    Wyoming Legislature has NOT amended the Selective Sales
    Tax Act to adopt the SST "specified digital products"
    definitions. A defensive regression test
    (`test_wyoming_digital_goods_NOT_taxable_with_statutory_citation`)
    catches a future maintainer who copies a digital-goods-
    taxable pattern from a peer SST state.
  - **No-sales-tax-holiday is the third notable finding.**
    Wyoming is one of the cleanest "no holidays in any year"
    states (alongside MI, ID, IN, KY, NE, NJ, ND). A
    defensive regression test
    (`test_wyoming_holidays_for_all_years_returns_empty`)
    locks in this position across 2024-2030. If a future
    Legislature enacts a holiday, that test will fail -- the
    appropriate response is to add the explicit
    HolidayWindow rather than weaken the test.
  - **Grocery exemption is dated.** The
    food-for-domestic-home-consumption exemption is
    relatively recent in WY's tax history -- enacted in 2006
    under Senate Enrolled Act 64 and codified at Wyo. Stat.
    section 39-15-105(a)(iii)(C). Before 2006-07-01, groceries
    were taxable at the full state + local rate. The historical
    cutoff matters if a downstream consumer needs to compute
    historical Wyoming sales tax for any pre-2006 transaction
    audit (the engine's TaxabilityRule.effective_from defaults
    to 1900-01-01 in v1, which over-grants the exemption for
    pre-2006 dates -- a v0.6+ improvement candidate but not
    blocking for current-year calculations).
  - **SST jurisdiction-type code mapping is an ASSUMPTION**:
    WY's actual rate-file codes were not empirically validated
    at promotion time. The module defaults to the canonical
    MN/WI mapping (45=state, 00=county, 01=city, 63=district).
    Validating against an actual WYR<...>.csv file is the
    natural next maintenance task.
  - **Local-option overlay is voter-driven.** Per-county rates
    in WY shift over time as voters approve / sunset 5th-penny
    and 6th-penny options. The SST quarterly file is the
    authoritative source; ad-hoc rate updates between
    quarterly files (rare in practice but possible) would
    require an out-of-band data refresh.

### ME -- Maine

- **Statewide rate:** **5.500% effective 2013-10-01** (raised from
  5.0% by PL 2013, c. 368, Part M; the original sunset date of
  2015-06-30 was eliminated and the 5.5% rate made permanent by
  PL 2015, c. 267, Part OOOO)
- **Tax model:** sales tax (NOT SST -- verified 2026-05-03 against
  the SST membership list at streamlinedsalestax.org; Maine is
  noted explicitly as not a Streamlined member state and runs its
  own audit/compliance program through Maine Revenue Services)
- **Local jurisdictions:** **NONE.** Maine levies no general local
  (county or municipal) sales tax. The 5.5% statewide rate is the
  entire combined rate at every Maine address. This puts ME in the
  small "no-local-tax" club alongside Indiana (7.0%), Kentucky
  (6.0%), Michigan (6.0%), and Rhode Island (7.0%).
- **Statutory category-specific higher rates (NOT modeled in v1):**
  - **8% on prepared food** -- Me. Rev. Stat. tit. 36 § 1811(1)
    third paragraph
  - **9% on lodging** (rental of living quarters in hotels,
    rooming houses, tourist/trailer camps) -- § 1811(1) fourth
    paragraph; was 8% from 2013-10-01 through 2015-12-31, raised
    to 9% effective 2016-01-01 by PL 2015, c. 267, Part OOOO
  - **10% on short-term automobile rental** (rentals less than
    one year) -- § 1811(1) fifth paragraph
  - **14% on adult-use cannabis** for sales on or after 2026-01-01
    -- PL 2025, c. 87 § 7; PL 2025, c. 388, Pt. F §§ 1, 5
  - These are **deferred** until the OpenSalesTax engine adds
    category-aware rate application (currently a single rate per
    authority applies to all taxable categories). The
    prepared_food taxability rule is encoded as taxable; the
    engine applies 5.5% rather than 8%, **under-collecting by 2.5
    percentage points** on prepared-food line items until the
    extension lands. Lodging and auto-rental are not in the v1
    baseline category set.
- **Sales-tax holidays:** **NONE.** Maine has no enacted sales-tax
  holiday. Bills to establish a back-to-school holiday have been
  introduced multiple sessions (HP0227 / LD 318 in the 126th
  Legislature; HP0512 / LD 759 in the 127th Legislature) but none
  have passed. Confirmed 2026-05-03 against Maine Revenue Services
  guidance and current statute. The module's ``holidays_for(year)``
  returns an empty iterator for every year, with a regression test
  in ``test_state_maine.py`` that exercises 2024-2030.
- **Threshold rules:** none.
- **DOR URL:** **https://www.maine.gov/revenue/taxes/sales-use-service-provider-tax**
  *(retrieved 2026-05-03)*
- **Statutes consulted (Me. Rev. Stat. tit. 36, Part 3 unless noted):**
  - § 1811(1) -- imposition and rate (5.5% general; 8% prepared
    food; 9% lodging; 10% short-term auto rental; 14% cannabis)
  - § 1752(3-B) -- definition of "grocery staples" (excludes
    alcohol, candy, soft drinks, dietary supplements, prepared
    food, marijuana, and various snack categories)
  - § 1752(8-A) -- definition of "prepared food" (meals served on
    or off premises; food/drinks prepared by retailer ready for
    consumption)
  - § 1752(17) -- definition of "tangible personal property"
    (expressly INCLUDES "any product transferred electronically",
    making digital goods part of the TPP base; digital-products
    inclusion added by PL 2009, c. 211 effective 2010 and broadened
    by subsequent acts)
  - § 1760(3) -- exemption: sales of grocery staples
  - § 1760(5) -- exemption: prescription drugs (medicines for
    human beings sold on a doctor's prescription; cannabis
    expressly excluded from this exemption)
  - PL 2013, c. 368, Part M -- enacted 5.0%-to-5.5% rate increase
    effective 2013-10-01 (originally with 2015-06-30 sunset)
  - PL 2015, c. 267, Part OOOO -- removed sunset, made 5.5% rate
    permanent, raised lodging rate from 8% to 9% effective
    2016-01-01
  - PL 2025, c. 87 § 7 / PL 2025, c. 388, Pt. F §§ 1, 5 -- 14%
    cannabis rate effective 2026-01-01
  - LD 210 of the 132nd Legislature (signed June 2025) --
    expanded the taxable digital-services base effective
    2026-01-01 to include subscription-based streaming/audio/
    ebook/app services that lack a permanent right to use; the
    unified TPP definition in § 1752(17) makes this an expansion
    of the existing 5.5% digital-goods treatment rather than a
    new tax category
- *Sources for rate/taxability:*
  - Maine Legislature statute repository
    (https://legislature.maine.gov/statutes/36/title36sec1811.html)
    retrieved 2026-05-03 -- primary source for § 1811 (current
    rate text and 2025 amendment history)
  - Maine Legislature statute repository
    (https://legislature.maine.gov/statutes/36/title36sec1752.html)
    retrieved 2026-05-03 -- primary source for § 1752 definitions
    (TPP, grocery staples, prepared food)
  - Maine Legislature statute repository
    (https://legislature.maine.gov/statutes/36/title36sec1760.html)
    retrieved 2026-05-03 -- primary source for § 1760 exemptions
    (grocery staples, prescription drugs)
  - Maine Revenue Services, "Sales and Use Tax Rates & Due Dates"
    (https://www.maine.gov/revenue/taxes/sales-use-service-provider-tax/rates-due-dates)
    retrieved 2026-05-03 -- confirmed 5.5% general / 8% prepared
    food / 9% lodging / 10% short-term auto rental, all effective
    10/1/2019 onward
  - Edwards, Faust & Smith, "Maine Sales Tax Rate Changes"
    (https://efscpa.com/maine-sales-tax-rate-changes/) retrieved
    2026-05-03 -- confirmed PL 2013, c. 368, Part M and PL 2015,
    c. 267, Part OOOO history (CPA-firm summary, used as
    cross-reference to primary statutory citations)
  - TaxCloud, "Maine Expands Sales Tax to Digital Services
    (January 1, 2026)"
    (https://taxcloud.com/sales-tax-radar/maine-expands-sales-tax-to-digital-services-2026/)
    retrieved 2026-05-03 -- documented LD 210 of 2025
    subscription-services expansion; cross-checked against the
    bill text via Maine Legislature
  - Streamlined Sales Tax, "Maine"
    (https://www.streamlinedsalestax.org/state-details/maine)
    retrieved 2026-05-03 -- confirmed Maine is NOT a member state
- **Module file:** `src/opensalestax/states/maine.py`
- **Last verified:** 2026-05-03 by per-state agent (Phase 8
  non-SST tier-0 -> tier-1 ratchet)
- *Notes:*
  - Maine is one of the rare "no-local-tax" sales-tax states. The
    combined rate at every ME address equals the state rate
    exactly (5.5%); there is no county-level or municipal-level
    sales tax to add. Integrators querying the rate stack for a
    Maine address will receive a single state-level authority and
    no children. (Some Maine municipalities have proposed
    local-option lodging taxes; these would be a separate hotel/
    short-term-rental tax layer outside the general sales-tax
    regime and are not in scope for v1.)
  - The 8% prepared-food / 9% lodging / 10% auto-rental / 14%
    cannabis statutory rates are NOT applied by the v1 engine
    because the engine does not yet support per-category rate
    application (one rate per authority applies to all taxable
    line items). The prepared_food taxability rule is encoded as
    taxable so that meals are not silently dropped from the tax
    base, but the actual tax applied is 5.5% rather than the
    statutory 8% -- a 2.5-percentage-point under-collection on
    prepared food. The module's docstring AND the prepared_food
    rule's notes call this out explicitly; a regression test
    asserts the notes mention "8%" and "under-collect" so a
    future maintainer cannot accidentally drop the warning. When
    the category-aware-rate engine extension lands, this module
    should emit additional ``RateRow`` instances with
    ``applies_to_categories=("prepared_food",)`` etc.
  - Maine's digital-goods tax base is unusually broad for a
    non-SST state: § 1752(17)'s "any product transferred
    electronically" inclusion (added 2009) plus the LD 210 of
    2025 subscription-services expansion (effective 2026-01-01)
    means the 5.5% rate covers both downloaded-with-permanent-
    right software/media AND subscription streaming/audio/
    ebook/app services. The unified TPP-definition approach
    means the OpenSalesTax module does not need a sub-category
    split between "permanent right" and "subscription" digital
    media (unlike Idaho, where § 63-3616(b) treats them
    differently).
  - The 2009 digital-products inclusion was originally enacted by
    PL 2009, c. 211 (the so-called "Maine iTunes tax" at the
    time); the language has been amended multiple times since,
    most recently by LD 210 of 2025. The current module pins
    ``effective_from`` for the rate row to 2013-10-01 (the date
    of the current 5.5% rate); the digital_goods taxability rule
    inherits the protocol's default ``effective_from=1900-01-01``
    sentinel because the engine resolves taxability rules per
    request date and the relevant 1900 -> present coverage
    matches the current statutory state.
  - Maine has historically considered (but never enacted) a
    back-to-school sales-tax holiday. If a future legislative
    session passes one, this module should be updated to emit
    ``HolidayWindow`` instances from ``holidays_for(year)`` and
    the regression test in ``test_state_maine.py`` should be
    relaxed for the affected years.

### AL -- Alabama

- **Statewide rate:** **4.000% effective 1969-12-08** (raised from
  3.0% to 4.0% by Act 1969-833 effective 1969-12-08; has been
  stable at 4.0% in the general-tangible-personal-property tier
  since)
- **Tax model:** sales tax (NOT SST -- verified 2026-05-03 against
  the SST membership roster on streamlinedsalestax.org; Alabama is
  not on the SST member-state list and runs its own audit /
  compliance program through the Alabama Department of Revenue
  (ALDOR))
- **Local jurisdictions:** **MOST FRAGMENTED IN THE NATION.**
  - **67 counties**, most of which levy their own county sales tax
    (typically 1.0-3.0%); a subset are state-administered (ALDOR
    collects on the county's behalf), the rest are county- or
    third-party-administered (RDS, Avenu, Berman).
  - **~700+ municipalities** (cities and towns), MANY of which
    **self-administer** their own sales tax under Ala. Code
    section 11-51-200 et seq. with their own rates, exemptions,
    and definitions of taxable items. Combined municipal rates of
    4.0-5.5% are common; combined state+county+city rates commonly
    fall in 9-12% and reach 13.5% in some cities (Arab in
    Marshall/Cullman counties has historically been among the
    highest combined rates).
  - **NOT MODELED in v1.** Encoding ~700+ self-administering
    municipalities and 67 counties requires the SubJurisdiction
    Protocol abstraction deferred to v1.0+. Alabama is one of the
    three canonical priority candidates (with CO and LA) for that
    abstraction. The deferral rationale is documented in
    ``specs/decisions/04-colorado-home-rule.md`` (the Colorado
    home-rule precedent for the same self-administering-cities
    pattern) and ``specs/decisions/05-louisiana-parishes.md`` (the
    Louisiana parish precedent for a state with comparable local
    fragmentation).
- **Grocery rate phase-down (state-portion only):**
  - Pre-2023-09-01: 4.0% (full general state rate)
  - 2023-09-01 to 2025-08-31: **3.0%** per HB 479 of 2023 (Act
    2023-554); originally with a conditional further reduction to
    2.0% if Education Trust Fund growth conditions were met
  - **2025-09-01 onward: 2.0%** per HB 386 of 2024 (Act 2024-437)
    which removed the ETF-growth precondition
  - Codified at Ala. Code section 40-23-2(5) (post-2024
    renumbering)
  - Encoded in this module via ``rate_modifier=Decimal("2.000")``
    on the groceries TaxabilityRule (mirrors the AR/KS/OK/NC/MS/MO
    reduced-grocery-rate pattern). The engine has applied
    ``rate_modifier`` since v0.11.1, so the reduced 2.0% state
    rate is correctly applied.
  - **Local sales taxes (county and municipal) still apply at
    FULL local rate** to groceries -- the state phase-down does
    not reduce the local-portion grocery tax. Combined effective
    grocery rates inside Alabama cities therefore commonly remain
    in the 7-9% range despite the reduced state rate.
- **Specific lower state rates (NOT modeled in v1; documented for
  future category-aware-rate engine work):**
  - **Automotive 2.0%** -- Ala. Code section 40-23-2(4)
  - **Manufacturing machinery 1.5%** -- Ala. Code section
    40-23-2(3)
  - **Farm machinery 1.5%** -- Ala. Code section 40-23-37
- **Sales-tax holidays:** **2 annual STATE holidays** (counties /
  cities must opt in by ordinance to extend the exemption to
  their local portion):
  1. **Severe Weather Preparedness Sales Tax Holiday** -- Ala.
     Code section 40-23-210 et seq. Three-day weekend covering
     the **last full weekend of February**. **2026: Friday Feb
     27 - Sunday Mar 1** (Feb 28 is a Saturday; Friday is Feb 27;
     Sunday is March 1). Two scopes:
     - generators with sales price $1,000 or less per item
     - severe-weather-preparedness items with sales price $60 or
       less per item (batteries, flashlights, weather-band radios,
       tarps, plywood, ground anchor systems, gas/diesel fuel
       containers, ice packs, fire extinguishers, smoke / CO
       detectors, first-aid kits, etc.)
  2. **Back-to-School Sales Tax Holiday** -- Ala. Code section
     40-23-211. Three-day weekend covering the **third full
     weekend of July**. **2026: Friday July 17 - Sunday July 19**
     (Fridays in July 2026: 3, 10, 17, 24, 31; third is the
     17th). Four scopes:
     - clothing -- $100 or less per article
     - computers / computer equipment / software -- $750 or less
       per single-purchase transaction
     - school supplies -- $50 or less per item
     - books -- $30 or less per item (noncommercial)
- **Threshold rules:** none beyond the per-item caps in the two
  holidays above.
- **DOR URL:** **https://revenue.alabama.gov/sales-use/**
  *(retrieved 2026-05-03)*
- **Statutes consulted (Ala. Code Title 40, Chapter 23 unless
  noted):**
  - § 40-23-1 -- definitions (including treatment of digital
    products as TPP via ALDOR Administrative Rule 810-6-1-.37)
  - § 40-23-2(1) -- general 4.0% state sales tax rate
  - § 40-23-2(3) -- 1.5% manufacturing machinery rate (not
    modeled)
  - § 40-23-2(4) -- 2.0% automotive rate (not modeled)
  - § 40-23-2(5) -- reduced state-portion grocery rate (post-2024
    renumbering)
  - § 40-23-4(a)(20) -- prescription drug exemption
  - § 40-23-37 -- 1.5% farm machinery rate (not modeled)
  - § 40-23-210 et seq. -- Severe Weather Preparedness Sales Tax
    Holiday (last full February weekend; $1,000 generator cap and
    $60 supplies cap)
  - § 40-23-211 -- Back-to-School Sales Tax Holiday (third full
    July weekend; $100 clothing / $750 computers / $50 supplies /
    $30 books per-item caps)
  - § 11-51-200 et seq. -- municipal sales/use tax authority
    (the home-rule statute under which ~700+ AL cities
    self-administer their local sales tax)
  - HB 479 of 2023 (Act 2023-554) -- reduced state-portion
    grocery rate from 4.0% to 3.0% effective 2023-09-01
  - HB 386 of 2024 (Act 2024-437) -- removed ETF-growth
    precondition; reduced state-portion grocery rate from 3.0% to
    2.0% effective 2025-09-01
  - ALDOR Administrative Rule 810-6-1-.37 -- treatment of
    specified digital products as tangible personal property
- *Sources for rate/taxability:*
  - ALDOR Sales Tax FAQ
    (https://revenue.alabama.gov/sales-use/faq/) retrieved
    2026-05-03 -- primary source for the current 4.0% general
    state rate, the 2.0% reduced grocery rate, and the
    prescription-drug exemption
  - ALDOR Sales Tax Holiday landing page
    (https://revenue.alabama.gov/sales-use/sales-tax-holidays/)
    retrieved 2026-05-03 -- primary source for the SWP and BTS
    holiday dates, scopes, per-item caps, and the local-opt-in
    annual participating-locality list
  - Alabama Legislature statute repository -- primary source for
    Ala. Code Title 40, Chapter 23 sections cited above
  - Streamlined Sales Tax Project member roster
    (https://www.streamlinedsalestax.org) retrieved 2026-05-03 --
    confirmed Alabama is NOT a member state
  - Sales Tax Institute "Alabama Cuts Grocery Tax to 2%" coverage
    (cross-reference; HB 386 of 2024 statutory primary source)
- **Module file:** `src/opensalestax/states/alabama.py`
- **Last verified:** 2026-05-03 by per-state agent (Phase 6 Batch
  C tier-0 -> tier-1 ratchet; AL state-portion only; ~700+
  self-administering home-rule cities and 67 counties deferred
  to SubJurisdiction Protocol abstraction per
  ``specs/decisions/04-colorado-home-rule.md`` and
  ``specs/decisions/05-louisiana-parishes.md``)
- *Notes:*
  - Alabama has the most fragmented local sales-tax landscape in
    the United States. The 4.0% state rate is one of the lowest
    state-level general sales tax rates in the nation (Colorado is
    lower at 2.9%; everyone else with a general sales tax is
    higher) -- a deliberate design choice that pushes the bulk of
    sales-tax revenue down to the county and municipal layers.
    Combined rates inside Alabama localities reach 13.5% in some
    cities, so a v1 caller using the engine for a populated AL
    address will UNDER-COLLECT by 5-9 percentage points. The
    module's general-rule notes and module docstring both call
    this out explicitly; regression tests assert the warning is
    present in both places.
  - The grocery phase-down is one of the more significant recent
    changes in US state sales tax policy: Alabama was historically
    one of only a handful of states still taxing food at the full
    general state rate, and the 2023-09-01 -> 2025-09-01 reduction
    from 4.0% -> 3.0% -> 2.0% halved the state-portion grocery
    burden in two years. The local portions remain at full rate,
    so the household impact is meaningful but not as dramatic as
    the headline state-rate change suggests.
  - Both AL holidays are state-side holidays where counties and
    cities MUST OPT IN by ordinance to extend the exemption to
    their local portion. ALDOR publishes an annual
    participating-locality list each year; this module encodes
    only the state-side scope and documents the local-opt-in
    caveat in every HolidayWindow's notes (verified by a
    regression test that asserts "opt in" appears in every
    notes field for every holiday).
  - Digital goods treatment in Alabama is a moving target across
    multiple legislative sessions and pending ALDOR guidance
    iterations. The module encodes the conservative position
    (taxable at the 4.0% general rate per ALDOR Rule 810-6-1-.37
    and section 40-23-1) and explicitly notes that streaming
    services / SaaS specifically should be re-verified against
    current ALDOR guidance before relying on the digital_goods
    rule for those subscription transactions.
  - When the SubJurisdiction Protocol abstraction lands, AL will
    be a major test case alongside CO and LA. Modelling the
    ALDOR-administered locals (state-collected counties and
    municipalities) is straightforward once the abstraction
    exists; modelling the self-administered home-rule
    municipalities will require per-city data ingestion since
    most home-rule cities publish their rate ordinances directly
    rather than via a centralized feed.

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
