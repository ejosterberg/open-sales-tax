# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pick ONE county for a ZIP that straddles several.

Self-seeded (non-SST) state modules emit at most one county boundary
row per ZIP, but a meaningful minority of ZIPs cross county lines. This
module owns the rule for choosing which county wins, so all 12 modules
share one implementation instead of each re-deriving it.

History
-------
Until 2026-08-01 every module inlined the same tiebreak: "take the
first county in FIPS-sorted order." FIPS numbering encodes nothing
about where a ZIP's addresses are, so the choice was effectively a coin
flip. The 2026-08-01 daily audit measured **617 ZIPs across 7 states**
(AL 172, NY 112, FL 96, SC 93, CA 89, AZ 28, PA 27) where that
arbitrary pick landed on a county whose rate differs from at least one
other candidate. Confirmed wrong case: ZIP 35040 (Calera, AL) bound
Chilton County 3.000% though Calera is in Shelby County 1.000% --
over-collecting the county component by 2.00pp.

TX/VA/MS/NM/HI measured zero affected ZIPs only because their county
rates are currently uniform; they ran the same rule and would have
started returning wrong answers the moment any county diverged.

The rule
--------
1. **A hand-curated city anchor always wins.** If the module knows the
   ZIP belongs to a seeded city, that city's county is authoritative --
   it is a human-verified assertion and outranks any geometry.
2. **Otherwise, land-area majority** per Census ``AREALAND_PART``
   (:data:`opensalestax.data.zip_county_dominant.ZIP_COUNTY_DOMINANT`).
   This is the same rule the cross-state ZCTA dedup already uses to
   pick a ZIP's canonical *state*; here it is extended state -> county.
3. **Only if Census records nothing usable**, fall back to the lowest
   FIPS -- the historical behaviour, kept so the function is total.

Land area is a proxy for "where the addresses are", not a perfect one:
a ZIP whose population clusters in a small dense sliver of county A but
whose acreage is mostly rural county B will still pick B. The Census
relationship file publishes no population-part column, so area is the
best signal available from the primary source. Where that proxy is
known to be wrong for a specific ZIP, add a city anchor (rule 1) rather
than special-casing here.
"""

from __future__ import annotations

from collections.abc import Container, Iterable

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county_dominant import dominant_county

__all__ = ["choose_county_name"]


def choose_county_name(
    state_abbrev: str,
    zip5: str,
    pairs: Iterable[tuple[str, str]],
    rated: Container[str],
    preferred: str | None = None,
) -> str | None:
    """Return the single county name to bind to ``zip5``, or ``None``.

    :param state_abbrev: Two-letter USPS abbreviation, e.g. ``"AL"``.
    :param zip5: The 5-digit ZIP being bound.
    :param pairs: ``(state_abbrev, county_fips)`` tuples the ZIP
        intersects -- i.e. a ``ZIP_COUNTY`` value. Entries for other
        states are ignored.
    :param rated: Membership test for county names the module actually
        has a rate for (typically its ``*_COUNTY_RATE_PCT`` dict).
        Unrated counties are never chosen.
    :param preferred: County name of a hand-curated city anchor for this
        ZIP, when the module knows one. Takes precedence over geometry.
    :returns: A county name present in ``rated``, ``preferred`` when the
        anchor's county is not among the Census candidates, or ``None``
        when there is nothing to bind.
    """
    candidates: list[tuple[str, str]] = []
    for pair_abbrev, county_fips in pairs:
        if pair_abbrev != state_abbrev:
            continue
        name = county_name(state_abbrev, county_fips)
        if name is not None and name in rated:
            candidates.append((county_fips, name))

    # Rule 1: a human-verified city anchor outranks geometry. If Census
    # doesn't list the anchor's county for this ZIP at all (USPS-only
    # ZIP, or a boundary mismatch), still trust the anchor.
    if preferred is not None:
        for _fips, name in candidates:
            if name == preferred:
                return name
        return preferred

    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0][1]

    # Rule 2: land-area majority.
    dominant_fips = dominant_county(zip5, state_abbrev)
    if dominant_fips is not None:
        for county_fips, name in candidates:
            if county_fips == dominant_fips:
                return name

    # Rule 3: Census records no dominant county among the *rated*
    # candidates (e.g. the majority county exists but the module has no
    # rate for it). Lowest FIPS keeps the result deterministic.
    return min(candidates)[1]
