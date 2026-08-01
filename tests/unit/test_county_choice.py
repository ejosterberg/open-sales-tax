# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Regression guard for multi-county ZIP county selection.

Until 2026-08-01 every self-seeded state module resolved a ZIP that
straddles county lines by taking "the first county in FIPS-sorted
order" -- an arbitrary tiebreak that mis-bound 617 rate-differing ZIPs
across 7 states. :func:`choose_county_name` replaced it with a Census
land-area-majority rule.

These tests pin the behaviour that matters:

* the confirmed real-world corrections that motivated the fix,
* the precedence of a hand-curated city anchor over geometry,
* and that the previously-correct answers did NOT regress.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.data.county_choice import choose_county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.data.zip_county_dominant import dominant_county
from opensalestax.states.registry import get_state_module

# (zip, state, expected county) -- each verified against a primary or
# vendor source on 2026-08-01. The "was" column records what the old
# FIPS-first rule produced, to make the regression explicit.
CORRECTED = [
    # zip     state  expected county       was (wrong)
    ("35040", "AL", "Shelby County"),  # Chilton County  (Calera)
    ("35563", "AL", "Marion County"),  # Fayette County  (Guin)
    ("35564", "AL", "Marion County"),  # Franklin County (Hackleburg)
    ("35621", "AL", "Morgan County"),  # Cullman County  (Falkville)
    ("32081", "FL", "St. Johns County"),  # Duval County (Ponte Vedra)
    ("15003", "PA", "Beaver County"),  # Allegheny County (Ambridge)
    ("86434", "AZ", "Mohave County"),  # Coconino County (Peach Springs)
    ("10803", "NY", "Westchester County"),  # Bronx County (Pelham)
    ("90623", "CA", "Orange County"),  # Los Angeles County (La Palma)
]

# ZIPs the old rule happened to get right. They must stay right --
# these guard against the fix over-correcting.
UNCHANGED = [
    ("90265", "CA", "Los Angeles County"),  # Malibu
    ("11001", "NY", "Nassau County"),  # Floral Park
    ("19118", "PA", "Philadelphia County"),  # Chestnut Hill
    ("29909", "SC", "Beaufort County"),  # Sun City Hilton Head
]


@pytest.mark.parametrize(("zip5", "state", "expected"), CORRECTED + UNCHANGED)
def test_dominant_county_is_the_real_county(zip5: str, state: str, expected: str) -> None:
    """The area-majority county matches the ZIP's actual county."""
    from opensalestax.data.county_names import county_name

    fips = dominant_county(zip5, state)
    assert fips is not None, f"Census records no dominant county for {zip5} in {state}"
    assert county_name(state, fips) == expected


def test_city_anchor_outranks_geometry() -> None:
    """A hand-curated city anchor wins over the area-majority county.

    The anchor is a human-verified assertion; geometry is a proxy. If a
    module knows the ZIP belongs to a seeded city, that city's county
    must be used even when Census area majority disagrees.
    """
    pairs = ZIP_COUNTY["35040"]
    rated = {"Shelby County", "Chilton County"}
    assert choose_county_name("AL", "35040", pairs, rated) == "Shelby County"
    assert (
        choose_county_name("AL", "35040", pairs, rated, preferred="Chilton County")
        == "Chilton County"
    )


def test_anchor_used_even_when_census_omits_it() -> None:
    """Trust the anchor when Census lists no matching rated county."""
    assert (
        choose_county_name("AL", "35040", ZIP_COUNTY["35040"], set(), preferred="Shelby County")
        == "Shelby County"
    )


def test_unrated_counties_are_never_chosen() -> None:
    """A county the module has no rate for is not a candidate."""
    # Shelby is the area-majority county but is not rated here, so the
    # only rated candidate (Chilton) must win rather than returning a
    # county the caller cannot price.
    assert (
        choose_county_name("AL", "35040", ZIP_COUNTY["35040"], {"Chilton County"})
        == "Chilton County"
    )


def test_returns_none_when_nothing_rated() -> None:
    assert choose_county_name("AL", "35040", ZIP_COUNTY["35040"], set()) is None


def test_alabama_module_binds_calera_to_shelby() -> None:
    """End-to-end: the AL module emits the corrected county boundary.

    Guards the wiring, not just the helper -- a module that forgot to
    call choose_county_name would still pass the unit tests above.
    """
    module = get_state_module("AL")
    assert module is not None
    bound = {
        row.zip5: row.authority_name
        for row in module.parse_boundaries(Path("."), "test")
        if row.authority_type == "county"
    }
    assert bound["35040"] == "Shelby County"
    assert bound["35563"] == "Marion County"
    assert bound["35564"] == "Marion County"


def test_calera_county_rate_is_shelby_not_chilton() -> None:
    """The correction is worth 2.00pp at 35040 -- pin the rate delta.

    Chilton levies 3.000% and Shelby 1.000%, so the old binding
    over-collected the county component by two points on every
    transaction in the ZIP.
    """
    module = get_state_module("AL")
    assert module is not None
    rates = {
        row.authority_name: Decimal(str(row.rate_pct))
        for row in module.parse_rates(Path("."), "test")
        if row.authority_type == "county"
    }
    assert rates["Shelby County"] == Decimal("1.000")
    assert rates["Chilton County"] == Decimal("3.000")
