# Decision 06: Additional tax types beyond general sales/use

**Status:** Roadmap (open) -- recorded 2026-05-04 from a user request.

## Context

Through v0.27, OpenSalesTax exclusively models **general retail
sales/use tax** (the everyday "ring up at the register" tax). Eric was
asked by an external party whether the API would also handle these
**transactional taxes that retailers sometimes collect alongside
general sales tax**:

- **Admissions tax** -- ticket sales for events / movie theaters /
  amusement parks. Often a city/county tax piggybacking on the venue
  location (e.g. Atlanta admissions, Chicago amusement tax).
- **Entertainment tax** -- typically synonymous with admissions, but
  some jurisdictions distinguish (e.g. live performance vs cinema vs
  spectator sport).
- **Liquor tax** -- excise tax on beer / wine / spirits. Frequently
  a state-level rate plus optional county / city add-ons. Often
  applied at the wholesale tier rather than retail; retail
  implications include the higher posted shelf price.
- **Lodging / hotel-occupancy tax** -- short-term rental + hotel
  taxes. Almost universally a state base + local add-on. Materially
  large in tourism-heavy jurisdictions (Las Vegas room tax can
  reach 13.38%; NYC occupancy 14.75% + $3.50/night). Affects:
  hotels, Airbnb, VRBO, B&Bs.
- **Restaurant / prepared-food tax** -- a meals tax in some states
  (MA's 6.25% meals tax, VA Restaurant Sales Tax in many counties,
  city-level restaurant taxes in Chicago / New Orleans / etc.).
  Usually an additional rate ON TOP OF the general sales tax for
  the same transaction.

These are all transactional taxes that a POS system or ecommerce
platform might need to compute alongside the general sales tax,
depending on what's being sold and where.

## What changes if we add them

Each of the 5 tax types is a separate calculation pipeline:

1. **Different rate publication source.** The same state DOR usually
   publishes them in a separate document from the general sales tax
   table. We'd add per-type loaders mirroring the existing pattern.
2. **Different jurisdiction stacks.** A meals tax may apply only
   inside Chicago city limits even when general sales tax is also
   levied county-wide. Boundary tables are independent.
3. **Different taxability rules.** A POS system needs to know:
   "this line item is a hotel night -> apply lodging tax stack;
   this line item is a movie ticket -> admissions stack; this line
   item is a beer -> liquor stack PLUS general sales tax."
4. **Different `category` values in the API.** The existing
   `category` field on a line item (`"general"`, `"clothing"`,
   `"groceries"`, `"prescription_drugs"`, `"prepared_food"`,
   `"digital_goods"`) would extend with `"admissions"`, `"lodging"`,
   `"liquor"`, `"restaurant_meal"`. The engine would route each
   line to the right tax stack based on category.

## Architectural impact

The good news: the existing schema generalizes to handle these
without major changes.

- **`tax_authorities`** already supports `authority_type` for
  state/county/city/district. Add new authority sub-classifications
  via a new column or a parallel table for tax-type tagging
  (e.g. `applies_to_tax_type = 'general' | 'lodging' | ...`).
- **`rates`** already has `applies_to_categories: list[str]`.
  Extending this list to include `'lodging'`, `'admissions'`,
  etc. is straightforward.
- **State modules** would gain new methods: `parse_lodging_rates`,
  `parse_admissions_rates`, `parse_meals_rates`, etc. -- mirroring
  the existing `parse_rates` shape.
- **API** would accept the new categories transparently. No
  breaking change; clients that don't send these categories see no
  difference.

The harder parts:

- **Data sourcing**. State DORs publish lodging rates ad-hoc; some
  jurisdictions have aggregated CSVs, others only PDF rate
  schedules per county. Sourcing one tax type per state is roughly
  the same work as sourcing the general sales tax was.
- **Effective dates and seasonality**. Some lodging taxes have
  seasonal rates or short-term-rental-specific rates that don't
  apply to traditional hotels. The current effective_from / to
  shape handles seasonal but the per-line-item nuance (is this a
  hotel or an Airbnb?) requires API extensions.
- **Liquor specifically** is mostly a wholesaler tax in many
  states. POS systems usually don't compute liquor tax at retail
  ring -- it's already baked into the shelf price. We may decide
  liquor is **out of scope** for v1 of this initiative and only
  add admissions/entertainment/lodging/restaurant.

## Recommended sequencing

1. **Hold for v0.30+.** Get general sales tax to a polished state
   first (more states, friendly names everywhere, the data-restore
   UX, web demo) before forking into multi-tax-type territory.
2. **Start with lodging tax** when we do start. It's the highest-
   demand tax type after general sales (every hotel / Airbnb
   needs it), has the cleanest published data per state, and the
   seasonal/STR nuance can be deferred to a v2 of lodging support.
3. **Restaurant/meals tax second.** Chicago / Boston / many VA
   counties -- material for any food-service platform.
4. **Admissions/entertainment third.** Smaller market (event
   ticketing, movie theaters), narrower set of jurisdictions.
5. **Liquor last (or never).** Wholesale-tier complexity makes
   this a separate product dimension; defer until there's pull
   from a real consumer.

## Decision

We will **not implement these tax types in v0.x** (the current
"sales tax MVP" track). They are recorded here as the canonical
roadmap and will be revisited once general sales tax coverage
reaches a polished state across all 52 jurisdictions.

When we do start, lodging is the v0.30 candidate. The architectural
shape outlined above (`category` extension + per-type RateRow
fields) is the working assumption -- subject to revision when we
actually start implementing.

## References

- User request flagged 2026-05-04 in /loop iter 10. Eric:
  "additional tax types ... admissions, entertainment, liquor,
  lodging, and restaurant taxes? Maybe those could be added to a
  future roadmap or started as soon as you have a detailed pass on
  what we have now?"
