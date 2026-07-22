#!/usr/bin/env bash
# Run the alpha research diagnostic chain end-to-end on the bundled
# synthetic factor panel. Produces JSON + Markdown reports under
# examples/out/alpha/ and feeds them into alpha_research_gate_report.py.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SCRIPTS="$ROOT/scripts"
OUT="$HERE/out/alpha"
DATA="$HERE/data"

mkdir -p "$OUT"

# Regenerate data if missing
if [ ! -f "$DATA/factor_panel.csv" ]; then
    python3 "$HERE/generate_data.py"
fi

cd "$SCRIPTS"

echo "[1/6] factor_ic_report"
python3 factor_ic_report.py "$DATA/factor_panel.csv" \
    --date-col date --factor-col factor_value --forward-return-col forward_return_1d \
    --min-assets-per-date 6 \
    --output-json "$OUT/factor_ic.json" --output-md "$OUT/factor_ic.md" --format markdown > /dev/null

echo "[2/6] factor_turnover_report"
python3 factor_turnover_report.py "$DATA/factor_panel.csv" \
    --date-col date --asset-col asset --factor-col factor_value \
    --top-frac 0.25 --side long_short --min-assets-per-date 6 \
    --output-json "$OUT/factor_turnover.json" --output-md "$OUT/factor_turnover.md" --format markdown > /dev/null

echo "[3/6] signal_overlap_report"
python3 signal_overlap_report.py "$DATA/factor_panel.csv" \
    --date-col date --asset-col asset \
    --signal-cols factor_value,factor_redundant,factor_unrelated \
    --selection-frac 0.25 --selection-side both \
    --output-json "$OUT/signal_overlap.json" --output-md "$OUT/signal_overlap.md" --format markdown > /dev/null

echo "[4/6] incremental_alpha_report"
python3 incremental_alpha_report.py "$DATA/factor_panel.csv" \
    --date-col date --asset-col asset --forward-return-col forward_return_1d \
    --candidate-col factor_value --base-cols factor_redundant,factor_unrelated \
    --min-assets-per-date 6 --min-dates 3 \
    --output-json "$OUT/incremental_alpha.json" --output-md "$OUT/incremental_alpha.md" --format markdown > /dev/null

echo "[5/6] transaction_cost_report"
python3 transaction_cost_report.py "$DATA/portfolio_weights.csv" \
    --date-col date --asset-col asset --weight-col weight --return-col asset_return_1d \
    --commission-bps 1.0 --slippage-bps 2.0 \
    --output-json "$OUT/transaction_cost.json" --output-md "$OUT/transaction_cost.md" --format markdown > /dev/null

echo "[6/6] alpha_research_gate_report (consumes the JSON outputs above)"
python3 alpha_research_gate_report.py \
    "$OUT/factor_ic.json" \
    "$OUT/factor_turnover.json" \
    "$OUT/signal_overlap.json" \
    "$OUT/incremental_alpha.json" \
    "$OUT/transaction_cost.json" \
    --output-json "$OUT/alpha_research_gate.json" --output-md "$OUT/alpha_research_gate.md" \
    --format markdown > /dev/null

echo
echo "Done. Outputs in $OUT"
ls -1 "$OUT"
