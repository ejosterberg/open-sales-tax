# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tax calculation -- the engine's top-level entry point.

Given a ZIP+4 address and a list of line items, produce a per-line
tax decomposition with jurisdictional detail. Combines:

- :mod:`opensalestax.core.lookup`  -- ZIP -> tax authorities
- :mod:`opensalestax.core.resolve` -- authorities -> active rates
- per-state taxability rules from the database

Currency math: every monetary value is :class:`decimal.Decimal`.
We never use floats for money. Tax amounts round to 4 decimal
places (HALF_UP) -- callers are responsible for any further
rounding when presenting to a customer.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.core.disclaimer import disclaimer
from opensalestax.core.lookup import (
    lookup_jurisdictions_by_zip,
    lookup_jurisdictions_by_zip5_loose,
)
from opensalestax.core.resolve import combined_rate_pct, resolve_rates_for_authorities
from opensalestax.db.models import HolidayPeriod, State, TaxabilityRule
from opensalestax.states.protocol import ShippingRule
from opensalestax.states.registry import get_state_module

# Tax amounts round to 4 dp internally. Display rounding is the
# caller's job.
TAX_QUANTUM = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class LineItem:
    """A single product/service line being taxed."""

    amount: Decimal
    category: str = "general"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"amount must be non-negative, got {self.amount}")


@dataclass(frozen=True, slots=True)
class JurisdictionResult:
    """One authority's contribution to the tax on a single line.

    ``tax`` is the dollar amount this authority contributes to the
    line's tax total. The line's ``tax`` field equals the sum of
    its jurisdictions' ``tax`` values (no rounding drift): the
    engine quantizes per-jurisdiction first, then sums.
    """

    name: str
    type: str
    rate_pct: Decimal
    tax: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class CalculatedLine:
    """The result of taxing one :class:`LineItem`."""

    amount: Decimal
    category: str
    tax: Decimal
    rate_pct: Decimal
    jurisdictions: list[JurisdictionResult] = field(default_factory=list)
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ShippingRequest:
    """Shipping component of a calculation request.

    v0.59.0 first-class shipping (per connector-tier captain Ask 3).
    The engine applies the destination state's `ShippingRule`
    (CONDITIONAL / EXEMPT_IF_SEPARATELY_STATED / ALWAYS_TAXABLE /
    MIXED / NONE) and returns a `ShippingResult` on the calculation.
    """

    amount: Decimal
    separately_stated: bool = True
    is_handling_charge: bool = False
    method: str | None = None

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"shipping amount must be non-negative, got {self.amount}")


@dataclass(frozen=True, slots=True)
class ShippingResult:
    """Computed shipping tax."""

    amount: Decimal
    tax_amount: Decimal
    rate_pct: Decimal
    taxable_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CalculationResult:
    """Top-level result of :func:`calculate_tax`."""

    subtotal: Decimal
    tax_total: Decimal
    lines: list[CalculatedLine]
    disclaimer: str
    data_versions: dict[str, str] = field(default_factory=dict)
    """Map of state abbrev -> active data version label, for traceability."""
    shipping: ShippingResult | None = None
    """Computed shipping tax. None when the request didn't include a `shipping` component."""


async def calculate_tax(
    session: AsyncSession,
    zip5: str,
    line_items: list[LineItem],
    zip4: str | None = None,
    effective_date: dt.date | None = None,
    shipping: ShippingRequest | None = None,
) -> CalculationResult:
    """Tax a list of line items at a given address.

    Returns a :class:`CalculationResult` with per-line decomposition
    and a constitution-§13 disclaimer field. If the ZIP doesn't
    match any known jurisdiction, every line gets ``tax=0`` with a
    ``note`` explaining why -- the call doesn't fail.

    When ``shipping`` is provided, the engine applies the destination
    state's ``ShippingRule`` and returns a parallel ``shipping``
    block on the result. See ``opensalestax.states.protocol.ShippingRule``
    for the five-pattern enumeration and
    ``specs/research/shipping-taxability.md`` for per-state primary
    citations.
    """
    if not line_items and shipping is None:
        return CalculationResult(
            subtotal=Decimal("0"),
            tax_total=Decimal("0"),
            lines=[],
            disclaimer=disclaimer(),
        )

    eff_date = effective_date or dt.date.today()
    # Prefer the strict ZIP+4 lookup when the caller supplies a +4
    # (precise per-+4 boundary match). When no +4 is supplied, fall
    # back to the loose lookup so that authorities only bound at
    # the +4 level (e.g. Minneapolis on ZIP 55417, where the city
    # code lives in type-4 records but no type-z record carries it)
    # still surface in the result. The loose lookup may over-count
    # for ZIPs that genuinely span multiple cities with different
    # rates -- callers wanting per-address precision should pass a
    # ZIP+4. ``DISTINCT`` on TaxAuthority means duplicate boundary
    # rows for the same authority don't double-count.
    if zip4 is not None:
        authorities = await lookup_jurisdictions_by_zip(session, zip5, zip4)
    else:
        authorities = await lookup_jurisdictions_by_zip5_loose(session, zip5)
    state_abbrev = _resolve_state_abbrev(authorities)
    no_jurisdiction_note = _no_jurisdiction_note(zip5, zip4) if not authorities else None

    lines_out: list[CalculatedLine] = []
    subtotal = Decimal("0")
    tax_total = Decimal("0")

    for item in line_items:
        subtotal += item.amount
        line = await _tax_one_line(
            session,
            item,
            authorities,
            state_abbrev,
            eff_date,
            no_jurisdiction_note,
        )
        tax_total += line.tax
        lines_out.append(line)

    shipping_result: ShippingResult | None = None
    if shipping is not None:
        shipping_result = await _compute_shipping_tax(
            session=session,
            shipping=shipping,
            authorities=authorities,
            state_abbrev=state_abbrev,
            lines_out=lines_out,
            eff_date=eff_date,
        )
        if shipping_result is not None:
            tax_total += shipping_result.tax_amount

    return CalculationResult(
        subtotal=subtotal,
        tax_total=tax_total,
        lines=lines_out,
        disclaimer=disclaimer(),
        shipping=shipping_result,
    )


