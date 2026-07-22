# Reference Architecture

Use when: the agent needs to understand the reference directory layout, choose the next category to load, or avoid loading detailed knowledge before the current decision is clear.

Purpose: make the directory structure enforce the intended reasoning order. Start from control files, then load evidence, strategy, method, model, practice, or theory files only when the current uncertainty requires them.

## Contents

- [Default Loading Order](#default-loading-order)
- [Directory Roles](#directory-roles)
- [Task-Oriented Paths](#task-oriented-paths)
- [Do Not](#do-not)

## Default Loading Order

Use this order unless the user asks for exact source coverage:

```text
core/decision-core.md
-> core/task-router.md
-> core/full-analysis-run-record.md only for complete analysis, audit, repair, or stage-gate records
-> one task-specific directory
-> strategy/research-governance.md when evidence, iteration, or promotion decisions appear
-> core/report-templates.md when a user-facing deliverable is needed
```

Do not load an entire directory. Load the smallest file set that can answer the next decision.

## Directory Roles

| Directory | Role | Start here when |
| --- | --- | --- |
| `core/` | Reasoning spine, task routing, analysis run records, report shapes, source coverage, Chinese term routing. | The request is broad, ambiguous, needs a complete process record, or needs final output discipline. |
| `data/` | Data artifacts, implementation details, point-in-time data, A-share data rules, external lookup. | Files, fields, schemas, code, backtests, weights, trades, APIs, vendor definitions, or market rules matter. |
| `strategy/` | Strategy entrypoint discovery, worked examples, build-diagnose-repair loops, research governance, forward tests. | The user wants to develop, debug, iterate, promote, pause, or retire a factor strategy. |
| `methods/` | Method anchors, econometric tests, model/anomaly construction recipes. | The current uncertainty is which statistical method, construction recipe, or test matches the claim. |
| `models-factors/` | Factor and model catalog, A-share model evidence, mechanism diagnostics. | The task needs specific factor families, local model evidence, or mechanism interpretation. |
| `playbooks/` | Execution playbooks for research, data/backtest review, and portfolio/ML workflows. | A task needs a full procedural workflow after the first decision is known. |
| `practice/` | Portfolio practice, Smart Beta, ML/frontiers, validation, costs, capacity, risks. | The claim must become an investable portfolio, product, optimizer, timing rule, or production review. |
| `theory/` | Foundations, behavioral finance, factor zoo, and fundamental/quantamental context. | The user asks conceptual questions or the mechanism needs theoretical grounding. |

## Task-Oriented Paths

| Task shape | Load path |
| --- | --- |
| Broad factor-strategy request | [decision-core.md](decision-core.md), then [task-router.md](task-router.md). |
| Dataset or field list arrives first | [decision-core.md](decision-core.md), [../data/data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), [../strategy/strategy-worked-examples.md](../strategy/strategy-worked-examples.md). |
| Need strategy entrypoint and first baseline | [decision-core.md](decision-core.md), [../methods/method-idea-anchors.md](../methods/method-idea-anchors.md), [../strategy/strategy-development-map.md](../strategy/strategy-development-map.md). |
| Strategy flaw or surprising result | [decision-core.md](decision-core.md), [../strategy/strategy-development-map.md](../strategy/strategy-development-map.md), [../strategy/research-governance.md](../strategy/research-governance.md). |
| Complete analysis, workflow record, strategy run record, or end-to-end audit | [decision-core.md](decision-core.md), [task-router.md](task-router.md), [full-analysis-run-record.md](full-analysis-run-record.md), then only the task-specific references needed by the current uncertainty. |
| Promotion, paper trading, live monitoring, reduction, pause, or retirement | [decision-core.md](decision-core.md), [../strategy/research-governance.md](../strategy/research-governance.md), [report-templates.md](report-templates.md). |
| Exact chapter coverage or source lookup | [source-coverage-map.md](source-coverage-map.md), then the original local `md/` summaries if exact values are required. |
| Exact API, library, vendor, market-rule, or paper-construction uncertainty | [../data/data-analysis-and-external-research.md](../data/data-analysis-and-external-research.md), then the task-specific reference. |

## Do Not

- Do not start from deep methods, model catalogs, or theory files before naming the object and timing.
- Do not load every file in a directory because one file in that directory was useful.
- Do not use directory names as evidence. Use the referenced file's actual checks, rules, and output contracts.
- Do not bypass [decision-core.md](decision-core.md) for strategy design, repair, audit, or promotion tasks.
- Do not bypass [full-analysis-run-record.md](full-analysis-run-record.md) when the user asks for a complete analysis, workflow record, strategy run record, end-to-end audit, or production-readiness reasoning trace.
- Do not bypass [../strategy/research-governance.md](../strategy/research-governance.md) when evidence conflicts or stage decisions are involved.
