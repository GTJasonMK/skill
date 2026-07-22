#!/usr/bin/env bash
# Repository smoke checks for the statistical-learning-analysis skill.
#
# Usage:
#   bash scripts/smoke_check.sh --quick   # no third-party dependencies required
#   bash scripts/smoke_check.sh --full    # requires requirements + optional + dev deps

set -euo pipefail

MODE="${1:---quick}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1

if [[ "$MODE" != "--quick" && "$MODE" != "--full" ]]; then
    echo "Usage: bash scripts/smoke_check.sh [--quick|--full]" >&2
    exit 2
fi

echo "[1/7] SKILL.md frontmatter"
python3 - <<'PY'
from pathlib import Path
import re
import sys

text = Path("SKILL.md").read_text(encoding="utf-8")
match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
if not match:
    raise SystemExit("SKILL.md must start with YAML frontmatter")
frontmatter = match.group(1)
fields = {}
for line in frontmatter.splitlines():
    if ":" not in line:
        continue
    key, value = line.split(":", 1)
    fields[key.strip()] = value.strip().strip('"')
name = fields.get("name", "")
description = fields.get("description", "")
if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
    raise SystemExit(f"Invalid skill name: {name!r}")
if not description:
    raise SystemExit("SKILL.md frontmatter must include a description")
print(f"OK: {name}")
PY

echo "[2/7] Index consistency"
python3 scripts/_check_skill_index.py

echo "[3/7] Python syntax"
python3 - <<'PY'
from pathlib import Path
import ast

paths = sorted(Path("scripts").glob("*.py")) + [Path("examples/generate_data.py")]
for path in paths:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
print(f"OK: parsed {len(paths)} Python files")
PY

echo "[4/7] Standard-library CLI help"
for script in \
    profile_dataset.py \
    split_dataset.py \
    causal_balance_check.py \
    time_series_backtest.py \
    classification_report.py \
    threshold_tuning.py \
    missingness_report.py \
    panel_summary.py \
    compare_model_reports.py \
    quant_checklist_template.py
do
    python3 "scripts/$script" --help >/dev/null
done
echo "OK: standard-library CLI help"

echo "[5/7] Standard-library fixture reports"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
cat > "$TMP_DIR/classification.csv" <<'CSV'
id,y,score,group,date
1,1,0.90,A,2024-01-01
2,0,0.20,A,2024-01-02
3,1,0.70,B,2024-01-03
4,0,0.10,B,2024-01-04
CSV
python3 scripts/profile_dataset.py "$TMP_DIR/classification.csv" \
    --target y --group group --time date --format json >/dev/null
python3 scripts/classification_report.py "$TMP_DIR/classification.csv" \
    --truth y --score score --positive-label 1 --threshold 0.5 --format json >/dev/null
python3 scripts/quant_checklist_template.py --template go-live --format json >/dev/null
echo "OK: fixture reports"

echo "[6/7] Reference navigation"
python3 - <<'PY'
from pathlib import Path

missing = []
for path in sorted(Path("references").glob("*.md")):
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) > 100 and "## Contents" not in lines:
        missing.append(f"{path} ({len(lines)} lines)")
if missing:
    raise SystemExit("Reference files longer than 100 lines need ## Contents: " + ", ".join(missing))
print("OK: long references have contents sections")
PY

echo "[7/7] Full dependency and example checks"
if [[ "$MODE" == "--quick" ]]; then
    echo "SKIP: run 'bash scripts/smoke_check.sh --full' after installing requirements."
    exit 0
fi

python3 - <<'PY'
import importlib.util

required = {
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "sklearn": "scikit-learn",
    "joblib": "joblib",
    "yaml": "PyYAML",
}
missing = [package for module, package in required.items() if importlib.util.find_spec(module) is None]
if missing:
    raise SystemExit(
        "Missing dependencies: "
        + ", ".join(missing)
        + ". Install with: pip install -r requirements.txt -r requirements-optional.txt -r requirements-dev.txt"
    )
print("OK: full dependency set")
PY

python3 - <<'PY' > "$TMP_DIR/help_scripts.txt"
from pathlib import Path

for path in sorted(Path("scripts").glob("*.py")):
    text = path.read_text(encoding="utf-8")
    if "argparse.ArgumentParser" in text:
        print(path)
PY

while IFS= read -r script; do
    python3 "$script" --help >/dev/null
done < "$TMP_DIR/help_scripts.txt"

validator="$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$validator" ]]; then
    python3 "$validator" "$ROOT"
fi

bash examples/run_alpha_pipeline.sh >/dev/null
bash examples/run_portfolio_pipeline.sh >/dev/null
bash examples/run_nonquant_examples.sh >/dev/null
python3 - <<'PY'
import json
from pathlib import Path

allowed = {"pass", "conditional_pass", "review", "fail"}
gate_paths = [
    Path("examples/out/alpha/alpha_research_gate.json"),
    Path("examples/out/portfolio/portfolio_construction_gate.json"),
]
for path in gate_paths:
    if not path.exists():
        raise SystemExit(f"Expected gate output missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    decision = data.get("decision")
    gate_decision = data.get("gate_decision")
    if decision != gate_decision or decision not in allowed:
        raise SystemExit(f"Invalid decision fields in {path}: decision={decision!r}, gate_decision={gate_decision!r}")
    for field in ["blockers", "warnings", "evidence_gaps"]:
        if not isinstance(data.get(field), list):
            raise SystemExit(f"{path} must contain list field {field!r}")
print("OK: example gate output contracts")
PY
echo "OK: full smoke checks"
