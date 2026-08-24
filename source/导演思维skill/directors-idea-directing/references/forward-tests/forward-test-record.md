# Forward Test Record

This record checks whether the generated skill routes tasks through the smallest useful references and escalates to source notes only when needed.

| Prompt | References loaded | Answer shape | Verdict | Notes |
| --- | --- | --- | --- | --- |
| Explain the central framework of *The Director's Idea*. | `SKILL.md`, `references/core/decision-core.md`, `references/concepts/directors-idea-framework.md` | Define director's idea; distinguish theme, style, plot, competent/good/great directing; name source notes for exact lookup. | pass | The route avoids loading all chapter notes and gives book-specific distinctions. |
| Where does the book cover camera movement, and what files should I inspect? | `references/core/source-coverage-map.md`, then `md/第7章_摄影机_总结.md` | Source lookup with PDF 101-118, raw text path, and Chapter 7 subsection coverage for fixed-point and moving-camera movement. | pass | The answer points to both source-unit note and raw page files for exact terms such as tilt, pan, zoom, swish pan, tracking, and handheld. |
| Apply Dancyger's method to a short scene about a daughter confronting her father over a family secret. | `references/methods/script-interpretation-playbook.md`, `references/core/decision-core.md` | Candidate director's idea; interpretive axes; actor arc for daughter/father; camera stance; validation questions. | pass | The route forces interpretation before shot advice and ties actor/camera choices to one stated idea. |
| Audit this weak plan: "Use handheld camera and dark lighting because the story is intense." | `references/guardrails/directing-review-guardrails.md`, `references/core/decision-core.md` | Finding, severity, why it fails under Dancyger, fix, source basis. | pass | The guardrail catches technique-first directing and requires a subtextual idea before camera choices. |
| Give an exact quote defining the director's idea. | `references/core/source-coverage-map.md`, raw pages `txt/00_pages/PDF第027页.txt` to `PDF第038页.txt` | Refuse to invent wording; identify exact lookup path; quote only after raw text/PDF inspection. | pass | The skill escalates to raw pages for exact wording and does not rely on generated references as quotation source. |

## Acceptance Decision

Verdict: `pass`.

The skill is book-specific, source-grounded, and context-efficient after the 2026-06-25 source-note audit update. Exact quotations, film lists, and scene details still route to raw page text or PDF inspection.
