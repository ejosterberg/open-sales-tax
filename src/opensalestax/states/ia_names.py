# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Iowa special-district tax authorities.

IA's local sales tax is the 1% Local Option Sales Tax (LOST)
under Iowa Code chapter 423B; each county that adopts it
publishes a 98XXX-series jurisdiction code in the SST file.
Verified by ZIP probe against IA DOR's LOST adoption table
(2026-Q1).
"""

from __future__ import annotations

IA_DISTRICT_NAMES: dict[str, str] = {
    # iter-80: 98103 = Johnson County LOST. Verified by probing
    # Iowa City 52240 / Coralville 52241 -- the SST file DOES include
    # the Johnson Co LOST as code 98103 at 1.0% (initial assumption
    # that it was missing was wrong; the placeholder name was just
    # masking it). Adding the friendly name resolves Iowa City's
    # combined to 7.0% per IA DOR.
    "98103": "Johnson County Local Option Sales Tax",
    "98113": "Linn County Local Option Sales Tax",
    "98153": "Polk County Local Option Sales Tax",
    "98163": "Scott County Local Option Sales Tax",
}


def district_name(code: str) -> str | None:
    """Return the friendly IA district name for an SST code, or None."""
    return IA_DISTRICT_NAMES.get(code)


__all__ = ["IA_DISTRICT_NAMES", "district_name"]
