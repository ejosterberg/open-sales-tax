# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Unit tests for SST listing parsing and pin-drift detection.

Regression cover for 2026-09-16, when 18 of the 24 pins in
``.github/workflows/build-data-dump.yml`` had silently died: SST hosts
exactly one file per state per kind and deletes the previous one when a
state republishes. Nothing noticed until a release-tag build failed
fifteen minutes in with a bare ``HTTPStatusError: 404``.

The listings are checked in as fixtures (captured 2026-09-16) so these
tests never touch the network.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from opensalestax.data.sst_index import (
    SstIndexError,
    UpstreamFile,
    fetch_listing,
    parse_listing,
    version_of,
    versions_match,
)

_FIXTURES = Path(__file__).parent / "fixtures"
_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_sst_pins.py"


def _load_script() -> ModuleType:
    """Import the checker by path (``scripts/`` is not a package)."""
    spec = importlib.util.spec_from_file_location("check_sst_pins", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load_script()


@pytest.fixture
def rates_listing() -> dict[str, UpstreamFile]:
    html = (_FIXTURES / "sst_listing_rates.html").read_text(encoding="utf-8")
    return parse_listing(html, "R")


@pytest.fixture
def boundary_listing() -> dict[str, UpstreamFile]:
    html = (_FIXTURES / "sst_listing_boundary.html").read_text(encoding="utf-8")
    return parse_listing(html, "B")


class TestListingParsing:
    def test_each_listing_holds_exactly_one_file_per_sst_state(
        self, rates_listing: dict[str, UpstreamFile], boundary_listing: dict[str, UpstreamFile]
    ) -> None:
        """The structural fact the whole drift check rests on.

        Because upstream keeps exactly one file per (state, kind),
        "pin differs from upstream" and "pin is dead" are the same
        condition -- which is why no age heuristic is needed.
        """
        assert len(rates_listing) == 24
        assert len(boundary_listing) == 24
        assert set(rates_listing) == set(boundary_listing)

    def test_uppercase_extension_is_parsed(self, rates_listing: dict[str, UpstreamFile]) -> None:
        """Wyoming publishes ``WYR2026Q4AUG20.CSV`` -- note the case."""
        assert rates_listing["WY"].filename.endswith(".CSV")
        assert rates_listing["WY"].version == "2026Q4AUG20"

    def test_mixed_case_version_is_preserved(self, rates_listing: dict[str, UpstreamFile]) -> None:
        """Kentucky's file is ``KYR2012Q4Aug13.csv`` -- mixed case."""
        assert rates_listing["KY"].version == "2012Q4Aug13"

    def test_single_digit_day_is_not_zero_padded(
        self, rates_listing: dict[str, UpstreamFile]
    ) -> None:
        """``INR2008Q4MAY7.csv`` must round-trip as MAY7, not MAY07.

        Zero-padding it would produce a pin that 404s -- the exact
        failure this tooling exists to prevent.
        """
        assert rates_listing["IN"].version == "2008Q4MAY7"

    def test_parent_directory_link_is_ignored(self) -> None:
        html = '<A HREF="/ratesandboundry/">[To Parent Directory]</A><br>'
        assert parse_listing(html, "R") == {}

    def test_wrong_kind_is_filtered_out(self) -> None:
        html = '<A HREF="/x/ARB2026Q4SEP02.zip">ARB2026Q4SEP02.zip</A>'
        assert parse_listing(html, "R") == {}
        assert set(parse_listing(html, "B")) == {"AR"}

    def test_empty_listing_raises_rather_than_reporting_drift(self) -> None:
        """A listing we cannot read is a different problem from a dead pin.

        Reporting it as drift would propose blanking every pin.
        """

        class _Resp:
            text = "<html><body>directory browsing disabled</body></html>"

            def raise_for_status(self) -> None:
                pass

        class _Client:
            def __enter__(self) -> _Client:
                return self

            def __exit__(self, *a: object) -> None:
                pass

            def get(self, url: str) -> _Resp:
                return _Resp()

        with pytest.raises(SstIndexError, match="no recognizable SST filenames"):
            fetch_listing("R", http_client_factory=_Client)


class TestVersionComparison:
    def test_version_is_the_filename_stem_minus_state_and_kind(self) -> None:
        assert version_of("ARR2026Q4AUG28.csv") == "2026Q4AUG28"
        assert version_of("INR2008Q4MAY7.csv") == "2008Q4MAY7"

    @pytest.mark.parametrize(
        ("pinned", "upstream"),
        [
            ("2012Q4Aug13", "2012Q4AUG13"),
            ("2026Q4AUG20", "2026q4aug20"),
            ("  2026Q4AUG28 ", "2026Q4AUG28"),
        ],
    )
    def test_case_and_whitespace_differences_are_not_drift(
        self, pinned: str, upstream: str
    ) -> None:
        """SST's own casing is inconsistent and IIS is case-insensitive.

        Treating a case difference as drift would be a permanent false
        alarm on Kentucky and Wyoming.
        """
        assert versions_match(pinned, upstream)

    def test_a_real_version_change_is_drift(self) -> None:
        assert not versions_match("2026Q2FEB18", "2026Q4AUG18")


class TestDriftDetection:
    def test_current_pins_report_clean(
        self, rates_listing: dict[str, UpstreamFile], boundary_listing: dict[str, UpstreamFile]
    ) -> None:
        pins = {
            s: checker.Pin(s, rates_listing[s].version, boundary_listing[s].version)
            for s in rates_listing
        }
        drifted, vanished, appeared = checker.compare(pins, rates_listing, boundary_listing)
        assert (drifted, vanished, appeared) == ([], [], [])

    def test_never_republished_states_are_never_flagged(
        self, rates_listing: dict[str, UpstreamFile], boundary_listing: dict[str, UpstreamFile]
    ) -> None:
        """IN 2008, KY 2012, MI 2023, NJ 2018, NV 2025, RI 2019 are current.

        SST simply never republished them. An age-based check would
        flag all six forever; a match-based one cannot.
        """
        stale_looking = ["IN", "KY", "MI", "NJ", "NV", "RI"]
        pins = {
            s: checker.Pin(s, rates_listing[s].version, boundary_listing[s].version)
            for s in stale_looking
        }
        drifted, _, _ = checker.compare(pins, rates_listing, boundary_listing)
        assert drifted == []

    def test_dead_pin_is_reported_per_kind(
        self, rates_listing: dict[str, UpstreamFile], boundary_listing: dict[str, UpstreamFile]
    ) -> None:
        pins = {"MN": checker.Pin("MN", "2026Q2FEB18", boundary_listing["MN"].version)}
        drifted, _, _ = checker.compare(pins, rates_listing, boundary_listing)
        assert len(drifted) == 1
        assert drifted[0].state == "MN"
        assert drifted[0].kind_label == "rates"
        assert drifted[0].upstream == rates_listing["MN"].version

    def test_membership_changes_are_distinguished_from_drift(
        self, rates_listing: dict[str, UpstreamFile], boundary_listing: dict[str, UpstreamFile]
    ) -> None:
        """A state joining or leaving SST needs a decision, not a bump."""
        pins = {"ZZ": checker.Pin("ZZ", "2026Q1JAN1", "2026Q1JAN1")}
        drifted, vanished, appeared = checker.compare(pins, rates_listing, boundary_listing)
        assert drifted == []
        assert vanished == ["ZZ"]
        assert len(appeared) == 24


class TestWorkflowRewrite:
    WORKFLOW = _SCRIPT.parent.parent / ".github" / "workflows" / "build-data-dump.yml"

    def test_parses_all_pins_from_the_real_workflow(self) -> None:
        pins = checker.parse_workflow_pins(self.WORKFLOW.read_text(encoding="utf-8"))
        assert len(pins) == 24
        assert pins["IN"].rates == "2008Q4MAY7"

    def test_rewrite_round_trips_unchanged_pins(self) -> None:
        text = self.WORKFLOW.read_text(encoding="utf-8")
        pins = checker.parse_workflow_pins(text)
        assert checker.parse_workflow_pins(checker.rewrite_workflow(text, pins)) == pins

    def test_rewrite_replaces_only_the_pin_lines(self) -> None:
        text = self.WORKFLOW.read_text(encoding="utf-8")
        pins = checker.parse_workflow_pins(text)
        bumped = dict(pins)
        bumped["MN"] = checker.Pin("MN", "2027Q1DEC01", "2027Q1DEC01")
        out = checker.rewrite_workflow(text, bumped)
        assert checker.parse_workflow_pins(out)["MN"].rates == "2027Q1DEC01"
        # Everything outside the array survives untouched.
        assert "Load Census ZCTA -> state boundaries" in out
        assert "verify_dump_coverage.py" in out

    def test_rewrite_raises_when_no_pins_present(self) -> None:
        with pytest.raises(ValueError, match="no SST pin lines"):
            checker.rewrite_workflow("name: nothing here\n", {})
