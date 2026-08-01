# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Regenerate src/opensalestax/data/zip_county_dominant.py.

Companion to ``regen_zip_county.py``. Where :data:`ZIP_COUNTY` records
**every** county a ZIP intersects, this emits the single **dominant**
county per (ZIP, state) -- the one holding the largest share of the
ZIP's land area, per the Census ``AREALAND_PART`` column.

Why this exists
---------------
Self-seeded (non-SST) state modules bind at most one county per ZIP.
Until 2026-08-01 they resolved a straddling ZIP by taking "the first
county in FIPS-sorted order", an arbitrary tiebreak unrelated to where
the ZIP's addresses actually are. That mis-assigned the county rate for
**617 ZIPs across 7 states**; e.g. ZIP 35040 (Calera, AL) bound Chilton
County 3.000% when Calera is in Shelby County 1.000%, over-collecting
the county component by 2.00pp.

The area-majority rule used here is the same one the cross-state ZCTA
dedup already applies to pick a ZIP's canonical *state*
(``zcta_loader.parse_zcta_states``); this extends it state -> county.

Land area is a proxy for "where the addresses are", not a perfect one --
a ZIP whose population clusters in a small dense sliver of county A but
whose acreage is mostly rural county B will still pick B. Census
publishes no population-part column in this relationship file, so area
is the best available signal from the primary source. Modules may still
override per-ZIP where a hand-curated city anchor is known; the anchor
takes precedence over this map.

Usage:

    poetry run python scripts/regen_zip_county_dominant.py

The Census file (~6.6 MB, public domain) is fetched once and cached at
``$OPENSALESTAX_DATA_DIR/tab20_zcta520_county20_natl.txt`` (defaults to
``~/.opensalestax/data/``). Re-run after the 2030 decennial
relationship file is published.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opensalestax.data.state_fips import FIPS_TO_ABBREV  # noqa: E402

CENSUS_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
    "tab20_zcta520_county20_natl.txt"
)
CENSUS_FILENAME = "tab20_zcta520_county20_natl.txt"
TARGET = ROOT / "src" / "opensalestax" / "data" / "zip_county_dominant.py"

# Pipe-delimited layout, 0-indexed. Mirrors zcta_loader's constants.
_COL_GEOID_ZCTA = 1
_COL_GEOID_COUNTY = 9
_COL_AREALAND_PART = 16


def _cache_dir() -> Path:
    env = os.environ.get("OPENSALESTAX_DATA_DIR")
    return Path(env) if env else Path.home() / ".opensalestax" / "data"


def load_source() -> str:
    """Return the Census file text, fetching + caching it if needed."""
    cached = _cache_dir() / CENSUS_FILENAME
    if cached.is_file():
        print(f"using cached {cached}")
        return cached.read_text(encoding="utf-8-sig")
    print(f"fetching {CENSUS_URL} ...")
    with urlopen(CENSUS_URL, timeout=120) as resp:  # noqa: S310 - hard-coded URL
        text = resp.read().decode("utf-8-sig")
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_text(text, encoding="utf-8")
    print(f"cached to {cached}")
    return text


def build(text: str) -> dict[tuple[str, str], str]:
    """Return {(zip5, state_abbrev): dominant county FIPS}."""
    # Sum land area per (zip, state, county). One Census row per
    # (ZCTA, county) intersection; a ZIP can appear many times.
    area: dict[tuple[str, str, str], int] = {}
    for i, line in enumerate(text.splitlines()):
        if i == 0:  # header
            continue
        cols = line.rstrip("\r\n").split("|")
        if len(cols) <= _COL_AREALAND_PART:
            continue
        zip5 = cols[_COL_GEOID_ZCTA].strip()
        county_geoid = cols[_COL_GEOID_COUNTY].strip()
        if not zip5 or len(county_geoid) != 5 or not county_geoid.isdigit():
            continue
        abbrev = FIPS_TO_ABBREV.get(county_geoid[:2])
        if abbrev is None:
            continue
        try:
            part = int(cols[_COL_AREALAND_PART].strip() or "0")
        except ValueError:
            part = 0
        key = (zip5, abbrev, county_geoid[2:])
        # +1 so a zero-area (water-only) intersection still registers as
        # presence when every candidate is zero.
        area[key] = area.get(key, 0) + part + 1

    # Pick the max-area county per (zip, state). Iterating in sorted
    # order and using a strict > comparison means ties resolve to the
    # lowest FIPS -- deterministic, and only reachable when two counties
    # hold byte-identical land area, which is effectively never.
    best: dict[tuple[str, str], tuple[int, str]] = {}
    for (zip5, abbrev, county_fips), total in sorted(area.items()):
        key = (zip5, abbrev)
        current = best.get(key)
        if current is None or total > current[0]:
            best[key] = (total, county_fips)
    return {k: v[1] for k, v in best.items()}


def main() -> None:
    dominant = build(load_source())
    multi_state = len({z for z, _ in dominant})
    print(f"{len(dominant)} (zip, state) pairs across {multi_state} ZIPs")

    out = [
        "# SPDX-License-Identifier: Apache-2.0",
        "# Copyright 2026 Eric Osterberg and OpenSalesTax contributors",
        '"""Dominant (land-area majority) county per ZIP (Census ZCTA 2020).',
        "",
        "Generated by scripts/regen_zip_county_dominant.py from the Census",
        "Bureau ZCTA->County 2020 relationship file (public domain). DO NOT",
        "EDIT BY HAND -- re-run the generator instead.",
        "",
        "Companion to :data:`opensalestax.data.zip_county.ZIP_COUNTY`, which",
        "records EVERY county a ZIP intersects. This records the ONE county",
        "holding the largest share of the ZIP's land area, so a module that",
        "can bind only a single county per ZIP has a principled answer",
        "instead of an arbitrary FIPS-order tiebreak.",
        "",
        "See :func:`opensalestax.data.zip_county_dominant.dominant_county`",
        "for the accessor state modules should call.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "# Key: (5-digit ZIP, state abbrev). Value: 3-digit county FIPS,",
        "# matching the keys in opensalestax.data.county_names.COUNTY_NAMES.",
        "ZIP_COUNTY_DOMINANT: dict[tuple[str, str], str] = {",
    ]
    for (zip5, abbrev), county_fips in sorted(dominant.items()):
        out.append(f'    ("{zip5}", "{abbrev}"): "{county_fips}",')
    out.append("}")
    out.append("")
    out.append(
        '''

def dominant_county(zip5: str, state_abbrev: str) -> str | None:
    """Return the land-area-majority county FIPS for ``zip5`` in a state.

    Returns ``None`` when Census records no intersection for that
    (ZIP, state) pair -- callers should fall back to their own
    candidate ordering in that case.
    """
    return ZIP_COUNTY_DOMINANT.get((zip5, state_abbrev))
'''.strip()
    )
    out.append("")
    TARGET.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
