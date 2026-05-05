# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Vermont city/town tax authorities.

Vermont's SST quarterly file (verified against ``VTR2026Q2FEB20``)
ships ~28 type-1 (city/town) rows at 1% each, encoding the
municipalities that have adopted a Local Option Sales Tax under
24 V.S.A. section 138. Mapping every code is gated on a careful
cross-check against the Vermont Department of Taxes
"Municipalities with a Local Option Tax" page; the table below
covers only the codes whose FIPS Place attribution has been
confirmed against the 2020 Census Place gazetteer. Codes not yet
mapped fall through to the ``VT-city-<code>`` placeholder until a
subsequent contributor can verify them.

5-digit codes here are FIPS Place codes (state 50 + place suffix).
The SST file uses these codes verbatim in jurisdiction-type ``1``
(city) rows.
"""

from __future__ import annotations

VT_CITY_NAMES: dict[str, str] = {
    "07900": "Brattleboro",
    "10675": "Burlington",
    "14875": "Colchester",
    "17875": "Dover",
    "41275": "Manchester",
    "43375": "Middlebury",
    "46000": "Montpelier",
    "66175": "South Burlington",
    "84475": "Wilmington",
    "85075": "Williston",
}


def city_name(code: str) -> str | None:
    """Return the friendly VT city/town name for an SST code, or None."""
    return VT_CITY_NAMES.get(code)


__all__ = ["VT_CITY_NAMES", "city_name"]
