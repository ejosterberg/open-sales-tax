# Captain investigation request: error-envelope migration audit

> **From**: engine team
> **To**: connector-tier captain
> **Date**: 2026-05-16
> **Trigger**: ``engine-team-requests.md`` cross-cutting note re: standardized error envelope
> **Eric to forward**

## Context

In your 2026-05-16 brief (``engine-team-requests.md``) you proposed a
standardized error envelope:

```json
{
  "error": {
    "code": "INVALID_ADDRESS",
    "message": "ZIP code 99999 is not assigned to a US state",
    "field": "address.zip5",
    "documentation_url": "https://docs.opensalestax.../errors#INVALID_ADDRESS"
  }
}
```

Eric is provisionally favorable on shipping this **soon**, while OST
has effectively no third-party consumers other than the connector
portfolio you maintain. His exact phrasing: *"we're moving quickly
and I'm guessing we're the only ones building on the platform now. So
getting this done quickly might be advantageous. But I think we need
our captain process to investigate all known plugins for any possible
errors this would create."*

This document is the engine team's request for that investigation.

## What we need from the captain process

Before the engine team ships the new envelope, please audit **all 13
connectors in the portfolio** and produce a single report that
answers, for each connector:

1. **What's the current error-handling code path?** Where does the
   connector translate an engine HTTP error response into a
   host-platform exception (e.g., ``WC_Tax_Calculation_Exception``,
   ``Magento_Sales_Exception``, etc.)?

2. **Does it parse the response body, or only the HTTP status?**
   - Status-only handlers are SAFE — no change needed; new envelope
     is backward compatible at the HTTP-status layer.
   - Body-parsing handlers are AT RISK — if they extract ``detail``,
     ``message``, or any other key from the current FastAPI default
     error shape, they'll need updating when the envelope changes.

3. **What's the connector's update tolerance?**
   - "Auto-updates from a registry / next install picks up the fix" =
     low coordination cost.
   - "Requires merchant to manually update plugin" = the migration
     needs to roll out in lockstep, or there must be a
     backward-compatible transition.

4. **Are there merchant-facing error messages?** If a connector
   shows the raw engine error to the merchant (e.g., a checkout
   error: "Tax engine returned 'ZIP 99999 not assigned to a US
   state'"), the new envelope's ``message`` field needs to be
   user-readable, not just developer-readable.

## Per-connector questions (specific knowns)

Please confirm or correct these engine-team guesses per connector:

| Connector | Engine team's guess | Captain confirms / corrects |
|---|---|---|
| WooCommerce | PHP exception class catches HTTP non-2xx; reads ``$body['detail']`` for merchant message | |
| Magento | Observer pattern; reads ``Mage_Core_Exception::getMessage()`` from API client response | |
| Vendure | TypeScript service throws ``InternalServerError`` with response.body.detail; surfaces in admin UI | |
| Saleor | Python service; reads ``response.json().get('detail')``; passes through to checkout error | |
| Medusa | TS-based; ``MedusaError`` wrapper; reads ``data.detail`` for message | |
| Bagisto | Laravel; ``\Webkul\OpenSalesTax\Exceptions\EngineException``; reads body verbatim | |
| OpenCart | Single PHP class; reads ``$response['error']['message']`` (already nested!) -- may need check | |
| Invoice Ninja | Laravel; ``OpenSalesTaxClient`` reads HTTP code only | |
| Odoo | Python; ``opensalestax.exception.EngineError``; reads ``response.text`` | |
| ERPNext | Python (Frappe); ``frappe.throw`` with engine's response body | |
| Square | Node.js Lambda; reads ``response.body.detail`` for SQS DLQ message | |
| QuickBooks Online | Node.js; reads ``response.body.detail`` for QBO error mapping | |
| WHMCS | PHP module; reads response body literally; renders to WHMCS admin UI |  |
| PrestaShop | PHP module; reads ``$response['detail']`` for back-office error log | |
| Sylius | PHP; ``OpenSalesTaxException`` wraps response body | |

If any of those guesses are wrong, please correct in the table.

## Migration shapes the engine team is willing to ship

Pick whichever the captain process determines is lowest-risk
across the portfolio:

### Option A — Hard cutover, single version

Engine ships the new envelope in v0.60.0. Every connector that
parses the response body must update simultaneously. The 7-day
transition window is the captain's coordination problem.

- **Pro**: clean, single migration, no transition cruft in the engine
- **Con**: any unmaintained / forked / stale install breaks until
  someone updates the connector
- **Recommended if**: every connector confirms it auto-updates from
  a registry within the transition window

### Option B — Dual-shape envelope for one major

Engine ships v0.60.0 returning BOTH the old shape AND the new shape:

```json
{
  "detail": "ZIP code 99999 is not assigned to a US state",
  "error": {
    "code": "INVALID_ADDRESS",
    "message": "ZIP code 99999 is not assigned to a US state",
    "field": "address.zip5",
    "documentation_url": "..."
  }
}
```

Connectors migrate at their own pace. Engine drops ``detail`` in
v0.70.0 (or whenever the captain confirms 100% portfolio migrated).

- **Pro**: zero risk; nothing breaks
- **Con**: slight response-payload bloat; engine carries dual-shape
  code for one major
- **Recommended if**: any connector is manually-updated or has a
  long install tail (multiple stale versions in the wild)

### Option C — Capability-flag gated

Engine returns the new envelope ONLY when the connector signals
support via a request header:

```
X-OST-Error-Envelope-Version: 2
```

Old connectors get the old shape; new connectors opt in. Engine
drops the legacy path when the capability flag has been required
for a major version cycle.

- **Pro**: cleanest backward compat
- **Con**: only works if every connector can be updated to send
  the header; adds connector code paths
- **Recommended if**: the captain wants a one-time port-once-
  forever model

## The engine team's recommendation

Honestly: **Option B (dual-shape)** unless the captain confirms
the entire portfolio auto-updates. The cost of carrying the dual
shape for one major is small (~3 extra lines per error path);
the cost of breaking a merchant install is unbounded.

Eric's "we're moving quickly" framing is consistent with Option A,
but only if the captain's audit confirms all 13 connectors can
update simultaneously.

## What we'd like back

A markdown report with:

1. The filled-in per-connector table above.
2. A recommendation: A / B / C, with the captain's reasoning.
3. A list of any connector code paths that need updating, by file
   path inside the connector's repo, so the engine team can
   estimate the captain's downstream coordination work.
4. Any merchant-facing impact (admin UI strings that would change,
   error messages displayed at checkout, etc.).

We're not in a rush — Eric wants this thought through. Forward
when ready and the engine team will sequence the envelope work
behind the v0.59.0 shipping release.

## What the engine team is doing in parallel

- Shipping first-class (Ask 3): in progress for v0.59.0.
- Capabilities endpoint (your cross-cutting note): shipped in
  v0.59.0 as part of this same release. Connectors can call
  ``GET /v1/capabilities`` to feature-detect.
- Transactions (Ask 1): decided OUT-OF-SCOPE; see
  ``specs/decisions/06-calculation-only-positioning.md``.
- Per-vendor (Ask 2): decided OUT-OF-SCOPE; B-9 can be closed.

Engine team's hope: by the time you finish this investigation
and reply, we'll be ready to ship the error-envelope migration
in v0.60.0 (with your recommended shape).

---

**Engine-side contact**: Eric (forward replies through him).
**Captain-side**: per usual portfolio cadence.
