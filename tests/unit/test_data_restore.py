# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Unit tests for the ``opensalestax data restore`` pipeline.

These tests exercise the pure-Python helpers (URL construction, source
resolution, schema-version sniffing, MariaDB error path) without
touching a real database or hitting the network. The CLI itself is
tested via Typer's :class:`CliRunner` with subprocess + httpx mocked.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from unittest import mock

import pytest
from typer.testing import CliRunner

from opensalestax.cli.main import app
from opensalestax.data.restore import (
    DUMP_FILENAME_TEMPLATE,
    GITHUB_OWNER,
    GITHUB_REPO,
    RestoreError,
    build_asset_url,
    download_dump,
    dsn_to_psql_args,
    is_postgres_dsn,
    is_valid_tag,
    latest_release_api_url,
    read_dump_sample,
    resolve_source,
    sniff_alembic_version,
    stream_dump_to_psql,
    validate_schema_compatibility,
)


# ---------------------------------------------------------------------------
# is_valid_tag / build_asset_url -- guards against URL injection
# ---------------------------------------------------------------------------
class TestTagValidation:
    @pytest.mark.parametrize(
        "tag",
        [
            "v0.1.0",
            "v0.23.0",
            "v1.2.3",
            "v0.23.0-rc1",
            "v10.20.30",
            "v0.0.0+build.7",
        ],
    )
    def test_accepts_well_formed_tags(self, tag: str) -> None:
        assert is_valid_tag(tag) is True

    @pytest.mark.parametrize(
        "tag",
        [
            "0.23.0",  # missing 'v'
            "v0.23",  # only two segments
            "v0.23.0.0",  # four segments
            "v0.23.0/../etc",  # path traversal attempt
            "v0.23.0; rm -rf /",  # shell metachar
            "",
            "latest",  # 'latest' is special-cased upstream of build_asset_url
            "vX.Y.Z",
        ],
    )
    def test_rejects_malformed_tags(self, tag: str) -> None:
        assert is_valid_tag(tag) is False

    def test_build_asset_url_for_normal_release(self) -> None:
        url = build_asset_url("v0.23.0")
        assert url == (
            f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/"
            f"v0.23.0/{DUMP_FILENAME_TEMPLATE.format(tag='v0.23.0')}"
        )

    def test_build_asset_url_for_prerelease(self) -> None:
        url = build_asset_url("v0.23.0-rc1")
        assert url.endswith("opensalestax-dump-v0.23.0-rc1-postgres.sql.gz")

    def test_build_asset_url_rejects_garbage(self) -> None:
        with pytest.raises(RestoreError, match="invalid release tag"):
            build_asset_url("../../../etc/passwd")

    def test_latest_release_api_url(self) -> None:
        assert latest_release_api_url() == (
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
        )


