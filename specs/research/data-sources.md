# Research — Data Sources

> What data is available for free, in machine-readable form, that
> OpenSalesTax can consume? Compiled 2026-05-02 from direct fetches
> of the source URLs.

## TL;DR

| Source | Coverage | Format | Update | License | Cost | Acceptable? |
|---|---|---|---|---|---|---|
| **SST Rates** | 24 states | CSV + ZIP | Quarterly | Public | Free | ✅ |
| **SST Boundary** | 24 states | CSV + ZIP | Quarterly | Public | Free | ✅ |
| **SST Taxability Matrix** | 24 states | HTML/PDF (no structured download) | Periodic | Public | Free | ✅ — must scrape |
| **State DOR rate files** | Some non-SST states | CSV/PDF varies | Varies | Public | Free | ✅ — per-state effort |
| **Census TIGER/Line** | All US | Shapefile (GIS) | Annual | Public | Free | ✅ |
| **OpenStreetMap (Nominatim)** | Geocoding | API | Continuous | ODbL | Free | ✅ — self-host required for production |
| **TaxCloud Lookups API** | All US | JSON API | Real-time | Commercial-licensed | Free for SST states; paid otherwise | ❌ — license incompat with §3 |
| **Avalara AvaTax API** | All US | JSON API | Real-time | Commercial | Paid | ❌ |
| **TaxJar SmartCalcs API** | All US | JSON API | Real-time | Commercial | Paid | ❌ |
| **TaxRates.com (Avalara owned)** | US ZIP-level | CSV | Quarterly | "Free for personal use" | Free for non-commercial | ⚠️ — license review needed |

## 1. Streamlined Sales Tax (SST) Rates

**URL:** https://www.streamlinedsalestax.org/ratesandboundry/Rates/

**What it is:** quarterly-published rate files from each of the 24 SST member states.

**Format:**
- 13 states publish CSV directly (Arkansas, Georgia, Indiana, Kentucky,
  Michigan, North Carolina, Ohio, Rhode Island, Tennessee, Wisconsin,
  West Virginia, Wyoming, +1 more depending on quarter)
- 13 states publish ZIP archives containing the rate data (Iowa, Kansas,
  Minnesota, Nebraska, Nevada, New Jersey, North Dakota, Oklahoma, South
  Dakota, Utah, Vermont, Washington — file count varies)

**Naming convention:** `<STATE_ABBREV>R<YEAR>Q<QUARTER><MONTH><DAY>.<ext>`
- Example: `MNR2026Q2APR15.zip` = Minnesota Rates, 2026 Q2, published Apr 15
- Each filename pins to a specific publication date — perfect for
  reproducibility per constitution §6.

**Update cadence:** quarterly (Q1 / Q2 / Q3 / Q4). Files appear ~mid-quarter
ahead of the effective date.

**Access:** public web directory, no authentication, no rate limits
mentioned. Direct HTTP/HTTPS download.

**Schema:** not visible from the directory listing — you must download
and inspect a sample file. The Phase 1 implementation should:
1. Download a representative sample (e.g., MN current quarter)
2. Parse the column structure
3. Document it in `specs/research/sst-file-format.md` (a follow-up doc)
4. Build state parsers against that documented format

**SST publishes a "Format" / "Layout" specification** somewhere on their
site — track it down in Phase 1 before parsing.

**Coverage: 24 states.** Full members:
> AR, GA, IA, IN, KS, KY, MI, MN, NE, NV, NJ, NC, ND, OH, OK, RI, SD,
> UT, VT, WA, WV, WI, WY (23 full members)

> Plus TN as the only associate member.

## 2. Streamlined Sales Tax Boundary Files

**URL:** https://www.streamlinedsalestax.org/ratesandboundry/Boundary/

**What it is:** geographic / jurisdictional boundary data for the same
24 states. Maps ZIP+4 ranges (or higher precision) to the specific
taxing jurisdictions that apply.

**Why this matters:** ZIP codes alone are insufficient for sales-tax
calculation — many ZIPs span multiple taxing jurisdictions (a single
ZIP in Hennepin County might cover Minneapolis city, Bloomington city,
and an unincorporated area, each with different rates). Boundary files
solve this by providing more granular address-to-jurisdiction mapping.

