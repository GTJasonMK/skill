# Skill 来源与目录规范

中央目录：/home/fufu/Code/Skills

## 当前领域入口

| 领域 | 当前入口 | 来源性质 |
| --- | --- | --- |
| 00-core | 00-core/brainstorming、00-core/book-to-skill | 通用工作流与书籍提炼工具 |
| 10-data-quant | 10-data-quant/statistical-learning-analysis、factor-quant-analysis、quant-trading-black-box-analysis | 用户自制/派生入口；原始书籍资料在 source/ |
| 20-film-media | 20-film-media/directors-idea-directing、shot-design-directing | 用户自制/派生入口；原始书籍资料在 source/ |
| 30-security | 30-security/ctf-super-hub/ctf-super-hub/SKILL.md、30-security/reverse-skill/skills/MASTER-ROUTING.md | CTF Super Hub、Strix 和 reverse-skill 完整树 |
| 40-dev-tools | 40-dev-tools/cli-anything/SKILL.md、cua-driver/SKILL.md、gdmcp/SKILL.md；完整 Cua 源树在 cua/ | 公开上游工具树与 Agent 入口 |
| 50-ui-design | 50-ui-design/SKILL.md；子源树为 ckw-design-skill、skill-frontend-excellence、claude-design-skills | 本地混合入口，来源为三套公开设计 Skill 树 |

## 用户自制原始资料

- source/因子量化分析skill/
- source/量化交易skill/
- source/导演思维skill/
- source/书籍提炼skill/
- source/镜头设计skill/
- 10-data-quant/statistical-learning-analysis/（本地统计学习 Skill 包）

## 公开来源

- 30-security/ctf-super-hub/ ← https://github.com/asdfgh1445/ctf-super-hub.git
- 30-security/reverse-skill/ ← https://github.com/zhaoxuya520/reverse-skill.git
- 40-dev-tools/cli-anything/ ← https://github.com/HKUDS/CLI-Anything.git
- 40-dev-tools/cua/ ← https://github.com/trycua/cua.git
- 40-dev-tools/gdmcp/ ← https://github.com/yurineko73/Godot-MCP-Native.git
- 50-ui-design/skill-frontend-excellence/ ← https://github.com/ctxr-dev/skill-frontend-excellence.git
- 50-ui-design/ckw-design-skill/ ← https://github.com/connerkward/ckw-design-skill.git
- 50-ui-design/claude-design-skills/ ← https://github.com/master5d/claude-design-skills.git

## Canonical 规则

- 日常加载和领域检索从六个领域目录进入；UI 任务优先从 50-ui-design/SKILL.md 进入。
- source/ 只用于原文证据、书籍资料和生成/维护工作。
- 各领域中的完整上游树保留原始仓库内部结构，不依赖父目录外的散落文件。
- 混合 Skill 只路由到本目录内的子 Skill，不在运行时依赖网络仓库路径。
