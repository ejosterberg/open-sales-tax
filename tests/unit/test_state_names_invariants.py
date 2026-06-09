# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Cross-check `<state>_names.py` district-code mappings against
known structural invariants.

Several states' SST jurisdiction codes follow a deterministic
"prefix + last 3 of county FIPS" scheme that maps each code to
a specific county:

- **IA**: 98XXX where XXX is the last 3 digits of the county
  FIPS code. Source: revenue.iowa.gov/taxes/tax-guidance/sales-
  use-excise-tax/streamlined-sales-tax. Example: 98103 -> FIPS
  19103 -> Johnson County.
- **NC**: 99XXX where XXX is the last 3 digits of the county
  FIPS code. Source: NCDOR's "North Carolina Information for
  Streamlined Sales Tax Participants" page. Example: 99063 ->
  FIPS 37063 -> Durham County.

These structural invariants are what the iter-80 / iter-83
hand-curated tables were SUPPOSED to follow but didn't:

- iter-221 caught an off-by-one in ia_names.py (98175 was
  labelled "Taylor County" but FIPS 19175 = Union; 98181 was
  "Union" but FIPS 19181 = Warren).
- iter-221 also caught nc_names.py's duplicate "Durham" label
  on both 99055 and 99063 -- under the FIPS pattern 99055 maps
  to Dare County, not Durham.

This test re-runs that check at every CI run so the next time
someone hand-edits a code mapping, a typo or swap is caught
immediately rather than surfacing months later as a mysterious
"wrong jurisdiction returned for this ZIP."

States NOT covered by this test:
- MN (80XXX codes are state-assigned, not FIPS-derived -- the
  authoritative mapping is MN DOR's xlsx, which is what iter-220
  consulted).
- States whose <state>_names.py contains only city/place codes
  (most states; the test only matches *_DISTRICT_NAMES dicts).
"""

from __future__ import annotations

import re

import pytest

from opensalestax.data.county_names import county_name

# (state_abbrev, sst_code_prefix, expected_label_template_regex)
# The regex captures the county name in the friendly label so the
# test can compare against the FIPS lookup. The regex is intentionally
# loose: any of the published label suffixes ("Local Option Sales Tax",
# "Public Transportation Tax", "Public Transportation Sales Tax",
# "Local Option", etc.) should match.
FIPS_DERIVED_CODE_INVARIANTS = [
    # IA: 98XXX where XXX is last 3 of county FIPS code 19XXX.
    (
        "IA",
        "98",
        re.compile(r"^(?P<county>.+?) County\s+Local Option", re.IGNORECASE),
    ),
    # NC: 99XXX where XXX is last 3 of county FIPS code 37XXX.
    (
        "NC",
        "99",
        re.compile(r"^(?P<county>.+?) County\s+Public Transportation", re.IGNORECASE),
    ),
]


def _load_dict(state_abbrev: str) -> dict[str, str]:
    """Import <state>_names.py for `state_abbrev` and return its district dict."""
    module_name = f"opensalestax.states.{state_abbrev.lower()}_names"
    try:
        mod = __import__(module_name, fromlist=["*"])
    except ImportError:
        return {}
    for attr in (f"{state_abbrev}_DISTRICT_NAMES", "DISTRICT_NAMES"):
        if hasattr(mod, attr):
            return getattr(mod, attr)
    return {}


@pytest.mark.parametrize(
    "state_abbrev,code_prefix,county_pattern",
    FIPS_DERIVED_CODE_INVARIANTS,
    ids=[f"{r[0]}-{r[1]}xxx" for r in FIPS_DERIVED_CODE_INVARIANTS],
)
def test_fips_derived_codes_match_county_name(
    state_abbrev: str,
    code_prefix: str,
    county_pattern: re.Pattern[str],
) -> None:
    """Each SST code starting with `code_prefix` whose remaining 3 digits
    match a real county FIPS code must label that county correctly."""
    district_map = _load_dict(state_abbrev)
    if not district_map:
        pytest.skip(f"no district dict for {state_abbrev}")

    mismatches: list[str] = []
    for code, label in district_map.items():
        # Only check codes that fit the "prefix + 3 digits" shape.
        if not code.startswith(code_prefix) or len(code) != 5:
            continue
        fips_suffix = code[len(code_prefix) :]
        if not fips_suffix.isdigit():
            continue
        expected_county = county_name(state_abbrev, fips_suffix)
        if expected_county is None:
            # Code's suffix isn't a real county FIPS; skip (could be
            # a multi-county-city district like IA 98201+).
            continue
        match = county_pattern.match(label)
        if not match:
            mismatches.append(
                f"  {code} = {label!r}: label does not match the expected "
                f"'<County> County <tax type>' shape -- can't verify"
            )
            continue
        labelled_county = match.group("county")
        # county_name returns e.g. "Union County"; strip the suffix.
        expected_county_short = expected_county.removesuffix(" County")
        if labelled_county.lower() != expected_county_short.lower():
            mismatches.append(
                f"  {code} = {label!r}: claims '{labelled_county} County' "
                f"but FIPS {fips_suffix} in {state_abbrev} = '{expected_county}'"
            )

    if mismatches:
        msg = (
            f"{state_abbrev} district codes ({code_prefix}XXX) have label mismatches "
            f"against the county FIPS table:\n" + "\n".join(mismatches)
        )
        pytest.fail(msg)
