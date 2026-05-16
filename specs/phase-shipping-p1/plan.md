# Shipping P1 implementation plan (v0.59.0)

> **Status**: pre-build outline, 2026-05-16. Drafted overnight to
> make tomorrow's build session efficient. **Eric to review and
> adjust order/scope before we start.**
>
> **Driver**: connector-tier captain Ask 3
> (engine-team-requests.md). OpenCart O-3 ticket unblocks.
>
> **Research input**: ``specs/research/shipping-taxability.md``
> (all 50 + DC at H confidence; PR at M).

## Goal

Ship a first-class ``shipping`` field on ``/v1/calculate`` requests
and responses. Engine applies per-state taxability rules and
returns ``shipping.tax_amount``.

Target: one focused session.

## Order of operations

### 1. Protocol additions (~30 min)

**File**: ``src/opensalestax/states/protocol.py``

Add to existing protocol:

```python
class ShippingRule(str, Enum):
    NONE = "none"                  # no state sales tax
    ALWAYS_TAXABLE = "always"      # tax shipping unconditionally
    CONDITIONAL = "conditional"    # tax when items are taxable
    EXEMPT_IF_SEPARATE = "exempt_if_separately_stated"
    MIXED = "mixed"                # state has special rules (MD handling)


@dataclass(frozen=True, slots=True)
class ShippingRuleSet:
    """How a state taxes shipping/delivery charges.

    Default rule applies unless `is_handling_charge` is True
    AND a handling-distinct override is provided.
    """

    default_rule: ShippingRule
    handling_rule: ShippingRule | None = None  # for MD-style states
    citation: str = ""                          # DOR / statute cite
```

Update ``StateModule`` Protocol to add ``shipping_rule_set()``:

```python
class StateModule(Protocol):
    # ... existing methods ...

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return how this state taxes shipping charges."""
```

Default implementation in ``_sst_base.SstStateModule``:
``CONDITIONAL`` (matches 26-state plurality).

### 2. Per-state shipping rule (~2 hours, mostly mechanical)

**Files**: each ``src/opensalestax/states/<state>.py``

For each of the 52 jurisdictions, override ``shipping_rule_set()``
to return the correct rule + citation. Source: ``specs/research/
shipping-taxability.md`` table.

Pattern:

```python
def shipping_rule_set(self) -> ShippingRuleSet:
    return ShippingRuleSet(
        default_rule=ShippingRule.EXEMPT_IF_SEPARATE,
        citation="FL Rule 12A-1.045",
    )
```

For MD, also set ``handling_rule=ShippingRule.ALWAYS_TAXABLE``.

For NOMAD states (AK, DE, MT, NH, OR), return
``ShippingRule.NONE``.

Mostly mechanical 52-touches; safe to batch in one commit since
the change is additive (no behavior change until the engine
actually consults the rule).

### 3. Request/response schema (~30 min)

**File**: ``src/opensalestax/api/v1/schemas.py``

```python
class ShippingInput(BaseModel):
    """Shipping component of a /v1/calculate request."""

    amount: Decimal = Field(ge=0, examples=["12.50"])
    separately_stated: bool = Field(
        default=True,
        description=(
            "True if shipping is shown as a separate line on the "
            "invoice (default for e-commerce). Relevant in states "
            "where shipping is exempt only when separately stated "
            "(IL, MA, CA, MO, VA, etc. -- see ShippingRule).",
        ),
    )
    is_handling_charge: bool = Field(
        default=False,
        description=(
            "True if this charge is a handling fee rather than "
            "pure shipping. Relevant in states (MD) that "
            "distinguish."
        ),
    )
    method: str | None = Field(
        default=None,
        examples=["ups_ground", "usps_priority", None],
        description="Carrier / method label, optional. Analytics only.",
    )


class ShippingOutput(BaseModel):
    """Shipping component of a /v1/calculate response."""

    amount: Decimal
    tax_amount: Decimal
    rate_pct: Decimal
    taxable_reason: str | None = Field(
        default=None,
        description=(
            "Debug aid explaining why shipping was/wasn't taxed. "
            "Optional and non-stable; do not present to merchants."
        ),
    )
```

Add ``shipping: ShippingInput | None`` to ``CalculateRequest``.
Add ``shipping: ShippingOutput | None`` to ``CalculateResponse``.

### 4. Engine wiring (~1-2 hours)

**File**: ``src/opensalestax/core/calculate.py``

After the line-items loop, before returning:

```python
shipping_output: ShippingOutput | None = None
if body.shipping is not None:
    shipping_output = await _calculate_shipping_tax(
        session=session,
        shipping_input=body.shipping,
        authorities=authorities,
        line_items=line_items,
        state_abbrev=state_abbrev,
    )
```

Helper:

