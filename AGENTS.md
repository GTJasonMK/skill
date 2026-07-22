# Repository Guidelines

## Project Structure & Module Organization

This repository is an Agent Skill package, not an application. The main package lives in `statistical-learning-analysis/`.

- `SKILL.md` is the skill entry point, workflow contract, and manual index.
- `scripts/` contains flat, standalone Python CLI tools. Shared helpers live in `scripts/quant_utils.py`; do not add script subdirectories.
- `references/` contains method maps, guardrails, report templates, and quant-finance guidance.
- `examples/` contains synthetic-data demos and shell pipelines. Generated demo data and outputs are written under `examples/data/` and `examples/out/`.
- `agents/openai.yaml` stores agent configuration.

## Build, Test, and Development Commands

Run commands from `statistical-learning-analysis/` unless noted.

```bash
pip install -r requirements.txt
pip install -r requirements-optional.txt
pip install -r requirements-dev.txt
```

Installs required `numpy`, `pandas`, and `scipy`; optional dependencies support `sklearn_tabular_model.py` and `cluster_quality_report.py`; dev dependencies support upstream skill validation.

```bash
bash scripts/smoke_check.sh --quick
bash scripts/smoke_check.sh --full
python3 scripts/<script_name>.py --help
python3 scripts/_check_skill_index.py
bash examples/run_alpha_pipeline.sh
bash examples/run_portfolio_pipeline.sh
bash examples/run_nonquant_examples.sh
```

Use quick smoke checks before every change handoff. Run the full smoke check after installing all requirements; it includes CLI help, upstream validation, and the three example pipelines. Use `_check_skill_index.py` when changing scripts or references.

## Coding Style & Naming Conventions

Use Python 3 scripts with `#!/usr/bin/env python3`, `from __future__ import annotations`, a top-level docstring, and `argparse` for CLIs. Prefer `snake_case` for filenames, functions, arguments, and JSON fields. Keep scripts standalone and executable from `scripts/`; if a feature belongs in shared numerical or CSV handling, extend `quant_utils.py` instead of duplicating logic. Use pandas/numpy/scipy for matrix and tabular work. Keep Markdown headings descriptive and update links when moving documents.

## Testing Guidelines

There is no dedicated coverage target in this checkout. Treat validation as: run `bash scripts/smoke_check.sh --quick`, execute changed scripts on small representative inputs, then run `bash scripts/smoke_check.sh --full` when dependencies are installed. For new scripts, add deterministic output examples or connect them to an existing demo chain when practical.

## Commit & Pull Request Guidelines

Git history is not available in this checkout, so use concise imperative commit messages such as `Add calibration report example` or `Update quant gate documentation`. Pull requests should describe the changed workflow, list validation commands and outputs, link any relevant issue, and include screenshots or report snippets only when Markdown/JSON output changed.

## Agent-Specific Instructions

When adding a script, update `SKILL.md` in both `## Scripts` and `## References`, add it to `references/implementation-map.md`, and consider quant reference updates if it supports finance workflows. Do not weaken guardrails in `SKILL.md`; they are part of the skill behavior contract.