**Format:** mostly ZIP archives (presumably containing geometry files
or detailed address-range tables). 6 states publish CSV directly
(Indiana, Kentucky, Michigan, New Jersey, Rhode Island, West Virginia,
Wyoming).

**Naming:** `<STATE_ABBREV>B<YEAR>Q<QUARTER><MONTH><DAY>.<ext>`
- Example: `MNB2026Q2APR15.zip`

**Update cadence:** quarterly, paired with rates.

**Access:** public, no auth.

**Implementation note:** boundary handling needs PostGIS or equivalent
geometry library. Phase 1 can punt on full address-level resolution
and use ZIP+4 lookup as a stepping stone.

## 3. SST State Taxability Matrix

**URL:** https://www.streamlinedsalestax.org/Shared-Pages/State-taxability-matrix

**What it is:** per-state document specifying which products and services
are taxable, by category (e.g., is clothing taxable in this state? Is
prepared food? Is software-as-a-service?). Two sub-documents:
- **Library of Definitions** — common product definitions from SSUTA
  (Streamlined Sales and Use Tax Agreement) Appendix C
- **Tax Administration Practices** — per-state administrative rules
  with deviation explanations

**Categories covered:** sales tax holidays, product definitions, sales
tax holidays, specific treatment per category.

**Format:** **HTML and PDF only** as of last check — no JSON/CSV/XML
download. Must be scraped or manually transcribed for OpenSalesTax to
consume programmatically.

**Implications:**
- The product-taxability layer (Phase 5 in our roadmap) is more work
  than the rate layer. Each state's matrix needs structured extraction
  → schema → tests.
- Could be an early community-contribution opportunity: ask state
  maintainers to transcribe their state's matrix into our YAML/JSON
  schema.
- One-time per quarter when the matrix updates; not a hot path.

## 4. SST State Detail (per-state info pages)

**URL:** https://www.streamlinedsalestax.org/Shared-Pages/State-Detail

**What it is:** index page with links to each member state's specific
resources, contacts, and tax-rate information. Useful for finding
state DOR endpoints and knowing who to contact for clarifications.

