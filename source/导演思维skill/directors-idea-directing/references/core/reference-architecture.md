# Reference Architecture

This skill separates the source layer from the agent reasoning layer.

## Loading Order

```text
SKILL.md
-> references/core/decision-core.md
-> references/core/task-router.md
-> one topic reference
-> parent md note for chapter-level detail
-> txt/00_pages or PDF for exact wording
```

## Directory Roles

| Directory | Role |
| --- | --- |
| `references/core/` | Routing, source coverage, answer formats, and validation records. |
| `references/concepts/` | Compact concept distinctions: director's idea, competent/good/great directing, craft unity. |
| `references/methods/` | Procedures for script reading, interpretation, and craft translation. |
| `references/cases/` | Director and film case lookup with transfer limits. |
| `references/guardrails/` | Review rules for weak, decorative, or unsupported directing plans. |
| `md/` in the parent project | Complete chapter-level source notes for human reading and source-grounded reasoning. |
| `txt/00_pages/` in the parent project | Page-level extracted source text named by PDF page number. |

## Source Convention

The stable citation unit is PDF page number, not printed page number. In the body of the book, printed page number is usually PDF page minus 15; use the coverage map for exact source ranges.
