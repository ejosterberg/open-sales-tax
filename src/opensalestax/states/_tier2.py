# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tier-2 SST member states (rate-only via SST data, default taxability).

The 19 SST members not yet promoted to tier 1 (MN, WI, AR, GA, IA).
Each is a ~10-line subclass of :class:`SstStateModule` providing
only the state-specific metadata (USPS abbreviation, full name,
state FIPS).

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
# 19 tier-2 SST states. Order roughly alphabetical for readability.
# Sources:
# - Sovos summary: specs/research/sovos-state-summary.md
# - SST membership list: specs/research/state-coverage.md
# - State FIPS codes: census.gov / NIST
#
# Arkansas (AR), Georgia (GA), and Iowa (IA) were promoted to
# tier 1 in v0.8 -- see their dedicated modules in
# ``opensalestax/states/``.
# ---------------------------------------------------------------------------


class Indiana(SstStateModule):
    """Indiana (IN) -- SST member, state base 7.0%, FIPS 18."""

    state_abbrev = "IN"
    state_name = "Indiana"
    state_fips = "18"


class Kansas(SstStateModule):
    """Kansas (KS) -- SST member, state base 6.5%, FIPS 20."""

    state_abbrev = "KS"
    state_name = "Kansas"
    state_fips = "20"


class Kentucky(SstStateModule):
    """Kentucky (KY) -- SST member, state base 6.0%, FIPS 21."""

    state_abbrev = "KY"
    state_name = "Kentucky"
    state_fips = "21"


class Michigan(SstStateModule):
    """Michigan (MI) -- SST member, state base 6.0%, FIPS 26."""

    state_abbrev = "MI"
    state_name = "Michigan"
    state_fips = "26"


class Nebraska(SstStateModule):
    """Nebraska (NE) -- SST member, state base 5.5%, FIPS 31."""

    state_abbrev = "NE"
    state_name = "Nebraska"
    state_fips = "31"


class Nevada(SstStateModule):
    """Nevada (NV) -- SST member, state base 6.85%, FIPS 32."""

    state_abbrev = "NV"
    state_name = "Nevada"
    state_fips = "32"


class NewJersey(SstStateModule):
    """New Jersey (NJ) -- SST member, state base 6.625%, FIPS 34.

    Note: NJ has the Jersey Gardens District with independent local
    nexus -- a tier-2 caveat to validate when promoting to tier 1.
    """

    state_abbrev = "NJ"
    state_name = "New Jersey"
    state_fips = "34"


class NorthCarolina(SstStateModule):
    """North Carolina (NC) -- SST member, state base 4.75%, FIPS 37."""

    state_abbrev = "NC"
    state_name = "North Carolina"
    state_fips = "37"


class NorthDakota(SstStateModule):
    """North Dakota (ND) -- SST member, state base 5.0%, FIPS 38."""

    state_abbrev = "ND"
    state_name = "North Dakota"
    state_fips = "38"


class Ohio(SstStateModule):
    """Ohio (OH) -- SST member, state base 5.75%, FIPS 39."""

    state_abbrev = "OH"
    state_name = "Ohio"
    state_fips = "39"


class Oklahoma(SstStateModule):
    """Oklahoma (OK) -- SST member, state base 4.5%, FIPS 40.

    Note: OK marketplace nexus threshold is dramatically lower
    ($10k vs $100k seller) -- a tier-2 caveat to validate when
    promoting to tier 1.
    """

    state_abbrev = "OK"
    state_name = "Oklahoma"
    state_fips = "40"


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
# Register all 19 instances at import time
# ---------------------------------------------------------------------------
TIER_2_CLASSES: tuple[type[SstStateModule], ...] = (
    Indiana,
    Kansas,
    Kentucky,
    Michigan,
    Nebraska,
    Nevada,
    NewJersey,
    NorthCarolina,
    NorthDakota,
    Ohio,
    Oklahoma,
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