# ---------------------------------------------------------------------------
# resolve_source -- the URL-vs-file-vs-latest decision tree
# ---------------------------------------------------------------------------
class TestResolveSource:
    def test_local_file_path_short_circuits_network(self, tmp_path: Path) -> None:
        local = tmp_path / "dump.sql.gz"
        local.write_bytes(b"placeholder")

        # No http_client_factory passed; must not be called.
        def boom():  # pragma: no cover -- must not be invoked
            raise AssertionError("HTTP client should not be constructed for local files")

        source = resolve_source(release=None, file=local, http_client_factory=boom)
        assert source.is_local is True
        assert source.local_path == local
        assert source.url is None
        assert source.tag is None
        assert source.display == str(local)

    def test_local_file_must_exist(self, tmp_path: Path) -> None:
        missing = tmp_path / "nope.sql.gz"
        with pytest.raises(RestoreError, match="does not exist"):
            resolve_source(release=None, file=missing)

    def test_local_file_must_be_a_file(self, tmp_path: Path) -> None:
        a_dir = tmp_path / "subdir"
        a_dir.mkdir()
        with pytest.raises(RestoreError, match="not a file"):
            resolve_source(release=None, file=a_dir)

    def test_specific_release_builds_direct_url_no_api_call(self) -> None:
        def boom():  # pragma: no cover -- must not be invoked
            raise AssertionError("HTTP client should not be constructed for explicit tag")

        source = resolve_source(release="v0.5.0", file=None, http_client_factory=boom)
        assert source.is_local is False
        assert source.tag == "v0.5.0"
        assert source.url is not None
        assert "v0.5.0" in source.url
        assert source.url.endswith("opensalestax-dump-v0.5.0-postgres.sql.gz")

    def test_release_and_file_are_mutually_exclusive(self, tmp_path: Path) -> None:
        local = tmp_path / "dump.sql.gz"
        local.write_bytes(b"placeholder")
        with pytest.raises(RestoreError, match="mutually exclusive"):
            resolve_source(release="v0.5.0", file=local)

    def test_latest_resolves_via_api(self) -> None:
        captured = {}

        class FakeResponse:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                return {"tag_name": "v0.42.0", "name": "v0.42.0"}

        class FakeClient:
            def __enter__(self) -> FakeClient:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def get(self, url: str) -> FakeResponse:
                captured["url"] = url
                return FakeResponse()

        source = resolve_source(release=None, file=None, http_client_factory=FakeClient)
        assert source.tag == "v0.42.0"
        assert source.url is not None
        assert source.url.endswith("opensalestax-dump-v0.42.0-postgres.sql.gz")
        assert captured["url"] == latest_release_api_url()

    def test_latest_string_resolves_via_api(self) -> None:
        class FakeResponse:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                return {"tag_name": "v9.9.9"}

        class FakeClient:
            def __enter__(self) -> FakeClient:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def get(self, url: str) -> FakeResponse:
                return FakeResponse()

        source = resolve_source(release="latest", file=None, http_client_factory=FakeClient)
        assert source.tag == "v9.9.9"

    def test_latest_rejects_garbage_tag_from_api(self) -> None:
        class FakeResponse:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                return {"tag_name": "totally-not-a-version"}

        class FakeClient:
            def __enter__(self) -> FakeClient:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def get(self, url: str) -> FakeResponse:
                return FakeResponse()

        with pytest.raises(RestoreError, match="unexpected shape"):
            resolve_source(release=None, file=None, http_client_factory=FakeClient)

    def test_latest_handles_missing_tag_name_field(self) -> None:
        class FakeResponse:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                return {"name": "v9.9.9"}  # no tag_name

        class FakeClient:
            def __enter__(self) -> FakeClient:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def get(self, url: str) -> FakeResponse:
                return FakeResponse()

        with pytest.raises(RestoreError, match="missing 'tag_name'"):
            resolve_source(release=None, file=None, http_client_factory=FakeClient)


# ---------------------------------------------------------------------------
# DSN handling -- distinguishes Postgres from MariaDB
# ---------------------------------------------------------------------------
class TestDsnHandling:
    @pytest.mark.parametrize(
        "dsn",
        [
            "postgresql://u:p@h:5432/d",
            "postgresql+asyncpg://u:p@h:5432/d",
            "postgres://u:p@h:5432/d",
        ],
    )
    def test_postgres_dsn_recognized(self, dsn: str) -> None:
        assert is_postgres_dsn(dsn) is True

    @pytest.mark.parametrize(
        "dsn",
        [
            "mysql://u:p@h:3306/d",
            "mysql+asyncmy://u:p@h:3306/d",
            "mariadb://u:p@h:3306/d",
            "sqlite:///x.db",
            "",
        ],
    )
    def test_non_postgres_dsn_rejected(self, dsn: str) -> None:
        assert is_postgres_dsn(dsn) is False

    def test_dsn_to_psql_args_strips_async_driver(self) -> None:
        args = dsn_to_psql_args("postgresql+asyncpg://u:p@h:5432/d")
        assert args == ["-d", "postgresql://u:p@h:5432/d"]

    def test_dsn_to_psql_args_keeps_sync_dsn(self) -> None:
        args = dsn_to_psql_args("postgresql://u:p@h:5432/d")
        assert args == ["-d", "postgresql://u:p@h:5432/d"]

    def test_dsn_to_psql_args_refuses_mariadb(self) -> None:
        with pytest.raises(RestoreError, match="not PostgreSQL"):
            dsn_to_psql_args("mysql+asyncmy://u:p@h:3306/d")


