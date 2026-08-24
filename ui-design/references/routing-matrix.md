# UI Design Hybrid Routing Matrix

Use the smallest route that fully covers the request. The paths below are relative to the hybrid Skill root.

| Request signal | Primary | Supporting routes | Typical output |
| --- | --- | --- | --- |
| Visual direction, brand language, art direction | ckw-design-skill/SKILL.md | ckw-design-skill/design-thinking/SKILL.md, ckw-design-skill/design-philosophy/SKILL.md, ckw-design-skill/design-system/SKILL.md | visual brief, token direction, composition rules |
| Dashboard, admin, editor, SaaS, tool, data UI | claude-design-skills/skills/interface-design/SKILL.md | ckw-design-skill/design-thinking/SKILL.md, ckw-design-skill/design-system/SKILL.md, ckw-design-skill/deterministic-design/design-ux/SKILL.md | information architecture, interaction model, UI states |
| New page or component implementation | skill-frontend-excellence/SKILL.md | ckw-design-skill/design-system/SKILL.md, skill-frontend-excellence/references/components.md, skill-frontend-excellence/references/responsive.md | implementation plan and quality checks |
| Existing page visual polish | ckw-design-skill/SKILL.md | skill-frontend-excellence/references/design.md, skill-frontend-excellence/references/defects.md | prioritized visual fixes and re-render evidence |
| Accessibility, keyboard, focus, dialogs, forms | claude-design-skills/skills/fixing-accessibility/SKILL.md | skill-frontend-excellence/references/accessibility.md | finding, impact, targeted fix, verification |
| Usability or difficult interactive workflow | ckw-design-skill/deterministic-design/design-ux/SKILL.md | claude-design-skills/skills/interface-design/SKILL.md, skill-frontend-excellence/references/ui-ux.md | fresh-eyes heuristic score and fix order |
| Layout collision, overlap, weak hierarchy, overflow | ckw-design-skill/deterministic-design/design-spatial/SKILL.md | ckw-design-skill/design-system/SKILL.md, skill-frontend-excellence/references/responsive.md | screenshot findings and layout corrections |
| Motion, transition, animation jank | claude-design-skills/skills/fixing-motion-performance/SKILL.md | skill-frontend-excellence/references/motion.md and skill-frontend-excellence/references/performance.md | animation diagnosis and reduced-motion-safe fix |
| Typography and interaction micro-polish | claude-design-skills/skills/emil-design-eng/SKILL.md | ckw-design-skill/design-system/SKILL.md | Before/After/Why review table |
| SEO, metadata, social cards, structured data | claude-design-skills/skills/fixing-metadata/SKILL.md | skill-frontend-excellence/references/seo.md and skill-frontend-excellence/references/pre-launch.md | metadata audit and deterministic corrections |
| Tailwind component baseline | claude-design-skills/skills/baseline-ui/SKILL.md | only the project's existing Tailwind primitives | stack-specific component review |
| Small mechanical CSS fix | relevant local source rule only | no full pipeline unless risk warrants | focused patch and narrow verification |

## Route Selection Rules

1. Prefer the route matching the user's desired outcome, not the technology keyword.
2. If the task changes product meaning or hierarchy, use interface-design or ckw design-thinking before frontend implementation rules.
3. If the task changes interactive behavior, add fixing-accessibility and consider design-ux.
4. If the task changes animation, add fixing-motion-performance and reduced-motion checks.
5. If the task ships a public or shareable page, add fixing-metadata and the relevant SEO checks.
6. If the task is a visual claim, require rendered evidence; do not stop at source inspection.
7. If more than one route applies, run them in the order: intent -> structure -> implementation -> quality gate.
8. Never load all reference files by default. Follow each source package's own routing tables.

## Conflict Rules

- Existing project tokens, component primitives, and framework conventions outrank generic source defaults.
- Accessibility, data integrity, keyboard access, and responsive correctness outrank aesthetic preference.
- Reduced motion outranks motion polish.
- Performance budgets outrank nonessential animation or decorative effects.
- A child Skill may add stricter constraints, but the hybrid router never weakens a child guardrail.
