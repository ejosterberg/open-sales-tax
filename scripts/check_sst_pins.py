# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Check the dump workflow's SST pins against what SST publishes today.

Why
---
``.github/workflows/build-data-dump.yml`` pins each SST state to a
specific quarterly file. SST hosts exactly **one file per state per
kind** and *deletes* the previous one when a state republishes, so
pins perish on upstream's schedule rather than ours.

On 2026-09-16, 18 of 24 pins were dead. Nothing noticed until a
release-tag build failed fifteen minutes in with a bare
``HTTPStatusError: 404``. This turns that into a five-second check with
an actionable message, and into a weekly scheduled report so the news
arrives before a release does rather than during one.

Because upstream keeps exactly one file per (state, kind), **"differs
from upstream" and "is dead" are the same condition** -- so this needs
no age heuristic and no allowlist, and it cannot false-positive on the
states SST simply never republished (IN 2008, KY 2012, MI 2023,
NJ 2018, NV 2025, RI 2019). Those still match the only file upstream.

Deliberately: this reports and can rewrite the pin block, but it never
adopts a new quarter on its own. Constitution §11 requires data updates
to be explicit operations rather than a silent background poll, and an
unreviewed bump can ship a wrong rate as easily as fix one -- upstream
drift has been found in both directions, including over-collections.

Usage
-----
::

    python scripts/check_sst_pins.py              # report; exit 1 on drift
    python scripts/check_sst_pins.py --write      # rewrite the pins in place
    python scripts/check_sst_pins.py --format sh  # emit prod's sst-load.sh array

Exit codes
----------
0   every pin matches the only file upstream
1   drift -- one or more pins no longer exist upstream
2   upstream unreachable, or the listing shape changed (not a pin problem;
    a release should not fail because SST had an outage)
3   membership change -- a state appeared in or vanished from the listing
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from opensalestax.data.sst_index import (  # noqa: E402
    SstIndexError,
    UpstreamFile,
    fetch_listing,
    versions_match,
)

WORKFLOW_PATH = _REPO_ROOT / ".github" / "workflows" / "build-data-dump.yml"

#: One pin line inside the workflow's ``STATES=( ... )`` array, e.g.
#: ``            "AR 2026Q4AUG28 2026Q4SEP02"``. Capturing the leading
#: whitespace lets a rewrite preserve the block's indentation exactly.
_PIN_RE = re.compile(
    r'^(?P<indent>\s*)"(?P<state>[A-Z]{2})\s+(?P<rates>\S+)\s+(?P<boundary>\S+)"\s*$',
    re.MULTILINE,
)

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_UNREACHABLE = 2
EXIT_MEMBERSHIP = 3


@dataclass(frozen=True, slots=True)
class Pin:
    """A pinned (rates, boundary) pair for one state."""

    state: str
    rates: str
    boundary: str


@dataclass(frozen=True, slots=True)
class Drift:
    """One pin that no longer resolves upstream."""

    state: str
    kind: str
    pinned: str
    upstream: str

    @property
    def kind_label(self) -> str:
        return "rates" if self.kind == "R" else "boundary"


def parse_workflow_pins(text: str) -> dict[str, Pin]:
    """Extract ``{state: Pin}`` from the workflow's STATES array."""
    pins: dict[str, Pin] = {}
    for m in _PIN_RE.finditer(text):
        pins[m.group("state")] = Pin(
            state=m.group("state"),
            rates=m.group("rates"),
            boundary=m.group("boundary"),
        )
    return pins


def compare(
    pins: dict[str, Pin],
    upstream_rates: dict[str, UpstreamFile],
    upstream_boundary: dict[str, UpstreamFile],
) -> tuple[list[Drift], list[str], list[str]]:
    """Diff pins against upstream.

    Returns ``(drifted, vanished, appeared)`` where ``vanished`` are
    pinned states no longer listed upstream at all and ``appeared`` are
    states upstream now lists that we do not pin. Both of the latter are
    membership changes -- SST gaining or losing a member state -- which
    need a human decision, not a version bump.
    """
    drifted: list[Drift] = []
    vanished: list[str] = []

    for state in sorted(pins):
        pin = pins[state]
        up_r = upstream_rates.get(state)
        up_b = upstream_boundary.get(state)
        if up_r is None and up_b is None:
            vanished.append(state)
            continue
        if up_r is not None and not versions_match(pin.rates, up_r.version):
            drifted.append(Drift(state, "R", pin.rates, up_r.version))
        if up_b is not None and not versions_match(pin.boundary, up_b.version):
            drifted.append(Drift(state, "B", pin.boundary, up_b.version))

    appeared = sorted((set(upstream_rates) | set(upstream_boundary)) - set(pins))
    return drifted, vanished, appeared


