# Progressive Disclosure

Use this file when designing the generated skill's loading path.

## Contents

- [Loading Layers](#loading-layers)
- [`SKILL.md` Budget](#skillmd-budget)
- [Reference Routing Pattern](#reference-routing-pattern)
- [Task Router Pattern](#task-router-pattern)
- [Source Lookup Escalation](#source-lookup-escalation)
- [Avoid Context Bloat](#avoid-context-bloat)
- [Minimum Viable Generated Skill](#minimum-viable-generated-skill)

## Loading Layers

A book-derived skill should use these layers:

| Layer | Loaded when | Content |
| --- | --- | --- |
| Metadata | Always available | `name` and description with strong trigger terms. |
| `SKILL.md` | Skill triggers | Overview, routing, reasoning spine, output contract, hard rules. |
| Core references | Broad or ambiguous task | `core/decision-core.md`, `core/task-router.md`, `core/reference-architecture.md`, `core/source-coverage-map.md`, `core/report-templates.md`. |
| Topic references | Specific task | Concepts, methods, arguments, timelines, people maps, case indexes, playbooks, guardrails, examples; for literature, character maps, theme/motif maps, narrative/style notes, and reading prompts. |
| Complete source-unit notes | Exact source unit, full knowledge-point review, or source lookup | Parent `md/` notes. |
| Raw page text | Exact quote/formula/table check | Parent `txt/` page files or PDF visual inspection. |

The default answer path should rarely go beyond topic references.

## `SKILL.md` Budget

Keep the generated `SKILL.md` small:

- frontmatter description with trigger terms;
- 1 to 3 paragraph overview;
- reference routing bullets;
- core reasoning spine;
- output contract;
- hard rules.

Do not place source-unit full notes in `SKILL.md`. Put lookup maps in `references/core/source-coverage-map.md` and the full notes in parent `md/`.

## Reference Routing Pattern

Generated `SKILL.md` should contain routing like:

```markdown
## Reference Routing

- For broad tasks, read `references/core/decision-core.md` first, then `references/core/task-router.md`.
- For directory layout or load-order uncertainty, read `references/core/reference-architecture.md`.
- For exact chapter coverage, read `references/core/source-coverage-map.md`.
- For final deliverables, read `references/core/report-templates.md`.
```

Each route should explain **when** to read the file, not only what the file is.

## Task Router Pattern

The generated `task-router.md` should map:

- task shape;
- when to use it;
- minimum references;
- optional references;
- output shape;
- source lookup escalation.

Do not route every task to every reference.

## Source Lookup Escalation

Use this order:

1. Generated skill `SKILL.md` for the correct reasoning mode.
2. Generated `references/core/decision-core.md` or `references/core/task-router.md` for the task path.
3. Generated topic reference for distilled rules.
4. Parent `md/` note for chapter-level source details and full knowledge-point coverage.
5. Parent `txt/` raw page file or original PDF for exact wording, formulas, tables, and ambiguous extraction.

If exact wording matters and the raw text is garbled, inspect the PDF page image instead of guessing.

## Avoid Context Bloat

Do not:

- read all `md/` notes before classifying the task;
- copy full `md/` notes into generated references;
- duplicate hard rules in several files;
- create many tiny files with overlapping purpose;
- add a reference only because the source book has a chapter with that title.

Create references around future task shapes, not around the book's table of contents, unless the book is primarily used for chapter lookup.

## Minimum Viable Generated Skill

For an initial version:

```text
SKILL.md
references/core/decision-core.md
references/core/task-router.md
references/core/source-coverage-map.md
references/core/report-templates.md
```

Add task-specific directories such as `methods/`, `playbooks/`, `arguments/`, `reading/`, `characters/`, `themes/`, or `style/` only when the book supports recurring tasks that benefit from those layers.

For argumentative nonfiction, history, biography, or theory books, add only the references matching the book's future use:

```text
arguments/argument-map.md
concepts/concept-map.md
history/timeline.md
people/people-map.md
cases/case-index.md
evidence/evidence-ledger.md
```

For a literary book, the minimum viable generated skill is usually:

```text
SKILL.md
references/core/decision-core.md
references/core/task-router.md
references/core/source-coverage-map.md
references/reading/reading-spine.md
```

Add `characters/character-map.md`, `themes/themes-motifs.md`, `style/narrative-style.md`, or `reading/discussion-prompts.md` when the work's future use requires character analysis, motif tracking, close reading, or essay planning.
