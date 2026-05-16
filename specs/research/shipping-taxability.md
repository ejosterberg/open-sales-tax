# Shipping taxability by US jurisdiction

> **Status**: research draft, 2026-05-15. Compiled from TaxJar's
> nationwide summary + practitioner-knowledge cross-check. Each
> state-level rule needs a primary-source DOR citation before we
> ship engine logic; this file is the working draft.
>
> **Driver**: connector-tier captain Ask 3 (engine-team-requests.md).
> OpenCart O-3 ticket blocked on first-class shipping field.
>
> **Scope**: Phase 1 — pick a taxability pattern per state, model in
> the engine, expose via new `shipping` field in `/v1/calculate`.

## Five rule categories

The 52 US sales-tax jurisdictions cluster into 6 patterns:

| Code | Pattern | States |
|---|---|---|
| `NONE` | No state sales tax → no shipping tax | 5 |
| `ALWAYS` | Tax shipping regardless | 1 |
| `CONDITIONAL` | Tax shipping when items are taxable | 26 |
| `EXEMPT_IF_SEPARATE` | Default taxable; exempt if separately stated | 19 |
| `MIXED` | State has special rules (handling distinction, etc.) | 1 (MD) |
| `TBD` | Needs verification | -- |

Per the TaxJar source, the dominant pattern is `CONDITIONAL` (26
states) followed by `EXEMPT_IF_SEPARATE` (19 states). Only HI
collects tax on shipping unconditionally. The 5 NOMAD states (NH,
OR, MT, AK, DE) have no state sales tax to apply.

## Per-state matrix

Confidence column: **H**igh = TaxJar + practitioner cross-check
agree; **M**edium = TaxJar source only; **L**ow = needs primary
DOR verification before shipping code goes live.

| State | Rule | Confidence | Notes / DOR cite needed |
|---|---|---|---|
| AL | EXEMPT_IF_SEPARATE | M | TaxJar list |
| AK | NONE | H | No state sales tax |
| AZ | EXEMPT_IF_SEPARATE | M | TaxJar list |
| AR | CONDITIONAL | M | TaxJar list |
| CA | EXEMPT_IF_SEPARATE | H | Direct DOR confirm: must be (a) common carrier, (b) separately itemized, (c) not exceed actual cost |
| CO | EXEMPT_IF_SEPARATE | M | Plus home-rule cities each have own rule (Denver taxes) |
| CT | CONDITIONAL | M | TaxJar list |
| DE | NONE | H | No state sales tax |
| DC | CONDITIONAL | M | TaxJar list |
| FL | EXEMPT_IF_SEPARATE | M | Plus county surtax follows. FL DOR Rule 12A-1.045 |
| GA | CONDITIONAL | M | TaxJar list |
| HI | ALWAYS | H | Hawaii's GET applies to all gross receipts including shipping |
| ID | EXEMPT_IF_SEPARATE | M | TaxJar list |
| IL | EXEMPT_IF_SEPARATE | H | IL DOR ST-04 (separately stated rule); also "shipping is non-taxable IF customer can buy product without shipping" complication |
| IN | CONDITIONAL | M | TaxJar list |
| IA | EXEMPT_IF_SEPARATE | M | TaxJar list |
| KS | EXEMPT_IF_SEPARATE | M | TaxJar list |
| KY | CONDITIONAL | M | TaxJar list |
| LA | CONDITIONAL | M | Plus parish complexity (LA has known coverage gap; see core/coverage.py) |
| ME | EXEMPT_IF_SEPARATE | M | TaxJar list |
| MD | MIXED | H | MD distinguishes "shipping" (exempt) from "handling" (taxable) and "shipping and handling combined" (taxable). Needs `is_handling_charge` field per captain Ask 3 |
| MA | EXEMPT_IF_SEPARATE | M | TaxJar list |
| MI | EXEMPT_IF_SEPARATE | M | TaxJar list |
| MN | CONDITIONAL | H | MN Stat 297A.61 subd 7 — delivery charges are part of "sales price" when item is taxable |
| MS | CONDITIONAL | M | TaxJar list |
| MO | EXEMPT_IF_SEPARATE | H | MO DOR — separately-stated and elected-by-purchaser is the test |
| MT | NONE | H | No state sales tax |
| NE | CONDITIONAL | M | TaxJar list |
| NV | EXEMPT_IF_SEPARATE | M | TaxJar list |
| NH | NONE | H | No state sales tax |
| NJ | CONDITIONAL | M | TaxJar list |
| NM | CONDITIONAL | M | TaxJar list. NM uses GRT (Gross Receipts Tax); delivery is part of GR |
| NY | CONDITIONAL | H | NY Tax Bulletin ST-838 — delivery charges are part of taxable receipt when shipping taxable item |
| NC | CONDITIONAL | M | TaxJar list |
| ND | CONDITIONAL | M | TaxJar list |
| OH | CONDITIONAL | M | TaxJar list |
| OK | EXEMPT_IF_SEPARATE | M | TaxJar list |
| OR | NONE | H | No state sales tax |
| PA | CONDITIONAL | M | TaxJar list |
| RI | CONDITIONAL | M | TaxJar list |
| SC | CONDITIONAL | M | TaxJar list |
| SD | CONDITIONAL | M | TaxJar list |
| TN | CONDITIONAL | M | TaxJar list |
| TX | CONDITIONAL | H | TX Tax Code 151.007(a) — delivery charges are part of "sales price" when item taxable |
| UT | EXEMPT_IF_SEPARATE | M | TaxJar list |
| VT | CONDITIONAL | M | TaxJar list |
| VA | EXEMPT_IF_SEPARATE | H | VA Code 58.1-609.5(3) — separately stated transportation charges are exempt |
| WA | CONDITIONAL | M | TaxJar list |
| WV | CONDITIONAL | M | TaxJar list |
| WI | CONDITIONAL | M | TaxJar list |
| WY | EXEMPT_IF_SEPARATE | M | TaxJar list |
| PR | TBD | L | Puerto Rico SUT — needs separate research |

