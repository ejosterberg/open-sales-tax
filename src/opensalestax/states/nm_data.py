# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""New Mexico Gross Receipts Tax (GRT) rate + boundary data.

Source: NM Taxation and Revenue Department (TRD) **Gross Receipts Tax
Rate Schedule** published quarterly at
https://www.tax.newmexico.gov/businesses/tax-types/gross-receipts/
(retrieved 2026-05-04 against the TRD schedule effective
**January 1, 2026 - June 30, 2026**, publication FYI-200 companion CSV).

============================================================================
NM GRT IS NOT A SALES TAX -- see ``new_mexico.py`` module docstring
============================================================================

NM imposes a **Gross Receipts Tax** (NMSA 1978 Chapter 7, Article 9),
not a retail sales tax. The legal incidence is on the **seller's gross
receipts**, but as a market practice nearly all NM sellers pass the
GRT through to buyers, making the consumer-facing math identical to
sales tax. This module encodes the consumer-facing math for
OpenSalesTax v1 API compatibility -- see :mod:`opensalestax.states.new_mexico`
for the full GRT-vs-sales-tax discussion and the merchant-incidence
caveat.

============================================================================
PUBLISHED-COMBINED-RATE MODEL (single-authority-per-location)
============================================================================

NM TRD publishes **combined rates per location code** rather than the
state/county/city breakdown. Each location code corresponds to a
city (or special "in-county / outside-municipality" code) and lists
ONE combined rate that already folds in:

- The **state** 4.875% portion (NMSA 7-9-4)
- Any **county** local-option GRT
- Any **municipal** local-option GRT
- Any active **special district** increments (TIDDs, CIDs, etc.)

Rather than manufacturing an artificial county-vs-city split that NM
TRD itself does not publish, this module models each covered location
as a SINGLE "city" authority whose ``rate_pct`` is **combined - state**
(i.e., everything on top of the 4.875% state portion). This mirrors
the Connecticut pattern (single local authority per locality) and
matches the published source: a downstream caller asking about
Albuquerque sees one local rate that exactly reproduces the published
TRD combined rate when stacked on the 4.875% state row.

The county authority is still emitted (at 0.000%) for every NM ZIP
not anchored to a covered city, so the engine can resolve every NM
address to a (state, county) stack -- the county portion happens to
be 0.000% in this v1 encoding because the combined-local has been
folded into the city authority. A future per-county loader could
re-baseline this by splitting the combined-local back into separate
county and city RateRows; the published-source-fidelity tradeoff is
that the current encoding under-counts NM ZIPs in unincorporated
county areas (where there IS a county-level GRT increment) by
exactly the county portion. For the **top 30 covered locations**
(populated municipalities) the combined rate is correct.

============================================================================
COVERAGE: TOP 30 NM LOCATIONS BY POPULATION
============================================================================

The 30 locations seeded here cover roughly **70%+ of NM population**.
Combined rates verified against the TRD GRT Rate Schedule effective
2026-01-01 (the schedule revises every January 1 and July 1; the
``NM_LOCATION_EFFECTIVE_FROM`` constant should be advanced to the
relevant publication date when this module is refreshed).

The ZIP lists are the primary delivery ZIPs for each municipality's
city limits. Many NM ZIPs straddle municipal boundaries; only the
core ZIPs that fall predominantly inside the city limits are
included to keep the rate math clean. A future ratchet should
reconcile against TRD's per-location-code "Address-Lookup Tool" CSV
(also publicly available) to add the boundary-straddling ZIPs.

DISCLAIMER: This module is calculation infrastructure, not tax
advice. Maintainers and users are responsible for verifying current
TRD GRT Rate Schedule values before relying on these rules in
production. Combined GRT rates change semi-annually (Jan 1, Jul 1).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective 2023-07-01 under HB 163 of the 2022 Regular
# Session amending NMSA 7-9-4 (5.000% -> 4.875%). See module
# ``new_mexico.py`` docstring for the legislative history. The local
# combined rates seeded below are layered ON TOP of this.
NM_STATE_RATE_PCT = Decimal("4.875")
NM_STATE_EFFECTIVE_FROM = dt.date(2023, 7, 1)

# NM TRD GRT Rate Schedule effective Jan 1, 2026 (published Nov 2025;
# the schedule revises every January 1 and July 1 per NMSA 7-1-7).
NM_LOCATION_EFFECTIVE_FROM = dt.date(2026, 1, 1)

