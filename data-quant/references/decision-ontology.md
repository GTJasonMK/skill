# Shared Decision Ontology

This file is the single source of truth for the shared evidence-priority ordering and the stage/decision/action/claim-strength vocabulary. Child Skills may restate these for self-containment (including the governed book-derived mirrors), but any divergence resolves in favor of this file. Do not introduce a competing ordering or vocabulary in the root layer.

The four dimensions below are orthogonal. Do not use a stage label as a gate result or an action as evidence strength.

## Stage

| Value | Meaning |
| --- | --- |
| `idea` | Falsifiable claim and data path are being defined. |
| `research_candidate` | Timing, universe, labels, and minimum test can be reconstructed. |
| `validated_component` | The component has claim-appropriate out-of-sample or stress evidence. |
| `portfolio_candidate` | Net performance, constraints, risk, costs, and capacity are tested. |
| `paper_trading` | Frozen code/data path, locked test, execution assumptions, and monitoring exist. |
| `production_candidate` | Paper evidence, limits, rollback, ownership, and disaster controls exist. |
| `live_monitoring` | A live process is being observed; this bundle still does not place orders. |
| `retired` | The strategy or component is no longer eligible for promotion or trading. |

## Decision

- `pass`: every required check for the named gate passed.
- `conditional_pass`: no blocker, but named warnings/evidence gaps require conditions.
- `review`: evidence is incomplete, conflicting, or not strong enough to decide.
- `fail`: at least one mandatory check failed.

## Action

- `promote`, `hold`, `downgrade`, `reject`, `pause`, `retire`.

## Claim Strength

- `not_determinable`
- `research_only`
- `validated_component`
- `portfolio_candidate`
- `paper_candidate`
- `production_candidate`

## Legacy Mapping

- Legacy gate `gate_decision` maps directly to `decision`.
- Factor `research-only` maps to `claim_strength=research_only`, not `decision=pass`.
- `paper trade` maps to stage/action only after a gate decision supports it.
- Black-box `investigate` or `modify` maps to `decision=review`, `action=hold`, with an explicit defect and experiment.
- `reduce` maps to `action=downgrade`; `stop` maps to `action=pause` or `retire` according to reversibility.

## Evidence Priority

Observable timing > universe/tradability > execution > net value > OOS/live stability > risk/capacity > mechanism > significance > in-sample fit.
