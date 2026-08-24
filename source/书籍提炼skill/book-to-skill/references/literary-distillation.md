# Literary Distillation

Use this file for fiction, poetry, drama, memoir with literary aims, literary essays, and humanities works whose value depends on form, voice, ambiguity, imagery, character, or interpretation.

## Contents

- [Core Principle](#core-principle)
- [Literary Source Layers](#literary-source-layers)
- [Complete Chapter Or Section Note](#complete-chapter-or-section-note)
- [Interpretive Skill Design](#interpretive-skill-design)
- [Reference Routing For Literary Skills](#reference-routing-for-literary-skills)
- [Quality Rules](#quality-rules)
- [Common Failure Modes](#common-failure-modes)

## Core Principle

Do not treat literature as a container of propositions. A literary book-derived skill should help future agents read, interpret, compare, discuss, and cite the work without flattening it into one moral, one plot recap, or one checklist.

For literary books, preserve:

- plot sequence and scene function;
- character relationships, desires, conflicts, and changes;
- narrator position, focalization, reliability, and distance;
- themes, motifs, symbols, imagery, and recurring objects;
- style, diction, syntax, rhythm, humor, irony, silence, and repetition;
- setting, social world, historical context, and genre convention;
- ambiguity, unresolved tensions, and competing readings;
- passages or page ranges needed for exact quotation.

## Literary Source Layers

Use these layers:

| Layer | Purpose | Example output |
| --- | --- | --- |
| Event layer | What happens? | scene-by-scene or chapter plot movement. |
| Character layer | Who wants what and how does it change? | character map, relationship shifts, motive conflicts. |
| Formal layer | How is it told? | narrator, time structure, style, genre, point of view. |
| Thematic layer | What questions does the work stage? | themes, motifs, symbols, ethical tensions. |
| Reception/use layer | What can an agent do with it? | discussion questions, essay angles, comparison paths, source lookup. |

Keep event recap separate from interpretation. A plot fact can support several readings.

## Complete Chapter Or Section Note

For each chapter, scene, poem, act, or section, write a complete `md/` note for human reading. Capture:

- **Source range**: PDF pages and raw text paths.
- **Surface movement**: what happens, who appears, and what changes.
- **Character state**: motives, knowledge, relationships, conflicts, and turning points.
- **Narrative technique**: point of view, time handling, reliability, scene pacing, withheld information.
- **Language and style**: repeated words, images, rhythm, registers, irony, tonal changes.
- **Motifs and symbols**: recurring images, objects, places, gestures, colors, sounds, or metaphors.
- **Interpretive pressure**: what question, contradiction, or ambiguity the section opens.
- **Source anchors**: pages that need exact quotation or visual PDF checking.

For poetry, replace plot movement with speaker situation, image sequence, sonic pattern, formal structure, and volta/turn.

For drama, track acts/scenes, stage directions, dialogue conflict, entrances/exits, dramatic irony, and performative constraints.

## Interpretive Skill Design

A literary book skill should usually include:

| Reference | Role |
| --- | --- |
| `task-router.md` | Route between plot lookup, character analysis, theme/motif analysis, close reading, comparison, essay planning, and quote lookup. |
| `reading-spine.md` | Compact reading order: event -> character -> form -> theme -> ambiguity -> source. |
| `character-map.md` | Characters, relationships, desires, conflicts, changes, and key scenes. |
| `themes-motifs.md` | Themes, motifs, symbols, imagery, and where they recur. |
| `narrative-style.md` | Narrator, point of view, time, genre, tone, diction, irony, structure. |
| `core/source-coverage-map.md` | Chapter/section to page and `md/` note map. |
| `discussion-prompts.md` | Essay questions, seminar questions, comparison paths, and close-reading prompts. |

Create only the references the work needs. A short poetry collection may need `poem-index.md` instead of `character-map.md`; a novel usually benefits from character and motif tracking.

## Reference Routing For Literary Skills

Route by question type:

| User task | Load first | Then load only if needed |
| --- | --- | --- |
| Plot recap | `core/source-coverage-map.md` | full section note in parent `md/` |
| Character analysis | `characters/character-map.md` | relevant `md/` notes and raw pages for quotes |
| Theme or motif | `themes/themes-motifs.md` | `style/narrative-style.md`, relevant `md/` notes |
| Close reading | `narrative-style.md` | raw page text and PDF visual check |
| Essay plan | `reading-spine.md`, `discussion-prompts.md` | theme/character references |
| Compare with another work | `themes-motifs.md`, `narrative-style.md` | only matching source sections |
| Exact quote or wording | `core/source-coverage-map.md` | raw `txt/` page or PDF page |

Do not load every `md/` note for a character/theme question. Use maps to identify the smallest relevant sections first.

## Quality Rules

- Separate **what happens** from **what it might mean**.
- Preserve competing interpretations when the text supports more than one.
- Mark narrator claims as narrator claims, not author claims.
- Do not turn character speech into the book's thesis without context.
- Do not overclaim symbolism from one isolated object unless recurrence or scene pressure supports it.
- Use exact source lookup for quotations, distinctive wording, translated phrases, poem lines, or close reading.
- Track translation/version issues when the work is translated or has multiple editions.
- Keep spoilers explicit if the generated skill may support spoiler-sensitive requests.

## Common Failure Modes

| Failure | Correction |
| --- | --- |
| Reducing a novel to a moral lesson | Track plot, character, form, theme, and ambiguity separately. |
| Confusing narrator and author | Record narrator position, reliability, and distance. |
| Over-indexing on plot recap | Add motif, style, and form notes for each section. |
| Treating one interpretation as final | Preserve alternative readings and source evidence. |
| Ignoring language | Add diction, syntax, image, rhythm, and tone observations. |
| Inventing quotes | Use raw pages or PDF inspection for exact wording. |
| Loading the whole book for one theme | Use motif/theme maps and source coverage first. |
