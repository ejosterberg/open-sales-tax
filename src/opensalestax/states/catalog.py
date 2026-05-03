# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Static catalog of all 52 US tax jurisdictions (50 states + DC + PR).

Used by the ``/v1/states`` endpoint to report coverage for every
jurisdiction whether or not it has a state module loaded. States
NOT in the registry are returned with ``tier=0``; states in the
registry override the ``has_sales_tax`` and ``sst_member`` flags
from their own metadata.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StateCatalogEntry:
    """Static facts about a US tax jurisdiction."""

    abbrev: str
    name: str
    has_sales_tax: bool
    sst_member: bool
    notes: str = ""


# All 50 states + DC + PR. Source: state DOR pages + SST membership list,
# cross-checked against specs/research/sovos-state-summary.md.
STATE_CATALOG: tuple[StateCatalogEntry, ...] = (
    StateCatalogEntry("AL", "Alabama", True, False),
    StateCatalogEntry(
        "AK", "Alaska", False, False, "Some boroughs/cities collect local tax via ARSSTC."
    ),
    StateCatalogEntry("AZ", "Arizona", True, False, "Transaction Privilege Tax model."),
    StateCatalogEntry("AR", "Arkansas", True, True),
    StateCatalogEntry("CA", "California", True, False),
    StateCatalogEntry("CO", "Colorado", True, False, "Home-rule cities self-administer."),
    StateCatalogEntry("CT", "Connecticut", True, False),
    StateCatalogEntry("DE", "Delaware", False, False),
    StateCatalogEntry("DC", "District of Columbia", True, False),
    StateCatalogEntry("FL", "Florida", True, False),
    StateCatalogEntry("GA", "Georgia", True, True),
    StateCatalogEntry("HI", "Hawaii", True, False, "General Excise Tax model."),
    StateCatalogEntry("ID", "Idaho", True, False),
    StateCatalogEntry("IL", "Illinois", True, False),
    StateCatalogEntry("IN", "Indiana", True, True),
    StateCatalogEntry("IA", "Iowa", True, True),
    StateCatalogEntry("KS", "Kansas", True, True),
    StateCatalogEntry("KY", "Kentucky", True, True),
    StateCatalogEntry("LA", "Louisiana", True, False, "Parishes self-administer."),
    StateCatalogEntry("ME", "Maine", True, False),
    StateCatalogEntry("MD", "Maryland", True, False),
    StateCatalogEntry("MA", "Massachusetts", True, False),
    StateCatalogEntry("MI", "Michigan", True, True),
    StateCatalogEntry("MN", "Minnesota", True, True),
    StateCatalogEntry("MS", "Mississippi", True, False),
    StateCatalogEntry("MO", "Missouri", True, False),
    StateCatalogEntry("MT", "Montana", False, False, "Some resort towns levy local taxes."),
    StateCatalogEntry("NE", "Nebraska", True, True),
    StateCatalogEntry("NV", "Nevada", True, True),
    StateCatalogEntry("NH", "New Hampshire", False, False),
    StateCatalogEntry("NJ", "New Jersey", True, True),
    StateCatalogEntry("NM", "New Mexico", True, False, "Gross Receipts Tax model."),
    StateCatalogEntry("NY", "New York", True, False),
    StateCatalogEntry("NC", "North Carolina", True, True),
    StateCatalogEntry("ND", "North Dakota", True, True),
    StateCatalogEntry("OH", "Ohio", True, True),
    StateCatalogEntry("OK", "Oklahoma", True, True),
    StateCatalogEntry("OR", "Oregon", False, False),
    StateCatalogEntry("PA", "Pennsylvania", True, False),
    StateCatalogEntry("PR", "Puerto Rico", True, False),
    StateCatalogEntry("RI", "Rhode Island", True, True),
    StateCatalogEntry("SC", "South Carolina", True, False),
    StateCatalogEntry("SD", "South Dakota", True, True),
    StateCatalogEntry("TN", "Tennessee", True, True, "SST associate member."),
    StateCatalogEntry("TX", "Texas", True, False),
    StateCatalogEntry("UT", "Utah", True, True),
    StateCatalogEntry("VT", "Vermont", True, True),
    StateCatalogEntry("VA", "Virginia", True, False),
    StateCatalogEntry("WA", "Washington", True, True),
    StateCatalogEntry("WV", "West Virginia", True, True),
    StateCatalogEntry("WI", "Wisconsin", True, True),
    StateCatalogEntry("WY", "Wyoming", True, True),
)


def get_catalog_entry(abbrev: str) -> StateCatalogEntry | None:
    """Look up a catalog entry by USPS abbreviation (case-insensitive)."""
    upper = abbrev.upper()
    for entry in STATE_CATALOG:
        if entry.abbrev == upper:
            return entry
    return None
