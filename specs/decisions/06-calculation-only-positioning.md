# Decision: OpenSalesTax is calculation-only

> **Status**: accepted 2026-05-16 (Eric)
> **Captain ask**: engine-team-requests.md Ask 1 — `POST /v1/transactions`
> **Outcome**: NOT BUILDING. OST is positioned as calc-only.

## The ask

The connector-tier captain proposed a `POST /v1/transactions`
endpoint that would record committed transactions back to the
engine, enabling audit trails, refund handling, differential
reporting, and filing-prep export. Patterned after Avalara / TaxJar
/ Stripe Tax's commit endpoints.

## The decision

**OpenSalesTax stays calculation-only.** No transaction record-back
endpoint in v0.x or v1.x.

## Reasoning

### 1. Authentication / tenancy is a prerequisite, not an afterthought

A record-back endpoint that stores transactions tied to a merchant
identity requires:

- **Strong authentication**: today's API-key auth is per-instance,
  not per-merchant. A multi-merchant deployment can't safely
  attribute records to the right merchant.
- **Multi-tenancy data model**: every transaction record needs a
  merchant_id foreign key, isolation per merchant, query patterns
  that respect those boundaries.
- **Audit log integrity**: tax records have legal weight (IRS
  audit defense). Storing them without integrity guarantees
  (immutable append-only log, signed entries, retention guarantees)
  creates more liability than not storing them at all.

None of these primitives exist in the current engine. Building
them is a multi-quarter project, not a feature addition.

### 2. Calculation-only matches the project's positioning

OST's constitution and README position the project as a **free,
self-hostable, calculation-only API**. Hosted SaaS is named as a
*future* option, but the current product is "drop in via Docker
Compose, run it yourself, no accounts, no logging beyond request
logs."

A record-back endpoint shifts the engine into "store-of-record"
territory, which:

- Conflicts with "no logging beyond request logs"
- Implies 7-year retention (IRS audit defense), which conflicts
  with "self-hostable: your storage, your problem"
- Pushes complexity to merchants who are running tiny self-hosted
  instances and don't want a 7-year-growing database

### 3. Connectors already own this

Every connector in the 13-platform portfolio already writes the
final committed tax to its host platform's database (WooCommerce
orders table, Magento sales_order, Vendure Order entity, etc.).
That's the audit trail. The engine duplicating it adds noise
without adding correctness.

Differential reporting ("quote vs. commit") is genuinely
interesting, but the right place to compute it is the host
platform side (it has both halves natively) or a separate
analytics tool — not the calculation engine.

### 4. Audit defense flows from data versions, not transactions

OST's audit story is "given a calc result from date X, here are
the rate tables (DataVersion) that produced it, and here's the
exact code path." The connector logs the calc result + version
into its host platform. The audit defense is constructed from
those two artifacts.

A record-back endpoint adds a third artifact (engine-side
transaction record) but doesn't strengthen the audit story —
it just creates a third place to keep consistent.

## What this means in practice

For connectors:

- **Keep host-platform tax logging as the system of record.**
  WooCommerce's order meta, Magento's sales_order_tax, Vendure's
  Order.taxLines, etc.
- **Don't plan around a future `POST /v1/transactions` call.**
  It's not coming.
- **The captain can close the ~13 future "record-back" tickets
  as won't-do.**
- **Use the calc response's `data_versions` metadata + connector-
  side log together for audit defense.**

For the engine:

- **Document this in constitution.md and README** so the position
  is unambiguous.
- **Reject feature requests that would require us to become a
  store-of-record** (filing-prep export, differential reporting,
  merchant dashboards). Those belong in adjacent tools, not OST.

## When this might be revisited

If OST ever ships a hosted-SaaS tier (named on the roadmap; not
imminent), the auth/tenancy work for that tier may unlock cheap
transaction records as a side effect. Revisit then, not before.

Concrete preconditions to reopen this decision:

1. Per-merchant authentication shipped (not per-instance API
   keys).
2. Multi-tenant schema in place.
3. A hosted-SaaS deployment offered (so OST has the data
   custodianship that justifies the retention burden).

Until all three are true, calculation-only is the answer.

## What we ARE building

The captain's other asks remain in scope per their separate
direction calls:

- **Ask 2 (per-vendor allocation)**: also deferred, but for
  different reasons (low connector pressure + scope creep).
  Captain marks B-9 as won't-fix.
- **Ask 3 (first-class shipping)**: **green-lit for v0.59.0**.
  Research underway; see specs/research/shipping-taxability.md.
- **Discovery endpoint `GET /v1/capabilities`**: green-lit for
  v0.59.0 alongside shipping. Lets connectors do version-aware
  feature detection without parsing strings.

The captain can plan the connector tier accordingly:

| Captain ticket | Engine answer |
|---|---|
| ~13 future record-back tickets | Won't-do; close as out-of-scope by design |
| B-9 Bagisto Marketplace | Won't-do; close as out-of-scope by design |
| O-3 OpenCart shipping | Wait for v0.59.0; or use `category: shipping` shim today (works) |
| Future Magento Marketplace | Won't-do; same as B-9 |

---

**This decision is a constitution-level posture.** Updating it
requires the same level of consensus as a constitution change.
