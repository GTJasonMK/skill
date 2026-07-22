# Output Architecture

Use this file before creating or changing the target directory layout.

## Project Layout

Use this default structure:

```text
<book-project>/
├── <book>.pdf
├── txt/
│   ├── 00_前置内容/
│   │   └── PDF第001页.txt
│   ├── 01_第一部分_主题/
│   │   └── PDF第010页.txt
│   └── 99_参考文献/
├── md/
│   ├── 00_书籍地图与抽取质量_总结.md
│   ├── 第1章_主题_总结.md
│   └── 第2章_主题_总结.md
└── <generated-skill>/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    └── references/
        ├── core/
        │   ├── decision-core.md
        │   ├── task-router.md
        │   ├── reference-architecture.md
        │   ├── source-coverage-map.md
        │   └── report-templates.md
        └── <task-specific-directories>/
```

The parent directory is the evidence workspace. The generated skill is the agent-facing entrypoint.

## Naming Rules

- Use a human-readable parent directory, often `<中文书名>skill`.
- Use lowercase hyphen-case for the generated skill folder and `name` field.
- Use stable page filenames: `PDF第001页.txt`, `PDF第002页.txt`, and so on.
- Prefix large text groups with sortable numbers: `00_`, `01_`, `02_`, `99_`.
- Keep Markdown source-unit note filenames in the local reference style: `第1章_主题_总结.md`. The word `总结` means complete content notes, not a brief abstract.
- Keep a book-map/TOC coverage file such as `md/00_书籍地图与抽取质量_总结.md` that maps each substantive source unit to a complete `md` note or an explicit status.
- Avoid spaces in generated skill paths when possible.

## What Goes Where

| Artifact | Location | Rule |
| --- | --- | --- |
| Original PDF | `<book-project>/` | Keep the PDF near extracted text for reproducibility. |
| Raw extracted text | `<book-project>/txt/` | Preserve page-level text. Do not edit away extraction errors silently. |
| Complete source-unit notes | `<book-project>/md/` | Source-cited, human-readable notes that cover all material knowledge points, not brief abstracts. |
| Generated skill | `<book-project>/<generated-skill>/` | Domain workflow skill derived from the book, like `factor-quant-analysis`. |
| Generated skill references | `<generated-skill>/references/` | Task-routed reasoning files, playbooks, maps, report templates, and source coverage. |
| Full source excerpts | Parent `txt/` or short cited excerpts in `md/` | Do not duplicate them inside generated `SKILL.md`. |
| Discovery link | `$CODEX_HOME/skills/<generated-skill>` or `~/.codex/skills/<generated-skill>` | Symlink or copy when the generated skill should be available in future sessions. |

## Generated Skill Reference Architecture

Follow the reference skill's one-level category pattern. Use `references/core/` for control files, then create task-specific directories only when the book supports those tasks.

Default control files:

| Reference | Purpose |
| --- | --- |
| `core/decision-core.md` | Compact reasoning or reading spine; first file for broad tasks. |
| `core/task-router.md` | Map user requests to the smallest useful reference bundle. |
| `core/reference-architecture.md` | Explain directory roles and loading order. |
| `core/source-coverage-map.md` | Map source units, complete `md/` notes, generated references, and raw source paths. |
| `core/report-templates.md` | Hold user-facing output shapes. |

Task-specific examples:

| Reference | Purpose |
| --- | --- |
| `methods/`, `playbooks/`, `practice/` | Technical or procedural methods, recipes, implementation workflows. |
| `arguments/`, `concepts/`, `evidence/` | Nonfiction claims, concept maps, evidence ledgers, objections. |
| `history/`, `people/`, `cases/` | Timelines, actors, institutions, cases, chronology. |
| `reading/`, `characters/`, `themes/`, `style/` | Literary reading spine, character maps, motifs, narration, close-reading cues. |
| `visual/` | Images, plates, figures, diagrams, captions, visual-inspection rules. |

Do not create all of these by default. Create only what the book and future tasks require.

## Portability Rule

If the generated skill will be moved away from the parent book project, copy or regenerate the source coverage paths. Otherwise absolute local paths are acceptable and match the existing local book-skill pattern.
