# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""GET /v1/states -- coverage list for all 52 US tax jurisdictions."""

from __future__ import annotations

from fastapi import APIRouter

from opensalestax.api.v1.schemas import StateInfo, StatesResponse
from opensalestax.states.catalog import STATE_CATALOG
from opensalestax.states.registry import get_state_module

router = APIRouter(tags=["states"])


@router.get("/states", response_model=StatesResponse)
async def list_states() -> StatesResponse:
    """List every US tax jurisdiction with its coverage tier.

    Tier semantics (also in StateInfo schema):

    - **0** -- unsupported. The catalog entry is returned but no
      module is loaded; calculation requests for these states will
      return zero with a "no jurisdictions found" note.
    - **1** -- fully maintained. Module + taxability matrix +
      tests. Phase 1: MN, WI, AK, DE, MT, NH, OR.
    - **2** -- rate-only via SST data with default taxability.
      Phase 1 ships this for the other 22 SST states after
      Section G2 lands.
    """
    items: list[StateInfo] = []
    for entry in STATE_CATALOG:
        module = get_state_module(entry.abbrev)
        tier = module.tier if module is not None else 0
        # Module overrides catalog facts when both exist (module is closer
        # to the truth -- it's the implementation).
        has_sales_tax = module.has_sales_tax if module is not None else entry.has_sales_tax
        sst_member = module.sst_member if module is not None else entry.sst_member
        items.append(
            StateInfo(
                abbrev=entry.abbrev,
                name=entry.name,
                has_sales_tax=has_sales_tax,
                sst_member=sst_member,
                tier=tier,
                notes=entry.notes,
            )
        )
    return StatesResponse(states=items, total=len(items))
