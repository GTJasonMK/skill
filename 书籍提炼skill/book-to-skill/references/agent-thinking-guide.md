# Agent Thinking Guide

Use this file when turning book content into instructions that shape how an agent reasons.

## Contents

- [Distillation Goal](#distillation-goal)
- [Three Layers](#three-layers)
- [Convert Technical Content Into Agent Rules](#convert-technical-content-into-agent-rules)
- [Convert Literary Content Into Reading Guides](#convert-literary-content-into-reading-guides)
- [Decision Spine Pattern](#decision-spine-pattern)
- [Literary Reading Spine Pattern](#literary-reading-spine-pattern)
- [What To Preserve](#what-to-preserve)
- [What To Compress Aggressively](#what-to-compress-aggressively)
- [Generated Skill Tone](#generated-skill-tone)
- [Self-Review](#self-review)

## Distillation Goal

The output is not a book report. The output is an operating guide for future agents. The operating guide must match the book type: technical books need procedural reasoning; literary books need interpretive reading paths.

For each technical, argumentative, or instructional source chapter or independently titled source unit, extract:

- what problem the author is solving;
- what concepts must be distinguished;
- what sequence of decisions the author implies;
- what evidence the author treats as valid or invalid;
- what common mistakes the author warns against;
- what output a user would expect after applying the book;
- where the book is descriptive, normative, empirical, speculative, or outdated.

For each literary chapter, scene, poem, act, or section, extract:

- what happens or what situation is staged;
- which characters, voices, speakers, or perspectives matter;
- what desires, conflicts, silences, or changes drive the section;
- how narration, focalization, time, genre, rhythm, or form shapes meaning;
- what themes, motifs, images, symbols, or repeated words appear;
- what ambiguity or interpretive tension should remain open;
- which pages require exact quotation or PDF inspection.

## Three Layers

Distill every important idea through three layers:

| Layer | Question | Output |
| --- | --- | --- |
| Source layer | What does the book say? | Complete source-unit `md` note with page range and exact caveats. |
| Reasoning layer | How should an agent think with it? | Decision spine, reading spine, task routing, examples, failure modes. |
| Execution layer | What should an agent do for a user? | Workflow, checklist, interpretive map, output contract, validation steps. |

Keep these layers separate. The source layer in `md/` is a complete note for human reading and traceability, not a brief abstract; reasoning references support future problem solving.

## Convert Technical Content Into Agent Rules

Use this conversion pattern:

```text
Book claim -> agent rule -> evidence needed -> failure mode -> source pointer
```

Example:

```text
Book claim: A method only works under a specific data-generating assumption.
Agent rule: Before recommending the method, name the assumption and test whether the user's case violates it.
Evidence needed: User data schema, sampling process, known constraints.
Failure mode: Recommending a method by name because it appears in the book.
Source pointer: md/第X章_..._总结.md, PDF第YYY页.txt.
```

## Convert Literary Content Into Reading Guides

Use this conversion pattern:

```text
Textual feature -> interpretive function -> competing readings -> source anchor -> user task
```

Example:

```text
Textual feature: The narrator repeatedly withholds direct explanation of a character's motive.
Interpretive function: The reader must infer motive from gesture, dialogue, and scene arrangement.
Competing readings: The character may be self-protective, manipulative, or socially constrained.
Source anchor: md/第X章_..._总结.md, PDF第YYY页.txt.
User task: close reading, character analysis, essay prompt, theme discussion.
```

For literary works, do not force every feature into an instruction like "do X". Often the useful agent behavior is "keep these interpretations separate and cite the passage that supports each one."

## Decision Spine Pattern

For broad book skills, define a short decision spine:

1. **Object**: What is being analyzed, designed, explained, or audited?
2. **Claim**: What type of claim is being made?
3. **Context**: What assumptions, domain constraints, time horizon, or data conditions matter?
4. **Mechanism**: What causal, logical, procedural, or empirical mechanism does the book use?
5. **Evidence**: What would support or falsify the claim?
6. **Failure Mode**: What mistake would a user or agent likely make?
7. **Action**: What recommendation, workflow, test, or deliverable should follow?

If the book is conceptual, the spine can be shorter. If the book is technical, include validation and implementation steps.

## Literary Reading Spine Pattern

For literary book skills, define a reading spine:

1. **Text Unit**: Which chapter, scene, poem, act, or passage is in question?
2. **Surface Movement**: What happens, who speaks, or what situation is staged?
3. **Voice/Form**: Who sees or tells it, and how does style, time, structure, or genre shape it?
4. **Character/Relation**: What motives, conflicts, relationships, or changes matter?
5. **Motif/Theme**: What images, symbols, themes, or repeated patterns are active?
6. **Ambiguity**: What remains unresolved or supports more than one reading?
7. **Source Evidence**: Which `md/` note and raw page support the answer?
8. **Response Shape**: Plot recap, close reading, character analysis, theme map, essay plan, or quote lookup.

## What To Preserve

Preserve high-value material:

- definitions with sharp distinctions;
- formulas and assumptions;
- tables that classify methods or cases;
- examples that change how decisions are made;
- checklists, sequences, and diagrams;
- author caveats and boundary conditions;
- disagreements or alternative interpretations;
- literary scenes, speaker shifts, character turns, motifs, images, symbols, and distinctive language when they drive interpretation;
- local terminology, especially Chinese/English term mappings.

## What To Compress Aggressively

Compress low-value material:

- anecdotes or plot details that do not affect later scenes, character, theme, or form;
- repeated historical background;
- motivational prose;
- examples that only illustrate a definition already captured;
- long literature lists unless they affect source lookup or further research.

## Generated Skill Tone

Write the generated skill as instructions, not exposition:

- Use verbs: "Classify", "Check", "Load", "Reject", "Report".
- Prefer conditionals: "If the user asks X, read Y before answering."
- Add hard rules only for mistakes that materially change outcomes.
- Add output contracts for repeatable deliverables.
- Mention exact source lookup paths when source fidelity matters.

For literary generated skills, allow interpretive language:

- Use verbs such as "Trace", "Compare", "Distinguish", "Locate", "Preserve", "Test against the passage".
- Prefer source-grounded alternatives over single definitive readings.
- Add spoiler and translation/version handling when relevant.

## Self-Review

Before finalizing generated references, ask:

- Would a future agent know what to read first?
- Would it know what not to load?
- Would it produce a different answer because of this book?
- Can it trace exact claims to `md/` notes or raw pages?
- Are rules centralized, or duplicated across files?
- Are uncertainties visible rather than smoothed over?
