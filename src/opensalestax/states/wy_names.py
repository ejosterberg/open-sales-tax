# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Wyoming city/place tax authorities.

Wyoming's SST quarterly rate file (verified against
``WYR2026Q2APR1.csv`` on 2026-05-05) is unusually sparse on
jurisdiction-type 01 (city/place) rows -- only **one** active row
appears, for FIPS Place ``13150`` = Casper. This is consistent with
Wyo. Stat. section 39-15-204, which limits local sales-tax
imposition to counties (the "5th penny" general-purpose levy and
the "6th penny" specific-purpose levy); Wyoming municipalities have
no statutory authority to impose a separate city sales tax.

The single 01-typed row in the WY file therefore most likely
encodes a Natrona County specific-purpose levy whose collection is
restricted to the Casper city limits, not a Casper-imposed tax. The
friendly name "Casper" reflects the geographic placename associated
with FIPS Place 13150 and matches what an integrator looking up the
juris code would expect to see; the underlying rate semantics are
captured in :mod:`opensalestax.states.wyoming` and
``specs/decisions/07-wyoming-multi-row-counties.md``.

5-digit codes here are FIPS Place codes (state 56 + place
suffix). The SST file uses these codes verbatim in
jurisdiction-type ``01`` rows.
"""

from __future__ import annotations

WY_CITY_NAMES: dict[str, str] = {
    "13150": "Casper",
}


def city_name(code: str) -> str | None:
    """Return the friendly WY place name for an SST code, or None."""
    return WY_CITY_NAMES.get(code)


__all__ = ["WY_CITY_NAMES", "city_name"]
