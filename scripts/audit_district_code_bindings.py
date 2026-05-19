# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Audit district-code → ZIP-prefix bindings from the raw SST boundary files.

iter-215 follow-up. For each state, scan the SST boundary CSV and
report which ZIP prefixes each district-type jurisdiction code
actually binds to. Cross-check those against the curated friendly
names in ``opensalestax.states.<state>_names`` to surface where a
name was hand-curated incorrectly.

Background
----------
iter-211 originally hypothesized a loader bug causing MN transit
districts to "leak" across county boundaries. iter-215 disproved
that by inspecting the source CSV directly: the loader is fine, but
``mn_names.py`` maps code 80001 to "Cook County Transportation Sales
Tax" while the SST file actually binds 80001 only to 563xx ZIPs
(Stearns/Benton — the St. Cloud area). The label is wrong; the
binding is correct. Likely affects 80003 / 80005 / 80011 too, plus
analogous codes in ``ia_names.py`` and ``nc_names.py``.

This script generates an auditable map so a maintainer can:

1. See each named district code's actual ZIP-prefix range from the
   live SST quarterly file (so they can guess the right name).
2. Compare to the hand-curated friendly name and flag mismatches.

Usage
-----
Run inside the production container (the SST zip files live there)::

    docker exec open-sales-tax-api-1 python -m \
        opensalestax.scripts.audit_district_code_bindings \
        --state MN

Or pass an explicit zip path::

    python scripts/audit_district_code_bindings.py \
        --zip /path/to/MNB2026Q2FEB18.zip --state MN

Output is plain text -- one row per district code with the
prefixes and any name discrepancy noted. Pipe to a file if you
want to diff future quarterly drops against today's.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

DATA_DIR_DEFAULT = Path("/var/lib/opensalestax/data")

# Per-state district-code-prefix ranges to scan. Each state's SST file
# may use different code spans for its special districts.
DISTRICT_CODE_PREFIXES: dict[str, tuple[str, ...]] = {
    "MN": ("80",),  # MN district codes are 80xxx
    "IA": ("98",),  # IA Local Option Sales Tax codes are 98xxx
    "NC": ("99",),  # NC has 99xxx transit/special codes (heuristic)
    "TN": ("99",),  # TN single-art reservation codes are 99xxx
    "WI": ("90",),  # WI premier-resort area district codes
    "AR": ("99",),  # AR special-purpose districts
    "OK": ("98",),  # OK has 98xxx city-level composite remote codes
}


def find_zip_for_state(data_dir: Path, state: str) -> Path | None:
    """Find the most recent SST boundary file for a state."""
    pattern = f"{state}B*.zip"
    matches = sorted(data_dir.glob(pattern))
    return matches[-1] if matches else None


def _row_active_on(cols: list[str], as_of: dt.date) -> bool:
    """Return True if the SST boundary row is effective on the given date."""
    eff_from_raw = cols[1] if len(cols) > 1 else ""
    eff_to_raw = cols[2] if len(cols) > 2 else ""
    if not eff_from_raw:
        return True
    try:
        eff_from = dt.date(int(eff_from_raw[:4]), int(eff_from_raw[4:6]), int(eff_from_raw[6:8]))
    except (ValueError, IndexError):
        return True
    if eff_from > as_of:
        return False
    if eff_to_raw and eff_to_raw != "29991231":
        try:
            eff_to = dt.date(int(eff_to_raw[:4]), int(eff_to_raw[4:6]), int(eff_to_raw[6:8]))
            if eff_to < as_of:
                return False
        except (ValueError, IndexError):
            pass
    return True


