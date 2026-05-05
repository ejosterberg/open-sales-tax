# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Fetch + cache Streamlined Sales Tax (SST) quarterly data files.

SST publishes per-state rate and boundary files at:

- https://www.streamlinedsalestax.org/ratesandboundry/Rates/
- https://www.streamlinedsalestax.org/ratesandboundry/Boundary/

Filenames follow the pattern
``<STATE><R|B><YEAR>Q<QUARTER><MONTH><DAY>.<csv|zip>``,
e.g. ``MNR2026Q2FEB18.zip``. The publication date in the filename
pins to a specific upstream version per constitution §6
(reproducibility).

This module:

- Downloads SST files via httpx (sync + async helpers)
- Verifies the SHA-256 hash against an optional expected value
- Caches into ``OPENSALESTAX_DATA_DIR`` (default ``~/.opensalestax/data``)
- Extracts ZIP archives transparently (yields the contained CSV)

It does NOT parse the file contents; that's :mod:`.sst_parser`'s job.
"""

from __future__ import annotations

import hashlib
import os
import re
import zipfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import httpx

SST_RATES_URL = "https://www.streamlinedsalestax.org/ratesandboundry/Rates/"
SST_BOUNDARY_URL = "https://www.streamlinedsalestax.org/ratesandboundry/Boundary/"

# Match SST quarterly filename pattern. SST sometimes publishes
# single-digit days (INR2008Q4MAY7.csv, WYR2026Q2APR1.csv) so the
# day is 1-2 digits, not strictly 2.
_SST_FILENAME_RE = re.compile(
    r"^(?P<state>[A-Z]{2})"
    r"(?P<kind>[RB])"
    r"(?P<year>\d{4})"
    r"Q(?P<quarter>[1-4])"
    r"(?P<month>[A-Z]{3})"
    r"(?P<day>\d{1,2})"
    r"\.(?P<ext>csv|zip)$",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class SstFilename:
    """Parsed components of an SST filename."""

    state: str
    kind: str  # 'R' for rates, 'B' for boundary
    year: int
    quarter: int
    month: str
    day: int
    ext: str

    @classmethod
    def parse(cls, filename: str) -> SstFilename:
        """Parse an SST filename, raising ValueError on malformed input."""
        m = _SST_FILENAME_RE.match(filename)
        if not m:
            raise ValueError(f"not a valid SST filename: {filename!r}")
        return cls(
            state=m.group("state").upper(),
            kind=m.group("kind").upper(),
            year=int(m.group("year")),
            quarter=int(m.group("quarter")),
            month=m.group("month").upper(),
            day=int(m.group("day")),
            ext=m.group("ext").lower(),
        )

    @property
    def version_label(self) -> str:
        """Return a deterministic version label, e.g. 'MN-SST-2026Q2FEB18'."""
        return f"{self.state}-SST-{self.year}Q{self.quarter}{self.month}{self.day:02d}"


def default_data_dir() -> Path:
    """Directory used to cache downloaded SST files.

    Override via ``OPENSALESTAX_DATA_DIR``. Default is
    ``~/.opensalestax/data`` (Linux/macOS) or
    ``%USERPROFILE%/.opensalestax/data`` (Windows).
    """
    override = os.environ.get("OPENSALESTAX_DATA_DIR")
    if override:
        return Path(override)
    return Path.home() / ".opensalestax" / "data"


def file_url(filename: str) -> str:
    """Build the full SST URL for a given filename.

    Routes to the rates or boundary directory based on the filename's
    kind component.
    """
    parsed = SstFilename.parse(filename)
    base = SST_RATES_URL if parsed.kind == "R" else SST_BOUNDARY_URL
    return base + filename


def download_sst_file(
    filename: str,
    dest_dir: Path | None = None,
    expected_sha256: str | None = None,
    *,
    timeout: float = 30.0,
) -> Path:
    """Download an SST file, cache it, and return the local path.

    If the file already exists in the cache and its SHA-256 matches
    ``expected_sha256`` (when provided), the download is skipped.

    SST publishes some states' files as ``.csv`` and others as
    ``.zip`` (and individual states migrate between formats over
    time). When the requested extension returns 404, retry with
    the alternate extension and -- if that succeeds -- cache the
    downloaded file under whichever extension actually exists
    upstream.

    Raises :class:`httpx.HTTPError` on non-recoverable transport
    failures and :class:`ValueError` on a hash mismatch.
    """
    parsed = SstFilename.parse(filename)
    target_dir = dest_dir or default_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    candidate_filenames: list[str] = [filename]
    alt_ext = "zip" if parsed.ext == "csv" else "csv"
    alt_filename = filename[: -len(parsed.ext)] + alt_ext
    candidate_filenames.append(alt_filename)

    # Cache hit short-circuit -- check both extensions for an
    # existing successful download.
    for candidate in candidate_filenames:
        cached = target_dir / candidate
        if cached.exists() and (
            expected_sha256 is None or _sha256(cached) == expected_sha256.lower()
        ):
            return cached

    last_error: httpx.HTTPStatusError | None = None
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for candidate in candidate_filenames:
            url = file_url(candidate)
            response = client.get(url)
            if response.status_code == 404:
                last_error = httpx.HTTPStatusError(
                    f"404 for {url}", request=response.request, response=response
                )
                continue
            response.raise_for_status()
            target_path = target_dir / candidate
            target_path.write_bytes(response.content)
            if expected_sha256 is not None:
                actual = _sha256(target_path)
                if actual != expected_sha256.lower():
                    target_path.unlink(missing_ok=True)
                    msg = (
                        f"SHA-256 mismatch for {candidate}: "
                        f"expected {expected_sha256}, got {actual}"
                    )
                    raise ValueError(msg)
            return target_path

    assert last_error is not None
    raise last_error


def open_sst_csv(path: Path) -> Iterator[str]:
    """Yield text lines from an SST file (CSV or ZIP-wrapped CSV).

    Handles both the .csv and .zip variants of SST publications.
    For ZIP files containing exactly one CSV, that CSV is yielded
    transparently. Raises :class:`ValueError` if the ZIP contains
    multiple files (shouldn't happen for SST data; defensive).
    """
    # ``utf-8-sig`` transparently strips the UTF-8 BOM (``﻿``)
    # if present. VT's quarterly files (e.g. ``VTB2026Q2FEB20.csv``)
    # ship with a BOM that would otherwise prefix the first row's
    # record-type column, turning ``A`` into ``﻿A`` and causing
    # the boundary parser to reject the entire first record. Without
    # this fix, VT loaded zero boundary rows and Burlington 05401
    # silently fell back to the state-only 6% rate.
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            yield from fh
        return

    if path.suffix.lower() != ".zip":
        raise ValueError(f"unsupported SST file extension: {path}")

    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError(f"expected exactly one CSV inside {path.name}, found {names}")
        with zf.open(names[0]) as fh:
            first = True
            for raw_line in fh:
                line = raw_line.decode("utf-8", errors="replace")
                if first:
                    # Same BOM-strip semantics as the CSV branch
                    # above, since reading from inside a zipfile
                    # bypasses Python's encoding= machinery.
                    line = line.lstrip("﻿")
                    first = False
                yield line


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file (used for cache verification)."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()
