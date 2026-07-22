# Output Contracts

Use this reference when chaining bundled scripts, modifying JSON fields, writing gate scripts, or reviewing backward compatibility. Script output should be deterministic enough for downstream gates and review packs to consume without custom parsing.

## Contents

- [Stability Rules](#stability-rules)
- [Common Top-Level Fields](#common-top-level-fields)
- [Diagnostic Artifacts](#diagnostic-artifacts)
- [Gate Artifacts](#gate-artifacts)
- [Aggregation and Review Artifacts](#aggregation-and-review-artifacts)
- [Markdown and CSV Sidecars](#markdown-and-csv-sidecars)

## Stability Rules

- Use lower snake case for JSON keys.
- Serialize missing numeric values as JSON `null`, not `"NA"`, `NaN`, or omitted fields.
- Add fields compatibly; do not rename or remove consumed fields without leaving an alias.
- Gate and aggregator scripts should ignore unknown fields but fail loudly when a required input file is missing or malformed.
- Keep script output deterministic for fixed input, seed, and arguments.
- If a metric has directionality, include enough context in the key or surrounding section to avoid ambiguity, such as `max_drawdown`, `mean_rank_ic`, or `cost_bps`.

## Common Top-Level Fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `diagnostic_type` | Machine-readable artifact type. | Recommended for every JSON consumed by gates or aggregators. |
| `n`, `row_count`, `date_count`, `asset_count` | Sample size evidence. | Use the most specific available count. |
| `parameters` | Effective command settings. | Include when choices affect interpretation. |
| `summary` | Compact metric block. | Keep stable for downstream consumers. |
| `warnings` | Non-fatal concerns. | Use plain strings or objects with `code` and `message`. |
| `blockers` | Fatal or gate-stopping issues. | Use for gate inputs and gate outputs. |
| `evidence_gaps` | Missing proof needed before promotion. | Distinguish gaps from observed failures. |

## Diagnostic Artifacts

Single-purpose diagnostics should include enough fields to stand alone in a report and to feed a gate. Prefer this shape:

```json
{
  "diagnostic_type": "factor_ic",
  "parameters": {},
  "summary": {},
  "warnings": [],
  "blockers": [],
  "details": []
}
```

Use `details` for per-date, per-asset, per-bin, per-regime, or per-group rows. Keep large row-level outputs in CSV sidecars when JSON would become unwieldy.

## Gate Artifacts

Gate scripts convert multiple diagnostics into a decision. Use these fields consistently:

| Field | Meaning |
| --- | --- |
| `decision` | One of `pass`, `conditional_pass`, `review`, or `fail`. |
| `blockers` | Issues that prevent promotion. |
| `warnings` | Issues that require monitoring or explanation. |
| `evidence_gaps` | Missing diagnostics or documentation. |
| `inputs` | Input artifact paths or summaries used by the gate. |
| `decision_stack` | Ordered reasons supporting the final decision, when available. |

Never treat a missing required diagnostic as a pass. Use `review` or `fail` depending on severity.

## Aggregation and Review Artifacts

Aggregators and review packs should preserve source diagnostics rather than flattening away evidence. Include source artifact names, extracted common metrics, gate decisions, and role-specific open questions. When multiple diagnostics disagree, report the conflict instead of averaging it away.

## Markdown and CSV Sidecars

Markdown output is for humans and may be reformatted. JSON output is the stable machine contract. CSV sidecars are appropriate for long scored rows, anomaly rankings, or per-period tables; include the CSV path in JSON when a downstream user needs to find it.
