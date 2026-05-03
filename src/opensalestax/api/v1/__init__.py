# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""v1 router -- mounts the four Phase 1 endpoints under /v1.

Versioning per constitution sec 5: backward-compatible changes
add fields to existing responses; breaking changes require a
new ``/v2/`` prefix.
"""

from fastapi import APIRouter

from opensalestax.api.v1.calculate import router as calculate_router
from opensalestax.api.v1.health import router as health_router
from opensalestax.api.v1.rates import router as rates_router
from opensalestax.api.v1.states import router as states_router

router = APIRouter(prefix="/v1")
router.include_router(health_router)
router.include_router(states_router)
router.include_router(rates_router)
router.include_router(calculate_router)

__all__ = ["router"]