def _resolve_state_abbrev(authorities: list) -> str | None:
    """Pick the state abbreviation from a list of authorities.

    Prefers the state-typed authority; falls back to the first
    authority's state. Returns None if the list is empty.
    """
    if not authorities:
        return None
    for a in authorities:
        if a.authority_type == "state":
            return str(a.state.abbrev)
    return str(authorities[0].state.abbrev)


def _no_jurisdiction_note(zip5: str, zip4: str | None) -> str:
    """Format the explanatory note for ZIPs with no boundaries on file."""
    suffix = f"-{zip4}" if zip4 else ""
    return f"No jurisdictions found for ZIP {zip5}{suffix}; tax assumed zero."


async def _tax_one_line(
    session: AsyncSession,
    item: LineItem,
    authorities: list,
    state_abbrev: str | None,
    eff_date: dt.date,
    no_jurisdiction_note: str | None,
) -> CalculatedLine:
    """Compute the :class:`CalculatedLine` for a single :class:`LineItem`."""
    if not authorities:
        return _zero_line(item, note=no_jurisdiction_note)

    # Holiday check -- if a holiday window covers this date + category +
    # amount, the line is non-taxable for the duration.
    if state_abbrev is not None:
        holiday = await _matching_holiday(
            session, state_abbrev, item.category, item.amount, eff_date
        )
        if holiday is not None:
            return _zero_line(
                item,
                note=f"{holiday.name}: this line falls within a sales-tax holiday in {state_abbrev}.",
            )

    # Taxability check -- a per-category rule may zero out this line
    # OR override the state-level rate (e.g. reduced grocery rates).
    rule: TaxabilityRule | None = None
    if state_abbrev is not None:
        rule = await _taxability_rule(session, state_abbrev, item.category, eff_date)
        if rule is not None and not rule.is_taxable:
            note = rule.notes or f"{item.category} is non-taxable in {state_abbrev}."
            return _zero_line(item, note=note)

    # Threshold check -- a rule may exempt the line outright or limit
    # the taxable basis to the excess over a per-item cap. NY <$110
    # clothing is fully exempt; MA $175 / RI $250 clothing exempt the
    # first N dollars and tax only the excess.
    threshold_note: str | None = None
    taxable_basis = item.amount
    if rule is not None and rule.taxable_threshold_amount is not None:
        outcome = _apply_threshold(rule, item.amount, state_abbrev, item.category)
        if outcome.zero_line:
            return _zero_line(item, note=outcome.note)
        taxable_basis = outcome.taxable_basis
        threshold_note = outcome.note

    resolved = await resolve_rates_for_authorities(session, authorities, eff_date, item.category)

    # Apply rate_modifier if the rule specifies one. The modifier
    # REPLACES the state-level authority's rate for this category;
    # local rates (county/city/district) pass through unchanged.
    # This encodes reduced state grocery rates (IL 1%, MO 1.225%,
    # TN 4%, UT 1.75%, MS 5%, AR 0%, KS 0%, OK 0%, VA 1%, NC 2%, etc.)
    # without per-state engine branches.
    rate_overrides: dict[int, Decimal] = {}
    if rule is not None and rule.rate_modifier is not None:
        for r in resolved:
            if r.authority.authority_type == "state":
                rate_overrides[r.authority.id] = rule.rate_modifier

    # Quantize per-jurisdiction first so the breakdown reconciles
    # exactly with the line total (line.tax == sum(j.tax for j in
    # line.jurisdictions)). Accounting callers depend on this.
    jurisdictions = [
        JurisdictionResult(
            name=r.authority.name,
            type=r.authority.authority_type,
            rate_pct=rate_overrides.get(r.authority.id, r.rate_pct),
            tax=(
                taxable_basis * rate_overrides.get(r.authority.id, r.rate_pct) / Decimal("100")
            ).quantize(TAX_QUANTUM, rounding=ROUND_HALF_UP),
        )
        for r in resolved
    ]
    line_tax = sum((j.tax for j in jurisdictions), Decimal("0"))
    rate_pct = sum((j.rate_pct for j in jurisdictions), Decimal("0"))

    return CalculatedLine(
        amount=item.amount,
        category=item.category,
        tax=line_tax,
        rate_pct=rate_pct,
        jurisdictions=jurisdictions,
        note=threshold_note,
    )


