# Specialty tax types — future-consideration research

> **Status**: research sketch, 2026-05-15. Surfacing the shape /
> complexity of three tax types Eric flagged for future
> consideration alongside the shipping work: **liquor**,
> **lodging**, **firearms**.
>
> **Purpose**: not a build plan; just enough context to size each
> category and decide whether it fits into a v0.6x roadmap, a
> v1.0 SubJurisdiction expansion, or stays out-of-scope.

## TL;DR per category

| Category | Complexity | Roadmap fit | Reason |
|---|---|---|---|
| **Lodging** | Medium | v0.6x candidate | Per-state hotel/transient occupancy tax; ~35 states + many cities. Cleanly bolts on as a new category. |
| **Liquor** | High | v0.7+ candidate | Three-tier system (state ABC + federal excise + local). Per-state rates AND product-class differentiation (beer/wine/spirits). |
| **Firearms** | High (politically charged) | v1.0+ or out-of-scope | Federal excise (TTB) + state-specific add-ons (WA's I-1639, NJ's permit fees, etc.). Patchwork of rules + handling of background-check fees. |

The pattern that emerges: **lodging is the cleanest fit** for an
OpenSalesTax expansion. The other two pull the engine into adjacent
regulatory regimes (alcohol distribution, firearms commerce) that
have substantially different data sources and audit expectations.

## Lodging tax

### Structure

Most US states levy a separate "hotel occupancy tax" or
"transient lodging tax" on top of (or sometimes instead of)
their general sales tax. Examples:

- **California**: state has no lodging tax; cities/counties levy
  Transient Occupancy Tax (TOT) ranging 8-14%. SF TOT = 14%.
- **New York**: state sales tax PLUS NYC Hotel Room Occupancy Tax
  (6%) PLUS NYC Hotel Unit Fee ($1.50/night) on rooms.
- **Texas**: state hotel tax 6% PLUS city/county hotel tax (up to
  9% combined). Austin = 17%, Houston = 17%.
- **Florida**: state sales tax 6% PLUS county "Tourist Development
  Tax" (up to 6%). Orlando = 12.5%.
- **Hawaii**: state Transient Accommodations Tax (TAT) 10.25% PLUS
  county TAT add-ons. Honolulu = 13.25%.

### Engine implications

- **Category**: cleanly fits as a new line-item `category` value:
  `"lodging"`.
- **Per-state rules**: each state module defines whether `lodging`
  is taxed at the general rate, a different rate, or both.
- **City-level rates**: in many places, lodging tax is **city-
  collected** (TOT) — which means the engine needs city-level data
  beyond what SST provides. Comparable to AL home-rule for general
  sales tax; the SubJurisdiction Protocol work would help here.

### Complexity sources

1. **Hosted SaaS vs. self-host accommodations**: Airbnb/VRBO collect
   different taxes than hotels in many states (e.g., FL: Airbnb
   remits state + county tourist development; hotel does state +
   county + city). Engine may or may not need to distinguish.
2. **Length-of-stay exemptions**: most states exempt long-term
   stays (> 30 nights typical). Engine would need a `stay_nights`
   line-item attribute.
3. **Resort fees, parking, room service**: layered taxability —
   each component may follow different rules.

### Fit assessment

**Doable as a v0.6x category expansion** with reasonable scope:
1. Define `lodging` as a first-class category (like the existing
   `clothing` / `groceries` / `prescription_drugs`).
2. Per-state lodging rate matrix (state portion only; defer city-
   level TOT to SubJurisdiction Protocol work).
3. Add `stay_nights` line-item attribute for long-term exemption.

Punch list to ship lodging v1 (state-portion only): roughly 1-2
weeks of focused work. Connector tier could then surface lodging
as a checkbox/dropdown for relevant verticals (hospitality, vacation
rentals).

## Liquor tax

### Structure

Three concurrent tax regimes apply to alcoholic beverages:

1. **Federal excise tax** (TTB). Per-gallon rates on beer, wine,
   spirits, paid by producer/importer; passed through in wholesale
   price; **not separately collected at retail**. Engine probably
   doesn't model this.

2. **State alcohol beverage control (ABC) tax**. Many states have
   separate per-volume excise taxes (e.g., WA's spirits markup +
   sales tax, ranging 20-30%+). 17 ABC ("control") states have
   state-owned monopoly distribution; rest are "license states."

3. **Local taxes**. Some cities add lodging-like taxes on alcohol
   (e.g., Cleveland's 4.5% Sin Tax on beer/wine, NYC's per-drink
   surcharges in specific districts).

### Per-product class differentiation

Liquor isn't a single category — it splits into:
- **Beer** (low-alcohol, volume-taxed)
- **Wine** (medium-alcohol, volume + ABV-band rates)
- **Spirits** (high-alcohol, separate higher rates)
- **Mixed/RTD** (ready-to-drink premixed; treated variably by state)

Per-state rates differ for each class. WA's spirits tax (20.5%
sales tax + $3.7708/L volume tax) vs WA's beer tax (sales tax only).

### Complexity sources

