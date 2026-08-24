# Forward-Test Scenarios

Use this before finalizing a generated book skill. The goal is to test whether the skill changes agent behavior in book-specific, source-grounded ways without loading unnecessary context.

## Contents

- [Test Setup](#test-setup)
- [Minimum Test Set](#minimum-test-set)
- [Technical Or Procedural Books](#technical-or-procedural-books)
- [Argumentative Nonfiction, Philosophy, Or Theory](#argumentative-nonfiction-philosophy-or-theory)
- [History, Biography, Or Memoir As Evidence](#history-biography-or-memoir-as-evidence)
- [Literary Or Narrative Works](#literary-or-narrative-works)
- [Reference, Handbook, Anthology, Or Collection](#reference-handbook-anthology-or-collection)
- [Visual, Design, Art, Or Image-Heavy Books](#visual-design-art-or-image-heavy-books)
- [Acceptance Decision](#acceptance-decision)

## Test Setup

Use prompts that resemble real user tasks:

- pass only the generated skill path and a realistic request;
- do not include expected answers or your diagnosis;
- use source lookup tasks that require correct routing;
- include at least one task that should expose a failure mode;
- record the prompt, references loaded, answer shape, failures, and fixes in the final handoff or maintenance notes.

Do not forward-test by asking another agent to "review the skill". Test it by asking the kind of question a future user would ask.

## Minimum Test Set

Every generated book skill should pass:

1. **Broad task**: answer a high-level question using the generated skill's core routing.
2. **Source lookup task**: locate where the book covers a topic, claim, scene, term, table, or quote.
3. **Application or interpretation task**: use the book's distilled structure on a concrete question.
4. **Failure-mode task**: ask something tempting but unsafe, such as an exact quote, over-broad claim, unsupported interpretation, or out-of-date factual claim.

## Technical Or Procedural Books

Prompts:

- "Use this skill to choose the right method from the book for this scenario: <scenario>."
- "Use this skill to audit this proposed workflow against the book's guardrails: <workflow>."
- "Where does the book cover <specific formula/table/API/method>, and what source files should I inspect?"
- "Apply the book's method to <case> and list assumptions that would invalidate the answer."

Pass signals:

- names the object, inputs, assumptions, steps, and validation;
- loads method or guardrail references before deep source;
- separates book rule from local implementation choice;
- escalates to raw pages for exact formulas or tables.

Fail signals:

- generic advice not specific to the book;
- no source path for exact values;
- treats examples as universal rules;
- skips assumptions and edge cases.

## Argumentative Nonfiction, Philosophy, Or Theory

Prompts:

- "What is the author's central argument about <topic>, and what evidence supports it?"
- "Critique the book's argument about <claim> using its own assumptions."
- "Explain the difference between <term A> and <term B> as this book uses them."
- "Does the book prove <strong claim>, or only suggest it?"

Pass signals:

- separates claim, evidence, assumption, inference, and interpretation;
- preserves objections and limits;
- distinguishes descriptive, causal, normative, and speculative claims;
- routes exact definitions to source coverage and raw pages.

Fail signals:

- turns the author's claim into fact without qualification;
- ignores counterarguments;
- treats anecdotes as sufficient evidence;
- cannot locate the source chapter or page range.

## History, Biography, Or Memoir As Evidence

Prompts:

- "Build a timeline for <event/person/period> from the book."
- "What actors or institutions shape <event>, and what causal explanation does the author give?"
- "How does the narrator or author present their own role in <episode>?"
- "Which facts require caution because they rely on memory, retrospective framing, or contested sources?"

Pass signals:

- separates chronology, actors, causal claims, and source limits;
- marks self-presentation and retrospective framing;
- avoids overclaiming causality from sequence alone;
- records unresolved or contested facts.

Fail signals:

- collapses timeline into a moralized overview;
- treats memoir voice as neutral factual record;
- omits dates, actors, places, or source uncertainty;
- invents causal links not supported by `md/` notes.

## Literary Or Narrative Works

Prompts:

- "Analyze <character> without reducing the answer to plot recap."
- "Trace the motif of <image/object/place> across the work."
- "Give a close reading of this passage or scene using the skill's source routing."
- "Plan an essay comparing two possible interpretations of <theme/scene/ending>."
- "Answer this spoiler-free: what should I watch for in the first third of the book?"

Pass signals:

- separates surface event from interpretation;
- distinguishes narrator, speaker, character, and author;
- preserves ambiguity and competing readings;
- uses character/theme/style references before raw pages;
- handles spoiler constraints when requested.

Fail signals:

- reduces the work to one moral;
- treats plot recap as analysis;
- invents quotes or wording;
- ignores voice, form, style, or imagery;
- loads the whole book for one motif question.

## Reference, Handbook, Anthology, Or Collection

Prompts:

- "Where should I look up <term/case/piece/author/topic>?"
- "Compare how two essays/pieces in the collection handle <theme>."
- "Which entries are relevant to <task>, and which are not?"
- "What exact table or definition should I inspect?"

Pass signals:

- uses lookup index, piece index, term map, or source coverage;
- distinguishes entries/pieces by author, genre, or purpose;
- does not imply a single unified argument when the book is a collection;
- escalates exact definitions and tables to source pages.

Fail signals:

- treats anthology pieces as one authorial voice;
- reads the whole collection for a narrow lookup;
- cannot identify relevant entry paths;
- invents table values or definitions.

## Visual, Design, Art, Or Image-Heavy Books

Prompts:

- "Which plates/figures/images matter for <topic>, and what should be visually inspected?"
- "Explain how the book uses layout or visual sequence in <section>."
- "Can the text extraction alone support this claim about an image?"

Pass signals:

- marks visual inspection requirements;
- separates caption text from visual evidence;
- refuses to infer image details from missing OCR;
- routes to `visual-index.md` or PDF inspection when needed.

Fail signals:

- treats OCR text as enough for visual claims;
- omits captions, plates, maps, or diagrams;
- invents image details;
- does not mark pages requiring PDF inspection.

## Acceptance Decision

After tests, classify the generated skill:

| Verdict | Meaning |
| --- | --- |
| `pass` | Answers are book-specific, source-grounded, and context-efficient. |
| `revise-routing` | The answer knows the domain but loads wrong or too many references. |
| `revise-md-notes` | The routing is sound but `md/` notes lack necessary evidence or omit material knowledge points. |
| `revise-source-coverage` | Source lookup is weak or page/chapter paths are missing. |
| `revise-skill` | The generated `SKILL.md` is generic, too broad, too long, or lacks hard rules. |
| `blocked` | The source extraction, OCR, edition metadata, or missing pages prevent reliable testing. |

Record the verdict and required fixes before final handoff.
