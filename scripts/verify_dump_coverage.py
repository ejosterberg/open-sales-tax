# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Verify a loaded database covers every taxing jurisdiction before it ships.

Guard for ``.github/workflows/build-data-dump.yml``. The published
``opensalestax-dump-<tag>-postgres.sql.gz`` is the flagship install
path: a fresh install runs ``data restore`` and is advertised as "live
in under two minutes". A dump that silently omits
states is worse than no dump at all: the API answers every request
with a well-formed empty jurisdiction list, so the consumer sees
"0% tax" rather than an error.

Why this exists
---------------
Issue #40 (2026-08-15, reported by an external contributor) observed
that a freshly restored install returned nothing for ZIP 90210 while
the hosted demo answered correctly. The cause was structural: the
dump workflow loaded the 24 SST states plus Arizona, and *no other
self-seeded state*. Twenty-three tier-1 states with a sales tax --
including California, Texas, New York, Florida, Pennsylvania and
Illinois -- were absent from every published dump.

The pre-existing verification step could not catch it. It asserted
``COUNT(*) FROM rates >= 1000``, a threshold the SST states clear on
their own, so the check passed on a dump missing nearly half the
country.

The lesson generalizes: a coverage gate must be derived from the
state registry, not from a hand-maintained list that drifts from it.
:func:`expected_taxing_states` reads the registry, so a new state
module is covered by this gate the moment it is registered -- and a
state module that nothing loads fails the release loudly.

What it checks
--------------
1. **Registry coverage.** Every registered state module with
   ``has_sales_tax`` must have at least one rate row in the database.
2. **End-to-end ZIP probes.** A sample of real ZIPs, spanning both
   data sources (SST quarterly files and in-tree self-seeded modules)
   and both jurisdiction shapes (stacked local rates and flat
   statewide rates), must resolve to a non-empty jurisdiction list in
   the expected state -- exercised through the same
   :func:`~opensalestax.core.lookup.lookup_jurisdictions_by_zip` the
   API serves from.

Deliberately NOT checked: specific rate values. Rates change every
quarter by design; asserting them here would duplicate the
``DOR_GRID`` validation suite and turn every legitimate rate change
into a release-pipeline failure. This gate answers "is the data
there?", not "is the data current?".

Usage
-----
Against whatever ``OPENSALESTAX_DATABASE_URL`` points at::

    python scripts/verify_dump_coverage.py

Exits 0 when every check passes, 1 otherwise, printing a report of
what is missing.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Allow running as a plain script from a source checkout (no install).
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from opensalestax.core.lookup import lookup_jurisdictions_by_zip  # noqa: E402
from opensalestax.db.models import Rate, State, TaxAuthority  # noqa: E402
from opensalestax.db.session import get_sessionmaker  # noqa: E402
from opensalestax.states import all_states  # noqa: E402


@dataclass(frozen=True, slots=True)
class ZipProbe:
    """A single end-to-end ZIP lookup expectation.

    ``zip5`` must resolve to at least one jurisdiction whose state is
    ``state``. Every probe below was verified against the hosted API
    at the time it was added; see ``note`` for what each one covers.
    """

    zip5: str
    state: str
    note: str


#: Probes span both data sources and both jurisdiction shapes, so a
#: partial load fails here even if it somehow satisfies the registry
#: check. The self-seeded entries are the ones issue #40 exposed.
ZIP_PROBES: tuple[ZipProbe, ...] = (
    ZipProbe("90210", "CA", "self-seeded, stacked local -- the ZIP reported in issue #40"),
    ZipProbe("77002", "TX", "self-seeded, city + transit-authority district"),
    ZipProbe("10001", "NY", "self-seeded, city + county + commuter district"),
    ZipProbe("33101", "FL", "self-seeded, county discretionary surtax"),
    ZipProbe("60601", "IL", "self-seeded, home-rule city + RTA district"),
    ZipProbe("19103", "PA", "self-seeded, county-level local tax"),
    ZipProbe("85004", "AZ", "self-seeded, the one non-SST state the dump already loaded"),
    ZipProbe("06103", "CT", "self-seeded, flat statewide -- resolves via ZCTA with no boundaries"),
    ZipProbe("02108", "MA", "self-seeded, flat statewide -- resolves via ZCTA with no boundaries"),
    ZipProbe("96813", "HI", "self-seeded, county surcharge on the general excise tax"),
    ZipProbe("55401", "MN", "SST-sourced, multiple stacked transit districts"),
    ZipProbe("98101", "WA", "SST-sourced, combined local rate"),
)


