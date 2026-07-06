# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""State-level coverage-gap warnings surfaced in API responses.

A handful of US states have local-tax structures the engine
cannot yet fully model. When a ``/v1/rates`` or ``/v1/calculate``
query lands in one of these states, the response now carries a
``coverage_warning`` string explaining why the returned rate may
be incomplete. This is preferable to silently returning a
state-only rate that a casual user might believe is the full
combined rate.

The states listed here are the ones whose docstrings (or
``specs/decisions/0*.md``) explicitly call out the gap:

- **CO** (Colorado) -- ~70 home-rule cities self-administer their
  own sales tax under Article XX of the Colorado Constitution.
  Engine ships only the 2.9% state portion. Denver, Boulder,
  Colorado Springs etc. all return state-only.
- **LA** (Louisiana) -- per-parish sales tax (4.45% state +
  parish 0-7%). Parishes administer their own collection in
  many cases. Engine ships state portion only pending the
  ``SubJurisdiction`` Protocol work.
- **AL** (Alabama) -- ~700 home-rule cities collect under their
  own ordinances rather than via the state. Engine ships state
  + county portions (per ALDOR) but not the ~700 home-rule city
  overlays.

(HI/Hawaii was removed from this set on 2026-07-06: all four
inhabited counties' GET surcharges are now correctly modeled --
the last open item, the Maui County 0.5% surcharge, was confirmed
in effect since 2024-01-01 and encoded. HI responses no longer
understate the rate, so a coverage warning would be misleading.)

The ``SubJurisdiction`` Protocol extension (planned for v1.0+,
spec'd in ``specs/decisions/04-colorado-home-rule.md`` and
``specs/decisions/05-louisiana-parishes.md``) is the durable
fix. Until then, the warning lets callers know to use a
commercial provider or self-look-up for these states.
"""

from __future__ import annotations

# State abbrev -> warning string. Keep messages factual and short
# enough to render in a UI banner (under ~280 chars).
STATE_COVERAGE_WARNINGS: dict[str, str] = {
    "CO": (
        "Colorado: ~70 home-rule cities (Denver, Boulder, Colorado Springs, "
        "Fort Collins, Aurora, Lakewood, Thornton, Arvada, Pueblo, Greeley, "
        "etc.) self-administer their own sales tax under Article XX of the "
        "Colorado Constitution. This API ships ONLY the 2.9% state-portion "
        "rate; per-city local rates are not modeled. Combined rates inside "
        "a home-rule city are typically 6-10%. Defer to the city's "
        "self-collection portal or a commercial provider for full "
        "compliance. Tracked in specs/decisions/04-colorado-home-rule.md."
    ),
    "LA": (
        "Louisiana: parish sales tax (4.45% state + 0-7% parish, varying by "
        "jurisdiction and tax category) is not yet modeled. This API ships "
        "ONLY the state portion; per-parish rates are deferred pending the "
        "SubJurisdiction Protocol extension. Tracked in "
        "specs/decisions/05-louisiana-parishes.md."
    ),
    "AL": (
        "Alabama: approximately 700 home-rule cities collect sales tax under "
        "their own ordinances rather than via the state. This API ships state "
        "+ county portions per ALDOR but does not model the city overlays. "
        "Combined rates inside a home-rule city are typically 1-5% higher "
        "than what this API returns."
    ),
    # HI removed 2026-07-06: all four inhabited counties' GET surcharges
    # (incl. Maui 0.5% since 2024-01-01) are now correctly modeled.
}


def coverage_warning_for_states(state_abbrevs: list[str]) -> str | None:
    """Return a combined coverage warning if any of ``state_abbrevs`` has one.

    If multiple states from the list have warnings, their messages are
    joined with ``" | "`` -- rare in practice (a single ZIP rarely spans
    multiple warning states), but defensive.
    """
    msgs = [STATE_COVERAGE_WARNINGS[a] for a in state_abbrevs if a in STATE_COVERAGE_WARNINGS]
    if not msgs:
        return None
    return " | ".join(msgs)


__all__ = ["STATE_COVERAGE_WARNINGS", "coverage_warning_for_states"]
