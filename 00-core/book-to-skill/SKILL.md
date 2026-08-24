---
name: book-to-skill
description: "Book PDF distillation workflow for turning a book PDF into a local skill bundle like the factor-quant-analysis pattern: PDF, page-level TXT, complete source-cited Markdown notes per source chapter or independently titled source unit, and a domain skill with progressive-disclosure references. Use when Codex needs to extract a book, write full source-unit notes, build a book-specific skill, convert PDF knowledge into agent reasoning guides, design source routing, or audit a generated book skill. Supports technical books, nonfiction, history, biography, theory, reference works, anthologies, visual/art books, literary works, humanities, and mixed books. 中文触发：书籍PDF提炼、PDF转skill、原文txt、完整内容总结、章节总结、全知识点总结、文学书籍提炼、小说提炼、历史书提炼、传记提炼、哲学理论书提炼、渐进披露、agent思维引导、source map、章节路由、书籍知识库。"
---

# Book To Skill

## Overview

Use this skill to convert a book PDF into a reusable local skill package. Preserve the book as evidence first, then distill it into the right agent-facing form for the genre: procedures and guardrails for technical books; argument maps for nonfiction; timelines and context for history/biography; interpretive reading paths for literary books.

The target shape follows the local book-skill pattern:

```text
<book-project>/
├── <book>.pdf
├── txt/                 # page-level original text
├── md/                  # complete source-chapter/source-unit notes for human reading
└── <generated-skill>/   # actual skill package
```

Follow the factor-quant-analysis pattern: the parent directory is the evidence workspace (`PDF`, `txt/`, `md/`), and the child skill is the agent-facing domain workflow. The generated skill should read like a real domain skill for that book, not like a generic PDF-processing tool.

`md/` uses the local `第X章_主题_总结.md` naming style, but these are not brief abstracts. They are complete content notes for human reading: cover every important knowledge point, argument step, example, formula, table, case, scene, character move, motif, style cue, uncertainty, and source range needed for a reader to use the source chapter or independently titled source unit without rereading the whole PDF. Keep verbatim source text in `txt/`/PDF and avoid large copied passages in `md/`.

The default `md/` unit is one source chapter or one independently titled substantive source unit. A part-level, volume-level, theme-level, or book-map file may be added as navigation or synthesis, but it never substitutes for the complete notes of the chapters inside it. If a source chapter is long, split it into multiple section notes with explicit source ranges. If a source unit is short, merge it only with adjacent front/back matter or an explicitly non-substantive unit, and record that decision in the book map.

Keep the generated skill lean. Put only routing, decision spines, and compact rules in `SKILL.md`; keep source text and full source-unit notes outside the default context path.

## Core Workflow

1. Classify the book and target skill: technical/procedural, argumentative nonfiction, literary/narrative, humanities criticism, reference work, or mixed. Name the domain, audience, language, likely trigger phrases, and what future agents should be able to do with the book.
2. Create the book project structure using `scripts/init_book_project.py` and [references/output-architecture.md](references/output-architecture.md).
3. Extract page-level text with `scripts/pdf_text_extract.py` or another reliable extractor. Keep extraction gaps visible.
4. Build or infer a table of contents, then map every substantive source chapter or independently titled source unit to PDF pages and raw text files.
5. Write complete source-chapter/source-unit notes in `md/` with source page ranges and genre-appropriate evidence. For technical books, cover all concepts, formulas, tables, examples, methods, limitations, assumptions, and edge cases. For literary books, cover plot movement, characters, scenes, themes, motifs, imagery, narrative voice, style, ambiguity, and interpretive questions. These files are meant for the user to read, so do not reduce them to brief abstracts or collapse multiple substantive chapters into a part-level summary.
6. Re-read the raw source pages for each `md/` note and iteratively expand that note until the omission audit finds no missing material knowledge points. Every final source-unit note must contain page/section coverage, omission-audit findings, revision passes, and a final no-known-omissions statement. If any material point remains missing, the coverage row is not final.
7. Distill the audited `md/` notes into a book-specific domain skill. Start from a compact reasoning or reading spine, then route to task-specific references only when needed.
8. Add source coverage and exact lookup paths so future agents can move from user question -> skill reference -> full source-chapter/source-unit note -> raw page text.
9. Link or copy the generated skill into the Codex skill discovery directory with `scripts/link_generated_skill.py` when the user wants it available in future sessions.
10. Generate or refresh `references/core/source-coverage-map.md` with `scripts/build_source_coverage_map.py`, replace every `UNMAPPED` row, and validate with `scripts/check_book_bundle.py --strict`. For final handoff or installation, `incomplete` and `deferred` coverage rows must be resolved; they are work-in-progress markers, not complete-coverage states.
11. Forward-test the generated skill on realistic questions before treating it as finished.

## Reference Routing

