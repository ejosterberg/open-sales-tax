# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""SST data acquisition and parsing.

- :mod:`.sst` -- fetcher and cache for upstream SST CSV/ZIP files
- :mod:`.sst_parser` -- generic CSV row parser yielding raw records
"""

from opensalestax.data.sst import (
    SstFilename,
    default_data_dir,
    download_sst_file,
    file_url,
    open_sst_csv,
)
from opensalestax.data.sst_parser import (
    BOUNDARY_COLUMNS,
    NO_END_DATE,
    RATES_COLUMNS,
    SstBoundaryRecord,
    SstRateRecord,
    active_only,
    parse_boundary_csv,
    parse_rates_csv,
)

__all__ = [
    "BOUNDARY_COLUMNS",
    "NO_END_DATE",
    "RATES_COLUMNS",
    "SstBoundaryRecord",
    "SstFilename",
    "SstRateRecord",
    "active_only",
    "default_data_dir",
    "download_sst_file",
    "file_url",
    "open_sst_csv",
    "parse_boundary_csv",
    "parse_rates_csv",
]