**Implementation note:** the per-state page link structure isn't
predictable from the index alone (one URL we tried 404'd). The Phase 1
implementation should manually map state → resource page URL.

## 5. State Department of Revenue feeds (non-SST)

For the 27 non-member jurisdictions (most importantly: California,
Texas, New York, Florida, Illinois, Pennsylvania), each state's DOR
publishes its own data:

| State | URL (start here) | Format | Notes |
|---|---|---|---|
| **California (CDTFA)** | cdtfa.ca.gov | CSV + lookup tool | High complexity — district taxes |
| **Texas** | comptroller.texas.gov | CSV (city/county lookup) | Origin-based sourcing |
| **New York** | tax.ny.gov | PDF + lookup tool | Many local jurisdictions |
| **Florida** | floridarevenue.com | CSV (DR-15DSS) | Discretionary surtax per county |
| **Illinois** | tax.illinois.gov | CSV (RUT-49) | Statewide + home-rule cities |
| **Pennsylvania** | revenue.pa.gov | Lookup tool | Allegheny / Philadelphia surtaxes |
| **Colorado** | tax.colorado.gov | CSV | Home rule cities self-collect — hardest in US |
| **Alabama** | revenue.alabama.gov | Per-county varies | Self-administered cities |

These are **per-state efforts** and ideal community-contributor
territory. Each needs:
1. URL/file format documentation
2. Parser implementation
3. Test fixtures
4. Update-cadence tracking

Colorado deserves a special call-out: ~70 home-rule cities self-administer
their sales tax, each with its own rules. Solving Colorado well is a
significant undertaking; getting it 80% right is achievable with SST-style
rate files for state + county levels.

## 6. US Census TIGER/Line shapefiles

**URL:** https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html

**What it is:** the authoritative free GIS dataset for US geographic
boundaries — places, counties, ZCTAs (ZIP code tabulation areas),
school districts, etc.

**Use cases for OpenSalesTax:**
- Convert addresses → places → jurisdictions when SST data is sparse
- Validate SST boundary data against Census ground truth
- Provide ZIP boundary polygons for visualization

**Format:** ESRI shapefiles (`.shp`) — universally supported by GIS
libraries.

**Update cadence:** annual.

**License:** US public domain. No restrictions.

**Implementation note:** Census ZCTAs are *approximations* of USPS ZIP
codes (USPS doesn't publish actual ZIP polygons since ZIPs are routes,
not regions). Use ZCTAs for "good enough" ZIP polygons; for production
addressing, prefer USPS-provided ZIP+4 → address lookup.

## 7. OpenStreetMap / Nominatim (geocoding)

For converting addresses into lat/lon coordinates (which then feed
into PostGIS jurisdiction lookups):

**Service:** Nominatim (https://nominatim.org/), self-hostable.

**License:** ODbL — share-alike attribution. Not GPL-incompatible but
some commercial users are wary.

**Implementation note:** the public Nominatim instance has strict rate
limits (1 req/sec) and shouldn't be used in production. Self-host on
the same VM as OpenSalesTax for production deployments.

**Alternative:** caller passes lat/lon in API requests; OpenSalesTax
doesn't geocode. Phase 1 should default to this — geocoding is a
separate concern.

## 8. Commercial APIs (for reference — NOT to be used as data sources)

| Service | Why excluded |
|---|---|
| Avalara AvaTax | Commercial license; closed data; per-call fees |
| TaxJar (Stripe-owned) | Commercial license; per-call fees |
| Vertex | Enterprise; expensive |
| Sovos | Enterprise; expensive |
| TaxCloud | Free for SST states but data license forbids redistribution |
| ZipTax | Subscription |

Useful for **competitive analysis** (see `prior-art.md`) but **NOT
acceptable** as data sources per constitution §3.

A snapshot of Sovos's public state-by-state guide (50 states + DC,
captured 2026-05-02) lives in `sovos-state-summary.md` + the raw
`sovos-state-summary.tsv` for **cross-reference** during
implementation — verifying base rates and economic-nexus
thresholds against an independent source. Same constitutional
constraint applies: do not ingest into the API as a runtime data
source.

## 9. Schema OpenSalesTax should use internally

Drawing from how SST structures its data + how taxes actually work:

```
states              one row per US state (ID, abbrev, name, sst_member, joined_date)
tax_authorities     state DORs, county taxing authorities, city taxing authorities, special districts
rates               (authority_id, effective_from, effective_to, rate_pct, applies_to_categories)
jurisdictions       hierarchical: state ⊃ county ⊃ city ⊃ district ⊃ ...
boundaries          (jurisdiction_id, geometry/polygon OR zip+4_range OR address_range)
data_versions       per-state, per-source (e.g., MN-SST-2026Q2APR15) for reproducibility
taxability_rules    per-(state, item_category) — is this taxable here? With effective dates.
holiday_periods     per-(state, item_category, date_range) — sales-tax-free days
exemption_certs     stored caller-side mostly; we just validate format
```

The exact schema lives in `phase-1-foundation/spec.md`.

## 10. SST publishes test fixtures (gold)

The SST Governing Board publishes **conformance test cases** for its
member states ("if you compute $X for transaction Y, you're correct").
These are the gold standard for verifying our implementation matches
official state expectations.

**Find them in Phase 1.** They live somewhere on streamlinedsalestax.org —
likely under "for technologists" or "for service providers." If we can't
find them, fall back to spot-checking against TaxCloud's public lookup
tool (which is SST-certified).

## Open questions for the implementation phase

1. **What's the exact column schema of an SST rate CSV?** Need to download
   one and document.
2. **What do the boundary ZIP archives contain?** Geometry? Address ranges?
   Both?
3. **Where does SST publish the conformance test fixtures?**
4. **Does any non-SST state publish rates as machine-readable JSON?**
   (Most are CSV or PDF.)
5. **Is Colorado worth tackling in Phase 3?** (Home-rule mess.)

The bootstrap session should track these in a `decisions/` or
`questions/` directory as they get answered.