def _zero_line(item: LineItem, note: str | None) -> CalculatedLine:
    """Build a CalculatedLine with zero tax (used for non-taxable + missing-juris cases)."""
    return CalculatedLine(
        amount=item.amount,
        category=item.category,
        tax=Decimal("0"),
        rate_pct=Decimal("0"),
        jurisdictions=[],
        note=note,
    )


async def _compute_shipping_tax(
    session: AsyncSession,
    shipping: ShippingRequest,
    authorities: list,
    state_abbrev: str | None,
    lines_out: list[CalculatedLine],
    eff_date: dt.date,
) -> ShippingResult | None:
    """Apply the destination state's ShippingRule and return a ShippingResult.

    Returns None when the state isn't loaded (engine can't determine
    the rule). The caller treats None as "engine ignored shipping"
    rather than "engine returned zero".

    Decision per `specs/phase-shipping-p1/plan.md`:
    - Shipping inherits the same combined rate as products (state +
      county + city + district).
    - `is_handling_charge=True` is honored only in MD (the only MIXED
      state); ignored elsewhere.
    - `separately_stated=True` (the default) makes
      EXEMPT_IF_SEPARATELY_STATED states return zero;
      `separately_stated=False` makes them taxable.
    - For CONDITIONAL states: taxable iff at least one line is taxable.
    - For NONE states: always zero.
    - For ALWAYS_TAXABLE (HI): always taxable.
    """
    if state_abbrev is None:
        return ShippingResult(
            amount=shipping.amount,
            tax_amount=Decimal("0"),
            rate_pct=Decimal("0"),
            taxable_reason=("No state-level jurisdiction matched the address; shipping not taxed."),
        )

    state_module = get_state_module(state_abbrev)
    if state_module is None:
        return ShippingResult(
            amount=shipping.amount,
            tax_amount=Decimal("0"),
            rate_pct=Decimal("0"),
            taxable_reason=(f"State {state_abbrev} has no engine module; shipping not taxed."),
        )

    rule_set = state_module.shipping_rule_set()
    rule = (
        rule_set.handling_rule
        if (shipping.is_handling_charge and rule_set.handling_rule is not None)
        else rule_set.default_rule
    )

    # Determine taxability.
    if rule == ShippingRule.NONE:
        is_taxable = False
        reason = f"{state_abbrev} has no state-level sales tax."
    elif rule == ShippingRule.ALWAYS_TAXABLE:
        is_taxable = True
        reason = f"{state_abbrev} taxes shipping unconditionally ({rule_set.citation})."
    elif rule == ShippingRule.CONDITIONAL:
        any_line_taxable = any(line.tax > 0 for line in lines_out)
        is_taxable = any_line_taxable
        reason = (
            f"{state_abbrev} taxes shipping when items are taxable ({rule_set.citation})."
            if is_taxable
            else f"{state_abbrev} exempts shipping when no items are taxable ({rule_set.citation})."
        )
    elif rule == ShippingRule.EXEMPT_IF_SEPARATELY_STATED:
        is_taxable = not shipping.separately_stated
        reason = (
            f"{state_abbrev} taxes shipping when not separately stated ({rule_set.citation})."
            if is_taxable
            else f"{state_abbrev} exempts separately-stated shipping ({rule_set.citation})."
        )
    else:
        # MIXED — currently only MD; the handling_rule override is
        # selected above so reaching this branch means the request
        # didn't ask for handling. Treat as taxable per the safer-
        # for-collection default. (assert_never enforces
        # exhaustiveness if ShippingRule grows.)
        assert (
            rule == ShippingRule.MIXED
        ), f"Unhandled ShippingRule variant {rule!r}; add an elif branch."
        is_taxable = True
        reason = (
            f"{state_abbrev} has special shipping rules; treating as taxable "
            f"by default ({rule_set.citation})."
        )

    if not is_taxable:
        return ShippingResult(
            amount=shipping.amount,
            tax_amount=Decimal("0"),
            rate_pct=Decimal("0"),
            taxable_reason=reason,
        )

    # Taxable -- compute using the combined rate from the resolved
    # authorities. Shipping inherits the same combined rate as
    # products (state + county + city + district per NY ST-838 / MN
    # delivery-charge guidance / dominant practitioner pattern).
    resolved = await resolve_rates_for_authorities(session, authorities, eff_date, "general")
    rate_pct = combined_rate_pct(resolved)
    tax_amount = (shipping.amount * rate_pct / Decimal("100")).quantize(
        TAX_QUANTUM, rounding=ROUND_HALF_UP
    )
    return ShippingResult(
        amount=shipping.amount,
        tax_amount=tax_amount,
        rate_pct=rate_pct,
        taxable_reason=reason,
    )


