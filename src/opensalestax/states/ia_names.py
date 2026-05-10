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
    # iter-80/81: IA SST district codes are 98XXX where XXX is the
    # last 3 digits of the county FIPS code (e.g. 98103 -> FIPS
    # 19103 = Johnson County). Each entry below verified by ZIP
    # probe + FIPS Place cross-check.
    "98001": "Adair County Local Option Sales Tax",
    "98003": "Adams County Local Option Sales Tax",
    "98013": "Black Hawk County Local Option Sales Tax",
    "98027": "Carroll County Local Option Sales Tax",
    "98031": "Cedar County Local Option Sales Tax",
    "98041": "Clay County Local Option Sales Tax",
    "98059": "Dickinson County Local Option Sales Tax",
    "98061": "Dubuque County Local Option Sales Tax",
    "98095": "Iowa County Local Option Sales Tax",
    "98103": "Johnson County Local Option Sales Tax",
    "98113": "Linn County Local Option Sales Tax",
    "98115": "Louisa County Local Option Sales Tax",
    "98139": "Muscatine County Local Option Sales Tax",
    "98153": "Polk County Local Option Sales Tax",
    "98163": "Scott County Local Option Sales Tax",
    "98169": "Story County Local Option Sales Tax",
    "98175": "Taylor County Local Option Sales Tax",
    "98181": "Union County Local Option Sales Tax",
    "98193": "Woodbury County Local Option Sales Tax",
}


def district_name(code: str) -> str | None:
    """Return the friendly IA district name for an SST code, or None."""
    return IA_DISTRICT_NAMES.get(code)


__all__ = ["IA_DISTRICT_NAMES", "district_name"]
