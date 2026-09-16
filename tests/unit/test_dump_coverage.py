# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Unit tests for the release-dump coverage gate.

Regression cover for issue #40: every published dump through v0.59.0
shipped the 24 SST states plus Arizona and no other self-seeded state,
so a restored install answered nothing for CA, TX, NY, FL, PA, IL and
17 more. The workflow's own verification step could not catch it
because it only asserted a global rate-row count.

These tests exercise the pure, DB-free parts of
``scripts/verify_dump_coverage.py``. The DB-backed half
(:func:`states_with_rates`, :func:`run_checks`) runs for real in the
dump workflow against a fully loaded PostgreSQL instance.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

from opensalestax.states import all_states

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify_dump_coverage.py"


def _load_script() -> ModuleType:
    """Import the gate script by path (``scripts/`` is not a package)."""
    spec = importlib.util.spec_from_file_location("verify_dump_coverage", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


coverage = _load_script()


def test_expected_states_is_derived_from_the_registry() -> None:
    """The gate must read the registry, never a hand-maintained list.

    A hardcoded list is exactly how the dump drifted out of sync with
    the shipped state modules in the first place.
    """
    registry = {m.state_abbrev for m in all_states() if m.has_sales_tax}
    assert set(coverage.expected_taxing_states()) == registry


def test_expected_states_excludes_the_no_sales_tax_states() -> None:
    """DE, MT, NH and OR levy no sales tax, so they contribute no rates."""
    expected = set(coverage.expected_taxing_states())
    assert not expected & {"DE", "MT", "NH", "OR"}


@pytest.mark.parametrize("abbrev", ["CA", "TX", "NY", "FL", "PA", "IL", "MA", "CT", "HI", "PR"])
def test_states_missing_from_the_v0_59_dump_are_now_required(abbrev: str) -> None:
    """Each state issue #40 exposed must be demanded by the gate.

    These are self-seeded (non-SST) states that levy a sales tax. If
    any of them ever stops being required here, a dump could ship
    without it again.
    """
    assert abbrev in coverage.expected_taxing_states()


def test_every_probe_targets_a_registered_taxing_state() -> None:
    """A probe naming an unknown or untaxed state could never pass."""
    expected = set(coverage.expected_taxing_states())
    for probe in coverage.ZIP_PROBES:
        assert probe.state in expected, f"{probe.zip5} targets unknown state {probe.state}"


def test_probes_span_both_data_sources() -> None:
    """Probes must cover SST-sourced and self-seeded states alike.

    The bug was invisible precisely because only SST states were
    exercised; a probe set drawn from one source could repeat that.
    """
    by_abbrev = {m.state_abbrev: m for m in all_states()}
    sources = {
        bool(getattr(by_abbrev[probe.state], "self_seeded", False)) for probe in coverage.ZIP_PROBES
    }
    assert sources == {True, False}


def test_probe_zips_are_well_formed_and_unique() -> None:
    zips = [probe.zip5 for probe in coverage.ZIP_PROBES]
    assert len(zips) == len(set(zips))
    for zip5 in zips:
        assert len(zip5) == 5 and zip5.isdigit()


#: Exactly what every published dump through v0.59.0 contained: the 24
#: SST states the workflow pinned, plus Arizona's dedicated load step.
_V0_59_DUMP_CONTENTS = frozenset(
    "AR GA IA IN KS KY MI MN NC ND NE NJ NV OH OK RI SD TN UT VT WA WI WV WY AZ".split()
)


def test_gate_rejects_the_dump_that_shipped_with_v0_59_0() -> None:
    """The gate must fail on the exact contents that caused issue #40.

    This is the test the old ``COUNT(*) FROM rates >= 1000`` check
    could never be: it is stated in terms of *which* states are
    present, so no amount of rate rows in the SST states can satisfy
    it while CA, TX, NY and the rest are absent.
    """
    expected = coverage.expected_taxing_states()
    missing = [abbrev for abbrev in expected if abbrev not in _V0_59_DUMP_CONTENTS]

    assert missing, "the v0.59.0 dump contents must not look complete"
    # The states an installing user could not get an answer for.
    assert {"CA", "TX", "NY", "FL", "PA", "IL"} <= set(missing)

    report = coverage.CoverageReport(missing_states=missing, checked_states=len(expected))
    assert not report.ok
    rendered = coverage.format_report(report)
    assert "FAILED" in rendered
    for abbrev in missing:
        assert abbrev in rendered


def test_clean_report_is_ok_and_says_so() -> None:
    report = coverage.CoverageReport(checked_states=48, checked_probes=12)
    assert report.ok
    assert "OK:" in coverage.format_report(report)


def test_missing_states_fail_the_report_and_are_named() -> None:
    report = coverage.CoverageReport(
        missing_states=["CA", "TX"], checked_states=48, checked_probes=12
    )
    assert not report.ok
    rendered = coverage.format_report(report)
    assert "FAILED" in rendered
    assert "CA TX" in rendered


def test_failed_probe_fails_the_report_and_explains_itself() -> None:
    probe = coverage.ZipProbe("90210", "CA", "the ZIP reported in issue #40")
    report = coverage.CoverageReport(
        failed_probes=[(probe, "no jurisdictions returned")],
        checked_states=48,
        checked_probes=12,
    )
    assert not report.ok
    rendered = coverage.format_report(report)
    assert "90210" in rendered
    assert "no jurisdictions returned" in rendered
    assert "issue #40" in rendered
