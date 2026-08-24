---
name: directors-idea-directing
description: "Ken Dancyger The Director's Idea directing workflow. Use when Codex needs to explain the director's idea, analyze text interpretation, actor/camera choices, compare director case studies, design or review a directing plan, or locate source coverage. 中文触发：导演想法、导演思维、导演阐释、文本解读、演员调度、摄影选择、导演案例、Ken Dancyger。"
---

# Directors Idea Directing

## Overview

Use this skill to reason from Ken Dancyger's *The Director's Idea: The Path to Great Directing*. The book treats directing as the search for a deep subtextual interpretation that unifies text interpretation, actor work, camera, lighting, sound, editing, and production design.

The evidence workspace is `/home/fufu/Code/Skills/source/导演思维skill`: complete source-unit notes are in `/home/fufu/Code/Skills/source/导演思维skill/md`, and page-level extracted text is in `/home/fufu/Code/Skills/source/导演思维skill/txt/00_pages`.

## Reference Routing

- For broad directing questions, read [references/core/decision-core.md](references/core/decision-core.md), then [references/core/task-router.md](references/core/task-router.md).
- For the central framework and concept distinctions, read [references/concepts/directors-idea-framework.md](references/concepts/directors-idea-framework.md).
- For applying the book to a script, scene, pitch, or directing plan, read [references/methods/script-interpretation-playbook.md](references/methods/script-interpretation-playbook.md).
- For named directors, films, or case comparisons, read [references/cases/case-index.md](references/cases/case-index.md).
- For reviewing weak directing proposals, read [references/guardrails/directing-review-guardrails.md](references/guardrails/directing-review-guardrails.md).
- For exact chapter/page lookup, read [references/core/source-coverage-map.md](references/core/source-coverage-map.md).
- For answer shapes, read [references/core/report-templates.md](references/core/report-templates.md).

## Core Reasoning Spine

1. Identify the object: whole film, script, scene, character arc, actor direction, camera plan, or director case.
2. State the candidate director's idea as a subtextual claim, not a slogan.
3. Test whether text interpretation, actor work, camera, lighting, sound, editing, and design all point toward the same idea.
4. Classify the directing level: competent if choices clarify plot; good if choices add layered subtext; great if choices express a distinctive, audacious voice.
5. Separate book claim, local interpretation, and practical recommendation.
6. Escalate to parent `md/` notes, then raw `txt/` pages, when exact wording, film examples, page ranges, or chapter-specific claims matter.

## Output Contract

- Give the director's idea in one precise sentence before giving craft advice.
- Tie every recommendation to text interpretation, actor direction, camera/visual strategy, or case-study precedent.
- Name source chapters or `md/` files when the user asks where the book covers a topic.
- Preserve uncertainty when the source note or raw extraction does not support exact wording.

## Hard Rules

- Do not reduce "director's idea" to theme, mood, message, genre, or plot summary.
- Do not recommend camera style, performance style, or editing emphasis unless it serves a stated interpretation.
- Do not treat competent, good, and great directing as moral labels; use them as craft distinctions from the book.
- Do not universalize one director case study; identify the director's specific idea and the tools that serve it.
- Do not invent quotes, page numbers, scene details, or film claims. Use the source coverage map and raw page text for exact lookup.