```python
async def _calculate_shipping_tax(
    session: AsyncSession,
    shipping_input: ShippingInput,
    authorities: list[TaxAuthority],
    line_items: list[LineItem],
    state_abbrev: str | None,
) -> ShippingOutput:
    """Apply the state's shipping rule and return ShippingOutput."""
    state_module = STATES.get(state_abbrev)
    if state_module is None:
        return ShippingOutput(...)  # safe default

    rule_set = state_module.shipping_rule_set()
    rule = (
        rule_set.handling_rule
        if shipping_input.is_handling_charge and rule_set.handling_rule
        else rule_set.default_rule
    )

    is_taxable = _is_shipping_taxable(rule, shipping_input, line_items)
    if not is_taxable:
        return ShippingOutput(
            amount=shipping_input.amount,
            tax_amount=Decimal("0"),
            rate_pct=Decimal("0"),
            taxable_reason=_reason_text(rule, is_taxable=False),
        )

    combined_rate = combined_rate_pct(resolved_rates)
    return ShippingOutput(
        amount=shipping_input.amount,
        tax_amount=quantize_to_dollars(shipping_input.amount * combined_rate / 100),
        rate_pct=combined_rate,
        taxable_reason=_reason_text(rule, is_taxable=True),
    )
```

Decision: does shipping inherit the line-item authorities' combined
rate (state + county + city + districts)? **Yes, default to that.**
Per NY ST-838 / MN delivery guidance, district-level shipping
follows the same combined rate. Document the assumption.

### 5. Capabilities flag flip (~5 min)

**File**: ``src/opensalestax/api/v1/capabilities.py``

```python
"shipping_first_class": True,  # iter-1XX: shipped in v0.59.0
```

### 6. Tests (~1 hour)

**File**: ``tests/unit/test_core_shipping.py`` (new)

For each ShippingRule pattern, one unit test:

- ``test_shipping_none_returns_zero_for_no_tax_state``
- ``test_shipping_always_taxable_in_hawaii``
- ``test_shipping_conditional_when_items_taxable_in_mn``
- ``test_shipping_conditional_zero_when_items_exempt_in_mn``
- ``test_shipping_exempt_if_separately_stated_default_true_in_il``
- ``test_shipping_exempt_taxable_when_not_separately_stated``
- ``test_shipping_mixed_md_handling_taxable``

**File**: ``tests/integration/test_api.py``

Add 2-3 integration tests through /v1/calculate:

- Existing line items + shipping, returns shipping section
- Empty cart + shipping only, returns shipping section
- Shipping in NONE state (OR), returns zero tax

### 7. Pin + release (~30 min)

- Update ``tests/integration/test_sst_dor_validation.py`` with 3-5
  spot-check entries exercising shipping
- Cut v0.59.0 via /release skill

## Total estimated time

| Step | Time |
|---|---|
| Protocol additions | 30 min |
| Per-state shipping rules | 2 hours |
| Schema | 30 min |
| Engine wiring | 1-2 hours |
| Capabilities flip | 5 min |
| Tests | 1 hour |
| Pin + release | 30 min |
| **Total** | **~5-6 hours** |

## Risk / decisions Eric should pre-decide

1. **District-rate inheritance**: shipping uses the same combined
   rate as products. Confirm default.
2. **Handling charge for non-MD states**: if ``is_handling_charge``
   is true in a non-MD state, do we honor it (treat as taxable
   when shipping isn't), or ignore it? Recommend: **ignore for v1;
   only MD has the distinction**. Document.
3. **Shipping with no line items**: ``/v1/calculate`` with only
   shipping (e.g. a postage-purchase scenario)? Engine should
   accept and return shipping tax based on the destination state's
   rule. ``CONDITIONAL`` returns 0 since no items are taxable.
4. **Backward compat with `category: "shipping"`**: a line item with
   category="shipping" continues to work today (falls through to
   default taxability). With first-class field, do we (a) warn
   users to migrate, (b) silently both work, or (c) deprecate the
   category in v0.6x? Recommend: **(b) both work in v0.59.0; flag
   deprecation in v0.6x**.

## What NOT to do in P1 (deferred to P2/P3/P4 per captain ask)

- ``separately_stated`` is in the schema but the calc treats it
  always-True for ``EXEMPT_IF_SEPARATE`` states. P2 honors it.
  Actually -- let's just honor it in P1. The connector cost is
  zero and the engine cost is one ``if`` statement. Update plan.
- Handling distinction: only MD honors it. P1 ships MD honoring.
- ``method`` field: stored only, no behavior. P1 accepts and
  echoes back.
- ``taxable_reason``: P1 returns simple template strings; P2 makes
  them more informative.

## What we're explicitly NOT doing in v0.59.0

- ``category: shipping`` line-item convention: NOT deprecated.
  Stays as a non-blocking warning later.
- Multi-shipment arrays: NOT in P1. Single shipping object only.
  Captain confirmed this is fine for v1.
- Vendor-allocated shipping: out of scope (Ask 2 deferred).

---

**Reminder**: capabilities endpoint already shipped in iter-197.
When v0.59.0 deploys, we flip ``shipping_first_class: True`` in
the capabilities manifest and connectors can feature-detect.
