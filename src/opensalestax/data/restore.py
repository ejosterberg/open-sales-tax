# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Restore a pre-loaded PostgreSQL data dump from a GitHub release.

The companion to `.github/workflows/build-data-dump.yml`, which builds a
data-only ``opensalestax-dump-<tag>-postgres.sql.gz`` per release tag and
attaches it as a release asset. New users can ``opensalestax data restore``
to be live in under two minutes instead of running the ~50-minute manual
``data fetch`` + ``data load`` loop across all 24 SST states + AZ.

Design notes:

- All pure-Python helpers (URL construction, schema-version parsing,
  validation) live here so they're trivially unit-testable without a DB
  or network. The CLI in :mod:`opensalestax.cli.main` is a thin wrapper.
- We pipe the gzipped dump through ``psql`` rather than reimplement the
  pg_dump COPY protocol in Python -- portable, fast, and obvious.
- The dump is data-only; the consumer's ``alembic_version`` row stays
  pinned to whatever ``alembic upgrade head`` produced. We refuse to
  apply a dump whose own pin doesn't match (i.e. the dump was built
  against a different schema head than the one the consumer ran).
- MariaDB is not supported as a restore target: the dump is PostgreSQL
  COPY format. MariaDB users get a clear "use the manual load path"
  message and a non-zero exit (so CI scripts catch it).
"""

from __future__ import annotations

import gzip
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import IO, cast
from urllib.parse import urlsplit

import httpx

#: GitHub repo coordinates for the release assets. Hardcoded because the
#: dump is published from this repo's own CI; if the repo ever moves, the
#: dump publication moves with it and this constant updates in lockstep.
GITHUB_OWNER = "ejosterberg"
GITHUB_REPO = "open-sales-tax"

#: Filename pattern for the dump asset attached to each release.
#: Mirrors the workflow's ``opensalestax-dump-<tag>-postgres.sql.gz``.
DUMP_FILENAME_TEMPLATE = "opensalestax-dump-{tag}-postgres.sql.gz"

#: Direct-download URL for a release asset (works for public releases without
#: hitting the API). Avoids burning the unauthenticated-API rate limit.
RELEASE_ASSET_URL_TEMPLATE = "https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}"

#: GitHub API endpoint that resolves "latest" to a tag name.
LATEST_RELEASE_API_TEMPLATE = "https://api.github.com/repos/{owner}/{repo}/releases/latest"

#: Tag pattern accepted by ``--release``. Permissive enough to cover
#: pre-release suffixes (``v0.23.0-rc1``) without admitting arbitrary input
#: like ``../../etc/passwd`` into the URL.
_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.\-]+)?$")

#: Sample size for sniffing the dump's ``alembic_version`` row. The dump
#: is data-only and the alembic_version data is excluded by pg_dump, so
#: we expect to find ZERO rows -- meaning the consumer's own
#: ``alembic upgrade head`` row stays in place. If a future workflow
#: change ever bundles the alembic_version row, this sniff catches it.
_SCHEMA_SNIFF_BYTES = 256 * 1024  # 256 KiB: pg_dump emits header tables early


class RestoreError(Exception):
    """Top-level error raised by the restore pipeline."""


@dataclass(frozen=True, slots=True)
class RestoreSource:
    """Resolved source of a dump file (URL or local path).

    Exactly one of ``local_path`` or ``url`` is populated. The CLI
    builds this from user options before any network or disk activity
    so the resolution logic is unit-testable.
    """

    local_path: Path | None
    url: str | None
    tag: str | None

    @property
    def is_local(self) -> bool:
        return self.local_path is not None

    @property
    def display(self) -> str:
        """Human-readable description of where the dump came from."""
        if self.local_path is not None:
            return str(self.local_path)
        assert self.url is not None
        return self.url


@dataclass(frozen=True, slots=True)
class RestoreSummary:
    """Counts queried after a successful restore."""

    states: int
    rates: int
    boundaries: int
    authorities: int
    source: str


def is_valid_tag(tag: str) -> bool:
    """Return True if ``tag`` looks like a release tag we'd publish."""
    return bool(_TAG_RE.match(tag))


def build_asset_url(tag: str) -> str:
    """Build the direct download URL for a release tag's dump asset.

    Raises :class:`RestoreError` for tags that don't match the
    accepted shape -- this prevents an attacker-controlled
    ``--release`` value from rewriting the URL into arbitrary
    territory (e.g. ``../../other-repo/...``).
    """
    if not is_valid_tag(tag):
        raise RestoreError(
            f"invalid release tag {tag!r}: expected vMAJOR.MINOR.PATCH "
            f"(optionally with a -prerelease suffix)"
        )
    return RELEASE_ASSET_URL_TEMPLATE.format(
        owner=GITHUB_OWNER,
        repo=GITHUB_REPO,
        tag=tag,
        filename=DUMP_FILENAME_TEMPLATE.format(tag=tag),
    )


