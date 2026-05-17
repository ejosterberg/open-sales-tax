# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""GET /v1/capabilities -- discoverable feature manifest.

Connectors call this on Test Connection / first calc and cache
the result. Lets them do version-aware feature detection without
parsing the engine's semver string out of ``/v1/health``.

Driver: connector-tier captain's ``engine-team-requests.md``
(cross-cutting note), greenlit for v0.59.0.
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from opensalestax import __version__
from opensalestax.api.v1.schemas import CapabilitiesResponse, EndpointDescriptor

router = APIRouter(tags=["capabilities"])


# Per-endpoint spec versions. Bump when the request/response shape
# of an endpoint changes incompatibly. These are independent of the
# package version (``__version__``); the package can ship many
# patch releases without touching any endpoint's spec version.
_ENDPOINTS: dict[str, EndpointDescriptor] = {
    "health": EndpointDescriptor(path="/v1/health", version=1),
    "states": EndpointDescriptor(path="/v1/states", version=1),
    "rates": EndpointDescriptor(path="/v1/rates", version=1),
    "calculate": EndpointDescriptor(path="/v1/calculate", version=1),
    "capabilities": EndpointDescriptor(path="/v1/capabilities", version=1),
}


# Discoverable-feature contract. Keys are stable across engine
# releases; values flip true when the feature ships. Connectors
# can branch on these for graceful degradation.
#
# Contract:
# - Adding a key with value True is non-breaking; old connectors
#   that don't know the key just ignore it.
# - Flipping an existing True to False IS breaking and requires
#   a major version bump.
# - Removing a key IS breaking and requires a major version bump.
_FEATURES: dict[str, bool] = {
    # iter-189: /v1/rates and /v1/calculate include a coverage_warning
    # field when the requested ZIP falls in a state with documented
    # local-tax coverage gaps (CO/LA/AL/HI).
    "coverage_warning": True,
    # Captain Ask 3 (engine-team-requests.md). Shipped in v0.59.0.
    # Connectors can pass a top-level ``shipping`` field on
    # /v1/calculate; engine applies the destination state's
    # ``ShippingRule`` and returns a parallel ``shipping`` block.
    "shipping_first_class": True,
    # Captain Ask 2. Eric ruled out-of-scope 2026-05-16; stays
    # False permanently unless that decision is reopened.
    "vendor_allocation": False,
    # Captain Ask 1. Eric ruled calculation-only positioning
    # 2026-05-16 (specs/decisions/06-calculation-only-positioning.md);
    # stays False unless preconditions met.
    "transaction_record_back": False,
}


@router.get("/capabilities")
async def capabilities(response: Response) -> CapabilitiesResponse:
    """Return the engine's feature manifest.

    Static per release; can be cached aggressively by the connector
    AND by any CDN in front of the API.
    """
    # Cache aggressively. Per-release static data; manifest only
    # changes when a new engine version deploys. 1-hour TTL gives
    # connectors quick pickup of new features without hammering
    # the origin.
    response.headers["Cache-Control"] = "public, max-age=3600"
    return CapabilitiesResponse(
        version=__version__,
        endpoints=_ENDPOINTS,
        features=_FEATURES,
    )
