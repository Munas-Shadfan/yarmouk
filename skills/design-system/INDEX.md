# Design System Skill — v2.0.0

Premium Apple-style design system for **Angular 19** (Zard) + **Next.js** (shadcn/ui).
Tokens, components, animation, accessibility, anti-generic patterns — one skill covers it all.

## Files

| File | Lines | Purpose |
|------|-------|---------|
| SKILL.md | 574 | Main skill — tokens, components, animation, premium rules, a11y |
| references/component-map.md | 109 | Zard ↔ shadcn/ui mapping + status badges + keyboard shortcuts |
| references/premium-patterns.md | 154 | Creative arsenal: bento grids, glassmorphism, motion engine, vibe archetypes |
| references/redesign-audit.md | 118 | Checklist for upgrading existing projects to premium quality |
| references/quick-reference.md | 261 | 30-second token/component/spacing lookup |
| references/troubleshooting.md | 474 | Common issues with step-by-step fixes |
| evals/evals.json | 162 | 10 test cases covering both frameworks + premium patterns |
| scripts/validate.sh | — | Scans templates for design system violations |
| scripts/generate_component.sh | — | Creates component boilerplate (Angular or Next.js) |
| scripts/generate_tokens.py | — | Generates Tailwind config, CSS vars, or JSON tokens |

## What's New in v2.0.0

- Merged premium design patterns (animation, motion, glassmorphism, anti-generic rules)
- Added Framer Motion guidance for Next.js
- Added CSS animation patterns for Angular
- Added redesign audit checklist
- Added 5 new eval test cases (premium hero, redesign, glass card, empty state, stagger animation)
- Expanded component map with Tooltip, Avatar, Switch, Slider, Textarea
- Added interactive states section (mandatory loading/empty/error/hover/active/focus/disabled)
- Added RSC safety rules for Next.js
- Added premium typography rules (tracking, text-wrap, weight scale)
- Absorbed taste-design-skill (4 sub-skills) into this unified skill
