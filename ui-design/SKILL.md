---
name: ui-design-hybrid
description: Unified UI and frontend design router for visual direction, product interfaces, responsive implementation, accessibility, performance, motion, metadata, and rendered visual review. Use this as the single entrypoint for UI work and route to the smallest local specialist set.
version: 1.0.0
---

# UI Design Hybrid Router

This is the single entrypoint for the complete UI design collection under this directory. It composes three local source families without depending on external paths or network access:

- ckw-design-skill/: intent, visual direction, design system, spatial composition, and usability.
- skill-frontend-excellence/: frontend implementation quality, performance, responsive behavior, accessibility, SEO, and testing.
- claude-design-skills/: product interface design plus focused typography, accessibility, motion, metadata, and baseline checks.

Read this router first. Then load only the primary Skill and supporting specialists selected by the task. Do not concatenate every source package into the context.

## Operating Contract

1. Inspect the existing product, routes, components, theme tokens, assets, framework, and interaction conventions before proposing a direction.
2. Identify the user, repeated task, information density, primary action, important states, and viewport constraints.
3. Choose a visual direction with concrete reasons before implementation. Do not accept generic defaults such as purple gradients, ornamental blobs, nested cards, or a one-hue palette.
4. Preserve the existing design system and component primitives when they exist. Do not mix primitive systems inside one interaction surface.
5. Route to the smallest specialist set below. A supporting Skill supplies constraints; it does not replace the primary workflow.
6. Implement the real workflow and its states before decorative polish.
7. Render the real artifact, test wide and narrow viewports, and run the relevant quality gates before calling the work complete.

## Primary Routes

### Visual direction, art direction, or design language

Primary: ckw-design-skill/SKILL.md

Also load when relevant:

- ckw-design-skill/design-thinking/SKILL.md for audience, product domain, tone, signature, and visual intent.
- ckw-design-skill/design-system/SKILL.md when defining tokens, typography, colors, loading, or component mechanics.
- ckw-design-skill/deterministic-design/design-spatial/SKILL.md when composing layout or reviewing collisions, balance, and responsive geometry.
- ckw-design-skill/design-philosophy/SKILL.md for high-concept visual direction or a distinctive art-like treatment.

### Dashboard, admin panel, editor, SaaS tool, or data interface

Primary: claude-design-skills/skills/interface-design/SKILL.md

Supporting routes:

- ckw-design-skill/design-thinking/SKILL.md for domain-specific intent and hierarchy.
- ckw-design-skill/design-system/SKILL.md for tokens and implementation decisions.
- ckw-design-skill/deterministic-design/design-ux/SKILL.md before shipping an interactive tool or when the workflow is hard to learn.
- skill-frontend-excellence/references/ui-ux.md and skill-frontend-excellence/references/components.md for interaction and component review.

Do not use the interface-design route as the primary route for marketing or editorial pages; use the visual-direction route and the frontend-quality route instead.

### Frontend implementation, responsive behavior, or visual polish

Primary: skill-frontend-excellence/SKILL.md

Choose two or three targeted references from its routing tables, not the whole directory. Typical selections are:

- New page or component: skill-frontend-excellence/references/components.md, skill-frontend-excellence/references/design.md, skill-frontend-excellence/references/responsive.md.
- Existing visual audit: skill-frontend-excellence/references/audit-workflow.md, skill-frontend-excellence/references/defects.md, skill-frontend-excellence/references/design.md.
- Performance or Lighthouse issue: skill-frontend-excellence/references/lighthouse.md, skill-frontend-excellence/references/performance.md, skill-frontend-excellence/references/debug-recipes.md.
- Forms and interaction: skill-frontend-excellence/references/forms.md, skill-frontend-excellence/references/accessibility.md, skill-frontend-excellence/references/ui-ux.md.
- Pre-launch verification: skill-frontend-excellence/references/pre-launch.md and skill-frontend-excellence/references/quick-reference.md.

### Accessibility, keyboard, focus, dialogs, or forms

Primary: claude-design-skills/skills/fixing-accessibility/SKILL.md

Supporting: skill-frontend-excellence/references/accessibility.md and, for an interactive rendered artifact, ckw-design-skill/deterministic-design/design-ux/SKILL.md.

