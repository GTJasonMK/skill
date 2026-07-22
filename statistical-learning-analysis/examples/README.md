# Examples

End-to-end demos of the bundled skill. Three diagnostic chains using
synthetic data with a fixed random seed.

## Setup

```bash
pip install -r ../requirements.txt
# optional, only needed for cluster_quality_report.py and sklearn_tabular_model.py
pip install -r ../requirements-optional.txt
```

The demo shells will call `generate_data.py` automatically the first time
they run. To refresh data, delete `examples/data/` and rerun any shell.

## Demos

| Shell | What it does |
| --- | --- |
| `bash run_alpha_pipeline.sh` | Cross-sectional IC → turnover → multi-signal overlap → incremental alpha vs base set → transaction cost → **alpha research gate** decision |
| `bash run_portfolio_pipeline.sh` | Portfolio backtest → sector/category exposure → constraint check → performance attribution → **portfolio construction gate** decision |
| `bash run_nonquant_examples.sh` | Kaplan-Meier with log-rank by group, Mahalanobis anomaly score with chi-square reference, k-means cluster quality with bootstrap ARI stability, probability calibration with ECE and Brier |

Each shell writes JSON + Markdown outputs under `examples/out/<chain>/`.
The gate scripts in the first two chains consume the JSON from the
earlier steps — that is the **canonical pattern** for chaining bundled
diagnostics in real research workflows.

## Data sources (synthetic, seed 42)

| File | Schema | Notes |
| --- | --- | --- |
| `data/factor_panel.csv` | `date,asset,sector,factor_value,factor_redundant,factor_unrelated,forward_return_1d` | 12 assets × 20 dates. `factor_value` has a real but noisy edge; `factor_redundant` correlates with it (~0.7); `factor_unrelated` is pure noise. |
| `data/portfolio_weights.csv` | `date,asset,sector,weight,asset_return_1d` | Long top-3 / short bottom-3 by `factor_value` per date, equal-weighted. |
| `data/benchmark_returns.csv` | `date,return` | Reserved for future demos. |
| `data/survival_cohort.csv` | `subject_id,duration,event,group` | 60 subjects across groups A (higher hazard) and B (lower hazard). |
| `data/classification_scores.csv` | `y_true,score` | 200 rows, generally well-calibrated. |
| `data/anomaly_features.csv` | `row_id,feature_x,feature_y,feature_z` | 195 main + 5 planted outliers far from the cluster. |
| `data/cluster_features.csv` | `point_id,x,y,true_cluster` | 3 separated 2-D blobs. |

## Reading the outputs

- Markdown files (`*.md`) are the human-readable per-script reports.
- JSON files (`*.json`) are the canonical artifacts. Downstream gate /
  aggregator scripts consume them: see `alpha_research_gate_report.py`,
  `portfolio_construction_gate_report.py`, `quant_report_aggregator.py`,
  `quant_review_pack.py`.
- The gate scripts return one of: `pass`, `conditional_pass`, `review`,
  `fail`, with reasons and evidence gaps.

## Caveats

- Sample sizes are intentionally small for fast iteration. On real
  10k+ row factor panels the relative speed advantage of the
  vectorized implementation versus the previous pure-stdlib version is
  several orders of magnitude.
- The synthetic data is meant to make the demos return *something*
  interpretable, not to model real markets.