def resolved_pins(
    pins: dict[str, Pin],
    upstream_rates: dict[str, UpstreamFile],
    upstream_boundary: dict[str, UpstreamFile],
) -> dict[str, Pin]:
    """Return the pins as they would be after adopting upstream.

    Only states already pinned are returned; a newly-appeared state is a
    membership decision, not something to silently start loading.
    """
    updated: dict[str, Pin] = {}
    for state, pin in pins.items():
        up_r = upstream_rates.get(state)
        up_b = upstream_boundary.get(state)
        updated[state] = Pin(
            state=state,
            rates=up_r.version if up_r else pin.rates,
            boundary=up_b.version if up_b else pin.boundary,
        )
    return updated


def render_pin_block(pins: dict[str, Pin], indent: str) -> list[str]:
    """Render pin lines, column-aligned the way the workflow has them."""
    width = max((len(p.rates) for p in pins.values()), default=0)
    return [
        f'{indent}"{p.state} {p.rates.ljust(width)} {p.boundary}"'
        for p in (pins[s] for s in sorted(pins))
    ]


def rewrite_workflow(text: str, pins: dict[str, Pin]) -> str:
    """Replace every pin line in ``text`` with the given pins."""
    matches = list(_PIN_RE.finditer(text))
    if not matches:
        raise ValueError("no SST pin lines found in the workflow")
    indent = matches[0].group("indent")
    block = "\n".join(render_pin_block(pins, indent))
    start, end = matches[0].start(), matches[-1].end()
    return text[:start] + block + text[end:]


def format_report(
    pins: dict[str, Pin],
    drifted: list[Drift],
    vanished: list[str],
    appeared: list[str],
    updated: dict[str, Pin],
) -> str:
    """Render the human-facing report."""
    if not drifted and not vanished and not appeared:
        return f"OK: all {len(pins)} SST pins match the current file upstream."

    lines: list[str] = []
    if drifted:
        states = {d.state for d in drifted}
        lines.append(
            f"SST pin drift: {len(drifted)} pin(s) across {len(states)} state(s) "
            f"no longer exist upstream."
        )
        lines.append("")
        lines.append(f"  {'state':6}{'kind':10}{'pinned':16}{'upstream':16}status")
        for d in drifted:
            lines.append(f"  {d.state:6}{d.kind_label:10}{d.pinned:16}{d.upstream:16}DEAD (404)")
        clean = len(pins) - len(states)
        lines.append("")
        lines.append(f"  {clean} state(s) current -- including any SST has never republished.")
        lines.append("")
        lines.append("Fix:")
        lines.append("  python scripts/check_sst_pins.py --write")
        lines.append('  git commit -s -am "chore(data): refresh SST pins"')
        lines.append("")
        lines.append("Replacement array for the prod ~/sst-load.sh:")
        lines.extend(render_pin_block({s: updated[s] for s in sorted(states)}, "  "))

    if vanished:
        lines.append("")
        lines.append(
            f"MEMBERSHIP CHANGE: {len(vanished)} pinned state(s) are no longer listed "
            f"upstream at all: {' '.join(vanished)}"
        )
        lines.append("  SST may have lost a member. This needs a decision, not a pin bump.")

    if appeared:
        lines.append("")
        lines.append(
            f"MEMBERSHIP CHANGE: upstream lists {len(appeared)} state(s) we do not pin: "
            f"{' '.join(appeared)}"
        )
        lines.append("  SST may have gained a member. Adding it is a coverage decision.")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Rewrite the workflow's pins to match upstream (still needs review + commit).",
    )
    parser.add_argument(
        "--format",
        choices=["report", "sh"],
        default="report",
        help="'sh' emits the pin array for the prod ~/sst-load.sh instead of a report.",
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        default=WORKFLOW_PATH,
        help="Path to the dump workflow (default: the one in this repo).",
    )
    args = parser.parse_args(argv)

    text = args.workflow.read_text(encoding="utf-8")
    pins = parse_workflow_pins(text)
    if not pins:
        print(f"error: no SST pins found in {args.workflow}", file=sys.stderr)
        return EXIT_UNREACHABLE

    try:
        upstream_rates = fetch_listing("R")
        upstream_boundary = fetch_listing("B")
    except SstIndexError as exc:
        # An SST outage is not a pin problem. Say so, and exit with a
        # code the workflow can choose to tolerate.
        print(f"could not read the SST listings: {exc}", file=sys.stderr)
        return EXIT_UNREACHABLE

    drifted, vanished, appeared = compare(pins, upstream_rates, upstream_boundary)
    updated = resolved_pins(pins, upstream_rates, upstream_boundary)

    if args.format == "sh":
        print("\n".join(render_pin_block(updated, "  ")))
        return EXIT_OK

    print(format_report(pins, drifted, vanished, appeared, updated))

    if args.write and drifted:
        args.workflow.write_text(rewrite_workflow(text, updated), encoding="utf-8", newline="")
        print(f"\nwrote {len(drifted)} refreshed pin(s) to {args.workflow}")
        return EXIT_OK

    if vanished or appeared:
        return EXIT_MEMBERSHIP
    if drifted:
        return EXIT_DRIFT
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