1. **Volume-based vs. value-based**: most liquor tax is per-volume
   (per-gallon, per-liter), not percentage of price. Engine's
   current decimal-rate model doesn't fit. Would need a new
   `unit_tax` shape (amount per unit-of-volume).

2. **ABV-band rates**: wine over 14% ABV often taxed at higher
   spirits-like rates. Connector would need to send `alcohol_pct`
   per line item.

3. **License vs. control states**: in WA, OR, etc., the state acts
   as the wholesaler and bakes its markup into the shelf price.
   Connector calling our engine may be a retailer that's NOT
   collecting any additional alcohol tax (it's already in COGS).

4. **Three-tier system politics**: 21st-Amendment "tied house"
   rules vary by state. Engine isn't really the right place to
   enforce those, but they affect what gets called "tax" vs
   "markup" in the chain.

### Fit assessment

**Significant scope**: per-volume + per-class rate matrix +
ABV-band logic + per-state license/control distinction. Estimating:

- v0.7+ as an additive feature, not v0.6x
- Probably 3-4 weeks of focused work
- Useful primarily to retail-alcohol verticals (liquor stores,
  bars, restaurants) — niche compared to general retail
- Connector tier would need to gain awareness of alcohol verticals
  (none of the current 13 connectors are alcohol-specialist; they
  all defer to host platform's "is alcohol?" categorization)

**Recommendation**: defer to v0.7+ unless a vertical-specific
connector (e.g., a POS-for-bars integration) lands and creates
demand.

## Firearms tax

### Structure

Firearms taxation is a patchwork of:

1. **Federal excise tax** (TTB, Pittman-Robertson Act). 10% on
   pistols/revolvers, 11% on long guns + ammunition. **Paid by
   manufacturer/importer, passed through at wholesale**. Engine
   doesn't see this at retail.

2. **State-specific add-ons**:
   - **WA I-1639 / I-594**: 9-10 day waiting period + universal
     background checks. The "tax" component is mostly a permit
     fee, not a sales tax.
   - **NJ FID**: Firearms Purchaser ID card + permit-to-purchase
     handgun, with per-application fees.
   - **NY**: pistol permit fee + handgun license fee.
   - **CA**: 11% excise tax on firearms and ammunition (AB 28,
     effective July 2024).
   - **Cook County, IL**: $25 firearm tax + $0.05/round ammunition
     tax (local).
   - **Seattle**: $25 firearm tax + $0.025-0.05/round ammunition.

3. **Background-check fees**: NICS check is federal and free; some
   states layer on additional checks with fees ($10-25 typical).

### Complexity sources

1. **Fees vs. taxes**: permit fees, license fees, background-check
   fees are not really "sales tax" — they're regulatory fees.
   Connectors that calculate "tax" via OST might not want these
   bundled in.

2. **Per-round ammunition**: Cook County / Seattle / King County
   levies are per-round. Engine's decimal-rate model doesn't fit;
   need `unit_tax` (same problem as liquor).

3. **Politically charged**: building firearms tax features will
   draw notice. OST's positioning as a neutral utility ("Apache 2.0,
   pay $0, no opinions") may or may not be where you want to be.

4. **Specialty connector demand**: no current connector is
   firearms-specialist. The vertical's POS systems (NRA's "Cabela's
   Style Database" tooling, FFL-specific systems) are mostly
   proprietary.

### Fit assessment

**Recommendation**: stay out-of-scope for now. Document as
"not on roadmap"; revisit only if (a) a firearms-vertical
connector materializes AND (b) the legal landscape stabilizes
enough that ongoing maintenance burden is bounded.

Alternative path if the demand appears: a thin "regulatory fee"
extension to the response (`fees: [{code, amount, basis}]`) that
returns ammunition-per-round taxes etc. without the engine having
to model them as proper sales tax. Defer the design.

## Cross-cutting infrastructure these would need

All three categories share dependency on **unit-based tax** (per-
gallon / per-night / per-round), which the engine's current
`rate_pct * amount` model doesn't support. A reasonable
investment-of-record is:

1. Add a `BasisType` enum: `PERCENT` (current default) and `UNIT`
   (per-unit-of-measure).
2. Add `unit` and `unit_amount` to `LineItem` for unit-based.
3. Have state modules return `RateRow` instances with `basis` info.
4. Have the engine's quantize logic respect both.

This is **the same plumbing whether we do lodging, liquor, or
firearms**. If we do any of them, this is the foundation.

Estimating ~1 week of engine work for the basis-type infrastructure
alone, before any state-specific data lands.

## Recommendation for the build plan

1. **Ship Ask 3 (shipping) in v0.59.0** — concrete data + engine
   wiring. Already greenlit.
2. **Spec lodging for v0.6x** — clean fit, real connector value
   (hospitality vertical), uses existing percent-rate plumbing
   (mostly; the state-portion-only modeling avoids unit-tax need
   for v1).
3. **Defer liquor to v0.7+** — needs the basis-type infrastructure;
   wait for a retail-alcohol connector to confirm demand.
4. **Stay out of firearms** — political and infrastructure
   complexity outweigh the value; revisit if a firearms-vertical
   connector lands.