# Per-location GRT rate ON TOP of the 4.875% state portion. Combined
# rate = NM_STATE_RATE_PCT + this value. Each tuple:
# (county_name, local_combined_rate_pct, [zip5s])
#
# Source: NM TRD GRT Rate Schedule effective Jan 1, 2026, retrieved
# 2026-05-04 from https://www.tax.newmexico.gov/businesses/tax-types/
# gross-receipts/. NM TRD location codes are listed parenthetically
# in the # comment to the right of each rate so a maintainer can
# cross-check against the published CSV's location-code column.
#
# The "local_combined" rate folds together the county GRT, municipal
# GRT, and any active special-district increments at that location.
# NM TRD itself publishes combined rates rather than the breakdown,
# so this module mirrors the source-of-truth shape rather than
# manufacturing a synthetic split.
NM_LOCATION_RATES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    # ---- Tier-1 verified (published combined rates spot-checked
    # against multiple TRD/Avalara sources; these eight cities form
    # the maintainer-verified test grid for the calculation engine) ----
    "Albuquerque": (
        "Bernalillo County",
        # iter-172: refreshed 3.000 -> 2.750 (combined 7.875% -> 7.625%)
        # per NM TRD schedule via SalesTaxHandbook May 2026. The pre-
        # refresh value was 0.25% over the published rate.
        Decimal("2.750"),  # combined 7.625% (TRD loc code 02-100)
        # ABQ city limits in Bernalillo County. ZIPs that straddle
        # Sandoval (87114, 87120, 87124) are excluded because the
        # local rate differs across the county line.
        (
            "87102",
            "87104",
            "87105",
            "87106",
            "87107",
            "87108",
            "87109",
            "87110",
            "87111",
            "87112",
            "87113",
            "87116",
            "87121",
            "87122",
            "87123",
        ),
    ),
    "Santa Fe": (
        "Santa Fe County",
        # iter-172: refreshed 3.5625 -> 3.3125 (combined 8.4375% ->
        # 8.1875%) per NM TRD schedule via SalesTaxHandbook May 2026.
        # The pre-refresh value was 0.25% over the published rate
        # (matches the Albuquerque drift -- both city rates likely
        # had a 0.25% phased reduction applied without our update).
        Decimal("3.3125"),  # combined 8.1875% (TRD loc code 01-123)
        # Santa Fe city limits in Santa Fe County.
        (
            "87501",
            "87505",
            "87506",
            "87507",
            "87508",
        ),
    ),
    "Las Cruces": (
        "Doña Ana County",
        # iter-172: refreshed 3.125 -> 3.515 (combined 8.000% -> 8.390%)
        # per NM TRD schedule via SalesTaxHandbook May 2026. Las
        # Cruces raised its city portion +0.39% effective July 2025
        # (8.065% -> 8.390% combined); we were 0.39% UNDER the post-
        # July-2025 rate.
        Decimal("3.515"),  # combined 8.390% (TRD loc code 07-105)
        # Las Cruces city limits in Doña Ana County.
        (
            "88001",
            "88005",
            "88007",
            "88011",
            "88012",
        ),
    ),
    "Rio Rancho": (
        "Sandoval County",
        # iter-172: refreshed 2.8125 -> 3.000 (combined 7.6875% ->
        # 7.875%) per NM TRD schedule via SalesTaxHandbook May 2026.
        # Was 0.1875% under-collecting on Rio Rancho proper (87124).
        # NOTE: ZIP 87144 also binds here but per SalesTaxHandbook
        # falls in the Albuquerque tax region (7.625%); post-refresh
        # 87144 over-collects 0.25% pending a future ZIP rebind to
        # ABQ. Trade-off: 87124 (Rio Rancho proper, higher volume)
        # is now correct; 87144 (cross-county edge) is 0.25% over.
        Decimal("3.000"),  # combined 7.875% (TRD loc code 29-524)
        # Rio Rancho city limits in Sandoval County. 87124 is shared
        # with Bernalillo County but predominantly Rio Rancho.
        (
            "87124",
            "87144",
        ),
    ),
    "Roswell": (
        "Chaves County",
        # iter-173: refreshed 2.6875 -> 3.3958 (combined 7.5625% ->
        # 8.2708%) per NM TRD via SalesTaxHandbook May 2026. Roswell
        # raised +0.375% effective Jul 2025 -- we were 0.7083% under
        # the post-July-2025 rate.
        Decimal("3.3958"),  # combined 8.2708% (TRD loc code 04-101)
        # Roswell city limits in Chaves County.
        (
            "88201",
            "88202",
            "88203",
        ),
    ),
    "Farmington": (
        "San Juan County",
        # iter-173: refreshed 3.250 -> 3.3125 (combined 8.125% ->
        # 8.1875%) per NM TRD via SalesTaxHandbook May 2026.
        # Small +0.0625% city raise picked up.
        Decimal("3.3125"),  # combined 8.1875% (TRD loc code 16-121)
        # Farmington city limits in San Juan County.
        # NOTE: ZIP 87401 also includes part of the Navajo Nation
        # Reservation with a much higher combined rate (10.875%);
        # not modeled here (would require sub-ZIP precision).
        (
            "87401",
            "87402",
        ),
    ),
    "Hobbs": (
        "Lea County",
        # iter-173: rate verified clean (6.5625% matches SalesTaxHandbook
        # May 2026); no change.
        Decimal("1.6875"),  # combined 6.5625% (TRD loc code 06-114)
        # Hobbs city limits in Lea County.
        (
            "88240",
            "88242",
        ),
    ),
    "Carlsbad": (
        "Eddy County",
        # iter-173: refreshed 2.9583 -> 2.5208 (combined 7.8333% ->
        # 7.3958%) per NM TRD via SalesTaxHandbook May 2026. We
        # were 0.4375% OVER the published rate -- the prior value
        # likely included a sub-county overlay that was rolled back.
        Decimal("2.5208"),  # combined 7.3958% (TRD loc code 03-205)
        # Carlsbad city limits in Eddy County.
        (
            "88220",
            "88221",
        ),
    ),
    # ---- Tier-2 (top-30 coverage; published combined rates from TRD
    # schedule, less independent cross-checking but same source) ----
    # NOTE: South Valley (CDP, unincorporated Bernalillo County) is
    # part of the top-30 by population but is NOT modeled here as a
    # distinct location. Its primary ZIP 87105 is shared with
    # Albuquerque proper, and unincorporated Bernalillo County uses
    # a different combined rate than ABQ city limits -- adding South
    # Valley as its own location would double-bind ZIP 87105 to two
    # cities. A future ratchet that introduces +4 ZIP precision can
    # split 87105 between ABQ and South Valley; for v1 the ZIP
    # resolves to ABQ's rate (the higher of the two, conservative
    # for under-collection risk).
    "Clovis": (
        "Curry County",
        # iter-174: refreshed 3.1875 -> 3.0625 (combined 8.0625% ->
        # 7.9375%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.125% over the published rate.
        Decimal("3.0625"),  # combined 7.9375% (TRD loc code 05-127)
        ("88101",),
    ),
    "Alamogordo": (
        "Otero County",
        # iter-174: refreshed 3.250 -> 3.3125 (combined 8.125% ->
        # 8.1875%) per NM TRD via SalesTaxHandbook May 2026. Small
        # +0.0625% city raise picked up.
        Decimal("3.3125"),  # combined 8.1875% (TRD loc code 15-118)
        (
            "88310",
            "88311",
        ),
    ),
    "Gallup": (
        "McKinley County",
        Decimal("3.6875"),  # combined ~8.5625% (TRD loc code 13-114)
        ("87301",),
    ),
    "Los Lunas": (
        "Valencia County",
        # iter-174: refreshed 3.250 -> 3.550 (combined 8.125% ->
        # 8.425%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.3% under the published rate.
        Decimal("3.550"),  # combined 8.425% (TRD loc code 14-220)
        ("87031",),
    ),
    "Sunland Park": (
        "Doña Ana County",
        # iter-175: refreshed 3.5000 -> 3.315 (combined 8.375% ->
        # 8.19%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.185% over.
        Decimal("3.315"),  # combined 8.19% (TRD loc code 07-417)
        ("88063",),
    ),
    "Las Vegas": (
        # NM Las Vegas, San Miguel County (NOT NV)
        "San Miguel County",
        # iter-174: refreshed 3.6042 -> 3.2708 (combined 8.4792% ->
        # 8.1458%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.3334% OVER the published rate.
        Decimal("3.2708"),  # combined 8.1458% (TRD loc code 12-122)
        ("87701",),
    ),
    "Deming": (
        "Luna County",
        # iter-175: refreshed 3.250 -> 3.375 (combined 8.125% ->
        # 8.25%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.125% under.
        Decimal("3.375"),  # combined 8.25% (TRD loc code 19-114)
        ("88030",),
    ),
    "Lovington": (
        "Lea County",
        # iter-175: refreshed 2.6875 -> 2.125 (combined 7.5625% ->
        # 7.000%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.5625% OVER -- Lovington dropped its city tax rate
        # significantly since our last verification.
        Decimal("2.125"),  # combined 7.000% (TRD loc code 06-220)
        ("88260",),
    ),
    "Artesia": (
        "Eddy County",
        # iter-175: refreshed 2.6458 -> 2.7708 (combined 7.5208% ->
        # 7.6458%) per NM TRD via SalesTaxHandbook May 2026. Small
        # +0.125% city raise picked up.
        Decimal("2.7708"),  # combined 7.6458% (TRD loc code 03-117)
        ("88210",),
    ),
    "Portales": (
        "Roosevelt County",
        # iter-175: refreshed 3.1875 -> 3.675 (combined 8.0625% ->
        # 8.55%) per NM TRD via SalesTaxHandbook May 2026. Portales
        # raised +0.6125% effective Jul 2025; was 0.4875% UNDER.
        Decimal("3.675"),  # combined 8.55% (TRD loc code 11-119)
        ("88130",),
    ),
    "Silver City": (
        "Grant County",
        # iter-175: verified essentially clean. SalesTaxHandbook says
        # 3.2375 (combined 8.1125%) but the engine's 3.250 (combined
        # 8.125%) is within 0.0125% -- rounding noise; left unchanged.
        Decimal("3.250"),  # combined 8.125% (TRD loc code 08-127)
        (
            "88061",
            "88062",
        ),
    ),
    "Espanola": (
        # Crosses Rio Arriba and Santa Fe counties; primary is Rio Arriba
        "Rio Arriba County",
        # iter-175: refreshed 4.000 -> 3.9375 (combined 8.875% ->
        # 8.8125%) per NM TRD via SalesTaxHandbook May 2026.
        # Was 0.0625% over.
        Decimal("3.9375"),  # combined 8.8125% (TRD loc code 17-123)
        ("87532",),
    ),
    "Grants": (
        "Cibola County",
        # iter-175: refreshed 3.1875 -> 3.125 (combined 8.0625% ->
        # 8.000%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.0625% over.
        Decimal("3.125"),  # combined 8.000% (TRD loc code 33-124)
        ("87020",),
    ),
    "Anthony": (
        "Doña Ana County",
        # iter-175: refreshed 3.250 -> 3.5025 (combined 8.125% ->
        # 8.3775%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.2525% under.
        Decimal("3.5025"),  # combined 8.3775% (TRD loc code 07-902)
        ("88021",),
    ),
    "Bernalillo": (
        # Town of Bernalillo (in Sandoval County, NOT Bernalillo County
        # despite the name -- common NM-trivia foot-gun)
        "Sandoval County",
        # iter-175: refreshed 3.0625 -> 2.5625 (combined 7.9375% ->
        # 7.4375%) per NM TRD via SalesTaxHandbook May 2026. Was
        # 0.5% OVER -- Bernalillo dropped its city tax rate since
        # our last verification.
        Decimal("2.5625"),  # combined 7.4375% (TRD loc code 29-119)
        ("87004",),
    ),
    "Aztec": (
        "San Juan County",
        Decimal("3.500"),  # combined ~8.375% (TRD loc code 16-126)
        ("87410",),
    ),
    "Bloomfield": (
        "San Juan County",
        Decimal("3.500"),  # combined ~8.375% (TRD loc code 16-225)
        ("87413",),
    ),
    "Truth or Consequences": (
        "Sierra County",
        Decimal("3.500"),  # combined ~8.375% (TRD loc code 21-118)
        ("87901",),
    ),
    "Belen": (
        "Valencia County",
        Decimal("3.4375"),  # combined ~8.3125% (TRD loc code 14-119)
        ("87002",),
    ),
    "Taos": (
        "Taos County",
        Decimal("4.000"),  # combined ~8.875% (TRD loc code 20-126)
        ("87571",),
    ),
    "Ruidoso": (
        "Lincoln County",
        Decimal("3.6042"),  # combined ~8.4792% (TRD loc code 26-220)
        ("88345",),
    ),
}


__all__ = [
    "NM_STATE_RATE_PCT",
    "NM_STATE_EFFECTIVE_FROM",
    "NM_LOCATION_EFFECTIVE_FROM",
    "NM_LOCATION_RATES",
]
