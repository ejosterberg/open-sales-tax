# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Write every package pinned in ``poetry.lock`` as ``name==version`` files.

Why
---
CI's dependency audit (``pip-audit``) must check what the project
*locks*, not whatever happens to be installed in some environment. On
2026-11-12 a local ``poetry run pip-audit`` audited the developer's
global interpreter instead of the project venv, mixing unrelated
packages into the report while three genuinely vulnerable locked
packages (certifi, filelock, virtualenv) had gone unnoticed because CI
never audited anything.

``poetry export`` would do this, but it is a plugin in Poetry 2.x and
built in only for 1.x, so local and CI runs would need different
tooling. Reading the lockfile directly with ``tomllib`` works the same
on every Poetry version.

Every group (main + dev) and every optional extra is included, and
environment markers are ignored: a vulnerable package is worth
knowing about even if it is only selected on some platforms.

A lockfile can pin the same package at more than one version, split by
environment markers (it did, for typing-extensions, until 2026-11-12).
``pip-audit`` refuses a requirements file that names a package twice,
so the extra versions go into further files: ``locked-0.txt`` holds one
version of every package, ``locked-1.txt`` the second version of any
package that has two, and so on. Audit every file written.

Usage
-----
    python scripts/lock_requirements.py OUT_DIR [poetry.lock]
    for f in OUT_DIR/locked-*.txt; do pip-audit -r "$f" --no-deps --disable-pip; done
"""

from __future__ import annotations

import sys
import tomllib
from collections import defaultdict
from pathlib import Path

# Packages that come from a local path or VCS have no PyPI identity to audit.
_UNAUDITABLE_SOURCES = {"directory", "file", "git", "url"}


def locked_requirement_layers(lock_text: str) -> list[list[str]]:
    """Return ``name==version`` lines split into duplicate-free layers.

    Layer 0 holds one version of every locked package; layer ``i`` holds
    the ``i``-th extra version of any package locked more than once.
    """
    data = tomllib.loads(lock_text)
    versions: dict[str, set[str]] = defaultdict(set)
    for pkg in data.get("package", []):
        if pkg.get("source", {}).get("type") in _UNAUDITABLE_SOURCES:
            continue
        versions[pkg["name"].lower()].add(pkg["version"])

    depth = max((len(v) for v in versions.values()), default=0)
    layers: list[list[str]] = [[] for _ in range(depth)]
    for name in sorted(versions):
        for i, version in enumerate(sorted(versions[name])):
            layers[i].append(f"{name}=={version}")
    return layers


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: lock_requirements.py OUT_DIR [poetry.lock]", file=sys.stderr)
        return 2
    out_dir = Path(argv[1])
    lock_path = Path(argv[2]) if len(argv) > 2 else Path("poetry.lock")

    layers = locked_requirement_layers(lock_path.read_text(encoding="utf-8"))
    if not layers:
        print(f"error: no packages found in {lock_path}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("locked-*.txt"):
        stale.unlink()
    for i, lines in enumerate(layers):
        (out_dir / f"locked-{i}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(len(layer) for layer in layers)
    print(f"{total} pins from {lock_path} in {len(layers)} file(s) under {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