@dataclass(slots=True)
class CoverageReport:
    """Accumulated findings from a verification run."""

    missing_states: list[str] = field(default_factory=list)
    failed_probes: list[tuple[ZipProbe, str]] = field(default_factory=list)
    checked_states: int = 0
    checked_probes: int = 0

    @property
    def ok(self) -> bool:
        return not self.missing_states and not self.failed_probes


def expected_taxing_states() -> list[str]:
    """Return every registered state abbrev that levies a sales tax.

    Derived from the state registry rather than hand-maintained, so
    adding a state module automatically extends this gate. States
    with no sales tax at all (DE, MT, NH, OR) are excluded -- they
    legitimately contribute no rate rows.
    """
    return sorted(m.state_abbrev for m in all_states() if m.has_sales_tax)


async def states_with_rates(session: AsyncSession) -> set[str]:
    """Return the abbrevs of states that have at least one rate row."""
    stmt = (
        select(State.abbrev)
        .join(TaxAuthority, TaxAuthority.state_id == State.id)
        .join(Rate, Rate.authority_id == TaxAuthority.id)
        .distinct()
    )
    result = await session.execute(stmt)
    return {row[0] for row in result.all()}


async def run_checks(session: AsyncSession) -> CoverageReport:
    """Run every coverage check and collect the findings."""
    report = CoverageReport()

    expected = expected_taxing_states()
    present = await states_with_rates(session)
    report.checked_states = len(expected)
    report.missing_states = [abbrev for abbrev in expected if abbrev not in present]

    for probe in ZIP_PROBES:
        report.checked_probes += 1
        try:
            authorities = await lookup_jurisdictions_by_zip(session, probe.zip5)
        except Exception as exc:  # report every probe; one failure must not abort the sweep
            report.failed_probes.append((probe, f"lookup raised {type(exc).__name__}: {exc}"))
            continue
        if not authorities:
            report.failed_probes.append((probe, "no jurisdictions returned"))
            continue
        found = {
            abbrev
            for abbrev in (
                getattr(getattr(auth, "state", None), "abbrev", None) for auth in authorities
            )
            if abbrev is not None
        }
        if probe.state not in found:
            report.failed_probes.append(
                (probe, f"expected a {probe.state} jurisdiction, got {sorted(found) or 'none'}")
            )

    return report


def format_report(report: CoverageReport) -> str:
    """Render a human- and CI-readable summary of a run."""
    if report.ok:
        return (
            f"OK: all {report.checked_states} taxing states have rates; "
            f"all {report.checked_probes} ZIP probes resolved."
        )

    lines: list[str] = ["DUMP COVERAGE CHECK FAILED"]
    if report.missing_states:
        lines.append("")
        lines.append(
            f"{len(report.missing_states)} of {report.checked_states} taxing states have "
            f"no rate rows -- the dump would ship without them:"
        )
        lines.append("  " + " ".join(report.missing_states))
        lines.append("")
        lines.append(
            "  Every registered state module that levies a tax must be loaded before "
            "the dump is built. SST states need their quarterly file pinned in the "
            "workflow's STATES list; self-seeded states carry their data in-tree and "
            "only need a `data load --state <ST> --version <label>`."
        )
    if report.failed_probes:
        lines.append("")
        lines.append(f"{len(report.failed_probes)} ZIP probe(s) failed:")
        for probe, reason in report.failed_probes:
            lines.append(f"  {probe.zip5} ({probe.state}): {reason}")
            lines.append(f"      covers: {probe.note}")
    return "\n".join(lines)


async def _amain() -> int:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        report = await run_checks(session)
    print(format_report(report))
    return 0 if report.ok else 1


def main() -> int:
    """Entry point: run the checks and return a process exit code."""
    return asyncio.run(_amain())


if __name__ == "__main__":
    sys.exit(main())
