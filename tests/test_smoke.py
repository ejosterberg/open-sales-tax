# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Smoke tests — prove the package imports and the version is set."""

import re

from opensalestax import __version__


def test_version_is_set() -> None:
    """``__version__`` is a non-empty string in semver-ish format."""
    assert isinstance(__version__, str)
    assert __version__
    # Allow pre-release suffixes (a1, b2, rc1, dev0, etc.)
    assert re.match(r"^\d+\.\d+\.\d+", __version__), (
        f"unexpected __version__ format: {__version__!r}"
    )


def test_package_imports() -> None:
    """Top-level package and key subpackages import cleanly."""
    import opensalestax  # noqa: F401
    import opensalestax.api  # noqa: F401
    import opensalestax.api.v1  # noqa: F401
    import opensalestax.cli  # noqa: F401
    import opensalestax.core  # noqa: F401
    import opensalestax.data  # noqa: F401
    import opensalestax.db  # noqa: F401
    import opensalestax.states  # noqa: F401
