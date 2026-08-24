# UI Design Hybrid Skill

The canonical entry for this category is SKILL.md. It routes the complete local UI design collection instead of requiring the agent to choose among separate source packages manually.

## Source families

- ckw-design-skill/: visual intent, design systems, spatial composition, and usability.
- skill-frontend-excellence/: frontend implementation, responsive behavior, accessibility, performance, SEO, and launch checks.
- claude-design-skills/: interface design, typography, accessibility, motion performance, metadata, and Tailwind-specific baseline checks.

## Hybrid workflow

The normal order is intent -> structure -> implementation -> audit. The root router loads only the relevant child routes and keeps every source package self-contained under this directory.

See BUNDLE-MANIFEST.md for the complete local route inventory and references/routing-matrix.md for task selection.
