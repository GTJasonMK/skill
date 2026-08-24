from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "statistical-learning-analysis" / "scripts"


def test_legacy_factor_ic_cli_emits_v1_envelope_and_old_aliases(tmp_path: Path) -> None:
    rows = []
    for day in range(1, 4):
        for asset in range(6):
            rows.append(
                {
                    "date": f"2024-01-{day:02d}",
                    "asset": f"A{asset}",
                    "factor": asset,
                    "forward_return": asset * 0.01,
                }
            )
    csv_path = tmp_path / "factor.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    result = subprocess.run(
        [
            sys.executable,
            "factor_ic_report.py",
            str(csv_path),
            "--date-col",
            "date",
            "--factor-col",
            "factor",
            "--forward-return-col",
            "forward_return",
            "--min-assets-per-date",
            "5",
            "--format",
            "json",
        ],
        cwd=SCRIPT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "1.0"
    assert payload["artifact_type"] == "factor_ic"
    assert payload["artifact_id"].startswith("sha256:")
    assert payload["rank_ic_summary"]["mean"] == 1.0
    assert payload["summary"]["rank_ic_summary"] == payload["rank_ic_summary"]
