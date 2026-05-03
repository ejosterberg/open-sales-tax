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

from opensalestax.states import no_tax  # noqa: F401  -- side-effect: register 5 instances
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
