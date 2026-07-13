# Is shipping taxable? The five patterns across US jurisdictions

*A field guide for integrators and contributors. Last verified against
the engine's per-state rules on 2026-07-13 (52 jurisdictions).*

"Do I charge sales tax on the shipping charge?" is one of the most
common — and most confusing — questions in US sales tax. There is no
national answer. Each state decides for itself, and the rules cluster
into a small number of repeating patterns. OpenSalesTax models every
US jurisdiction with exactly one of **five shipping rules**, defined in
[`ShippingRule`](../../src/opensalestax/states/protocol.py). This page
explains what those five patterns mean, which states use each, and how
the `/v1/calculate` API applies them.

> **Scope.** This describes how states tax shipping charges, compiled
> from primary sources (state statutes, Department of Revenue
> regulations, and the Streamlined Sales Tax Agreement's uniform
> definition of "sales price"). It is **not legal or tax advice**, and
> it covers the *state-level* rule only — home-rule cities (notably in
> Colorado) can and do impose their own shipping rules on top. When a
> transaction's stakes are high, confirm against the destination
> state's DOR.

---

## The one concept that unlocks most of the map: "separately stated"

Before the five patterns make sense, you need one idea.

Most states define the taxable base as the **"sales price"** (or "gross
receipts," "purchase price," "selling price" — the wording varies).
The central question for shipping is: *is the delivery charge part of
the sales price, or not?*

Two facts drive the answer in most states:

1. **Is the charge separately stated?** — i.e., shown as its own line
   on the invoice (`Shipping: $12.50`) rather than baked into the item
   price. A charge folded into the item price is almost always taxable,
   because it is indistinguishable from the price of the goods.
2. **Are the goods themselves taxable?** — you generally do not tax
   delivery of a tax-exempt item (e.g., shipping on groceries in a
   state that exempts groceries).

Every one of the five patterns below is a different way of combining
those two facts. In the OpenSalesTax API these map to the
`separately_stated` flag on the request's `shipping` object, plus
whether any line item in the cart is taxable.

---

## The five patterns

| Rule (`ShippingRule`) | Plain-English meaning | # of jurisdictions |
|---|---|---:|
| `NONE` | State has no sales tax, so shipping is never taxed | 5 |
| `ALWAYS_TAXABLE` | Shipping is taxed unconditionally | 1 |
| `CONDITIONAL` | Shipping is taxed **when the items shipped are taxable** | 27 |
| `EXEMPT_IF_SEPARATELY_STATED` | Taxable by default, but **exempt when shown as a separate line** | 19 |
| `MIXED` | State treats "shipping" and "handling" differently | 1 (MD) |

A few things worth internalizing:

- **`CONDITIONAL` is the plurality (27 states).** This is the
  Streamlined Sales Tax Agreement's default: delivery charges are part
  of the "sales price," so they ride along with the taxability of the
  goods. If the cart is taxable, the shipping is taxed; if the cart is
  exempt, the shipping is exempt. Whether the charge is separately
  stated does *not* matter in these states.
- **`EXEMPT_IF_SEPARATELY_STATED` is the second-largest group (19
  states).** Here the separate-line test is the whole game: itemize the
  shipping and it drops out of the taxable base; bundle it into the
  item price and it stays taxable. This is the single most valuable
  lever a merchant has — in these 19 states, *how you format the
  invoice changes the tax*.
- **`ALWAYS_TAXABLE` is Hawaii alone.** Hawaii's General Excise Tax
  (GET) is levied on the business's gross receipts, not on the buyer as
  a sales tax, and gross receipts include everything — including the
  shipping the customer pays.
- **`NONE` is the five "NOMAD" states** — **N**ew Hampshire,
  **O**regon, **M**ontana, **A**laska, **D**elaware — which levy no
  statewide sales tax. (Alaska has *local* sales taxes in some
  boroughs, but no state-level tax; OpenSalesTax models the state
  level as `NONE`.)
- **`MIXED` is Maryland alone** — see [the Maryland
  wrinkle](#the-maryland-wrinkle-shipping-vs-handling) below.

---

## The full per-state matrix

Generated directly from the engine's registered state modules — this
is exactly what the live API applies. Each citation is the primary
source the state module carries in its `ShippingRuleSet.citation`
field. Where a state is a Streamlined Sales Tax member using the
Agreement's uniform default, the citation reads "SST Agreement uniform
definition of 'sales price'."

| State | Rule | Primary source |
|---|---|---|
| AL | `EXEMPT_IF_SEPARATELY_STATED` | Ala. Admin. Code 810-6-1-.84 |
| AK | `NONE` | No statewide sales tax |
| AZ | `EXEMPT_IF_SEPARATELY_STATED` | ARS 42-5061(A)(7) |
| AR | `CONDITIONAL` | SST Agreement uniform "sales price" |
| CA | `EXEMPT_IF_SEPARATELY_STATED` | CA RTC 6011/6012 + Reg. 1628 |
| CO | `EXEMPT_IF_SEPARATELY_STATED` | C.R.S. 39-26-104(1)(a) — **state portion only; home-rule cities apply their own rules** |
| CT | `CONDITIONAL` | Conn. Gen. Stat. 12-407(a)(2) |
| DC | `CONDITIONAL` | DC Code 47-2001(n)(1) |
| DE | `NONE` | No statewide sales tax |
| FL | `EXEMPT_IF_SEPARATELY_STATED` | FL Rule 12A-1.045 |
| GA | `CONDITIONAL` | GA Reg. 560-12-2-.105 |
| HI | `ALWAYS_TAXABLE` | HRS chapter 237 (GET on all gross receipts) |
| ID | `EXEMPT_IF_SEPARATELY_STATED` | IDAPA 35.01.02.045 |
| IL | `EXEMPT_IF_SEPARATELY_STATED` | 35 ILCS 120/3-5 (Use Tax Regulations) |
| IN | `CONDITIONAL` | SST Agreement uniform "sales price" |
| IA | `EXEMPT_IF_SEPARATELY_STATED` | Iowa Code 423.1(48) |
| KS | `EXEMPT_IF_SEPARATELY_STATED` | K.S.A. 79-3603 + EDU-87 |
| KY | `CONDITIONAL` | SST Agreement uniform "sales price" |
| LA | `CONDITIONAL` | LA RS 47:301(13) |
| ME | `EXEMPT_IF_SEPARATELY_STATED` | 36 MRSA 1752(14)(B) |
| MD | `EXEMPT_IF_SEPARATELY_STATED` (+ handling `ALWAYS_TAXABLE`) | COMAR 03.06.01.30 + Tax-General 11-101(l) |
| MA | `EXEMPT_IF_SEPARATELY_STATED` | 830 CMR 64H.6.5 |
| MI | `EXEMPT_IF_SEPARATELY_STATED` | MCL 205.51 / RAB 2015-17 |
| MN | `CONDITIONAL` | MN Stat. 297A.61 subd. 7 |
| MS | `CONDITIONAL` | Miss. Code 27-65-3 |
| MO | `EXEMPT_IF_SEPARATELY_STATED` | MO DOR LR 7820 + 144.025 |
| MT | `NONE` | No statewide sales tax |
| NE | `CONDITIONAL` | SST Agreement uniform "sales price" |
| NV | `EXEMPT_IF_SEPARATELY_STATED` | NRS 372.025 |
| NH | `NONE` | No statewide sales tax |
| NJ | `CONDITIONAL` | SST Agreement uniform "sales price" |
| NM | `CONDITIONAL` | NMSA 7-9-3 (gross receipts tax model) |
| NY | `CONDITIONAL` | NY Tax Bulletin ST-838 |
| NC | `CONDITIONAL` | SST Agreement uniform "sales price" |
| ND | `CONDITIONAL` | SST Agreement uniform "sales price" |
| OH | `CONDITIONAL` | SST Agreement uniform "sales price" |
| OK | `EXEMPT_IF_SEPARATELY_STATED` | 68 O.S. 1352(12) |
| OR | `NONE` | No statewide sales tax |
| PA | `CONDITIONAL` | 61 Pa. Code 32.6(b) |
| RI | `CONDITIONAL` | SST Agreement uniform "sales price" |
| SC | `CONDITIONAL` | SC Code 12-36-90 |
| SD | `CONDITIONAL` | SST Agreement uniform "sales price" |
| TN | `CONDITIONAL` | SST Agreement uniform "sales price" |
| TX | `CONDITIONAL` | TX Tax Code 151.007(a) |
| UT | `EXEMPT_IF_SEPARATELY_STATED` | UCA 59-12-103 |
| VT | `CONDITIONAL` | SST Agreement uniform "sales price" |
| VA | `EXEMPT_IF_SEPARATELY_STATED` | VA Code 58.1-609.5(3) |
| WA | `CONDITIONAL` | SST Agreement uniform "sales price" |
| WV | `CONDITIONAL` | SST Agreement uniform "sales price" |
| WI | `CONDITIONAL` | SST Agreement uniform "sales price" |
| WY | `EXEMPT_IF_SEPARATELY_STATED` | Wyo. Stat. 39-15-101(a)(viii) |
| PR | `CONDITIONAL` | 8 LPRA 32021 (IVU) — *primary-source verification pending* |

**Distribution:** `CONDITIONAL` × 27 · `EXEMPT_IF_SEPARATELY_STATED` ×
19 · `NONE` × 5 · `ALWAYS_TAXABLE` × 1. This exact distribution is
pinned by a CI test
([`test_core_shipping.py`](../../tests/unit/test_core_shipping.py)), so
the table above cannot silently drift from the code.

---

## Common carrier vs. the seller's own truck

Several `EXEMPT_IF_SEPARATELY_STATED` and `CONDITIONAL` states carry a
sub-rule that this page's single-rule-per-state model deliberately
simplifies: delivery in the **seller's own vehicle** is often treated
differently (usually *more* taxable) than delivery by a **common
carrier** (UPS, FedEx, USPS). Alabama and Pennsylvania are clear
examples — Alabama exempts separately stated common-carrier delivery
but always taxes delivery in the seller's vehicle.

OpenSalesTax models the **common-carrier case**, because that is what
virtually all e-commerce uses. If you are a merchant who delivers with
your own fleet, treat the engine's answer as the common-carrier answer
and check your state's own-vehicle rule separately.

---

## The Maryland wrinkle: shipping vs. handling

Maryland is the only `MIXED` state, and it earns the label by drawing a
line most states do not:

- A separately stated **shipping** charge is **exempt**.
- A **handling** charge — or a combined "shipping and handling" charge —
  is **taxable**.

Because the words on the invoice change the tax, Maryland is the one
state where the request needs to say *which kind* of charge it is. The
`/v1/calculate` request carries an `is_handling_charge` boolean on the
`shipping` object:

- `is_handling_charge: false` (the default) → routed through Maryland's
  default rule (`EXEMPT_IF_SEPARATELY_STATED`).
- `is_handling_charge: true` → routed through Maryland's
  `handling_rule` (`ALWAYS_TAXABLE`).

In **every other state**, the `is_handling_charge` flag is accepted but
ignored — those states do not distinguish the two, so a connector can
send the flag safely without special-casing Maryland.

---

## How the API applies all this

Send shipping as a first-class `shipping` object on `/v1/calculate`
(added in v0.59.0). The engine looks up the destination state's rule,
evaluates it against your cart, and returns a parallel `shipping` block:

```jsonc
// POST /v1/calculate
{
  "address": { "zip5": "55401" },            // Minneapolis, MN (CONDITIONAL)
  "line_items": [{ "amount": "100.00", "category": "general" }],
  "shipping": { "amount": "12.50", "separately_stated": true }
}
```

```jsonc
// response (shipping block only)
"shipping": {
  "amount": "12.50",
  "tax_amount": "1.13",                       // MN taxes it: cart is taxable
  "rate_pct": "9.025",
  "taxable_reason": "MN taxes shipping when at least one item is taxable"
}
```

Change the destination ZIP to a `NONE` state (e.g., Oregon `97201`) and
`tax_amount` comes back `0.00` with `taxable_reason: "OR has no state
sales tax"`. Change it to an `EXEMPT_IF_SEPARATELY_STATED` state with
`separately_stated: true` and the shipping drops out of the taxable
base; flip `separately_stated` to `false` and it becomes taxable.

The `taxable_reason` string is a human-readable debug aid for connector
logs and merchant support — it is intentionally *not* a stable
API contract, so don't parse it programmatically.

**Backward compatibility:** callers that predate v0.59.0 and send
shipping as an ordinary `line_items` entry with `category: "shipping"`
still work unchanged. Omit the `shipping` object entirely and the
engine computes no shipping tax, exactly as before.

---

## Further reading

- [`/v1/calculate` API reference](../api.md) — full request/response
  schema, including the `shipping` object.
- [Adding or improving a state module](../state-modules.md) — where a
  state's `shipping_rule_set()` is implemented.
- [`ShippingRule` / `ShippingRuleSet`](../../src/opensalestax/states/protocol.py)
  — the enum and dataclass this page describes.
- [`specs/research/shipping-taxability.md`](../../specs/research/shipping-taxability.md)
  — the original per-state research notes, with the confidence ratings
  and DOR-citation status behind each assignment.
- [`tests/unit/test_core_shipping.py`](../../tests/unit/test_core_shipping.py)
  — the CI test that pins the five-pattern distribution so this table
  cannot drift from the engine.