def scan_bindings(
    zip_path: Path,
    code_prefixes: tuple[str, ...],
    as_of: dt.date | None = None,
) -> dict[str, set[str]]:
    """Scan an SST boundary CSV and yield code -> set of 3-digit ZIP prefixes.

    Filters out historically-expired rows by default (mirrors the
    loader's ``_record_active_on`` behavior). Pass ``as_of`` to scan
    a different snapshot date.
    """
    target = as_of or dt.date.today()
    code_to_prefixes: dict[str, set[str]] = defaultdict(set)
    with zipfile.ZipFile(zip_path) as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as f:
            for raw in f:
                line = raw.decode("latin-1").rstrip()
                cols = line.split(",")
                if len(cols) < 35:
                    continue
                if not _row_active_on(cols, target):
                    continue
                zip5 = cols[17]
                if len(zip5) < 3:
                    continue
                prefix = zip5[:3]
                # Each row can carry MULTIPLE district codes in
                # repeating triplets starting at col 29 with stride 3:
                # (intra_state_class, jurisdiction_code, jurisdiction_type).
                # iter-218 fix: prior versions only checked cols[30] (the
                # first triplet), missing codes that appear in later
                # triplet positions. The MN parser handles all triplets;
                # the audit must mirror that to be accurate.
                for start in range(29, len(cols) - 2, 3):
                    code = cols[start + 1]
                    type_ = cols[start + 2] if (start + 2) < len(cols) else ""
                    if not code:
                        continue
                    # Skip type-45 (state location-reference codes)
                    # to match the loader's filter.
                    if type_ == "45":
                        continue
                    if not any(code.startswith(p) for p in code_prefixes):
                        continue
                    code_to_prefixes[code].add(prefix)
    return code_to_prefixes


def load_friendly_names(state: str) -> dict[str, str]:
    """Return the curated district friendly-name dict from <state>_names.py."""
    state_l = state.lower()
    module_candidates = [
        f"opensalestax.states.{state_l}_names",
    ]
    for modname in module_candidates:
        try:
            mod = importlib.import_module(modname)
        except ImportError:
            continue
        for attr in (f"{state}_DISTRICT_NAMES", "DISTRICT_NAMES"):
            if hasattr(mod, attr):
                return getattr(mod, attr)
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, help="State postal abbreviation (e.g. MN)")
    parser.add_argument(
        "--zip",
        type=Path,
        default=None,
        help="Path to SST boundary zip. If omitted, looks in /var/lib/opensalestax/data/",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR_DEFAULT,
        help=f"Data dir to search for SST zip (default {DATA_DIR_DEFAULT})",
    )
    args = parser.parse_args()

    state = args.state.upper()
    code_prefixes = DISTRICT_CODE_PREFIXES.get(state)
    if not code_prefixes:
        print(f"No district-code prefix registered for {state}.", file=sys.stderr)
        print(
            "Add an entry to DISTRICT_CODE_PREFIXES in this script.",
            file=sys.stderr,
        )
        return 2

    zip_path = args.zip or find_zip_for_state(args.data_dir, state)
    if not zip_path or not zip_path.exists():
        print(f"No SST boundary zip found for {state} in {args.data_dir}", file=sys.stderr)
        return 1

    print(f"Scanning {zip_path} for {state} district-code bindings...")
    bindings = scan_bindings(zip_path, code_prefixes)
    names = load_friendly_names(state)

    if not bindings:
        print(f"No district codes matching {code_prefixes} found in {zip_path}.")
        return 0

    print(f"\n{'code':<8}{'ZIP prefixes':<28}{'curated name':<60}{'flag'}")
    print("-" * 110)
    for code in sorted(bindings):
        prefixes = sorted(bindings[code])
        name = names.get(code, "(unlabelled)")
        flag = ""
        # Heuristic flag: if the curated name references a county/city
        # name not in the obvious ZIP-prefix range, surface it for review.
        if name != "(unlabelled)":
            # Crude heuristic: a name containing "<X> County" should
            # bind to that county's typical prefix span. Right now we
            # just print the data and let the auditor judge.
            pass
        print(f"{code:<8}{','.join(prefixes):<28}{name[:58]:<60}{flag}")
    print(f"\nTotal: {len(bindings)} district codes scanned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
