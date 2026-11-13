# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Unit tests for ``scripts/lock_requirements.py``.

That script feeds CI's ``pip-audit`` job. If it silently drops a package,
the audit passes without ever looking at it -- the failure mode that let
three vulnerable locked packages go unnoticed until 2026-11-12. So these
tests pin down that nothing locked goes missing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_script() -> ModuleType:
    path = REPO_ROOT / "scripts" / "lock_requirements.py"
    spec = importlib.util.spec_from_file_location("lock_requirements", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lock_requirements = _load_script()

_LOCK = """
[[package]]
name = "Certifi"
version = "2026.10.23"
groups = ["main"]

[[package]]
name = "filelock"
version = "4.2.10"
groups = ["dev"]

[[package]]
name = "typing-extensions"
version = "4.15.0"
markers = "python_version >= \\"3.15\\""

[[package]]
name = "typing-extensions"
version = "4.16.0"
markers = "python_version < \\"3.15\\""

[[package]]
name = "localpkg"
version = "0.1.0"

[package.source]
type = "directory"
url = "../localpkg"
"""


def test_every_registry_package_is_pinned_once_per_version() -> None:
    layers = lock_requirements.locked_requirement_layers(_LOCK)
    assert layers == [
        ["certifi==2026.10.23", "filelock==4.2.10", "typing-extensions==4.15.0"],
        ["typing-extensions==4.16.0"],
    ]


def test_no_layer_names_a_package_twice() -> None:
    # pip-audit rejects a requirements file that repeats a package.
    for layer in lock_requirements.locked_requirement_layers(_LOCK):
        names = [line.split("==")[0] for line in layer]
        assert len(names) == len(set(names))


def test_real_lockfile_covers_every_registry_package() -> None:
    import tomllib

    text = (REPO_ROOT / "poetry.lock").read_text(encoding="utf-8")
    expected = {
        (p["name"].lower(), p["version"])
        for p in tomllib.loads(text)["package"]
        if p.get("source", {}).get("type") not in {"directory", "file", "git", "url"}
    }
    got = {
        tuple(line.split("=="))
        for layer in lock_requirements.locked_requirement_layers(text)
        for line in layer
    }
    assert got == expected
    assert expected  # an empty lock would make the audit vacuous


def test_main_writes_layer_files_and_clears_stale_ones(tmp_path: Path) -> None:
    lock = tmp_path / "poetry.lock"
    lock.write_text(_LOCK, encoding="utf-8")
    out = tmp_path / "req"
    out.mkdir()
    (out / "locked-7.txt").write_text("stale==1\n", encoding="utf-8")

    assert lock_requirements.main(["prog", str(out), str(lock)]) == 0

    assert sorted(p.name for p in out.glob("locked-*.txt")) == ["locked-0.txt", "locked-1.txt"]
    assert (out / "locked-1.txt").read_text(encoding="utf-8") == "typing-extensions==4.16.0\n"


def test_main_fails_on_an_empty_lockfile(tmp_path: Path) -> None:
    lock = tmp_path / "poetry.lock"
    lock.write_text("", encoding="utf-8")
    assert lock_requirements.main(["prog", str(tmp_path / "req"), str(lock)]) == 1


def test_main_requires_an_output_directory() -> None:
    assert lock_requirements.main(["prog"]) == 2


@pytest.mark.parametrize("source_type", ["directory", "file", "git", "url"])
def test_non_registry_sources_are_skipped(source_type: str) -> None:
    lock = f"""
[[package]]
name = "thing"
version = "1.0"

[package.source]
type = "{source_type}"
url = "x"
"""
    assert lock_requirements.locked_requirement_layers(lock) == []