# ---------------------------------------------------------------------------
# Schema-version sniffing -- the alembic_version compatibility check
# ---------------------------------------------------------------------------
class TestSchemaSniffing:
    def test_no_alembic_table_returns_none(self) -> None:
        sample = b"-- some pg_dump preamble\nCOPY public.states ...\n"
        assert sniff_alembic_version(sample) is None

    def test_extracts_revision_from_copy_block(self) -> None:
        sample = (
            b"COPY public.alembic_version (version_num) FROM stdin;\n"
            b"0004_taxability_thresholds\n"
            b"\\.\n"
        )
        assert sniff_alembic_version(sample) == "0004_taxability_thresholds"

    def test_handles_unqualified_table_name(self) -> None:
        # Some pg_dump versions omit the schema-qualified prefix.
        sample = b"COPY alembic_version (version_num) FROM stdin;\n" b"abc1234567\n" b"\\.\n"
        assert sniff_alembic_version(sample) == "abc1234567"

    def test_returns_none_when_copy_block_is_empty(self) -> None:
        sample = b"COPY public.alembic_version (version_num) FROM stdin;\n" b"\\.\n"
        assert sniff_alembic_version(sample) is None

    def test_validate_passes_when_dump_has_no_pin(self) -> None:
        # Default workflow path: dump excludes alembic_version data.
        validate_schema_compatibility(None, "0004_taxability_thresholds")

    def test_validate_passes_when_revisions_match(self) -> None:
        validate_schema_compatibility("0004_taxability_thresholds", "0004_taxability_thresholds")

    def test_validate_raises_on_mismatch(self) -> None:
        with pytest.raises(RestoreError, match="schema mismatch"):
            validate_schema_compatibility("0004_old", "0005_new")

    def test_validate_raises_when_consumer_unmigrated(self) -> None:
        with pytest.raises(RestoreError, match="alembic upgrade head"):
            validate_schema_compatibility("0004_taxability_thresholds", None)


# ---------------------------------------------------------------------------
# read_dump_sample -- reads the head of a gzipped file
# ---------------------------------------------------------------------------
class TestReadDumpSample:
    def test_reads_decompressed_bytes(self, tmp_path: Path) -> None:
        target = tmp_path / "dump.sql.gz"
        with gzip.open(target, "wb") as fh:
            fh.write(b"hello world" * 100)
        sample = read_dump_sample(target, max_bytes=20)
        assert sample == b"hello worldhello wor"


