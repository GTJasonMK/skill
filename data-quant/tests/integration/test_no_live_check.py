from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "scripts/check_no_live.py"


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def test_current_bundle_passes_no_live_guard() -> None:
    result = run_checker(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "offline-only policy" in result.stdout


def test_guard_rejects_broker_import_and_live_action_call(tmp_path: Path) -> None:
    (tmp_path / "BUNDLE-MANIFEST.yaml").write_text(
        (
            "bundle:\n"
            "  offline_execution_only: true\n"
            "prohibited_capabilities:\n"
            "  - live_order_submission\n"
            "  - fund_transfer\n"
            "  - credential_storage\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'fixture'\nversion = '0.0.0'\ndependencies = []\n",
        encoding="utf-8",
    )
    source = tmp_path / "src/example.py"
    source.parent.mkdir()
    source.write_text("import ccxt\nclient.submit_order()\n", encoding="utf-8")

    result = run_checker(tmp_path)

    assert result.returncode == 1
    assert "prohibited import ccxt" in result.stdout
    assert "prohibited live-action call submit_order" in result.stdout