The critical order is accessible names, keyboard access, focus and dialogs, semantics, forms and errors, announcements, then contrast and state review.

### Motion, transitions, animation, or jank

Primary: claude-design-skills/skills/fixing-motion-performance/SKILL.md

Supporting: skill-frontend-excellence/references/motion.md and skill-frontend-excellence/references/performance.md. Use ckw-design-skill/design-system/SKILL.md for timing and semantic motion tokens. Default to transform and opacity, batch reads before writes, stop animation loops, and respect reduced motion.

### SEO, page metadata, social previews, or structured data

Primary: claude-design-skills/skills/fixing-metadata/SKILL.md

Supporting: skill-frontend-excellence/references/seo.md, skill-frontend-excellence/references/lighthouse.md, and skill-frontend-excellence/references/pre-launch.md. Keep title, description, canonical, Open Graph URL, and indexing intent deterministic and consistent.

### Typography and fine interaction polish

Primary: claude-design-skills/skills/emil-design-eng/SKILL.md

Supporting: ckw-design-skill/design-system/SKILL.md and skill-frontend-excellence/references/design.md. When reporting a code review through this route, use the source Skill's required Before/After/Why table format.

### Tailwind-specific baseline review

Load claude-design-skills/skills/baseline-ui/SKILL.md only when the project actually uses Tailwind and its stated primitive stack. Do not impose Tailwind, motion/react, or Base UI rules on a project using another framework or component system.

## Composite Pipelines

### New product UI

1. ckw-design-skill/design-thinking/SKILL.md: define user, domain, purpose, tone, and signature.
2. claude-design-skills/skills/interface-design/SKILL.md or the visual-direction primary: establish information architecture and the main workflow.
3. ckw-design-skill/design-system/SKILL.md: define or map tokens, typography, color roles, loading, and motion.
4. skill-frontend-excellence/SKILL.md: select implementation, responsive, accessibility, and performance checks.
5. ckw-design-skill/deterministic-design/design-spatial/SKILL.md: render and obtain a separate fresh-eyes critique.
6. Run the applicable accessibility, UX, motion, metadata, and pre-launch specialists before the final report.

### Existing UI polish or redesign

1. Inspect the existing artifact and identify the highest-impact workflow or visual defect.
2. Route to interface-design for product structure, ckw-design for visual direction, or frontend-excellence for implementation quality.
3. Add only the focused accessibility, motion, metadata, or UX specialist required by the observed defect.
4. Render the same primary path again and compare before/after behavior at wide and narrow widths.

### Review-only task

Report findings first, ordered by broken workflow or inaccessible behavior, then responsive and hierarchy failures, then polish issues. Quote concrete evidence from the artifact or code. End with tested viewports, exercised states, and remaining assumptions.

## Universal Quality Gates

These gates apply regardless of which route is primary:

- Render the real workflow with realistic content; a code-only inspection is insufficient for visual claims.
- Have a separate fresh-eyes reviewer inspect the rendered result when visual composition or usability is in scope.
- Measure horizontal overflow at approximately 390px and 1024px: document.documentElement.scrollWidth - document.documentElement.clientWidth must be zero unless an intentional local scroll container is documented.
- Check loading, empty, error, disabled, hover, focus-visible, pressed, selected, success, validation, and narrow-viewport states that exist in the workflow.
- Verify semantic elements, accessible names, keyboard traversal, focus visibility, dialog Escape behavior, contrast, reduced motion, zoom/reflow, and no keyboard traps.
- Keep layout stable with explicit tracks, min/max constraints, aspect ratios, or reserved media space. Do not hide overflow to conceal a defect.
- Use project tokens and existing primitives. Do not introduce arbitrary colors, random spacing, or a second interaction primitive system.
- For operational tools, prioritize scanning, comparison, clear status, predictable navigation, and efficient repeated actions over decorative presentation.

## Child Source Policy

All routed source files are descendants of this directory. Resolve every path relative to this file. The source packages are complete local bundles; do not fetch a missing rule from a parent directory or an online repository during normal Skill execution. Preserve upstream attribution and local package instructions when editing a child source package.

## Reference Map

- Routing decisions: references/routing-matrix.md
- Stage inputs, outputs, and handoff contract: references/hybrid-workflow.md
- Bundle inventory and provenance: BUNDLE-MANIFEST.md