**Counts**: NONE × 5; ALWAYS × 1; CONDITIONAL × 26; EXEMPT_IF_SEPARATE × 19; MIXED × 1; TBD × 1 (PR).

## Proposed engine data model

```python
# src/opensalestax/states/protocol.py  (additions)

class ShippingRule(Enum):
    NONE = "none"                       # no state sales tax
    ALWAYS_TAXABLE = "always"           # tax shipping unconditionally
    CONDITIONAL = "conditional"         # tax when items taxable
    EXEMPT_IF_SEPARATE = "exempt_if_separately_stated"
    MIXED = "mixed"                     # state has special rules (MD handling)


@dataclass(frozen=True, slots=True)
class ShippingRuleSet:
    """How a state taxes shipping/delivery charges.

    The default rule applies unless `is_handling_charge` is True
    AND a handling-distinct override is provided.
    """

    default_rule: ShippingRule
    handling_rule: ShippingRule | None = None  # for MD-style states
    notes: str = ""                            # DOR citation
```

Each state module then exposes a `shipping_rule()` method that returns
its `ShippingRuleSet`. The engine's calculate path:

1. Get the destination state's `ShippingRuleSet`.
2. Determine whether ANY line item is taxable in this state.
3. Apply the rule:
   - `NONE`: shipping_tax = 0
   - `ALWAYS_TAXABLE`: shipping_tax = shipping_amount * combined_rate
   - `CONDITIONAL`: shipping_tax = shipping_amount * combined_rate IF any item taxable, else 0
   - `EXEMPT_IF_SEPARATE`: if `shipping.separately_stated` (defaults True), shipping_tax = 0; else taxable
   - `MIXED` (MD): if `shipping.is_handling_charge` then taxable; else exempt

4. Return shipping section in response with `taxable_reason` debug string.

## Open questions for the implementation phase

1. **California**: CA's actual test is multi-factor (common carrier + separately itemized + actual cost). Simplifying to `EXEMPT_IF_SEPARATE` ignores the (c) "not exceed actual cost" criterion. Connector can't know actual cost. Acceptable simplification or do we need a separate `delivery_method` field?

2. **Illinois**: IL has a complication — even when separately stated, shipping is taxable if the customer is REQUIRED to take delivery (no in-store pickup option). Most e-commerce qualifies as "required delivery." Connector signal needed?

3. **Colorado**: home-rule cities (Denver, Boulder, Colorado Springs, etc.) each have their own shipping rule. Our engine ships only state-level CO; adding a state-level shipping rule is fine but the `coverage_warning` already flags the home-rule gap. Document that the shipping rule we return for CO is state-only.

4. **Hawaii GET**: HI's General Excise Tax is technically on the seller, not the buyer. We've been modeling it as a sales tax for consistency. Same treatment for shipping?

5. **District-level rules**: NY MCTD, MN Hennepin, etc. — do these districts get added to shipping the same way they get added to sales? Default assumption: yes (shipping inherits the same combined rate as products). Need to verify against NY ST-838 and MN's delivery-charge guidance.

## Primary-source TODOs before shipping P1 ships

States flagged `M` confidence above should get a primary-DOR-cite
in this doc before P1 production-ships. Priority order by traffic:

1. CA, NY, TX, FL, IL, GA, NC, OH (top-8 by population)
2. PA, MI, NJ, VA, WA, AZ, MA, TN
3. The rest as time permits

CA, NY, TX, IL, MN, MO, VA, MD, HI already have H-confidence
practitioner cross-checks. The traffic-weighted "must verify
before P1 ship" is therefore: FL, GA, NC, OH, PA, MI, NJ, WA, AZ,
MA, TN (11 states).
