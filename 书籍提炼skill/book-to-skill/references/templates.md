# Templates

Use these templates when drafting complete `md/` notes and generated skill files. Adapt headings to the book; keep source traceability.

## Contents

- [Complete Chapter Note Template](#complete-chapter-note-template)
- [Complete Literary Chapter Or Section Note Template](#complete-literary-chapter-or-section-note-template)
- [Book Map And TOC Coverage Template](#book-map-and-toc-coverage-template)
- [Generated SKILL.md Template](#generated-skillmd-template)
- [Nonfiction Argument Complete Note Template](#nonfiction-argument-complete-note-template)
- [Literary Generated SKILL.md Template](#literary-generated-skillmd-template)
- [Task Router Template](#task-router-template)
- [Source Coverage Template](#source-coverage-template)
- [Final Handoff Template](#final-handoff-template)

## Complete Chapter Note Template

```markdown
# 第X章 章节标题

来源：`txt/.../PDF第NNN页.txt` 至 `txt/.../PDF第MMM页.txt`

本章核心：一段话说明作者解决的问题、中心论点，以及这一章对全书框架的作用。

覆盖要求：本文件是给用户阅读的完整内容总结，不是摘要。必须覆盖本章所有实质知识点、论证步骤、例子、公式/表格、限制条件、作者保留意见和需要追溯原文的位置；只压缩重复、铺垫和不改变理解的修辞。

完成要求：初稿之后必须重读本章原文页，反复补充遗漏，直到遗漏审计不再发现任何实质知识点遗漏。没有完成“页/段落覆盖”“遗漏审计”“迭代修订记录”“最终无遗漏声明”的章节不能标记为 complete。

## 结构

- 主题一：...
- 主题二：...
- 主题三：...

## 完整内容展开

- 知识点/论证步骤一：
- 知识点/论证步骤二：
- 知识点/论证步骤三：
- 次要但不能遗漏的限定、例外或补充：

## 页/段落覆盖

| PDF 页/段落 | 原文内容块 | 已纳入本总结的位置 | 覆盖状态 | 备注 |
| --- | --- | --- | --- | --- |
| PDF第NNN页 | ... | `## 完整内容展开` / `## 例子与边界` | complete | ... |

## 关键概念

| 概念 | 含义 | 易混点 | Agent 用法 |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## 公式、表格或定义

- 公式/表格/定义：
- 前提假设：
- 提取问题或需人工核对处：

## 方法与流程

1. ...
2. ...
3. ...

## 例子与边界

- 例子：
- 适用边界：
- 反例或失败模式：

## Agent 提炼

- 未来遇到什么任务应读取本章：
- 本章带来的决策规则：
- 本章禁止的常见误用：
- 需要追溯原文时检查哪些页：

## 遗漏审计

逐页/逐节重读原文后记录：

| 审计轮次 | 发现的遗漏 | 处理方式 | 状态 |
| --- | --- | --- | --- |
| 第1轮 | ... | 已补入 ... | resolved |
| 第2轮 | 无新增实质遗漏 | 无需修改 | clear |

## 迭代修订记录

- 第1轮：补充了...
- 第2轮：复查 PDF第NNN页 至 PDF第MMM页，未发现新的实质遗漏。

## 最终无遗漏声明

本章已按来源页范围逐页/逐节复查；截至最后一轮审计，未发现仍遗漏的实质知识点、论证步骤、例子、公式/表格、限制条件或作者保留意见。若未来发现遗漏，必须先更新本章再更新 source coverage。

## 未决问题

- OCR/公式/表格问题：
- 解释不确定性：
- 后续需与其他章节合并的内容：
```

## Complete Literary Chapter Or Section Note Template

```markdown
# 第X章/场景/诗篇 标题

来源：`txt/.../PDF第NNN页.txt` 至 `txt/.../PDF第MMM页.txt`

本节核心：一段话说明表层事件、情感/关系变化、叙事或语言上的关键动作，以及它在全书中的作用。

覆盖要求：本文件是给用户阅读的完整内容总结，不是情节摘要。必须覆盖本节所有重要事件、人物状态变化、关系推进、叙事形式、语言风格、主题母题、意象象征、暧昧处和可追溯页码；只压缩重复场景或不影响解释的铺垫。

完成要求：初稿之后必须重读本节原文页，反复补充遗漏，直到遗漏审计不再发现任何实质文本细节遗漏。没有完成“页/段落覆盖”“遗漏审计”“迭代修订记录”“最终无遗漏声明”的章节不能标记为 complete。

## 表层推进

- 发生了什么：
- 出场人物/叙述声音：
- 本节开始与结束时的变化：

## 场景/段落展开

- 场景或段落一：
- 场景或段落二：
- 场景或段落三：
- 不能省略的细节、伏笔或转折：

## 页/段落覆盖

| PDF 页/段落 | 原文内容块 | 已纳入本总结的位置 | 覆盖状态 | 备注 |
| --- | --- | --- | --- | --- |
| PDF第NNN页 | ... | `## 场景/段落展开` / `## 语言与风格` | complete | ... |

## 人物与关系

| 人物/声音 | 状态与欲望 | 冲突/关系 | 关键证据页 |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## 叙事与形式

- 叙事视角/聚焦：
- 时间结构：
- 节奏与场景安排：
- 可靠性、反讽或留白：

## 主题、母题与意象

| 主题/母题/意象 | 在本节的表现 | 可能功能 | 后续追踪 |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## 语言与风格

- 关键词、重复词或句式：
- 比喻、象征、声音或节奏：
- 语域、语气、幽默、冷峻、抒情或讽刺：
- 需要核对原文/译文的页：

## 可并存的解读

- 解读 A：证据与限制。
- 解读 B：证据与限制。
- 尚未解决的张力：

## Agent 提炼

- 未来遇到什么任务应读取本节：
- 适合的回答形态：情节回顾/人物分析/主题追踪/细读/论文提纲/引文定位。
- 不应犯的误读：
- 需要追溯原文时检查哪些页：

## 遗漏审计

逐页/逐节重读原文后记录：

| 审计轮次 | 发现的遗漏 | 处理方式 | 状态 |
| --- | --- | --- | --- |
| 第1轮 | ... | 已补入 ... | resolved |
| 第2轮 | 无新增实质遗漏 | 无需修改 | clear |

## 迭代修订记录

- 第1轮：补充了...
- 第2轮：复查 PDF第NNN页 至 PDF第MMM页，未发现新的实质遗漏。

## 最终无遗漏声明

本节已按来源页范围逐页/逐节复查；截至最后一轮审计，未发现仍遗漏的重要事件、人物变化、关系推进、叙事形式、语言风格、主题母题、意象象征、暧昧处或可追溯页码。若未来发现遗漏，必须先更新本节再更新 source coverage。
```

## Book Map And TOC Coverage Template

Use this in `md/00_书籍地图与抽取质量_总结.md` or an equivalent book-map file before claiming the `md/` layer is complete.

Part synthesis files are optional navigation aids. They are not substitutes for per-chapter or per-source-unit complete notes.

```markdown
# 书籍地图与 TOC 覆盖

来源：`txt/.../PDF第001页.txt` 至 `txt/.../PDF第NNN页.txt`

## 抽取范围与版本

- PDF 文件：
- 抽取页数：
- 版本/译本/页码说明：
- OCR、图表、脚注、公式或版面风险：

## TOC 到 md 覆盖表

| 源书层级 | 源书 TOC 项 | PDF 页范围 | md 完整内容总结 | 状态 | 原因/处理说明 |
| --- | --- | --- | --- | --- | --- |
| Part | 第一部分 ... | 001-080 | 可选：`md/第1部分_..._地图.md` | synthesis | 只作导航，不替代章节笔记 |
| Chapter | 第1章 ... | 001-020 | `md/第1章_..._总结.md` | complete | 独立实质章节 |
| Chapter | 第2章 ... | 021-040 | `md/第2章_..._总结.md` | incomplete | 待补表格和例子 |
| Appendix | 附录 ... | 300-310 | `md/附录A_..._总结.md` | deferred | 用户暂未要求，不能计入完整覆盖 |
| Front matter | 致谢 | 006-008 | 合并至 `md/00_书籍地图与抽取质量_总结.md` | non-substantive | 无实质论证或情节内容 |

状态必须使用英文固定枚举：`complete`、`incomplete`、`deferred`、`non-substantive`、`synthesis`。不要使用“未完成”“待补”“暂缓”等中文近义词。

最终交付或安装前不得保留 `incomplete`、`deferred`、“未完成”“待补”“暂缓”等未完成状态或原因；这些只表示当前仍是本地施工状态。

## 覆盖结论

- 可称为完整覆盖的范围：
- 不能称为完整覆盖的范围：
- 下一步必须补的 md：
```

## Generated SKILL.md Template

```markdown
---
name: generated-skill-name
description: "Book-derived workflow for ... Use when Codex needs to ... 中文触发：..."
---

# Generated Skill Title

## Overview

Use this skill to ...

This skill is based on complete local Markdown source-unit notes in `/absolute/path/to/book-project/md` and page-level text in `/absolute/path/to/book-project/txt`.

## Reference Routing

- For broad tasks, read [references/core/decision-core.md](references/core/decision-core.md) first, then [references/core/task-router.md](references/core/task-router.md).
- For directory layout or load-order uncertainty, read [references/core/reference-architecture.md](references/core/reference-architecture.md).
- For exact chapter coverage, read [references/core/source-coverage-map.md](references/core/source-coverage-map.md).
- For final deliverables, read [references/core/report-templates.md](references/core/report-templates.md).

## Core Reasoning Spine

1. Classify the object.
2. Name the claim.
3. Check the book-specific assumptions.
4. Select the smallest relevant reference.
5. Separate source statement, interpretation, and recommendation.
6. Escalate to full source-unit notes or raw text only when exact source fidelity matters.

## Output Contract

- ...

## Hard Rules

- ...
```

## Nonfiction Argument Complete Note Template

```markdown
# 第X章 章节标题

来源：`txt/.../PDF第NNN页.txt` 至 `txt/.../PDF第MMM页.txt`

本章核心：一段话说明作者的中心论点、论证目标，以及本章在全书论证中的位置。

## 论点结构

| 层级 | 主张 | 依赖前提 | 支持证据 | 反驳/限制 |
| --- | --- | --- | --- | --- |
| 中心论点 | ... | ... | ... | ... |
| 子论点 | ... | ... | ... | ... |

## 关键概念

| 概念 | 定义 | 与相近概念区别 | 原文页 |
| --- | --- | --- | --- |
| ... | ... | ... | ... |

## 证据与案例

| 证据/案例 | 类型 | 支持什么主张 | 局限 |
| --- | --- | --- | --- |
| ... | 数据/案例/历史/实验/类比/权威引用 | ... | ... |

## 反方与缺口

- 作者处理的反对意见：
- 作者没有处理但重要的反对意见：
- 因果、规范、事实或外推风险：

## Agent 提炼

- 未来遇到什么任务应读取本章：
- 可迁移的论证规则或概念区分：
- 不应过度外推的地方：
- 需要追溯原文时检查哪些页：
```

## Literary Generated SKILL.md Template

```markdown
---
name: generated-literary-skill
description: "Book-derived literary analysis workflow for ... Use when Codex needs to explain plot, analyze characters, trace themes or motifs, perform close reading, plan essays, compare literary works, or locate source passages. 中文触发：..."
---

# Generated Literary Skill Title

## Overview

Use this skill to read and analyze `<book>` with source-grounded attention to plot, character, voice, form, theme, motif, style, ambiguity, and interpretation.

This skill is based on complete local Markdown source-unit notes in `/absolute/path/to/book-project/md` and page-level text in `/absolute/path/to/book-project/txt`.

## Reference Routing

- For broad literary questions, read [references/core/decision-core.md](references/core/decision-core.md) first, then [references/core/task-router.md](references/core/task-router.md).
- For the compact reading spine, read [references/reading/reading-spine.md](references/reading/reading-spine.md).
- For character questions, read [references/characters/character-map.md](references/characters/character-map.md).
- For theme, motif, image, and symbol questions, read [references/themes/themes-motifs.md](references/themes/themes-motifs.md).
- For narration, style, structure, and close reading, read [references/style/narrative-style.md](references/style/narrative-style.md).
- For exact chapter/page lookup, read [references/core/source-coverage-map.md](references/core/source-coverage-map.md).

## Reading Spine

1. Identify the text unit: chapter, scene, poem, act, or passage.
2. Separate surface event from interpretation.
3. Check voice, focalization, time, form, and style.
4. Track character desire, relation, conflict, and change.
5. Trace active themes, motifs, images, and symbols.
6. Preserve ambiguity and competing readings when the text supports them.
7. Escalate to raw pages or PDF for exact wording and close reading.

## Output Contract

- Plot or scene movement when relevant.
- Character/theme/form analysis with source anchors.
- Competing interpretations and their evidence.
- Quote/page lookup needs and translation/version caveats.
- Spoiler handling if the user asks for spoiler-safe handling.

## Hard Rules

- Do not reduce the work to a single moral.
- Do not confuse narrator, speaker, character, and author.
- Do not treat plot recap as interpretation.
- Do not invent quotations or distinctive wording.
- Do not erase ambiguity unless the text resolves it.
```

## Task Router Template

```markdown
# Task Router

Use this first for ordinary tasks. Load only the minimum bundle.

| Task | Use when | Minimum references | Add only if needed | Output shape |
| --- | --- | --- | --- | --- |
| Concept explanation | User asks what a concept means | `concepts/concept-map.md` or `methods/method-map.md` | `core/source-coverage-map.md` for exact chapter lookup | Definition, contrast, example, misuse |
| Method application | User wants to apply the book | `core/decision-core.md`, task-specific playbook | full source-unit note if assumptions are unclear | Workflow, inputs, checks, output |
| Audit/review | User asks if a plan follows the book | task-specific guardrails, `core/decision-core.md` | raw page text for exact claim | Findings, severity, source, fix |
| Chapter lookup | User asks where the book covers X | `core/source-coverage-map.md` | parent `md/` or `txt/` | Chapter/page path and short answer |
```

## Source Coverage Template

```markdown
# Source Coverage Map

The complete source notes live in `/absolute/path/to/book-project/md`.
The raw page text lives in `/absolute/path/to/book-project/txt`.

| Topic | Chapter note | PDF pages | Raw text path | Generated reference |
| --- | --- | --- | --- | --- |
| ... | `md/...md` | NNN-MMM | `txt/...` | `references/...md` |

## Exact Lookup Rules

- Use `md/` notes for chapter-level claims and complete knowledge-point review.
- Use raw text for exact wording, formulas, tables, or page-specific questions.
- If raw text extraction is garbled, inspect the PDF page.
```

## Final Handoff Template

```markdown
完成：已把 `<book>.pdf` 提炼为本地 book skill bundle。

关键文件：
- PDF: `<path>`
- 原文 TXT: `<path>/txt`
- 完整内容总结: `<path>/md`
- 生成 skill: `<path>/<generated-skill>`
- 自动发现路径: `<~/.codex/skills/generated-skill>` 或 `local-only`
- 来源覆盖图: `<path>/<generated-skill>/references/core/source-coverage-map.md`

验证：
- `<command>`: passed/failed
- `<command>`: passed/failed

仍需注意：
- ...
```
