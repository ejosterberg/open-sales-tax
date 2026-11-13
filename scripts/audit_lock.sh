#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
#
# Audit every package pinned in poetry.lock against known-vulnerability
# databases. Run by CI (the "Dependency audit" job) and by the pre-commit
# hook whenever poetry.lock changes, so the two cannot drift.
#
# It audits the LOCKFILE, not an installed environment: `poetry run
# pip-audit` can silently audit the wrong interpreter (it did on
# 2026-11-12). See scripts/lock_requirements.py for the conversion.
#
# Needs: pip-audit on PATH (or $PIP_AUDIT), and a Python >= 3.11 for
# tomllib (or $PYTHON; falls back to `poetry run python`).
# Exits non-zero if any locked package has a known vulnerability.
set -euo pipefail

cd "$(dirname "$0")/.."

PIP_AUDIT="${PIP_AUDIT:-pip-audit}"
if ! command -v "$PIP_AUDIT" >/dev/null 2>&1; then
  echo "audit_lock: pip-audit not found. Install it with: pipx install pip-audit" >&2
  exit 2
fi

py=()
for candidate in "${PYTHON:-}" python3 python; do
  [ -n "$candidate" ] || continue
  if "$candidate" -c "import tomllib" >/dev/null 2>&1; then py=("$candidate"); break; fi
done
if [ ${#py[@]} -eq 0 ]; then py=(poetry run python); fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

"${py[@]}" scripts/lock_requirements.py "$work" poetry.lock

status=0
for req in "$work"/locked-*.txt; do
  "$PIP_AUDIT" --requirement "$req" --no-deps --disable-pip --progress-spinner off || status=1
done

if [ "$status" -ne 0 ]; then
  echo "audit_lock: known vulnerabilities in poetry.lock -- run 'poetry update <pkg>' to a fixed version." >&2
fi
exit "$status"
