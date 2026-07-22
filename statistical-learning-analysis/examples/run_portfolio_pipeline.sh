#!/usr/bin/env bash
# Run the portfolio-construction diagnostic chain on the bundled synthetic
# portfolio weights and asset returns. Produces JSON + Markdown reports
# under examples/out/portfolio/ and feeds them into
# portfolio_construction_gate_report.py.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SCRIPTS="$ROOT/scripts"
OUT="$HERE/out/portfolio"
DATA="$HERE/data"

mkdir -p "$OUT"

if [ ! -f "$DATA/portfolio_weights.csv" ]; then
    python3 "$HERE/generate_data.py"
fi

cd "$SCRIPTS"

echo "[1/5] portfolio_backtest"
python3 portfolio_backtest.py "$DATA/portfolio_weights.csv" \
    --date-col date --asset-col asset --weight-col weight --return-col asset_return_1d \
    --cost-bps 5.0 \
    --output-json "$OUT/portfolio_backtest.json" --output-md "$OUT/portfolio_backtest.md" --format markdown > /dev/null

echo "[2/5] portfolio_exposure_report"
python3 portfolio_exposure_report.py "$DATA/portfolio_weights.csv" \
    --date-col date --asset-col asset --weight-col weight \
    --category-exposure-cols sector \
    --output-json "$OUT/portfolio_exposure.json" --output-md "$OUT/portfolio_exposure.md" --format markdown > /dev/null

echo "[3/5] portfolio_constraint_check"
python3 portfolio_constraint_check.py "$DATA/portfolio_weights.csv" \
    --date-col date --asset-col asset --weight-col weight \
    --category-cols sector \
    --max-gross 1.2 --min-net -0.05 --max-net 0.05 --max-abs-weight 0.25 \
    --output-json "$OUT/portfolio_constraints.json" --output-md "$OUT/portfolio_constraints.md" --format markdown > /dev/null

echo "[4/5] performance_attribution_report"
python3 performance_attribution_report.py "$DATA/portfolio_weights.csv" \
    --date-col date --asset-col asset --weight-col weight --return-col asset_return_1d \
    --group-cols sector \
    --output-json "$OUT/performance_attribution.json" --output-md "$OUT/performance_attribution.md" --format markdown > /dev/null

echo "[5/5] portfolio_construction_gate_report"
python3 portfolio_construction_gate_report.py \
    "$OUT/portfolio_backtest.json" \
    "$OUT/portfolio_constraints.json" \
    "$OUT/portfolio_exposure.json" \
    --output-json "$OUT/portfolio_construction_gate.json" --output-md "$OUT/portfolio_construction_gate.md" \
    --format markdown > /dev/null

echo
echo "Done. Outputs in $OUT"
ls -1 "$OUT"
