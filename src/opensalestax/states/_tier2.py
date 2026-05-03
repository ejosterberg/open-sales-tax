# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tier-2 SST member states (rate-only via SST data, default taxability).

**Phase 7 complete in v0.11.0**: every SST member state is now tier 1.
This module's :data:`TIER_2_CLASSES` tuple is intentionally empty --
nothing remains to register. The module is kept (rather than deleted)
for two reasons:

1. ``opensalestax/states/__init__.py`` imports it for its register-at-
   import side effect; deleting it would require ripping out that
   import too.
2. Future tier-2 states (e.g. if a non-SST state ever lands as
   rate-only via a separate data feed) can be registered here.

The 22 SST members were promoted to tier 1 across v0.1 (MN, WI), v0.8
(AR, GA, IA, IN), v0.9 (KS, KY, MI, NE, NV), v0.10 (NJ, NC, ND, OH,
OK), and v0.11 (RI, SD, TN, UT, VT, WA, WV, WY).
"""

from __future__ import annotations

from opensalestax.states._sst_base import SstStateModule

# ---------------------------------------------------------------------------
# 0 tier-2 SST states. Every SST member is now tier-1.
# Sources:
# - Sovos summary: specs/research/sovos-state-summary.md
# - SST membership list: specs/research/state-coverage.md
# - State FIPS codes: census.gov / NIST
#
# Phase 7 SST tier-2 -> tier-1 promotion ratchet completed in v0.11.0.
# All 22 SST members now have dedicated modules in
# ``opensalestax/states/`` with full taxability matrices grounded in
# state statutes (and any state-specific holiday windows).
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Empty registration tuple -- Phase 7 complete.
# ---------------------------------------------------------------------------
TIER_2_CLASSES: tuple[type[SstStateModule], ...] = ()


TIER_2_STATES: tuple[SstStateModule, ...] = ()
