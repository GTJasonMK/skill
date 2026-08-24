#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  echo "Python environment not found at $PYTHON. Install with: python3 -m venv .venv && .venv/bin/pip install -e '.[all,dev]'" >&2
  exit 2
fi

"$PYTHON" scripts/check_bundle.py
"$PYTHON" scripts/sync_source_skills.py
"$PYTHON" scripts/check_no_live.py
"$ROOT/.venv/bin/ruff" check src scripts tests
"$ROOT/.venv/bin/ruff" check statistical-learning-analysis/scripts --select E9,F63,F7,F82
"$ROOT/.venv/bin/mypy" src/data_quant
"$ROOT/.venv/bin/pytest" -q

EXAMPLE_OUT="$(mktemp -d)"
cleanup() { rm -rf "$EXAMPLE_OUT"; }
trap cleanup EXIT
DATA_QUANT_EXAMPLE_OUT="$EXAMPLE_OUT" PATH="$ROOT/.venv/bin:$PATH" \
  bash statistical-learning-analysis/scripts/smoke_check.sh --full

echo "OK: Data-Quant full local validation passed."
