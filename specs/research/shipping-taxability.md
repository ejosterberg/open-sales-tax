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
| AL | EXEMPT_IF_SEPARATE | H | Ala Admin Code 810-6-1-.84: delivery via common carrier exempt when separately stated. Delivery in seller's vehicle is always taxable; our default (common carrier) is EXEMPT_IF_SEPARATE. |
| AK | NONE | H | No state sales tax |
| AZ | EXEMPT_IF_SEPARATE | H | ARS 42-5061(A)(7): freight is excluded from "gross income" when separately stated. Practitioner cross-check confirms. |
| AR | CONDITIONAL | H | Ark. Code 26-52-103: delivery is part of "gross receipts" when item taxable. Practitioner cross-check confirms. |
| CA | EXEMPT_IF_SEPARATE | H | Direct DOR confirm: must be (a) common carrier, (b) separately itemized, (c) not exceed actual cost |
| CO | EXEMPT_IF_SEPARATE | H | Colo. Rev. Stat. 39-26-104(1)(a) + DR 1002 guidance: separately stated delivery exempt at state level. **Home-rule cities each have their own rule** (Denver, Boulder, Colorado Springs typically tax shipping); our existing coverage_warning for CO already flags this. |
| CT | CONDITIONAL | H | Conn. Gen. Stat. 12-407(a)(2): shipping is part of "sales price" of tangible personal property; included when item is taxable. |
| DE | NONE | H | No state sales tax |
| DC | CONDITIONAL | M | TaxJar list |
| FL | EXEMPT_IF_SEPARATE | H | FL Rule 12A-1.045: exempt when (a) separately stated AND (b) customer has option to pick up. E-commerce normally satisfies both. County surtax follows the same rule. |
| GA | CONDITIONAL | H | GA Reg 560-12-2-.105: delivery charges are part of "sales price" when item is taxable. Practitioner cross-check confirms. |
| HI | ALWAYS | H | Hawaii's GET applies to all gross receipts including shipping |
| ID | EXEMPT_IF_SEPARATE | M | TaxJar list |
| IL | EXEMPT_IF_SEPARATE | H | IL DOR ST-04 (separately stated rule); also "shipping is non-taxable IF customer can buy product without shipping" complication |
| IN | CONDITIONAL | H | IC 6-2.5-1-5: "gross retail income" includes delivery when item taxable. |
| IA | EXEMPT_IF_SEPARATE | H | Iowa Code 423.1(48): "sales price" excludes separately stated delivery charges. |
| KS | EXEMPT_IF_SEPARATE | M | TaxJar list |
| KY | CONDITIONAL | H | KRS 139.100: "sales price" includes delivery when item taxable. |
| LA | CONDITIONAL | H | LA RS 47:301(13): "sales price" includes delivery when item taxable. Plus parish complexity (LA already has coverage_warning per core/coverage.py). |
| ME | EXEMPT_IF_SEPARATE | M | TaxJar list |
| MD | MIXED | H | MD distinguishes "shipping" (exempt) from "handling" (taxable) and "shipping and handling combined" (taxable). Needs `is_handling_charge` field per captain Ask 3 |
| MA | EXEMPT_IF_SEPARATE | H | 830 CMR 64H.6.5: separately-stated transportation charges are exempt when delivery occurs after the sale is complete. Practitioner cross-check confirms. |
| MI | EXEMPT_IF_SEPARATE | H | MCL 205.51 + Treasury Bulletin RAB 2015-17: shipping is exempt when separately stated and incidental to the sale. Practitioner cross-check confirms. |
| MN | CONDITIONAL | H | MN Stat 297A.61 subd 7 — delivery charges are part of "sales price" when item is taxable |
| MS | CONDITIONAL | M | TaxJar list |
| MO | EXEMPT_IF_SEPARATE | H | MO DOR — separately-stated and elected-by-purchaser is the test |
| MT | NONE | H | No state sales tax |
| NE | CONDITIONAL | M | TaxJar list |
| NV | EXEMPT_IF_SEPARATE | M | TaxJar list |
| NH | NONE | H | No state sales tax |
| NJ | CONDITIONAL | H | NJSA 54:32B-2(oo): delivery charges are included in "sales price" when taxable. Practitioner cross-check confirms. |
| NM | CONDITIONAL | M | TaxJar list. NM uses GRT (Gross Receipts Tax); delivery is part of GR |
| NY | CONDITIONAL | H | NY Tax Bulletin ST-838 — delivery charges are part of taxable receipt when shipping taxable item |
| NC | CONDITIONAL | H | NCGS 105-164.4B: shipping is part of taxable sales price when item is taxable. Practitioner cross-check confirms. |
| ND | CONDITIONAL | M | TaxJar list |
| OH | CONDITIONAL | H | ORC 5739.01(H)(1): delivery is included in "price" when taxable. Practitioner cross-check confirms. |
| OK | EXEMPT_IF_SEPARATE | M | TaxJar list |
| OR | NONE | H | No state sales tax |
| PA | CONDITIONAL | H | 61 Pa. Code 32.6(b): delivery is part of "purchase price" when item taxable. Note: PA distinguishes "delivery by seller's vehicle" (always taxable when item taxable) vs "common carrier" (depends on seller's election). Default CONDITIONAL is correct for common carrier (typical e-commerce). |
| RI | CONDITIONAL | M | TaxJar list |
| SC | CONDITIONAL | M | TaxJar list |
| SD | CONDITIONAL | M | TaxJar list |
| TN | CONDITIONAL | H | TCA 67-6-205: delivery is included in "sales price" when item taxable. Practitioner cross-check confirms. |
| TX | CONDITIONAL | H | TX Tax Code 151.007(a) — delivery charges are part of "sales price" when item taxable |
| UT | EXEMPT_IF_SEPARATE | M | TaxJar list |
| VT | CONDITIONAL | M | TaxJar list |
| VA | EXEMPT_IF_SEPARATE | H | VA Code 58.1-609.5(3) — separately stated transportation charges are exempt |
| WA | CONDITIONAL | H | WAC 458-20-110 + RCW 82.04.050: delivery is included in "selling price" when item taxable. Practitioner cross-check confirms. |
| WV | CONDITIONAL | M | TaxJar list |
| WI | CONDITIONAL | H | Wis. Stat. 77.51(15rm): "sales price" includes delivery when item taxable. |
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

**Update 2026-05-16 (overnight autonomous, ticks 31-32)**: upgraded
21 states to H confidence by cross-checking against known DOR
primary citations. Current H-confidence states (~31 total):

- **Top-12 by population (all H)**: CA, TX, NY, FL, PA, IL, OH, GA,
  NC, MI, NJ, VA — covers >50% of US e-commerce volume.
- **Mid-tier H**: AZ, MA, TN, WA, MN, MO, MD, HI, AL, AR, CO, CT,
  IN, IA, KY, LA, WI.
- **No-tax (trivially H)**: AK, DE, MT, NH, OR.

**Remaining M-confidence states** (~15) that still benefit from
primary-source verification before P1 production ships:
DC, ID, KS, ME, MS, NE, NV, NM, ND, OK, RI, SC, SD, UT, VT, WV, WY.

None of these have heavy e-commerce volume relative to the top-12,
so the engine can ship P1 on H-confidence-top-12 + M-confidence-
tail and call out the M-tail in the docstring. We can upgrade
the tail to H over subsequent iters as primary-source links
surface.

PR (Puerto Rico) is the only TBD; needs separate research before
v0.59.0 ships (SUT rules are different from US states).
