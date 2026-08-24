# Book Map And Coverage

Use this when building or auditing the table of contents, page ranges, full-content coverage, deferred sections, or multi-volume coverage plan.

## Purpose

Raw text extraction proves that pages exist; it does not prove that the book has been understood or covered. Keep a separate book map so future agents know what each page range represents and what has not yet received a complete `md/` note.

## Required Artifacts

Every final book bundle needs an explicit TOC/source-unit coverage table. Source lines inside individual `md/` notes prove where those notes came from, but they do not prove that every substantive source unit has been accounted for.

Create one parent book-map file:

```text
md/00_书籍地图与抽取质量_总结.md
```

and keep the generated skill coverage map in:

```text
references/core/source-coverage-map.md
```

Both files should agree on which source units are complete, incomplete, deferred, non-substantive, or synthesis-only.

## Coverage Status

Use plain coverage notes. Mark whether the source exists, whether a complete `md/` note exists, whether generated references cover it, and what uncertainty remains.

## Book Map Template

```markdown
# Book Map

| Unit | PDF pages | Printed pages | Raw text path | Complete md note | Generated reference | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Front matter | 1-6 | i-vi | `txt/00_前置内容/` | `md/00_书籍地图与抽取质量_总结.md` | `references/core/source-coverage-map.md` | non-substantive | edition and extraction notes only |
| Chapter 1 | 7-26 | 1-20 | `txt/01_.../` | `md/第1章_..._总结.md` | `references/...md` | complete | independent substantive chapter |
| References | 389-423 |  | `txt/99_参考文献/` |  |  | deferred | bibliography only |
```

Use only these exact English statuses: `complete`, `incomplete`, `deferred`, `non-substantive`, `synthesis`. Do not use Chinese synonyms such as `未完成`, `待补`, or `暂缓`.

For final handoff, installation, and `check_book_bundle.py --strict`, no `incomplete`, `deferred`, `未完成`, `待补`, `暂缓`, or similar pending rows/reasons may remain. They are valid only while the project is explicitly unfinished.

## Coverage Rules

- Record PDF page ranges even when printed page numbers are also used.
- Keep front matter, appendices, bibliography, index, notes, and acknowledgements visible; mark as deferred or non-substantive if not covered in `md/`.
- Map each substantive source chapter or independently titled source unit to one dedicated complete `md/` note unless it is explicitly split, merged with a non-substantive adjacent unit, incomplete, or deferred.
- Mark part-level, volume-level, theme-level, and book-level rows as `synthesis` when they are navigation or synthesis only. They do not count as coverage for child chapters.
- For anthologies, map each piece separately, not only the whole chapter.
- For poetry or drama, map by poem, act, scene, or section when that is how users will ask questions.
- For visual-heavy books, map plates, figures, diagrams, and captions.
- For multi-volume works, include volume identifier in every row.

## Gap And Duplicate Handling

After moving extracted page files into chapter folders:

- duplicate PDF page filenames usually mean an accidental copy or split error;
- missing page numbers may be acceptable only if the selected range was intentional and recorded;
- short or empty pages should be marked, not silently ignored;
- chapter ranges should not overlap unless the overlap is an intentionally shared appendix, note, or index.

Run `check_book_bundle.py` after reorganizing `txt/`. It warns on duplicate PDF page numbers and page gaps in extracted text files.

## Partial Coverage

If only part of a book is processed, state that in:

- generated `references/core/source-coverage-map.md`;
- final handoff notes;
- final handoff.

Never present a generated skill as full-book coverage when only selected chapters or excerpts have complete `md/` notes.
