# Quality Gates

Use this before finalizing or auditing a generated book bundle.

## Contents

- [Extraction Gate](#extraction-gate)
- [Complete Markdown Note Gate](#complete-markdown-note-gate)
- [Generated Skill Gate](#generated-skill-gate)
- [Progressive Disclosure Gate](#progressive-disclosure-gate)
- [Source Fidelity Gate](#source-fidelity-gate)
- [Forward-Test Gate](#forward-test-gate)
- [Final Checklist](#final-checklist)

## Extraction Gate

Pass only when:

- the original PDF exists in the book project root;
- page-level text files exist with stable `PDF第NNN页.txt` names;
- page count matches the selected PDF range;
- PDF page numbering and printed page numbering conventions are recorded when both matter;
- duplicate PDF page files and missing page numbers inside the extracted range are either absent or explicitly recorded;
- empty or very short pages are listed with OCR/manual-check status;
- formulas, tables, figures, and OCR-heavy pages that matter are marked for manual review.

Reject or mark incomplete when:

- the PDF is scanned and no OCR pass was done;
- important tables or formulas are missing but used in `md/` source-unit notes;
- page numbering mixes PDF pages and printed book pages without explanation.
- duplicate or missing PDF page text files are ignored after pages are reorganized into chapter directories.
- translation, edition, or OCR uncertainty affects claims but is not marked.

## Complete Markdown Note Gate

Pass only when the book map or TOC coverage table accounts for every substantive source chapter or independently titled source unit:

- each substantive source unit has a dedicated complete `md/` note, or an explicit `non-substantive` or `synthesis` status with a reason;
- part-level, volume-level, theme-level, and book-map files are marked as maps or synthesis and are not counted as substitutes for child source-unit notes;
- any split or merge is recorded with source ranges and rationale.

`incomplete` and `deferred` rows are allowed only in work-in-progress coverage records. They must reject final handoff, installation, and `check_book_bundle.py --strict`.

Pass only when each `md/` chapter note has:

- source page range;
- source markers that resolve to existing raw page text files or explicitly recorded missing/OCR-risk pages;
- page/section coverage that maps the source pages or sections to the note content;
- chapter thesis or literary section function;
- complete coverage of the unit's material knowledge points, argument steps, examples, cases, formulas, tables, caveats, and exceptions;
- key concepts and distinctions for nonfiction, or plot/character/form/theme/style observations for literature;
- methods, workflows, or decision rules where applicable;
- agent-use notes;
- an omission audit produced by re-reading the raw source after the first draft;
- iteration/revision records showing what was added after omissions were found;
- a final no-known-omissions statement;
- uncertainties and extraction issues.

Reject when `md/` files are brief abstracts, loose reading notes, or only paraphrased prose that omits material knowledge points.

Also reject when:

- one `md/` note covers multiple substantive chapters or a long part-level page range as a substitute for source-unit notes;
- a part-level note uses several `## Chapter ...` or `## 第X章...` sections instead of separate complete chapter files;
- each chapter inside a part receives only a few paragraphs or a high-level guide;
- the file title says `第X部分`, `Part`, `主题`, or similar while source coverage shows many child chapters and no dedicated child notes.
- TOC/source-unit coverage still contains `incomplete` or `deferred` rows.
- a source-unit note lacks `## 页/段落覆盖`, `## 遗漏审计`, `## 迭代修订记录`, or `## 最终无遗漏声明`;
- the omission audit still lists unresolved material omissions, pending checks, or deferred expansion.

Also reject or mark incomplete when a chapter note cites PDF pages or `txt/` paths that do not exist in the project and the gap is not recorded.

For nonfiction notes, also reject when:

- author claims, evidence, assumptions, and interpretation are collapsed together;
- causal claims are not distinguished from descriptive or normative claims;
- anecdotes are treated as universal evidence without scope limits;
- timelines, names, dates, or cited works are untraceable.

For literary notes, also reject when:

- plot recap is mixed with interpretation without separation;
- narrator, speaker, character, and author are treated as interchangeable;
- symbolism or theme claims lack recurrence, scene pressure, or source evidence;
- ambiguity is collapsed into one unsupported reading;
- distinctive language is ignored when close reading is likely.

## Generated Skill Gate

Pass only when the generated skill has:

- valid frontmatter with strong trigger description;
- generated `agents/openai.yaml` contains `interface`, `display_name`, `short_description`, and `default_prompt`;
- compact overview;
- reference routing that explains when to load each reference;
- core reasoning spine;
- output contract;
- hard rules;
- source coverage path.
- a discovery decision: installed/symlinked/copied for future sessions, or intentionally left local-only.

Reject when:

- `SKILL.md` contains whole chapters or large excerpts;
- generated `SKILL.md`, `agents/openai.yaml`, or core references still contain default scaffold wording instead of book-specific domain guidance;
- generated files still contain template placeholders such as `generated-skill-name`, `/absolute/path/to/book-project`, `<book>`, or `中文触发：...`;
- generated references still contain TODO markers or unmapped source coverage rows;
- every task routes to every reference;
- source lookup requires guessing file locations;
- the skill can answer only broad book-overview requests and not practical tasks;
- a literary skill has no path for character, theme/motif, style/form, close reading, and quote lookup.

## Progressive Disclosure Gate

Pass only when:

- ordinary tasks can be answered from `SKILL.md` plus one or two references;
- exact claims escalate to `md/` and `txt/`;
- complete `md/` source-unit notes are not loaded by default;
- each reference has a distinct role.

Reject when generated files duplicate the same rules or when the only route is "read everything".

## Source Fidelity Gate

Pass only when:

- formulas and table values have source page pointers;
- uncertain extraction is labeled;
- exact wording claims point to raw pages or PDF inspection;
- `md/` source-unit notes distinguish book claims from agent interpretation.

Reject when exact values, quotes, or page references are invented.

## Forward-Test Gate

Read [forward-test-scenarios.md](forward-test-scenarios.md), then run at least four realistic prompts:

1. Broad conceptual task.
2. Exact chapter/source lookup task.
3. Application, audit, or review task in the book's domain.
4. Failure-mode task that should force uncertainty, source escalation, spoiler handling, or refusal to overclaim.

The generated skill passes only if answers:

- load the expected references;
- avoid unnecessary source loading;
- use book-specific reasoning;
- cite or point to the correct source layer when exactness matters;
- surface missing evidence rather than guessing.
- receive a `pass` or explicitly recorded revision verdict from the forward-test scenarios.

## Final Checklist

- [ ] `txt/` contains page-level extraction.
- [ ] `txt/` page files use stable `PDF第NNN页.txt` names.
- [ ] the original PDF exists in the book project root.
- [ ] `md/` contains source-cited complete source-chapter/source-unit notes, not brief abstracts.
- [ ] every final source-unit `md` note contains page/section coverage, omission audit, iteration records, and final no-known-omissions statement.
- [ ] TOC-to-md coverage maps every substantive source unit to a dedicated `md/` note, or records an explicit non-substantive/synthesis status.
- [ ] TOC-to-md coverage contains no `incomplete` or `deferred` rows for final handoff or installation.
- [ ] part-level, volume-level, theme-level, or book-map files are not being used as substitutes for complete child source-unit notes.
- [ ] `md/` note source markers resolve to existing `txt/` pages or recorded exceptions.
- [ ] `md/` notes contain no TODO, UNMAPPED, or template placeholders.
- [ ] generated `references/core/source-coverage-map.md` maps source chapters/source units, `md/`, `txt/`, and generated references.
- [ ] page gaps, duplicate page files, deferred sections, and partial coverage are recorded.
- [ ] generated skill validates with `quick_validate.py`.
- [ ] `check_book_bundle.py --strict` passes with no warnings.
- [ ] `link_generated_skill.py` refuses unfinished generated skills and installs only after frontmatter, core references, local links, metadata, placeholders, scaffold wording, TODO, and UNMAPPED markers are clean.
- [ ] generated skill references and parent-project links resolve locally.
- [ ] generated skill discovery state is recorded: symlinked, copied, or local-only.
- [ ] generated `SKILL.md` is compact and not a full source-unit note.
- [ ] final answer reports validation commands and residual risks.
- [ ] edition, translation, note, figure, table, OCR, and exact-quote risks are either resolved or explicitly recorded.
