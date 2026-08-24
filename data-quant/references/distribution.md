# Data-Quant Distribution And Version Contract

Data-Quant has two deliberate distribution surfaces:

1. **Full source Skill bundle** — the repository/archive rooted at `data-quant/`. It contains the root router, child Skills, schemas, source registry, compatibility scripts, examples, synchronization tools, CI checks, and the Python runtime source. The 64 legacy CLIs are executable only on this surface.
2. **`data-quant-core` runtime wheel** — the installable package built from `src/data_quant/`. It contains contracts, canonical data utilities, diagnostics, pipeline, portfolio/backtest/execution/risk/monitoring baselines, and `quantctl`. It intentionally does not duplicate Skill Markdown, source mirrors, schemas, examples, or legacy scripts inside site-packages.

`quantctl list-capabilities` remains a complete catalog on both surfaces. In a runtime-only wheel, legacy entries report `available: false`, `execution_mode: source_bundle_required`; attempting to run one fails explicitly instead of advertising a broken executable path. Native core capabilities remain available. `quantctl validate-bundle` likewise requires the full source bundle.

## Version Policy

- `BUNDLE-MANIFEST.yaml` and root `SKILL.md` version the full Skill/contract distribution.
- `pyproject.toml` and `data_quant.__version__` version the Python runtime wheel.
- The two versions may advance independently, but every Bundle release records the compatible runtime project and lock, and CI tests the wheel built from the same checkout.

## Release Checks

```bash
bash scripts/full_check.sh
python -m build --wheel --no-isolation
pytest -q tests/integration/test_wheel_distribution.py
```

The wheel acceptance test builds from a clean temporary project, installs without source-bundle assets, verifies truthful legacy availability, and runs a core Manifest pipeline. Neither distribution includes live-order, fund-transfer, or credential-storage capability.
