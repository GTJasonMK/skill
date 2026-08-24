#!/usr/bin/env python3
"""Kaplan-Meier survival curve and log-rank diagnostic.

Input is a long CSV with one row per subject: a duration column (time to
event or censoring), an event indicator column (1 = event, 0 = censored),
and an optional group column. Reports KM survival estimates per group,
median survival, and a Mantel-Haenszel log-rank test across groups.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from quant_utils import read_dataframe, require_columns
from scipy.stats import chi2


def _km_estimate(durations: np.ndarray, events: np.ndarray) -> pd.DataFrame:
    df = pd.DataFrame({"t": durations, "e": events}).sort_values("t").reset_index(drop=True)
    rows = []
    at_risk = len(df)
    survival = 1.0
    var_cum = 0.0
    for t, g in df.groupby("t", sort=True):
        events_at_t = int(g["e"].sum())
        n_at_risk = at_risk
        n_events = events_at_t
        at_risk -= len(g)
        if n_events > 0 and n_at_risk > 0:
            survival = survival * (1.0 - n_events / n_at_risk)
            var_cum += n_events / (n_at_risk * (n_at_risk - n_events)) if n_at_risk > n_events else 0.0
        se = survival * np.sqrt(var_cum) if var_cum > 0 else 0.0
        rows.append(
            {
                "time": float(t),
                "n_at_risk": int(n_at_risk),
                "n_events": int(n_events),
                "n_censored": int(len(g) - n_events),
                "survival": float(survival),
                "std_error": float(se),
                "ci_lower": float(max(0.0, survival - 1.96 * se)),
                "ci_upper": float(min(1.0, survival + 1.96 * se)),
            }
        )
    return pd.DataFrame(rows)


def _median_survival(curve: pd.DataFrame) -> float | None:
    crossing = curve[curve["survival"] <= 0.5]
    if crossing.empty:
        return None
    return float(crossing["time"].iloc[0])


def _logrank(df: pd.DataFrame, group_col: str) -> dict[str, Any]:
    groups = sorted(df[group_col].dropna().unique())
    if len(groups) < 2:
        return {"statistic": None, "df": None, "p_value": None, "reason": "fewer_than_two_groups"}
    times = np.sort(df.loc[df["e"] == 1, "t"].unique())
    k = len(groups)
    observed = np.zeros(k)
    expected = np.zeros(k)
    variance = np.zeros((k, k))
    for t in times:
        at_risk_total = float((df["t"] >= t).sum())
        events_total = float(((df["t"] == t) & (df["e"] == 1)).sum())
        if at_risk_total <= 1 or events_total == 0:
            continue
        n_g = np.array([float(((df[group_col] == g) & (df["t"] >= t)).sum()) for g in groups])
        d_g = np.array(
            [float(((df[group_col] == g) & (df["t"] == t) & (df["e"] == 1)).sum()) for g in groups]
        )
        observed += d_g
        e_g = events_total * n_g / at_risk_total
        expected += e_g
        var_factor = events_total * (at_risk_total - events_total) / (at_risk_total - 1) / at_risk_total
        for i in range(k):
            variance[i, i] += var_factor * n_g[i] * (at_risk_total - n_g[i]) / at_risk_total
            for j in range(i + 1, k):
                variance[i, j] -= var_factor * n_g[i] * n_g[j] / at_risk_total
                variance[j, i] = variance[i, j]
    obs_minus_exp = (observed - expected)[:-1]
    cov_reduced = variance[:-1, :-1]
    try:
        stat = float(obs_minus_exp @ np.linalg.pinv(cov_reduced) @ obs_minus_exp)
    except np.linalg.LinAlgError:
        return {"statistic": None, "df": None, "p_value": None, "reason": "singular_covariance"}
    dof = k - 1
    p_value = float(1.0 - chi2.cdf(stat, dof))
    return {
        "statistic": stat,
        "df": dof,
        "p_value": p_value,
        "groups": [str(g) for g in groups],
        "observed_events": observed.tolist(),
        "expected_events": expected.tolist(),
    }


def build_report(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    group_col: str | None,
) -> dict[str, Any]:
    df = df.copy()
    df[duration_col] = pd.to_numeric(df[duration_col], errors="coerce")
    df[event_col] = pd.to_numeric(df[event_col], errors="coerce")
    rows_in = len(df)
    needed = [duration_col, event_col]
    if group_col:
        needed.append(group_col)
    df = df.dropna(subset=needed)
    df = df[(df[duration_col] > 0)]
    dropped = rows_in - len(df)
    df = df.rename(columns={duration_col: "t", event_col: "e"})
    df["e"] = df["e"].astype(int)

    by_group: dict[str, Any] = {}
    if group_col:
        for group, sub in df.groupby(group_col, sort=True):
            curve = _km_estimate(sub["t"].to_numpy(), sub["e"].to_numpy())
            by_group[str(group)] = {
                "n_subjects": int(len(sub)),
                "n_events": int(sub["e"].sum()),
                "n_censored": int(len(sub) - sub["e"].sum()),
                "median_survival": _median_survival(curve),
                "curve": curve.to_dict("records"),
            }
        log_rank = _logrank(df, group_col)
    else:
        curve = _km_estimate(df["t"].to_numpy(), df["e"].to_numpy())
        by_group["all"] = {
            "n_subjects": int(len(df)),
            "n_events": int(df["e"].sum()),
            "n_censored": int(len(df) - df["e"].sum()),
            "median_survival": _median_survival(curve),
            "curve": curve.to_dict("records"),
        }
        log_rank = None

    return {
        "duration_col": duration_col,
        "event_col": event_col,
        "group_col": group_col,
        "rows_dropped": dropped,
        "subjects_used": int(len(df)),
        "events": int(df["e"].sum()),
        "censored": int(len(df) - df["e"].sum()),
        "by_group": by_group,
        "log_rank": log_rank,
        "notes": [
            "Kaplan-Meier assumes independent right-censoring and a single absorbing event.",
            "Log-rank assumes proportional hazards; consider stratification or weighted tests when curves cross.",
            "Median survival is undefined when the curve never crosses 0.5.",
        ],
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Kaplan-Meier Survival Report",
        "",
        f"- Duration column: {report['duration_col']}",
        f"- Event column: {report['event_col']}",
        f"- Group column: {report['group_col'] or 'None'}",
        f"- Subjects used: {report['subjects_used']} (events {report['events']}, censored {report['censored']})",
        f"- Rows dropped: {report['rows_dropped']}",
        "",
        "| Group | N | Events | Censored | Median survival |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, info in report["by_group"].items():
        lines.append(
            f"| {name} | {info['n_subjects']} | {info['n_events']} | {info['n_censored']} | {info['median_survival']} |"
        )
    if report["log_rank"]:
        lr = report["log_rank"]
        lines.extend(
            [
                "",
                "## Log-Rank Test",
                "",
                f"- Statistic: {lr.get('statistic')}",
                f"- df: {lr.get('df')}",
                f"- p-value: {lr.get('p_value')}",
            ]
        )
    lines.extend(["", "Notes:"])
    lines.extend(f"- {note}" for note in report["notes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Kaplan-Meier survival curves and log-rank test.")
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--duration-col", required=True)
    parser.add_argument("--event-col", required=True)
    parser.add_argument("--group-col")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    df = read_dataframe(args.csv_path)
    required = [args.duration_col, args.event_col] + ([args.group_col] if args.group_col else [])
    require_columns(df, required)
    report = build_report(df, args.duration_col, args.event_col, args.group_col)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(markdown(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
