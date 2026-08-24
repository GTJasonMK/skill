# Genre Router

Use this before choosing complete `md` note templates, reference files, or a generated skill structure for a new book.

## Routing Rule

Classify by the book's future use, not only by bookstore category. A memoir can be literary, historical evidence, leadership advice, or all three. A philosophy book can be conceptual argument, historical commentary, or close reading of primary texts.

If a book is mixed, create one dominant mode and one or two secondary routes. Do not force all chapters into the same template when parts behave differently.

## Book Modes

| Mode | Use when | Distill into | Minimum generated references |
| --- | --- | --- | --- |
| Technical/procedural | The book teaches a method, system, calculation, craft, API, or repeatable practice. | Concepts, workflows, checks, edge cases, implementation routes. | `core/decision-core.md`, `core/task-router.md`, `core/source-coverage-map.md`, plus `methods/` or `playbooks/` |
| Argumentative nonfiction | The book makes claims and supports them with evidence, examples, or counterarguments. | Claim map, argument structure, evidence ledger, objections, caveats. | `core/decision-core.md`, `core/task-router.md`, `core/source-coverage-map.md`, plus `arguments/` or `evidence/` |
| History | The book explains events over time, causes, institutions, actors, or contexts. | Timeline, actors, causal claims, periodization, source disputes. | `core/decision-core.md`, `core/task-router.md`, `core/source-coverage-map.md`, plus `history/` or `people/` |
| Biography/memoir as evidence | The book follows a life, witness account, career, or personal transformation. | Chronology, relationships, turning points, self-presentation, corroboration limits. | `core/decision-core.md`, `core/task-router.md`, `core/source-coverage-map.md`, plus `people/` or `history/` |
| Literary/narrative | The book's value depends on plot, character, voice, form, imagery, style, ambiguity, or interpretation. | Reading spine, character map, themes/motifs, narrative style, discussion prompts. | `core/decision-core.md`, `core/task-router.md`, `core/source-coverage-map.md`, plus `reading/`, `characters/`, `themes/`, or `style/` |
| Philosophy/theory | The book builds concepts, distinctions, definitions, critiques, or schools of thought. | Concept map, argument map, term genealogy, objections, application limits. | `core/decision-core.md`, `core/task-router.md`, `core/source-coverage-map.md`, plus `concepts/` or `arguments/` |
| Reference/handbook | The book is mainly lookup tables, definitions, standards, catalog entries, recipes, or cases. | Lookup index, term map, table extraction policy, exact source paths. | `core/task-router.md`, `core/source-coverage-map.md`, plus `lookup/` |
| Anthology/collection | The book contains essays, stories, poems, lectures, interviews, or chapters by different authors. | Piece index, author/speaker map, theme crosswalk, source coverage per piece. | `core/task-router.md`, `core/source-coverage-map.md`, plus `pieces/` or `themes/` |
| Visual/design/art book | Images, diagrams, layouts, plates, typography, or visual sequencing carry meaning. | Image/plate index, visual description, caption/source map, inspection requirements. | `core/task-router.md`, `core/source-coverage-map.md`, plus `visual/` |

## Mixed-Mode Examples

- A literary memoir: use `literary-distillation.md` for voice/form and `nonfiction-distillation.md` for chronology and factual claims.
- A history of ideas: use nonfiction argument maps plus timeline/context maps.
- A textbook with case narratives: use technical/procedural routes for methods and case evidence routes for examples.
- A poetry collection with critical introduction: use literary routes for poems and nonfiction routes for the introduction.

## Reference Selection

Pick references by future user tasks:

| Future user asks | Prefer |
| --- | --- |
| "How do I apply this?" | method/workflow references |
| "What does the author argue?" | argument map |
| "What happened when?" | timeline/chronology |
| "Who is related to whom?" | people or character map |
| "Where is this covered?" | source coverage |
| "What is the exact wording?" | source fidelity route to raw pages/PDF |
| "How should I interpret this passage?" | literary reading/style references |
| "Can I compare this to another book?" | theme/concept crosswalk |

## Stop Conditions

Do not add a reference file only because a genre table lists it. Add it only when:

- the book has enough material to justify the file;
- future tasks would load it independently;
- it reduces context load versus reading full `md/` notes;
- it does not duplicate another reference's role.