# ---------------------------------------------------------------------------
# stream_dump_to_psql -- subprocess.run is mocked
# ---------------------------------------------------------------------------
class TestStreamDumpToPsql:
    def test_invokes_psql_with_safe_flags(self, tmp_path: Path) -> None:
        target = tmp_path / "dump.sql.gz"
        with gzip.open(target, "wb") as fh:
            fh.write(b"-- empty dump\n")

        captured = {}

        def fake_runner(args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return mock.Mock(returncode=0, stderr=b"")

        stream_dump_to_psql(
            target,
            "postgresql+asyncpg://u:p@h:5432/d",
            runner=fake_runner,
        )
        assert captured["args"][0] == "psql"
        assert "--single-transaction" in captured["args"]
        assert "--variable=ON_ERROR_STOP=1" in captured["args"]
        assert "-d" in captured["args"]
        # DSN should be sync-rewritten before being handed to psql.
        idx = captured["args"].index("-d")
        assert captured["args"][idx + 1] == "postgresql://u:p@h:5432/d"

    def test_raises_on_nonzero_exit(self, tmp_path: Path) -> None:
        target = tmp_path / "dump.sql.gz"
        with gzip.open(target, "wb") as fh:
            fh.write(b"bogus dump\n")

        def fake_runner(args, **kwargs):
            return mock.Mock(returncode=1, stderr=b"ERROR: relation does not exist")

        with pytest.raises(RestoreError, match="psql exited with code 1"):
            stream_dump_to_psql(
                target,
                "postgresql://u:p@h:5432/d",
                runner=fake_runner,
            )

    def test_raises_when_psql_missing(self, tmp_path: Path) -> None:
        target = tmp_path / "dump.sql.gz"
        with gzip.open(target, "wb") as fh:
            fh.write(b"x\n")

        def fake_runner(args, **kwargs):
            raise FileNotFoundError("psql")

        with pytest.raises(RestoreError, match="psql.*not found"):
            stream_dump_to_psql(
                target,
                "postgresql://u:p@h:5432/d",
                runner=fake_runner,
            )


# ---------------------------------------------------------------------------
# download_dump -- httpx.Client streaming is mocked
# ---------------------------------------------------------------------------
class TestDownloadDump:
    def test_writes_streamed_bytes_to_destination(self, tmp_path: Path) -> None:
        body = b"--gzipped-bytes--" * 16
        dest = tmp_path / "out" / "dump.sql.gz"

        class FakeStreamCtx:
            def __enter__(self) -> FakeStreamCtx:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def raise_for_status(self) -> None:
                pass

            def iter_bytes(self, chunk_size: int) -> object:
                # Chunk it to exercise the loop boundary.
                yield body[: chunk_size // 2]
                yield body[chunk_size // 2 :]

        class FakeClient:
            def __enter__(self) -> FakeClient:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def stream(self, method: str, url: str) -> FakeStreamCtx:
                assert method == "GET"
                assert url == "https://example.invalid/dump"
                return FakeStreamCtx()

        download_dump(
            "https://example.invalid/dump",
            dest,
            http_client_factory=FakeClient,
        )
        assert dest.exists()
        assert dest.read_bytes() == body


# ---------------------------------------------------------------------------
# CLI integration -- the MariaDB error path + dry-run wiring
# ---------------------------------------------------------------------------
class TestCliRestoreCommand:
    def test_mariadb_dsn_exits_cleanly(self, monkeypatch: pytest.MonkeyPatch) -> None:
        runner = CliRunner()

        # Force settings to a MariaDB DSN. Settings is a singleton; clear
        # the cache before and after.
        from opensalestax import settings as settings_module

        monkeypatch.setattr(settings_module, "_settings", None)
        monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "mysql+asyncmy://u:p@localhost:3306/d")
        try:
            result = runner.invoke(app, ["data", "restore"])
        finally:
            monkeypatch.setattr(settings_module, "_settings", None)

        assert result.exit_code == 2, result.output
        # Message text lives in stderr per CLI convention.
        combined = result.output
        assert "MariaDB" in combined or "manual data load path" in combined

    def test_dry_run_skips_apply_and_returns_zero(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        runner = CliRunner()

        # Build a minimal local dump (with an alembic_version COPY block
        # that matches what we'll fake the DB head to be).
        dump = tmp_path / "dump.sql.gz"
        with gzip.open(dump, "wb") as fh:
            fh.write(
                b"COPY public.alembic_version (version_num) FROM stdin;\n"
                b"0004_taxability_thresholds\n"
                b"\\.\n"
            )

        from opensalestax import settings as settings_module
        from opensalestax.data import restore as restore_module

        monkeypatch.setattr(settings_module, "_settings", None)
        monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/d")
        # Stub out alembic interrogation (no real DB available in this test).
        monkeypatch.setattr(
            restore_module,
            "get_current_alembic_revision",
            lambda: "0004_taxability_thresholds",
        )
        # Mirror the patch into the CLI module's namespace, since main.py
        # imports the symbol by name at module load.
        from opensalestax.cli import main as cli_main

        monkeypatch.setattr(
            cli_main, "get_current_alembic_revision", lambda: "0004_taxability_thresholds"
        )

        try:
            result = runner.invoke(app, ["data", "restore", "--file", str(dump), "--dry-run"])
        finally:
            monkeypatch.setattr(settings_module, "_settings", None)

        assert result.exit_code == 0, result.output
        combined = result.output
        assert "dry-run" in combined.lower()

    def test_dry_run_aborts_on_schema_mismatch(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        runner = CliRunner()

        dump = tmp_path / "dump.sql.gz"
        with gzip.open(dump, "wb") as fh:
            fh.write(
                b"COPY public.alembic_version (version_num) FROM stdin;\n"
                b"9999_unknown_revision\n"
                b"\\.\n"
            )

        from opensalestax import settings as settings_module
        from opensalestax.cli import main as cli_main

        monkeypatch.setattr(settings_module, "_settings", None)
        monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/d")
        monkeypatch.setattr(
            cli_main, "get_current_alembic_revision", lambda: "0004_taxability_thresholds"
        )

        try:
            result = runner.invoke(app, ["data", "restore", "--file", str(dump), "--dry-run"])
        finally:
            monkeypatch.setattr(settings_module, "_settings", None)

        assert result.exit_code == 1, result.output
        combined = result.output
        assert "schema" in combined.lower()
