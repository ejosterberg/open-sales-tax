# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Idaho resort-city local-option sales tax data.

Idaho is a non-SST state with a flat 6% statewide rate
(:mod:`opensalestax.states.idaho`). It has no county-level sales
tax. A small number of "resort cities" with populations not
exceeding 10,000 are authorized under **Idaho Code section
50-1044** to impose, by 60% voter approval, a local-option sales
tax that may be levied alongside the state rate. The sales-tax
portion is typically 1-3%.

This module models the resort cities that levy a SALES tax
(some resort cities only impose lodging or by-the-drink alcohol
tax, not general retail; those are NOT modeled here).

Source: Idaho State Tax Commission "Resort Cities Sales Tax"
publication and per-city rate verification via the cities'
finance/treasurer publications. Captured 2026-05-10.

iter-75 added the 6 highest-population 3% resort cities (Sun
Valley / Ketchum / McCall / Stanley / Donnelly / Cascade ->
combined 9.0%). iter-76 expanded with the 1% and 0.5% resort
cities (Sandpoint / Salmon / Driggs / Riggins / Lava Hot
Springs / Crouch -> combined 6.5-7.0%). Total: 12 cities.
"""

from __future__ import annotations

from decimal import Decimal

# Map of resort-city name -> (rate_pct, frozenset[zip5]).
# Each entry levies a local-option SALES tax under Idaho Code
# section 50-1044, in addition to Idaho's flat 6% state rate.
ID_RESORT_CITIES: dict[str, tuple[Decimal, frozenset[str]]] = {
    # 3% resort cities (combined 9.0%)
    "Sun Valley": (Decimal("3.000"), frozenset({"83353"})),
    "Ketchum": (Decimal("3.000"), frozenset({"83340"})),
    "McCall": (Decimal("3.000"), frozenset({"83638"})),
    "Stanley": (Decimal("3.000"), frozenset({"83278"})),
    "Donnelly": (Decimal("3.000"), frozenset({"83615"})),
    "Cascade": (Decimal("3.000"), frozenset({"83611"})),
    # iter-76: 1% resort cities (combined 7.0%)
    "Sandpoint": (Decimal("1.000"), frozenset({"83864"})),
    "Driggs": (Decimal("1.000"), frozenset({"83422"})),
    "Riggins": (Decimal("1.000"), frozenset({"83549"})),
    "Lava Hot Springs": (Decimal("1.000"), frozenset({"83246"})),
    "Crouch": (Decimal("1.000"), frozenset({"83622"})),
    # iter-76: 0.5% resort city (combined 6.5%)
    "Salmon": (Decimal("0.500"), frozenset({"83467"})),
}


__all__ = ["ID_RESORT_CITIES"]
