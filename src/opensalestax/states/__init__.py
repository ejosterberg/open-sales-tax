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

# Each import below is for its register() side-effect at package load.
from opensalestax.states import (
    _tier2,  # noqa: F401
    arizona,  # noqa: F401
    arkansas,  # noqa: F401
    california,  # noqa: F401
    colorado,  # noqa: F401
    connecticut,  # noqa: F401
    district_of_columbia,  # noqa: F401
    florida,  # noqa: F401
    georgia,  # noqa: F401
    idaho,  # noqa: F401
    illinois,  # noqa: F401
    indiana,  # noqa: F401
    iowa,  # noqa: F401
    kansas,  # noqa: F401
    kentucky,  # noqa: F401
    louisiana,  # noqa: F401
    maryland,  # noqa: F401
    massachusetts,  # noqa: F401
    michigan,  # noqa: F401
    minnesota,  # noqa: F401
    mississippi,  # noqa: F401
    missouri,  # noqa: F401
    nebraska,  # noqa: F401
    nevada,  # noqa: F401
    new_jersey,  # noqa: F401
    new_york,  # noqa: F401
    no_tax,  # noqa: F401
    north_carolina,  # noqa: F401
    north_dakota,  # noqa: F401
    ohio,  # noqa: F401
    oklahoma,  # noqa: F401
    pennsylvania,  # noqa: F401
    south_carolina,  # noqa: F401
    texas,  # noqa: F401
    virginia,  # noqa: F401
    wisconsin,  # noqa: F401
    wyoming,  # noqa: F401
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
