# Run Record And Maintenance

Use this when a book project spans multiple sessions, `md/` notes change after initial generation, or the generated skill may drift from source text and complete source-unit notes.

## Maintenance Record Location

Follow the reference book-skill pattern:

- source evidence stays in the parent `txt/` and `md/` directories;
- source coverage and deferred sections live in the generated skill's `references/core/source-coverage-map.md`;
- validation commands, forward-test prompts, and remaining risks are reported in the final handoff.

If a long project needs a temporary work log, keep it outside the generated skill or as a short local note, not as a required output artifact.

## Drift Checks

After editing `txt/`, `md/`, or generated skill references:

1. Update `references/core/source-coverage-map.md`.
2. Run `check_book_bundle.py`.
3. Run `quick_validate.py` on the generated skill.
4. Re-run at least one task-specific forward test from [forward-test-scenarios.md](forward-test-scenarios.md) affected by the change.
5. Report the validation command and result in the handoff.

## Incremental Work

For large books, process in batches:

- mark deferred sections directly in `references/core/source-coverage-map.md`;
- do not imply full-book coverage when only selected chapters have complete `md/` notes;
- keep OCR, page-boundary, formula, table, figure, and translation risks visible;
- update generated task references only after the relevant `md/` note is complete enough to support them.

## Maintenance Rules

- If `md/` notes change, check whether generated `core/task-router.md`, `core/source-coverage-map.md`, concept maps, character maps, or argument maps must change.
- If raw extraction is corrected, check `md/` notes that used the affected pages.
- If the generated skill's frontmatter trigger changes, validate `agents/openai.yaml` still matches.
- If the book mode changes, revisit [genre-router.md](genre-router.md) and the generated reference set.
- If edition or translation metadata changes, revisit [source-fidelity.md](source-fidelity.md).

## Handoff Record

Final handoff should include:

- source PDF and extraction backend;
- `txt/` page count and known extraction issues;
- `md/` note coverage and deferred sections;
- generated skill path;
- generated `references/core/source-coverage-map.md` path;
- discovery path or local-only decision;
- validation commands and results;
- forward-test prompts and verdicts;
- unresolved risks and the next command to run.
