# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tier-2 SST member states (rate-only via SST data, default taxability).

The 8 SST members not yet promoted to tier 1 (MN, WI, AR, GA, IA, IN,
KS, KY, MI, NC, ND, NE, NJ, NV, OH, OK are now tier 1). Each is a ~10-line subclass of
:class:`SstStateModule` providing only the state-specific metadata
(USPS abbreviation, full name, state FIPS).

State base rates documented in the docstring per state are taken
from ``specs/research/sovos-state-summary.md`` and cross-checked
against each state's published SST rate file. They serve as
documentation only -- the actual rate that flows through the API
comes from the SST data file when loaded via the data-refresh CLI.

To promote a state to tier 1: create a new file
``opensalestax/states/<state_name>.py`` with full taxability rules
and 10+ test fixtures, then remove its entry from this module.
"""

from __future__ import annotations

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# 8 tier-2 SST states. Order roughly alphabetical for readability.
# Sources:
# - Sovos summary: specs/research/sovos-state-summary.md
# - SST membership list: specs/research/state-coverage.md
# - State FIPS codes: census.gov / NIST
#
# Arkansas (AR), Georgia (GA), Indiana (IN), Iowa (IA), Kansas (KS),
# Kentucky (KY), Michigan (MI), Nebraska (NE), Nevada (NV), New Jersey
# (NJ), North Carolina (NC), North Dakota (ND), Ohio (OH), and Oklahoma
# (OK) were promoted to tier 1 in v0.8/v0.9/v0.10 -- see their
# dedicated modules in ``opensalestax/states/``.
# ---------------------------------------------------------------------------


class RhodeIsland(SstStateModule):
    """Rhode Island (RI) -- SST member, state base 7.0%, FIPS 44."""

    state_abbrev = "RI"
    state_name = "Rhode Island"
    state_fips = "44"


class SouthDakota(SstStateModule):
    """South Dakota (SD) -- SST member, state base 4.2%, FIPS 46."""

    state_abbrev = "SD"
    state_name = "South Dakota"
    state_fips = "46"


class Tennessee(SstStateModule):
    """Tennessee (TN) -- SST associate member, state base 7.0%, FIPS 47."""

    state_abbrev = "TN"
    state_name = "Tennessee"
    state_fips = "47"


class Utah(SstStateModule):
    """Utah (UT) -- SST member, state base 4.85%, FIPS 49.

    Note: UT's Navajo Nation has independent nexus on the Utah
    portion -- a tier-2 caveat to validate when promoting to tier 1.
    """

    state_abbrev = "UT"
    state_name = "Utah"
    state_fips = "49"


class Vermont(SstStateModule):
    """Vermont (VT) -- SST member, state base 6.0%, FIPS 50."""

    state_abbrev = "VT"
    state_name = "Vermont"
    state_fips = "50"


class Washington(SstStateModule):
    """Washington (WA) -- SST member, state base 6.5%, FIPS 53."""

    state_abbrev = "WA"
    state_name = "Washington"
    state_fips = "53"


class WestVirginia(SstStateModule):
    """West Virginia (WV) -- SST member, state base 6.0%, FIPS 54."""

    state_abbrev = "WV"
    state_name = "West Virginia"
    state_fips = "54"


class Wyoming(SstStateModule):
    """Wyoming (WY) -- SST member, state base 4.0%, FIPS 56."""

    state_abbrev = "WY"
    state_name = "Wyoming"
    state_fips = "56"


# ---------------------------------------------------------------------------
# Register all 8 instances at import time
# ---------------------------------------------------------------------------
TIER_2_CLASSES: tuple[type[SstStateModule], ...] = (
    RhodeIsland,
    SouthDakota,
    Tennessee,
    Utah,
    Vermont,
    Washington,
    WestVirginia,
    Wyoming,
)


def _register(cls: type[SstStateModule]) -> SstStateModule:
    """Instantiate and register a tier-2 module, returning the instance.

    Wrapped in a typed helper so mypy sees ``SstStateModule`` rather
    than the broader Protocol return of ``register()``.
    """
    instance = cls()
    register(instance)
    return instance


TIER_2_STATES: tuple[SstStateModule, ...] = tuple(_register(cls) for cls in TIER_2_CLASSES)
