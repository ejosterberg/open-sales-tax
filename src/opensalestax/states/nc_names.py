# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for North Carolina special-district tax authorities.

NC's local tax stack is dominated by Article 39 (county base) +
Article 42 (county additional) + Article 46 (county transit).
The 99XXX type-79 codes encode the per-county Article 46 transit
half-percent (or 1% in some counties). Verified by ZIP probe +
rate cross-check against NC DOR's "Sales and Use Tax Rates -
Other Information" publication (2026-Q1).
"""

from __future__ import annotations

NC_DISTRICT_NAMES: dict[str, str] = {
    "99055": "Durham County Public Transportation Sales Tax",
    "99063": "Durham County Public Transportation Sales Tax",
    "99119": "Mecklenburg County Public Transportation Sales Tax",
    "99135": "Orange County Public Transportation Sales Tax",
    "99183": "Wake County Public Transportation Sales Tax",
}


def district_name(code: str) -> str | None:
    """Return the friendly NC district name for an SST code, or None."""
    return NC_DISTRICT_NAMES.get(code)


__all__ = ["NC_DISTRICT_NAMES", "district_name"]
