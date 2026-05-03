# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Per-state modules + the registry that discovers them.

Importing this package triggers registration of every shipped
state module via the import-time side effects in each module
(``register(...)`` calls).

Add a new state by:

1. Creating ``opensalestax/states/<state_name>.py``
2. Implementing the :class:`~.protocol.StateModule` Protocol
3. Calling :func:`~.registry.register` on the instance
4. Importing the new module here so it loads with the package
"""

from opensalestax.states import (
    _tier2,  # noqa: F401  -- side-effect: register 22 tier-2 SST states
    california,  # noqa: F401  -- side-effect: register CA (tier 1, non-SST)
    minnesota,  # noqa: F401  -- side-effect: register MN
    no_tax,  # noqa: F401  -- side-effect: register 5 no-tax states
    wisconsin,  # noqa: F401  -- side-effect: register WI
)
from opensalestax.states.protocol import (
    BoundaryRow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import (
    all_states,
    get_state_module,
    register,
    supported_abbrevs,
)

__all__ = [
    "BoundaryRow",
    "RateRow",
    "SpecialCase",
    "StateModule",
    "StateTier",
    "TaxabilityRule",
    "all_states",
    "get_state_module",
    "register",
    "supported_abbrevs",
]
