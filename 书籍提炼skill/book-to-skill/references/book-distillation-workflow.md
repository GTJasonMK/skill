# Book Distillation Workflow

Use this file when converting a specific book PDF into a structured local skill bundle.

## Contents

- [Stage 0: Scope The Book Skill](#stage-0-scope-the-book-skill)
- [Stage 1: Extract And Preserve Source](#stage-1-extract-and-preserve-source)
- [Stage 2: Build The Book Map](#stage-2-build-the-book-map)
- [Stage 3: Write Complete Source-Unit Notes](#stage-3-write-complete-source-unit-notes)
- [Stage 4: Distill Agent Reasoning](#stage-4-distill-agent-reasoning)
- [Stage 5: Generate The Skill](#stage-5-generate-the-skill)
- [Stage 6: Validate And Forward-Test](#stage-6-validate-and-forward-test)
- [Low-Context Work Mode](#low-context-work-mode)

## Stage 0: Scope The Book Skill

Before extraction, name the output:

- **Book project path**: normally a Chinese or human-readable parent directory under `/home/fufu/Code/Skills/`.
- **Generated skill name**: lowercase hyphen-case, under 64 characters, describing the book's practical use rather than only the title.
- **Skill purpose**: what future agents should do after reading this book, such as explain concepts, design workflows, audit methods, translate a theory into code, or review a strategy.
- **Book mode**: technical/procedural, argumentative nonfiction, literary/narrative, humanities criticism, reference work, or mixed.
- **Source language**: keep `md/` notes in the user's preferred language unless the book's terminology is easier to preserve in another language.

If the user provides no output location, place the book project near the PDF or under `/home/fufu/Code/Skills/<book-title>skill/`.

Read [genre-router.md](genre-router.md) before choosing templates or generated references. Read [source-fidelity.md](source-fidelity.md) if the book has edition, translation, note, figure, table, OCR, or exact quotation risks.

Initialize the project:

```bash
python3 /home/fufu/Code/Skills/书籍提炼skill/book-to-skill/scripts/init_book_project.py \
  /home/fufu/Code/Skills/<book-project> \
  --pdf /path/to/book.pdf \
  --skill-name "<generated-skill>"
```

## Stage 1: Extract And Preserve Source

Create raw page text before writing `md/` notes:

```bash
python3 /home/fufu/Code/Skills/书籍提炼skill/book-to-skill/scripts/pdf_text_extract.py \
  /path/to/book.pdf \
  --out-dir /home/fufu/Code/Skills/<book-project>/txt/00_pages
```

Check the extraction report for:

- total page count and selected page range;
- empty pages;
- pages with very short text;
- backend used;
- visible extraction warnings.

If the PDF is scanned or formulas/tables are broken, mark the affected pages. Use OCR or visual inspection for every section whose content matters to the `md/` notes or final answers.

Record whether page paths use PDF page numbers only or also map to printed page numbers.

## Stage 2: Build The Book Map

Use the table of contents, page headers, and repeated section markers to create a book map:

- front matter;
- parts;
- chapters;
- appendices;
- references and index;
- page ranges in PDF page numbers, not printed book page numbers unless both are recorded.

Read [book-map-and-coverage.md](book-map-and-coverage.md) for book map templates and gap/duplicate handling.

If chapter grouping is clear, move page files into chapter directories such as:

```text
txt/
├── 00_前置内容/
├── 01_第一部分_主题名/
├── 02_第二部分_主题名/
└── 99_参考文献/
```

If chapter boundaries are uncertain, keep the original `txt/00_pages/` dump and record uncertainty in the generated skill's `references/core/source-coverage-map.md`.

After moving pages into chapter directories, run `check_book_bundle.py` to surface duplicate PDF page files or missing page numbers inside the extracted range.

## Stage 3: Write Complete Source-Unit Notes

Write one complete Markdown note per source chapter or independently titled substantive source unit. Use the local reference naming style such as `第1章_主题_总结.md`, but treat `总结` as a complete content note, not a short abstract. Each file should be complete enough that a human can understand all important knowledge points in that unit without reopening the PDF, while still preserving raw text and exact quotations in `txt/`/PDF.

Part-level, volume-level, theme-level, and book-map files may be created as navigation or synthesis, but they do not count as coverage for the chapters inside them. A file named `第2部分_经典导演案例_总结.md` that covers 138 PDF pages and ten director chapters is not a complete source-unit note layer; it is a part-level guide and must be split into the source chapters or substantive titled units. If a chapter is unusually long, split it into section notes with explicit page ranges. If a source unit is short or non-substantive, merge it only with an adjacent front/back-matter unit and record the reason in the book map or TOC coverage table.

Before writing content notes, create or update a TOC coverage table with one row per source unit:

- source TOC item;
- PDF page range;
- intended `md/` note path;
- status: `complete`, `incomplete`, `deferred`, or `non-substantive`;
- reason for any merge, split, deferral, or non-substantive classification.

Set a source-unit row to `complete` only after the note has gone through iterative source re-reading and omission audit. A note is still `incomplete` when the first draft is written, when it lacks page/section coverage, when any knowledge point remains missing, or when the audit has not been recorded inside the note.

For technical or argumentative books, each file must include:

- title and source page range;
- one-paragraph chapter thesis;
- conceptual structure;
- key definitions and formulas;
- all material knowledge points, including secondary distinctions and caveats;
- workflows, methods, checklists, or decision rules;
- examples, cases, and edge conditions;
- tables, figures, data values, and formulas that affect understanding, with manual-check markers when extraction is uncertain;
- what an agent should do differently after reading the chapter;
- extraction or interpretation uncertainties.

For literary books, each note must instead preserve the reading experience and evidence structure:

- surface plot, scene, speaker situation, or dramatic action;
- character states, relations, desires, conflicts, and turning points;
- narrative voice, focalization, structure, pacing, form, and genre conventions;
- themes, motifs, symbols, imagery, recurring words, and style;
- ambiguity, competing interpretations, and passages needing exact quotation;
- spoiler-sensitive notes when future use may require them.

Do not merely compress paragraphs or produce a high-level abstract. The note should make future reasoning, human reading, source lookup, and interpretation cheaper and more reliable. Omit only low-value repetition, decorative prose that adds no content, or examples that truly duplicate an already captured point.

Reject the note as incomplete when it covers several substantive chapters with only a few paragraphs per chapter, when it uses chapter headings inside one large part file instead of dedicated chapter files, or when the page range is so broad that a reader cannot reasonably trust that all knowledge points were captured.

Before finalizing each source-unit note, repeat this loop until it finds no material omissions:

1. Re-read the source page range from `txt/` and, where extraction is suspect, the PDF.
2. Compare the raw source against the current `md` note page by page or section by section.
3. List missing concepts, argument steps, examples, scenes, cases, names, tables, figures, stylistic details, caveats, and source uncertainties in `## 遗漏审计`.
4. Expand the body of the `md` note to incorporate every material omission.
5. Add a dated or numbered entry to `## 迭代修订记录` describing what was added.
6. Repeat until `## 最终无遗漏声明` can honestly say that no known material knowledge points remain outside the note.

Do not use `## 遗漏审计` as a place to defer work. If it still lists unresolved material omissions, the note and its TOC row are not final.

## Stage 4: Distill Agent Reasoning

Turn the full `md/` notes into an agent control layer:

- task classes the book supports;
- decision spine for technical or argumentative tasks;
- reading spine for literary tasks;
- failure-mode routing;
- hard rules;
- output contracts;
- source lookup strategy;
- exact chapters to load for common questions;
- what evidence changes conclusions.

Use [agent-thinking-guide.md](agent-thinking-guide.md) for the general transformation rules, [nonfiction-distillation.md](nonfiction-distillation.md) for argument/history/biography/theory books, and [literary-distillation.md](literary-distillation.md) when the book is literary or interpretive.

## Stage 5: Generate The Skill

Create the generated skill as a child directory of the book project:

```text
<book-project>/<generated-skill>/
├── SKILL.md
├── agents/openai.yaml
└── references/
    ├── core/
    │   ├── decision-core.md
    │   ├── task-router.md
    │   ├── reference-architecture.md
    │   ├── source-coverage-map.md
    │   └── report-templates.md
    └── <task-specific-directories>/
```

The generated `SKILL.md` should read like the reference skill's entrypoint for a real domain:

- overview and domain stance;
- reference routing;
- core reasoning spine;
- output contract;
- hard rules.

Put detailed method maps, source coverage, report templates, source-unit maps, and playbooks in task-oriented `references/` directories. Keep original text in the parent `txt/` and complete human-readable source-unit notes in the parent `md/`.

For nonfiction, prefer references such as `argument-map.md`, `concept-map.md`, `timeline.md`, `people-map.md`, `case-index.md`, or `evidence-ledger.md` when they match future tasks. For literary works, prefer `reading-spine.md`, `character-map.md`, `themes-motifs.md`, `narrative-style.md`, and `discussion-prompts.md`.

## Stage 6: Validate And Forward-Test

Generate the source coverage map:

```bash
python3 /home/fufu/Code/Skills/书籍提炼skill/book-to-skill/scripts/build_source_coverage_map.py <book-project> --force
```

Then edit `references/core/source-coverage-map.md` so every generated `UNMAPPED` row is replaced by the actual generated reference coverage, or by an explicit incomplete/deferred/OCR-risk reason. `UNMAPPED` is a build-time placeholder, not an acceptable final coverage state.

Run final validation:

```bash
python3 /home/fufu/Code/Skills/书籍提炼skill/book-to-skill/scripts/check_book_bundle.py <book-project> --strict
python3 /home/fufu/.codex/skills/.system/skill-creator/scripts/quick_validate.py <book-project>/<generated-skill>
```

If the generated skill should be auto-discoverable in future Codex sessions, expose it through the skills directory:

```bash
python3 /home/fufu/Code/Skills/书籍提炼skill/book-to-skill/scripts/link_generated_skill.py \
  <book-project>/<generated-skill>
```

Prefer symlink mode for local book projects so generated skill files do not drift from the source project. Use copy mode only when the skill must be portable without the parent project.

Forward-test with prompts that resemble real future use:

- "Use this skill to explain the central framework of the book."
- "Use this skill to answer a chapter-specific source lookup question."
- "Use this skill to apply the book's method to a concrete scenario."
- "Use this skill to review a flawed plan using the book's guardrails."

Fix routing or `md/` notes when the test answer loads too much context, lacks source traceability, misses a knowledge point, or produces generic advice unrelated to the book.

## Low-Context Work Mode

For a very large book or limited time:

1. Initialize the project, extract raw text, and draft `references/core/source-coverage-map.md`.
2. Write complete `md/` notes only for the source units actually processed, each with a TOC coverage status.
3. Draft a local-only generated skill only if it clearly says coverage is incomplete and routes only to completed source units.
4. Add full source-unit notes incrementally and update source coverage.

This mode is not a final handoff path. Do not install the generated skill, do not call the `md/` layer complete, and do not pass `check_book_bundle.py --strict` until every substantive source chapter or source unit has a dedicated complete note or is explicitly marked `non-substantive` or `synthesis`. `incomplete` and `deferred` rows are work-in-progress markers and must fail final strict validation.
