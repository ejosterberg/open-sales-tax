# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Read the SST directory listings to see what is published *right now*.

Why this exists
---------------
SST hosts exactly **one file per state per kind** -- the current one.
When a state publishes a new quarter, the previous file is *removed*
from the server. A pinned filename is therefore a record of what a
build used, not a permanent address: it stops resolving the moment the
state republishes.

On 2026-09-16 that had quietly happened to **18 of the 24** pins in
``.github/workflows/build-data-dump.yml``. Every dump rebuild failed,
and the next release tag would have failed too -- the first sign was a
bare ``HTTPStatusError: 404`` fifteen minutes into a build.

The structural consequence is what makes this checkable: because
upstream keeps exactly one file per (state, kind), **"pin differs from
upstream" and "pin is dead" are the same condition.** There is no third
state to disambiguate, so a drift check needs no age heuristic and no
allowlist. States SST simply never republished (IN 2008, KY 2012,
MI 2023, NJ 2018, NV 2025, RI 2019) still match the only file upstream,
so they report clean -- an age-based check would have wrongly flagged
every one of them.

What this module does NOT do
----------------------------
It reads. It never adopts. Constitution §11 requires data updates to be
explicit operations rather than a silent background poll, and a release
that auto-bumped to an unreviewed quarter could ship a wrong rate as
easily as fix one -- the daily audit has found upstream drift in *both*
directions, including over-collections. Discovery is a read; adoption
is a commit a human makes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

import httpx

from opensalestax.data.sst import SST_BOUNDARY_URL, SST_RATES_URL, SstFilename

#: Directory listing per kind. 'R' = rates, 'B' = boundary.
LISTING_URLS = {"R": SST_RATES_URL, "B": SST_BOUNDARY_URL}

#: Any href that looks like a data file. Deliberately loose -- each
#: candidate is then validated by :meth:`SstFilename.parse`, which owns
#: the real grammar (including single-digit days and mixed case).
_HREF_RE = re.compile(r'href="([^"]+\.(?:csv|zip))"', re.IGNORECASE)


class SstIndexError(Exception):
    """Raised when a listing cannot be fetched or understood."""


@dataclass(frozen=True, slots=True)
class UpstreamFile:
    """One file currently published in an SST directory listing."""

    state: str
    kind: str
    version: str
    filename: str

    @property
    def url(self) -> str:
        return LISTING_URLS[self.kind] + self.filename


def version_of(filename: str) -> str:
    """Return the pin string embedded in an SST filename.

    The pin is the filename's stem minus the two-letter state and the
    one-letter kind: ``ARR2026Q4AUG28.csv`` -> ``2026Q4AUG28``.

    Taken as a raw substring rather than rebuilt from parsed parts,
    because the pins must round-trip byte-for-byte: SST publishes
    single-digit days (``INR2008Q4MAY7``, ``WYR2026Q2APR1``) that a
    zero-padded reconstruction would silently rewrite to ``MAY07``.
    """
    return PurePosixPath(filename).stem[3:]


def versions_match(pinned: str, upstream: str) -> bool:
    """Compare two pin strings the way the server does.

    Case-insensitive: SST's own casing is inconsistent
    (``KYR2012Q4Aug13.csv`` is mixed case, ``WYR2026Q4AUG20.CSV`` is
    upper) and the host is IIS, which serves either spelling. Treating
    a case difference as drift would produce a permanent false alarm.
    """
    return pinned.strip().upper() == upstream.strip().upper()


def parse_listing(html: str, kind: str) -> dict[str, UpstreamFile]:
    """Extract ``{state: UpstreamFile}`` from a directory listing.

    Hrefs that don't parse as SST filenames are ignored rather than
    raising -- the listing also contains a "[To Parent Directory]"
    link, and tolerating unknown entries means a cosmetic change to
    the page doesn't break the check.
    """
    found: dict[str, UpstreamFile] = {}
    for href in _HREF_RE.findall(html):
        name = PurePosixPath(href).name
        try:
            parsed = SstFilename.parse(name)
        except ValueError:
            continue
        if parsed.kind != kind:
            continue
        found[parsed.state] = UpstreamFile(
            state=parsed.state,
            kind=parsed.kind,
            version=version_of(name),
            filename=name,
        )
    return found


def fetch_listing(
    kind: str,
    *,
    http_client_factory=None,
    timeout: float = 30.0,
) -> dict[str, UpstreamFile]:
    """Fetch and parse one directory listing.

    ``http_client_factory`` is a test seam; production callers leave it
    ``None``. Raises :class:`SstIndexError` on a network failure or a
    listing that yields nothing parseable -- the latter usually means
    SST disabled directory browsing, which is a different problem from
    a dead pin and deserves a different exit code.
    """
    if kind not in LISTING_URLS:
        raise SstIndexError(f"unknown kind {kind!r}: expected 'R' or 'B'")

    factory = http_client_factory or (lambda: httpx.Client(timeout=timeout, follow_redirects=True))
    url = LISTING_URLS[kind]
    try:
        with factory() as client:
            response = client.get(url)
            response.raise_for_status()
            html = response.text
    except httpx.HTTPError as exc:
        raise SstIndexError(f"could not fetch {url}: {exc}") from exc

    listing = parse_listing(html, kind)
    if not listing:
        raise SstIndexError(
            f"{url} returned no recognizable SST filenames. Directory "
            f"browsing may be disabled upstream, or the page shape changed."
        )
    return listing


__all__ = [
    "LISTING_URLS",
    "SstIndexError",
    "UpstreamFile",
    "fetch_listing",
    "parse_listing",
    "version_of",
    "versions_match",
]
