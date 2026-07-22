#!/usr/bin/env python3
"""Generate reproducible synthetic example data for the bundled demos.

Run once to populate examples/data/*.csv. Re-run any time to refresh.
Uses numpy/pandas; seed is fixed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    rng = np.random.default_rng(42)
    n_assets = 12
    n_dates = 20
    dates = pd.date_range("2026-04-01", periods=n_dates, freq="B").strftime("%Y-%m-%d")
    assets = [f"A{i:02d}" for i in range(n_assets)]
    sectors = ["tech", "fin", "indu", "hlth"]
    sector_map = {asset: sectors[i % len(sectors)] for i, asset in enumerate(assets)}

    # Factor panel: true forward return = 0.4 * factor + noise; introduces a real but noisy signal
    rows = []
    for date in dates:
        true_factor = rng.standard_normal(n_assets)
        noise = rng.standard_normal(n_assets) * 0.02
        forward_ret = 0.004 * true_factor + noise
        # add a redundant signal that correlates with factor_value but is noisier
        redundant = true_factor * 0.7 + rng.standard_normal(n_assets) * 0.6
        # uncorrelated control signal
        unrelated = rng.standard_normal(n_assets)
        for asset, fv, ret, red, unr in zip(assets, true_factor, forward_ret, redundant, unrelated):
            rows.append({
                "date": date,
                "asset": asset,
                "sector": sector_map[asset],
                "factor_value": fv,
                "factor_redundant": red,
                "factor_unrelated": unr,
                "forward_return_1d": ret,
            })
    factor_df = pd.DataFrame(rows)
    factor_df.to_csv(DATA_DIR / "factor_panel.csv", index=False)

    # Portfolio weights: long top 3 factor names, short bottom 3, equal-weight; aligned with factor_panel
    weights_rows = []
    for date in dates:
        snap = factor_df[factor_df["date"] == date].sort_values("factor_value")
        bottoms = snap.head(3)["asset"].tolist()
        tops = snap.tail(3)["asset"].tolist()
        for asset in assets:
            if asset in tops:
                w = 1.0 / 6
            elif asset in bottoms:
                w = -1.0 / 6
            else:
                w = 0.0
            weights_rows.append({
                "date": date,
                "asset": asset,
                "sector": sector_map[asset],
                "weight": w,
                "asset_return_1d": float(factor_df[(factor_df["date"] == date) & (factor_df["asset"] == asset)]["forward_return_1d"].iloc[0]),
            })
    weights_df = pd.DataFrame(weights_rows)
    weights_df.to_csv(DATA_DIR / "portfolio_weights.csv", index=False)

    # Benchmark daily returns
    bench = pd.DataFrame({"date": dates, "return": rng.normal(0.0005, 0.01, n_dates)})
    bench.to_csv(DATA_DIR / "benchmark_returns.csv", index=False)

    # Survival cohort: 50 subjects, two groups, group A hazards higher
    n_subj = 60
    group = rng.choice(["A", "B"], size=n_subj)
    lam = np.where(group == "A", 0.06, 0.03)
    time_to_event = rng.exponential(scale=1.0 / lam)
    censor_time = rng.exponential(scale=30, size=n_subj)
    duration = np.minimum(time_to_event, censor_time)
    event = (time_to_event <= censor_time).astype(int)
    surv = pd.DataFrame({
        "subject_id": np.arange(n_subj),
        "duration": np.round(duration, 2),
        "event": event,
        "group": group,
    })
    surv.to_csv(DATA_DIR / "survival_cohort.csv", index=False)

    # Classification scores with imperfect but reasonable calibration
    n = 200
    p_true = rng.beta(2, 2, size=n)  # true positive probabilities
    score = np.clip(p_true + rng.normal(0, 0.08, n), 0.0, 1.0)
    y = rng.binomial(1, p_true)
    clf = pd.DataFrame({"y_true": y, "score": np.round(score, 4)})
    clf.to_csv(DATA_DIR / "classification_scores.csv", index=False)

    # Multivariate anomaly source: well-behaved cluster + 5 outliers
    n_main = 195
    n_out = 5
    X_main = rng.multivariate_normal([0.0, 0.0, 0.0], [[1, 0.3, 0], [0.3, 1, -0.2], [0, -0.2, 1]], size=n_main)
    X_out = rng.multivariate_normal([6.0, -6.0, 5.0], np.eye(3) * 0.5, size=n_out)
    X = np.vstack([X_main, X_out])
    idx = rng.permutation(len(X))
    anom = pd.DataFrame({
        "row_id": np.arange(len(X)),
        "feature_x": X[idx, 0],
        "feature_y": X[idx, 1],
        "feature_z": X[idx, 2],
    })
    anom.to_csv(DATA_DIR / "anomaly_features.csv", index=False)

    # Cluster source: 3 well-separated 2-D blobs
    n_per = 40
    centers = np.array([[0, 0], [5, 5], [-5, 5]])
    blobs = []
    labels = []
    for ci, c in enumerate(centers):
        blobs.append(rng.normal(loc=c, scale=0.7, size=(n_per, 2)))
        labels.extend([f"cluster_{ci}"] * n_per)
    pts = np.vstack(blobs)
    clu = pd.DataFrame({
        "point_id": np.arange(len(pts)),
        "x": pts[:, 0],
        "y": pts[:, 1],
        "true_cluster": labels,
    })
    clu.to_csv(DATA_DIR / "cluster_features.csv", index=False)

    print(f"Wrote 7 CSV files into {DATA_DIR}")


if __name__ == "__main__":
    main()
