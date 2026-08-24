#!/usr/bin/env python3
"""Benchmark canonical factor-panel validation on a synthetic large table."""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from data_quant.contracts.tables import get_table_contract  # noqa: E402
from data_quant.io.validation import canonicalize_table  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--assets", type=int, default=1_000)
    parser.add_argument("--max-rss-mb", type=float, default=4_096.0)
    args = parser.parse_args()
    if args.rows <= 0 or args.assets <= 0 or args.rows % args.assets != 0:
        raise SystemExit("--rows must be positive and divisible by --assets.")

    periods = args.rows // args.assets
    timestamps = pd.date_range("2000-01-01", periods=periods, freq="D", tz="UTC")
    frame = pd.DataFrame(
        {
            "as_of": np.repeat(timestamps.to_numpy(), args.assets),
            "asset_id": np.tile([f"A{index:05d}" for index in range(args.assets)], periods),
            "signal": "benchmark",
            "value": np.sin(np.arange(args.rows, dtype=float) / 100.0),
            "available_at": np.repeat(timestamps.to_numpy(), args.assets),
        }
    )
    started = time.perf_counter()
    result = canonicalize_table(frame, get_table_contract("factor_panel"))
    elapsed = time.perf_counter() - started
    max_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    payload = {
        "rows": len(result.frame),
        "assets": args.assets,
        "periods": periods,
        "elapsed_seconds": elapsed,
        "max_rss_mb": max_rss_mb,
        "max_rss_limit_mb": args.max_rss_mb,
        "pass": max_rss_mb <= args.max_rss_mb,
    }
    print(json.dumps(payload, indent=2))
    return 0 if payload["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