def latest_release_api_url() -> str:
    """Return the API URL that resolves ``latest`` to a concrete tag."""
    return LATEST_RELEASE_API_TEMPLATE.format(owner=GITHUB_OWNER, repo=GITHUB_REPO)


def resolve_source(
    *,
    release: str | None,
    file: Path | None,
    http_client_factory=None,
) -> RestoreSource:
    """Translate user CLI options into a concrete :class:`RestoreSource`.

    Resolution rules (the CLI guarantees ``release`` and ``file`` are not
    both set; this function reasserts):

    1. ``file`` set -> local path; no network.
    2. ``release`` set and not the literal string ``latest`` -> direct URL.
    3. ``release`` is None or the string ``latest`` -> API call to find the
       latest release's tag, then build the direct URL.

    ``http_client_factory`` is exposed for test injection. Production
    callers leave it as ``None`` and get a default :class:`httpx.Client`.
    """
    if file is not None and release is not None:
        raise RestoreError("--release and --file are mutually exclusive")

    if file is not None:
        if not file.exists():
            raise RestoreError(f"local dump file does not exist: {file}")
        if not file.is_file():
            raise RestoreError(f"local dump path is not a file: {file}")
        return RestoreSource(local_path=file, url=None, tag=None)

    if release is not None and release != "latest":
        return RestoreSource(local_path=None, url=build_asset_url(release), tag=release)

    # release is None OR release == "latest" -> resolve via API.
    factory = http_client_factory or _default_http_client
    with factory() as client:
        try:
            response = client.get(latest_release_api_url())
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RestoreError(f"failed to fetch latest release metadata: {exc}") from exc
        try:
            tag = response.json()["tag_name"]
        except (KeyError, ValueError) as exc:
            raise RestoreError("latest-release response missing 'tag_name'") from exc

    if not isinstance(tag, str) or not is_valid_tag(tag):
        raise RestoreError(f"latest-release tag has unexpected shape: {tag!r}")

    return RestoreSource(local_path=None, url=build_asset_url(tag), tag=tag)


def is_postgres_dsn(dsn: str) -> bool:
    """Return True if the DSN points at a PostgreSQL engine.

    Accepts ``postgresql``, ``postgresql+asyncpg``, and ``postgres``
    schemes. Anything else (notably ``mysql`` / ``mysql+asyncmy``) is
    treated as not-PostgreSQL and forces the restore to bail out.
    """
    scheme = urlsplit(dsn).scheme.split("+", 1)[0].lower()
    return scheme in {"postgres", "postgresql"}


def dsn_to_psql_args(dsn: str) -> list[str]:
    """Strip SQLAlchemy-isms from a DSN so libpq's psql can parse it.

    SQLAlchemy DSNs look like ``postgresql+asyncpg://user:pw@host:5432/db``;
    psql wants ``postgresql://user:pw@host:5432/db``. We rewrite the
    scheme and hand the result back as ``psql``'s connection-string arg.
    """
    parts = urlsplit(dsn)
    scheme = parts.scheme.split("+", 1)[0]
    if scheme not in {"postgres", "postgresql"}:
        raise RestoreError(f"refusing to restore: DSN scheme {parts.scheme!r} is not PostgreSQL")
    rebuilt = parts._replace(scheme="postgresql").geturl()
    return ["-d", rebuilt]


def sniff_alembic_version(sample: bytes) -> str | None:
    """Look for an ``alembic_version`` COPY row in a dump sample.

    Returns the pinned revision string if the dump bundles its own
    ``alembic_version`` data, or ``None`` if not (which is the expected
    case for our workflow, since pg_dump's ``--exclude-table-data`` skips
    that row).

    The sample is a chunk of decompressed dump bytes. We look for the
    ``COPY public.alembic_version ... FROM stdin;`` line followed by the
    revision identifier on the next non-empty line. A trailing ``\\.``
    terminates the COPY block.
    """
    text = sample.decode("utf-8", errors="replace")
    # Match the COPY header. pg_dump wraps the version_num column name in
    # parens; its position varies across pg_dump versions, so we just look
    # for the table name + FROM stdin marker.
    copy_re = re.compile(r"^COPY\s+(?:public\.)?alembic_version\b.*FROM\s+stdin\s*;\s*$", re.M)
    match = copy_re.search(text)
    if not match:
        return None
    after = text[match.end() :]
    for raw in after.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == r"\.":
            return None
        # COPY data is tab-delimited; the revision is the only column.
        return line.split("\t", 1)[0]
    return None


