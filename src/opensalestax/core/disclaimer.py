# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Standard disclaimer text required on every calculation response.

Constitution §13: "Every API response and the documentation must
clearly disclaim this." This module is the single source of truth
for that text so it doesn't drift across endpoints.
"""

from __future__ import annotations

DISCLAIMER: str = (
    "Calculation only; not legal or tax advice. Verify against your "
    "state Department of Revenue before remitting."
)


def disclaimer() -> str:
    """Return the standard disclaimer string.

    Wrapped in a function so callers don't have to import a
    module-level constant -- makes mocking and i18n easier later
    without changing call sites.
    """
    return DISCLAIMER