- Read [references/book-distillation-workflow.md](references/book-distillation-workflow.md) for the end-to-end process from PDF to finished skill.
- Read [references/genre-router.md](references/genre-router.md) before choosing source-unit note templates or generated skill references for a new book.
- Read [references/output-architecture.md](references/output-architecture.md) before creating directories, naming files, or deciding where raw text and generated skill files live.
- Read [references/book-map-and-coverage.md](references/book-map-and-coverage.md) when building the table of contents map, page ranges, full-content coverage, deferred sections, or multi-volume coverage plan.
- Read [references/agent-thinking-guide.md](references/agent-thinking-guide.md) when converting chapter content into agent reasoning, decision spines, hard rules, or task playbooks.
- Read [references/nonfiction-distillation.md](references/nonfiction-distillation.md) when the source is argumentative nonfiction, history, biography, memoir used as evidence, philosophy, social science, popular science, business, policy, or humanities theory.
- Read [references/literary-distillation.md](references/literary-distillation.md) when the source is fiction, poetry, drama, memoir with literary aims, literary criticism, or any book whose value depends on voice, form, ambiguity, character, imagery, or interpretation.
- Read [references/source-fidelity.md](references/source-fidelity.md) when editions, translations, page numbering, footnotes/endnotes, images, tables, quotations, OCR, or copyright-sensitive excerpts matter.
- Read [references/run-record-and-maintenance.md](references/run-record-and-maintenance.md) when work spans multiple sessions, `md/` notes are updated, source coverage changes, or generated skill files may drift from `txt/` and `md/`.
- Read [references/progressive-disclosure.md](references/progressive-disclosure.md) when designing the generated skill's `SKILL.md`, reference routing, source lookup, and context-loading order.
- Read [references/forward-test-scenarios.md](references/forward-test-scenarios.md) before finalizing a generated skill or when a generated skill feels generic, over-broad, or under-sourced.
- Read [references/templates.md](references/templates.md) when drafting complete source-chapter/source-unit notes, generated `SKILL.md`, task routers, source maps, or final handoff notes.
- Read [references/quality-gates.md](references/quality-gates.md) before finalizing or auditing a generated book bundle.

## Scripts

- `scripts/init_book_project.py`: create a book project directory, standard `txt/` and `md/` folders, optional PDF copy or symlink, and an optional generated-skill folder scaffold with lowercase hyphen-case skill-name validation.
- `scripts/link_generated_skill.py`: validate generated skill naming and reject missing core references, broken local links, missing metadata, unfinished markers, placeholders, default scaffold wording, unsupported frontmatter, or a parent book project that fails `check_book_bundle.py --strict` before exposing it through `$CODEX_HOME/skills` or `~/.codex/skills` using a symlink or copy.
- `scripts/pdf_text_extract.py`: extract PDF pages into `PDF第001页.txt` style files and write an extraction report. Uses `pypdf` or the `pdftotext` CLI when available.
- `scripts/build_source_coverage_map.py`: scan parent `txt/` and `md/`, then generate the generated skill's `references/core/source-coverage-map.md`.
- `scripts/check_book_bundle.py`: validate that a book project has the expected `PDF`, `txt/`, `md/`, and generated skill structure, plus source markers, parent-project link integrity, generated skill metadata, unreplaced placeholders, default-scaffold markers, generated skill naming, obvious `md/` granularity failures, and required completeness-audit sections in every final source-unit note; use `--strict` for final handoff so warnings such as TODO, UNMAPPED, placeholder text, broken metadata, unreplaced scaffold wording, missing omission audit, or chapter-compression warnings fail the check.

## Output Contract

When building a book bundle, return:

- book project path and generated skill path;
- PDF source and extraction backend;
- raw text page count, empty or suspicious pages, and any OCR/manual-check needs;
- complete `md/` source-unit note files created and their source page ranges;
- generated skill name, trigger description, reference routing, and source lookup strategy;
- discovery path or explicit note that the generated skill was not installed for auto-discovery;
- validation commands run and their results;
- remaining risks, especially OCR errors, missing pages, weak chapter boundaries, or unverified formulas/tables.

When only designing or reviewing a book skill, return:

- the proposed structure;
- what belongs in `SKILL.md` vs references vs external `md/`/`txt`;
- the reasoning spine future agents should follow;
- the progressive-disclosure path;
- the quality gates that would reject the skill.

## Hard Rules

- Do not put full book text, long `md/` source-unit notes, or large copied passages into the generated `SKILL.md`.
- Do not treat `md/` as brief abstracts. The `md/` layer must be complete enough for the user to read: include all material knowledge points, evidence, examples, exceptions, source ranges, and genre-specific details.
- Do not finalize a source-unit `md` note after one drafting pass. Re-read the raw source pages, add missed points, repeat until the omission audit has no material omissions, then record the final no-known-omissions statement inside the note.
- Do not use part-level, volume-level, or theme-level summaries as replacements for per-chapter or per-source-unit complete notes. These files may only be maps, synthesis, or navigation layers unless every substantive child unit also has its own complete note.
- Do not call coverage complete when multiple substantive chapters are compressed into one note, when a long source range receives only a few paragraphs, or when the book map lacks an explicit `md/` file for each substantive source unit.
- Do not reduce a book to loose reading notes. Convert technical books into procedures, decision rules, examples, and guardrails; convert literary books into interpretive maps, reading paths, character/theme/motif tracking, style notes, and source lookup.
- Do not force literary works into technical checklists. Preserve ambiguity, competing interpretations, emotional movement, and the difference between plot recap and interpretation.
- Do not invent exact quotes, formulas, page numbers, or table values. Trace them to `md/` source-unit notes or raw `txt/` pages.
- Do not collapse edition, translation, footnote, table, figure, or OCR uncertainty into a confident claim. Mark the source layer and the uncertainty.
- Do not imply full-book coverage when page ranges, `md/` notes, or generated references cover only part of the source. Mark pending, deferred, missing, and duplicate pages.
- Do not install or final-handoff a generated skill while TOC/source-unit coverage still contains `incomplete` or `deferred` rows. Those statuses are valid only for local work-in-progress.
- Do not hide extraction failures. Empty pages, garbled OCR, missing formulas, and broken tables must remain visible until checked.
- Do not load the entire book into context for ordinary questions. Route from compact skill guidance to the smallest relevant reference, then to exact source only when needed.
- Do not let generated references duplicate the same knowledge in several places. Choose one authoritative home for each rule.
- Do not let a generated skill drift silently from updated `txt/`, `md/`, or source coverage. Update `references/core/source-coverage-map.md` and rerun checks.
- Do not finalize a generated skill before running structural checks and genre-appropriate forward tests.
