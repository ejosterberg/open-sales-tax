# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Iowa special-district tax authorities.

IA's local sales tax is the 1% Local Option Sales Tax (LOST)
under Iowa Code chapter 423B; each county that adopts it
publishes a 98XXX-series jurisdiction code in the SST file.

Authoritative semantics (verified by deep-research iter-221,
sourced from
https://revenue.iowa.gov/taxes/tax-guidance/sales-use-excise-tax/streamlined-sales-tax
):

  98 + <3-digit county FIPS> identifies the unincorporated area
  of that county. Codes beginning at 98201 are reserved for the
  102 multi-county-city special tax districts (45 IA cities
  span two counties, 4 span three counties; 45*2 + 4*3 = 102).

  Note: the 98XXX code is a GEOGRAPHIC district identifier, not
  a tax-type assertion. Whether LOST is actively collected in
  that geographic area is a separate per-jurisdiction fact from
  the SST rate table. The "Local Option Sales Tax" suffix on
  each label below describes what is in fact collected there
  per IA DOR's current rate publication; it does not assert
  that EVERY 98XXX code represents an active LOST.

iter-221 fix (2026-05-19): the iter-80/81 hand-curated entries
for 98175 and 98181 were off-by-one against the FIPS table.
98175 is FIPS 19175 = Union County (not Taylor County); 98181
is FIPS 19181 = Warren County (not Union County); Taylor County
is 98173 (FIPS 19173 -- was missing from the table entirely).
"""

from __future__ import annotations

IA_DISTRICT_NAMES: dict[str, str] = {
    # IA SST district codes 98XXX = 98 + 3-digit county FIPS code.
    # Source: revenue.iowa.gov/taxes/tax-guidance/sales-use-excise-tax/streamlined-sales-tax
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
    "98173": "Taylor County Local Option Sales Tax",  # iter-221: missing in iter-80
    "98175": "Union County Local Option Sales Tax",  # iter-221: was wrongly "Taylor"
    "98181": "Warren County Local Option Sales Tax",  # iter-221: was wrongly "Union"
    "98193": "Woodbury County Local Option Sales Tax",
    # NOTE: codes 98201+ are the 102 multi-county-city special tax
    # districts per IA DOR. The line-item code -> city-county-pair
    # mapping is NOT published by IA DOR in tabular form -- needs
    # either a direct request to IA DOR or reverse-engineering
    # from the SST boundary file's ZIP-binding patterns.
}


def district_name(code: str) -> str | None:
    """Return the friendly IA district name for an SST code, or None."""
    return IA_DISTRICT_NAMES.get(code)


__all__ = ["IA_DISTRICT_NAMES", "district_name"]