def validate_schema_compatibility(dump_revision: str | None, current_revision: str | None) -> None:
    """Ensure a bundled alembic_version (if any) matches the consumer's head.

    A dump produced by our workflow has no bundled ``alembic_version``
    row (``--exclude-table-data=alembic_version``), so ``dump_revision``
    is normally ``None`` and the check passes trivially. If a future
    workflow change ever ships the row, we refuse to apply a dump whose
    pin disagrees with whatever ``alembic upgrade head`` produced on the
    consumer side -- the alternative would be silent data corruption
    against a schema the dump wasn't written for.
    """
    if dump_revision is None:
        return
    if current_revision is None:
        raise RestoreError(
            f"dump pins alembic revision {dump_revision!r}, but the consumer's "
            f"database has no alembic_version row. Run "
            f"`alembic upgrade head` and retry."
        )
    if dump_revision != current_revision:
        raise RestoreError(
            f"schema mismatch: dump was built against alembic revision "
            f"{dump_revision!r}, but the consumer's database is at "
            f"{current_revision!r}. Bring both sides to the same head and retry."
        )


def read_dump_sample(path: Path, max_bytes: int = _SCHEMA_SNIFF_BYTES) -> bytes:
    """Decompress and return the first ``max_bytes`` of a gzipped dump."""
    with gzip.open(path, "rb") as fh:
        return fh.read(max_bytes)


def get_current_alembic_revision() -> str | None:
    """Ask Alembic for the consumer database's current head, or ``None``.

    Returns ``None`` if the database has no ``alembic_version`` row
    (e.g. fresh database that has never run ``alembic upgrade``).
    """
    # Local imports keep the CLI start-up fast; alembic transitively
    # imports a bunch of SQLAlchemy machinery.
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    from opensalestax.settings import get_settings

    settings = get_settings()
    sync_dsn = _to_sync_dsn(settings.database_dsn)

    engine = create_engine(sync_dsn, future=True)
    try:
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            return ctx.get_current_revision()
    finally:
        engine.dispose()


def _to_sync_dsn(dsn: str) -> str:
    """Convert an async SQLAlchemy DSN to a sync one for alembic + psql."""
    parts = urlsplit(dsn)
    scheme = parts.scheme.split("+", 1)[0]
    return parts._replace(scheme=scheme).geturl()


def stream_dump_to_psql(
    dump_path: Path,
    dsn: str,
    *,
    runner=None,
) -> None:
    """Pipe a gzipped dump through ``gunzip | psql`` and raise on failure.

    The ``runner`` parameter is a hook for tests to substitute a fake
    :func:`subprocess.run`. Production callers leave it ``None`` and get
    the real one.

    psql is invoked with ``--single-transaction`` and ``ON_ERROR_STOP=1``
    so a partial failure rolls back rather than leaving the database in
    a half-loaded state. ``--quiet`` keeps the firehose of NOTICE lines
    out of the user's terminal.
    """
    use_runner = runner or subprocess.run
    args = [
        "psql",
        "--single-transaction",
        "--quiet",
        "--variable=ON_ERROR_STOP=1",
        *dsn_to_psql_args(_to_sync_dsn(dsn)),
        "-f",
        "-",
    ]
    with gzip.open(dump_path, "rb") as fh:
        try:
            # gzip.GzipFile is a binary file-like; mypy's stricter overloads
            # for subprocess.run want a concrete IO[bytes], so cast.
            result = use_runner(
                args,
                stdin=cast(IO[bytes], fh),
                check=False,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise RestoreError(
                "`psql` not found on PATH. Install the PostgreSQL client "
                "package (libpq) and re-run."
            ) from exc

    if result.returncode != 0:
        stderr = (result.stderr or b"").decode("utf-8", errors="replace").strip()
        raise RestoreError(f"psql exited with code {result.returncode}: {stderr or '(no stderr)'}")


def download_dump(url: str, dest: Path, *, http_client_factory=None) -> None:
    """Stream a URL to ``dest``. Used when ``--release`` resolves to a URL."""
    factory = http_client_factory or _default_http_client
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with factory() as client, client.stream("GET", url) as response:
            response.raise_for_status()
            with dest.open("wb") as fh:
                for chunk in response.iter_bytes(chunk_size=64 * 1024):
                    fh.write(chunk)
    except httpx.HTTPError as exc:
        raise RestoreError(f"failed to download dump from {url}: {exc}") from exc


def _default_http_client() -> httpx.Client:
    """Construct the production HTTP client (separated for test seams)."""
    return httpx.Client(
        timeout=httpx.Timeout(60.0, connect=10.0),
        follow_redirects=True,
        headers={"User-Agent": "opensalestax-restore"},
    )


__all__ = [
    "DUMP_FILENAME_TEMPLATE",
    "GITHUB_OWNER",
    "GITHUB_REPO",
    "LATEST_RELEASE_API_TEMPLATE",
    "RELEASE_ASSET_URL_TEMPLATE",
    "RestoreError",
    "RestoreSource",
    "RestoreSummary",
    "build_asset_url",
    "download_dump",
    "dsn_to_psql_args",
    "get_current_alembic_revision",
    "is_postgres_dsn",
    "is_valid_tag",
    "latest_release_api_url",
    "read_dump_sample",
    "resolve_source",
    "sniff_alembic_version",
    "stream_dump_to_psql",
    "validate_schema_compatibility",
]
