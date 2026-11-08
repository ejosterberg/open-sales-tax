# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Hand-curated county-of-record overrides for specific ZIPs.

:data:`opensalestax.data.zip_county_dominant.ZIP_COUNTY_DOMINANT` is
auto-generated from the Census ZCTA->County land-area-majority file.
That signal is correct for most ZIPs but is wrong when a city with a
dense incorporated footprint sits inside a geographically small
county (Washington 147), while a geographically large but sparsely
populated neighbouring county (Osage 113) covers more of the ZIP's
acreage.

Per the `choose_county_name` doc in `county_choice.py` the design
answer for such mismatches is a hand-curated anchor; this module is
that anchor for the ZIP+4 lookup path that doesn't consult the
self-seeded modules.

Add entries sparingly and only with a primary-source citation.
"""

from __future__ import annotations

#: (zip5, state_abbrev) -> county FIPS (3-digit).
#:
#: Entries override the Census area-majority dominant for a single
#: ZIP. Each must cite: (a) the aggregate rate the override produces,
#: (b) why the Census majority is wrong for THIS ZIP (geographic
#: facts), (c) the primary source for the correct county assignment.
ZIP_COUNTY_OVERRIDES: dict[tuple[str, str], str] = {
    # OK 74003 Bartlesville. Census ZCTA majority is Osage (113) because
    # the ZIP's rural acreage extends into Osage County, but the city of
    # Bartlesville (county seat of Washington County) is almost entirely
    # within Washington County (147). The Oklahoma Tax Commission's
    # city/county tables publish Bartlesville under Washington; the
    # business-filing address list used for municipal tax remittance
    # likewise places 74003 in Washington. Correct combined rate:
    # state 4.5 + Washington Co 1.0 + Bartlesville city 3.4 = 8.900%
    # (not Osage's 9.15% stack).
    ("74003", "OK"): "147",
}


def county_override(zip5: str, state_abbrev: str) -> str | None:
    """Return a hand-curated county FIPS override, or ``None``.

    Callers should consult this before falling back to the auto-
    generated :func:`opensalestax.data.zip_county_dominant.dominant_county`.
    """
    return ZIP_COUNTY_OVERRIDES.get((zip5, state_abbrev))


__all__ = ["ZIP_COUNTY_OVERRIDES", "county_override"]
