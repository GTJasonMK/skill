# Source Fidelity

Use this when exactness matters: editions, translations, page numbering, quotations, footnotes/endnotes, figures, tables, OCR, images, or copyright-sensitive excerpts.

## Edition And Translation

Record:

- title, author, translator/editor if visible;
- edition, publisher, year, ISBN if visible;
- language of source and `md/` notes;
- whether page numbers are PDF pages, printed pages, or both;
- known mismatch between table of contents and PDF page offsets.

For translated works:

- keep important original-language terms when available;
- mark translated wording as edition-specific;
- do not build a close reading from translated phrasing without noting that limitation;
- inspect the PDF for exact wording before quoting.

## Page Numbering

Use PDF page numbers for file paths because `PDF第001页.txt` is stable. If printed page numbers matter, record both:

```text
PDF第037页 / printed page 21
```

Never cite a printed page number when only the PDF page is known.

## Footnotes, Endnotes, References, And Indexes

Do not discard scholarly apparatus by default:

- footnotes may contain definitions, source disputes, caveats, or counterarguments;
- endnotes and references support source tracing;
- indexes reveal important topics and names;
- bibliographies are useful for external follow-up but should not be loaded by default.

Create a separate notes/reference map only when users are likely to ask source-history or exact citation questions.

## Figures, Tables, Plates, And Images

Text extraction often loses visual meaning. Mark pages requiring visual inspection when:

- tables drive the argument;
- figures, diagrams, maps, or plates carry meaning;
- captions contain important claims;
- typography, layout, or visual sequencing matters;
- formulas are garbled.

For visual-heavy books, create a `visual-index.md` with page, caption, subject, and why the image matters.

## Quotations And Excerpts

For exact wording:

1. Locate the source in `references/core/source-coverage-map.md`.
2. Check the complete source-unit note in `md/`.
3. Check raw `txt/`.
4. Inspect the PDF page if wording, line breaks, poetry, typography, formula layout, or OCR quality matters.

Do not invent quotes. Do not silently modernize, translate, or normalize wording.

When producing user-facing excerpts, keep them short and purpose-bound. Prefer `md/` note plus source path for long passages.

## OCR And Extraction Quality

Mark:

- empty pages;
- pages with very short text;
- garbled characters;
- broken line order;
- missing formulas;
- missing table columns;
- headers/footers mixed into body text;
- scanned pages requiring OCR.

`md/` notes may proceed with partial extraction only if the missing pieces are not material, and the uncertainty is recorded.

## Source Fidelity Gate

Before finalizing a book bundle, check:

- Does every `md/` note have a source range?
- Are PDF page and printed page conventions clear?
- Are exact quotes, dates, statistics, formulas, table values, names, and translated terms traceable?
- Are footnotes/endnotes handled deliberately rather than accidentally ignored?
- Are visual or OCR-dependent pages marked?
- Does the generated skill tell future agents when to escalate from `md/` note to raw page to PDF inspection?
