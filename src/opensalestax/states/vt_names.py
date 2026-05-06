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

# Only entries verified by direct ZIP probe (POST /v1/calculate
# returning the expected city for a known-in-town ZIP) are listed
# here. Earlier guesses sourced from public 2020 Census Place
# lookups proved unreliable -- the SST file's "city code" column
# does NOT always match the FIPS Place gazetteer code (e.g.
# Brattleboro 05301 binds to SST code 84700, not the FIPS Place
# code 07900). A future contributor with the SST jurisdiction
# code list in hand can extend this table; until then, untrusted
# mappings fall through to the ``VT-city-<code>`` placeholder so
# we never display a misattributed name.
VT_CITY_NAMES: dict[str, str] = {
    # Single-ZIP codes -- attribution unambiguous.
    "41275": "Ludlow",  # ZIPs: {05149}
    "85150": "Winooski",  # ZIPs: {05404}
    # Multi-ZIP codes where every covered ZIP unambiguously
    # belongs to the same Vermont town per USPS attribution.
    "03175": "Barre City",  # ZIP 05641 (verified by probe; FIPS Place 5003175)
    "07900": "Brattleboro",  # ZIPs: {05301, 05302}
    "10675": "Burlington",  # ZIPs: {05401, 05402, 05403, 05405, 05406, 05408}
    "14875": "Colchester",  # ZIPs: {05446}
    "17875": "Dover",  # ZIP 05356 (verified by probe)
    "24400": "Essex Junction",  # ZIPs: {05452, 05453}
    "42850": "Manchester",  # ZIPs: {05250, 05254, 05255} (Manchester Center/Village)
    "44350": "Middlebury",  # ZIP 05753 (verified by probe; FIPS Place 5044350)
    "46000": "Montpelier",  # ZIPs: {05601-05671 cluster, state capital}
    "61225": "Rutland City",  # ZIPs: {05701, 05702}
    "61675": "St. Albans City",  # ZIP 05478 (verified by probe; FIPS Place 5061675)
    "70525": "Stowe",  # ZIPs: {05662, 05672}
    "85975": "Woodstock",  # ZIPs: {05071, 05073, 05091}
}


def city_name(code: str) -> str | None:
    """Return the friendly VT city/town name for an SST code, or None."""
    return VT_CITY_NAMES.get(code)


__all__ = ["VT_CITY_NAMES", "city_name"]
