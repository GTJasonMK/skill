#!/usr/bin/env bash
# Run the 4 non-quant diagnostic scripts (survival KM, anomaly score,
# cluster quality, probability calibration) on bundled synthetic data.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
SCRIPTS="$ROOT/scripts"
OUT="${DATA_QUANT_EXAMPLE_OUT:-$HERE/out}/nonquant"
DATA="$HERE/data"

mkdir -p "$OUT"

if [ ! -f "$DATA/survival_cohort.csv" ]; then
    python3 "$HERE/generate_data.py"
fi

cd "$SCRIPTS"

echo "[1/4] survival_km_report"
python3 survival_km_report.py "$DATA/survival_cohort.csv" \
    --duration-col duration --event-col event --group-col group \
    --output-json "$OUT/survival_km.json" --output-md "$OUT/survival_km.md" --format markdown > /dev/null

echo "[2/4] anomaly_score_report (mahalanobis)"
python3 anomaly_score_report.py "$DATA/anomaly_features.csv" \
    --columns feature_x,feature_y,feature_z --method mahalanobis --threshold 3.5 --top-k 10 \
    --id-col row_id \
    --output-csv "$OUT/anomaly_scores.csv" \
    --output-json "$OUT/anomaly_score.json" --output-md "$OUT/anomaly_score.md" --format markdown > /dev/null

echo "[3/4] cluster_quality_report (kmeans k=3 + bootstrap stability)"
python3 cluster_quality_report.py "$DATA/cluster_features.csv" \
    --feature-cols x,y --k 3 --bootstrap 15 --seed 7 \
    --output-json "$OUT/cluster_quality.json" --output-md "$OUT/cluster_quality.md" --format markdown > /dev/null

echo "[4/4] calibration_report"
python3 calibration_report.py "$DATA/classification_scores.csv" \
    --label-col y_true --score-col score --bins 10 --binning equal_frequency \
    --output-json "$OUT/calibration.json" --output-md "$OUT/calibration.md" --format markdown > /dev/null

echo
echo "Done. Outputs in $OUT"
ls -1 "$OUT"
