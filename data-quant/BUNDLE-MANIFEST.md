# Data-Quant Hybrid Bundle

`BUNDLE-MANIFEST.yaml` is the canonical machine-readable inventory. This file summarizes it for human review.

## Canonical Entry

- `SKILL.md`: unified router and shared evidence contract.
- `references/routing-matrix.md`: primary/supporting route selection.
- `references/workflow-contract.md`: stage handoffs.
- `references/decision-ontology.md`: stage, decision, action, and claim strength.

## Active Child Skills

- `statistical-learning-analysis/`: general statistical method selection and bundled diagnostics.
- `factor-quant-analysis/`: equity factors, empirical asset pricing, and A-share workflows.
- `quant-trading-black-box-analysis/`: strategy components, execution, HFT, risk, and diligence.
- `quant-data-engineering/`: canonical tables, identifiers, calendars, point-in-time data, and labels.

## Active Asset-Class Skills

- `futures-quant-analysis/`
- `options-volatility-analysis/`
- `fixed-income-quant-analysis/`
- `fx-quant-analysis/`
- `crypto-quant-analysis/`

Each uses the shared machine contracts and offline-only runtime; none submits live orders.

## Runtime

- Python package: `src/data_quant/`
- CLI: `quantctl`
- Machine contracts: `schemas/`

## Safety Boundary

The bundle performs research, simulation, replay, monitoring, and audit. It never submits live orders, transfers funds, or stores credentials.
