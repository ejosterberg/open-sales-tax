# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Core engine: lookup, resolve, calculate.

The dependency arrow is one-directional:

    api -> core -> states + db.models

``core`` knows nothing about specific states; it iterates the
registry and queries the ORM. ``core`` knows nothing about HTTP;
endpoints in ``api/`` adapt its return values into responses.
"""

from opensalestax.core.calculate import (
    CalculatedLine,
    CalculationResult,
    JurisdictionResult,
    LineItem,
    calculate_tax,
)
from opensalestax.core.disclaimer import DISCLAIMER, disclaimer
from opensalestax.core.lookup import (
    lookup_jurisdictions_by_zip,
    lookup_jurisdictions_by_zip5_loose,
)
from opensalestax.core.resolve import (
    ResolvedRate,
    combined_rate_pct,
    resolve_rates_for_authorities,
)

__all__ = [
    "DISCLAIMER",
    "CalculatedLine",
    "CalculationResult",
    "JurisdictionResult",
    "LineItem",
    "ResolvedRate",
    "calculate_tax",
    "combined_rate_pct",
    "disclaimer",
    "lookup_jurisdictions_by_zip",
    "lookup_jurisdictions_by_zip5_loose",
    "resolve_rates_for_authorities",
]
