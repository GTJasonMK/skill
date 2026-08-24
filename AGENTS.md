# Repository Guidelines

## Project Structure & Module Organization

This repository is an Agent Skill package, not an application. The package is
under `10-data-quant/statistical-learning-analysis/`:

- `SKILL.md` defines the skill workflow and indexes its references.
- `scripts/` contains standalone Python CLIs; shared CSV and numerical helpers belong in `scripts/quant_utils.py`.
- `references/` contains method maps, guardrails, templates, and finance guidance.
- `examples/` contains synthetic-data demos and shell pipelines. Demo data and reports are written to `examples/data/` and `examples/out/`.
- `agents/openai.yaml` contains agent configuration.

Keep scripts flat and update the relevant indexes when adding files.

## Build, Test, and Development Commands

Run from `10-data-quant/statistical-learning-analysis/`:

```bash
pip install -r requirements.txt -r requirements-optional.txt -r requirements-dev.txt
bash scripts/smoke_check.sh --quick
bash scripts/smoke_check.sh --full
python3 scripts/<script_name>.py --help
python3 scripts/_check_skill_index.py
```

Use `--quick` for routine changes; `--full` also checks dependencies and all
example pipelines. Run the matching command when changing a pipeline:
`bash examples/run_alpha_pipeline.sh`,
`bash examples/run_portfolio_pipeline.sh`, or
`bash examples/run_nonquant_examples.sh`.

## Coding Style & Naming Conventions

Use Python 3 with `#!/usr/bin/env python3`, `from __future__ import annotations`,
a module docstring, and `argparse` for CLIs. Use four-space indentation,
`snake_case` filenames/functions/arguments, and clear Markdown headings. Prefer
the standard library where practical; use pandas, NumPy, and SciPy for tabular
or numerical work. Keep errors explicit and validate inputs at CLI boundaries.

## Testing Guidelines

There is no dedicated test suite or coverage threshold. Validate changed code
with the quick smoke check and a small representative CLI invocation. New
scripts should expose working `--help` output and, where practical, add a
deterministic fixture or example pipeline check.

## Commit & Pull Request Guidelines

History currently contains only `init`, so use concise imperative commits such
as `Add calibration report example`. Pull requests should explain the workflow
change, list validation commands and results, link the relevant issue, and
include report snippets when Markdown or JSON contracts change.

## Agent-Specific Instructions

When adding a script, update `SKILL.md` in both `## Scripts` and `## References`
and add it to `references/implementation-map.md`. Do not weaken the guardrails
or output contracts documented in `SKILL.md`.
