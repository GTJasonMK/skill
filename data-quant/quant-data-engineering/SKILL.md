---
name: quant-data-engineering
description: "Quantitative data engineering workflow for canonical tables, permanent identifiers, trading calendars, point-in-time joins, corporate actions, universe reconstruction, return labels, vendor field mapping, data lineage, schema validation, freshness, and reproducibility. Use when local files, schemas, databases, vendor fields, timestamps, adjustments, or data-pipeline correctness determine whether a statistical or trading claim is auditable. 中文触发：量化数据工程、数据契约、证券主数据、交易日历、时区、复权、公司行动、历史成分股、未来函数、财报可用日、标签构建、数据血缘、供应商字段。"
---

# Quant Data Engineering

## Purpose

Use this Skill when data correctness can change the research conclusion. Convert source-specific files and tables into versioned canonical tables before factor, model, portfolio, execution, or risk work. A clean-looking CSV is not proof that its values were observable or tradable at the historical decision time.

## Core Workflow

1. Classify the table: security master, market bars, corporate actions, universe membership, point-in-time fundamentals, factor panel, labels, weights, orders, fills, risk inputs, or sessions.
2. Record source, vendor field definitions, units, currency, timezone, update policy, revision policy, and credential references.
3. Map source columns to a canonical contract from `../schemas/tables/` and preserve source-column provenance.
4. Validate required fields, types, primary keys, finite numbers, timezone-aware timestamps, and table-specific semantics.
5. Resolve permanent identifiers and effective symbol/venue intervals before joins.
6. Load an authoritative effective-dated trading calendar; do not sort or compare raw date strings.
7. Reconstruct point-in-time availability, revisions, universe membership, corporate actions, and tradability.
8. Build return labels from explicit decision, execution, return-start, and return-end times. Preserve `label_end_time` for purging.
9. Fingerprint inputs, write a `data_contract` Artifact, and pass only canonical tables plus Artifact IDs to research.
10. Fail closed when a required field, rule, or source definition is missing; use an evidence gap for research-only use when appropriate.

## Reference Routing

- Canonical table definitions and units: [references/data-contracts.md](references/data-contracts.md).
- Point-in-time joins, calendars, corporate actions, and labels: [references/pit-and-labels.md](references/pit-and-labels.md).
- Source adapters, credentials, lineage, and vendor uncertainty: [references/source-adapters.md](references/source-adapters.md).
- A-share-specific rules: `../factor-quant-analysis/references/data/a-share-data-details.md`.
- Shared handoff and stage semantics: `../references/workflow-contract.md` and `../references/decision-ontology.md`.

## Runtime

Use the root package and CLI:

```bash
pip install -e '..[dev]'
quantctl doctor
quantctl validate-manifest <manifest.yaml>
quantctl run <manifest.yaml> --output <run-dir>
```

The current built-in adapters cover CSV and, with the `io` extra, Parquet, DuckDB, SQLite, and SQLAlchemy sources. Credentials are environment-variable names only and are never serialized into artifacts or logs.

## Required Output

For artifact work, return:

- source objects and canonical table types;
- key/timestamp/unit mappings;
- checks performed and input fingerprint;
- blockers, warnings, and evidence gaps;
- canonical table or sidecar locations;
- `data_contract` Artifact IDs;
- whether the data is eligible for research only or for downstream promotion.

## Guardrails

- Never infer availability from report period or observation date alone.
- Never use the latest revised value as historical truth without a version available at the decision time.
- Never use current constituents, current symbols, future corporate actions, or future tradability flags in historical tests.
- Never fill suspension, missing quote, delisting, and non-trading days with one common rule.
- Never bridge a price gap when building returns unless the gap policy is explicit and recorded.
- Never embed passwords, tokens, or connection strings containing credentials in a manifest.
- Never promote data with unknown market-rule effective dates to paper or production use.