@dataclass(frozen=True, slots=True)
class _ThresholdOutcome:
    """Result of applying a TaxabilityRule's threshold to a line.

    ``zero_line`` -- the line is fully exempt; caller returns a
        :func:`_zero_line`.
    ``taxable_basis`` -- the dollar basis the per-jurisdiction rate
        applies to. Equals the line amount when no exemption applies,
        or ``amount - threshold`` for ``"above_excess"`` semantics.
    ``note`` -- a human-readable explanation that flows onto the
        returned :class:`CalculatedLine`.
    """

    zero_line: bool
    taxable_basis: Decimal
    note: str | None


def _apply_threshold(
    rule: TaxabilityRule,
    amount: Decimal,
    state_abbrev: str | None,
    category: str,
) -> _ThresholdOutcome:
    """Compute the threshold outcome for a line.

    ``below_exempt``: amount < threshold -> zero; otherwise full amount.
    ``above_excess``: amount <= threshold -> zero; otherwise tax (amount - threshold).
    """
    threshold = rule.taxable_threshold_amount
    assert threshold is not None  # caller checks
    state_label = state_abbrev or "this state"
    if rule.threshold_semantic == "below_exempt":
        if amount < threshold:
            note = rule.notes or f"{category} under ${threshold} is exempt in {state_label}."
            return _ThresholdOutcome(zero_line=True, taxable_basis=Decimal("0"), note=note)
        return _ThresholdOutcome(zero_line=False, taxable_basis=amount, note=None)
    if rule.threshold_semantic == "above_excess":
        if amount <= threshold:
            note = rule.notes or f"{category} at or below ${threshold} is exempt in {state_label}."
            return _ThresholdOutcome(zero_line=True, taxable_basis=Decimal("0"), note=note)
        excess = amount - threshold
        note = (
            rule.notes
            or f"{state_label}: first ${threshold} of {category} is exempt; tax applies to ${excess}."
        )
        return _ThresholdOutcome(zero_line=False, taxable_basis=excess, note=note)
    # Unknown semantic -- treat as no threshold (safest default).
    return _ThresholdOutcome(zero_line=False, taxable_basis=amount, note=None)


async def _matching_holiday(
    session: AsyncSession,
    state_abbrev: str,
    item_category: str,
    amount: Decimal,
    effective_date: dt.date,
) -> HolidayPeriod | None:
    """Return the first holiday window covering this state + date + line item.

    A line item is "covered" when:
    1. The holiday's date range includes ``effective_date``,
    2. ``applicable_categories`` is NULL (covers everything) OR
       includes the requested category,
    3. ``max_amount_per_item`` is NULL OR the line amount is at
       or below it.
    """
    candidates = (
        (
            await session.execute(
                select(HolidayPeriod)
                .join(State, State.id == HolidayPeriod.state_id)
                .where(
                    State.abbrev == state_abbrev,
                    HolidayPeriod.starts_on <= effective_date,
                    HolidayPeriod.ends_on >= effective_date,
                )
            )
        )
        .scalars()
        .all()
    )
    for holiday in candidates:
        if holiday.applies_to(item_category, amount):
            return holiday
    return None


async def _taxability_rule(
    session: AsyncSession,
    state_abbrev: str,
    item_category: str,
    effective_date: dt.date,
) -> TaxabilityRule | None:
    """Look up the active taxability rule for a state + category + date."""
    stmt = (
        select(TaxabilityRule)
        .join(State, State.id == TaxabilityRule.state_id)
        .where(
            State.abbrev == state_abbrev,
            TaxabilityRule.item_category == item_category,
            TaxabilityRule.effective_from <= effective_date,
        )
    )
    result = await session.execute(stmt)
    candidates = list(result.scalars().all())

    # Pick the most recently effective rule that hasn't expired.
    winner: TaxabilityRule | None = None
    for rule in candidates:
        if rule.effective_to is not None and rule.effective_to < effective_date:
            continue
        if winner is None or rule.effective_from > winner.effective_from:
            winner = rule
    return winner
