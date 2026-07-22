# Task Router

Load the smallest bundle that answers the user's request.

| Task | Use when | Minimum references | Add only if needed | Output shape |
| --- | --- | --- | --- | --- |
| Explain the framework | User asks what "director's idea" means or how Dancyger grades directing | `core/decision-core.md`, `concepts/directors-idea-framework.md` | `core/source-coverage-map.md` for exact chapter lookup | Concept distinction, example, misuse warning |
| Apply to a script or scene | User gives story material and wants a directing approach | `methods/script-interpretation-playbook.md`, `core/decision-core.md` | chapter notes 6-8 if craft channel is unclear | Candidate idea, craft plan, assumptions, failure tests |
| Review a directing plan | User asks whether a proposal works or follows the book | `guardrails/directing-review-guardrails.md`, `core/decision-core.md` | `concepts/directors-idea-framework.md` for definitions | Findings by severity, fix, source basis |
| Compare directors | User asks about Eisenstein, Ford, Stevens, Wilder, Lubitsch, Kazan, Truffaut, Polanski, Kubrick, Spielberg, Von Trotta, Moodysson, Breillat, or Harron | `cases/case-index.md` | relevant parent chapter notes | Comparison table and transfer limits |
| Source lookup | User asks where the book covers a term, chapter, director, film, or method | `core/source-coverage-map.md` | parent `md/` note, then raw page text | Source paths and brief answer |
| Exact quote or page-specific claim | User asks for exact wording, page, or quote | `core/source-coverage-map.md` | raw `txt/` and PDF inspection | Exact lookup path, quoted only after checking |
| Teaching or critique output | User wants a lesson plan, rubric, or structured critique | `core/report-templates.md`, relevant topic reference | parent `md/` notes for source grounding | Reusable rubric or teaching outline |

## Routing Discipline

- Do not load every case chapter for a general question about the framework.
- Do not answer a case comparison from the concept file alone; use `cases/case-index.md` first.
- Do not infer exact quotations from Markdown notes. Exact wording requires raw page text or PDF inspection.
