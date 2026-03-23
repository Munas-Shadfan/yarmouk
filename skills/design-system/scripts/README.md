# Design System Scripts

Utility scripts for enforcing and implementing the Ovovex Design System.

## Scripts

### `validate.sh`

Scans Angular template files for design system compliance issues.

```bash
./validate.sh .
./validate.sh src/app/pages
```

Checks for:
- ❌ Raw hex colors (`#06B6D4` instead of `bg-primary`)
- ❌ Raw Tailwind colors (`bg-cyan-500` instead of `bg-primary`)
- ❌ Body text below 14px
- ❌ Arbitrary spacing (`p-[13px]` instead of `p-3`)
- ❌ Multiple primary buttons per view
- ❌ Number fields without `font-mono tabular-nums`
- ❌ Cards with `rounded-lg` (should be `rounded-2xl`)
- ❌ Missing focus rings on interactive elements

**Exit codes:**
- `0` = All checks pass ✅
- `1` = Issues found ⚠️

---

### `generate_tokens.py`

Generates framework-specific design token files from the OKLCH color system.

```bash
# Generate Tailwind config
python3 generate_tokens.py --format tailwind --output tailwind.config.ts

# Generate CSS custom properties
python3 generate_tokens.py --format css --output tokens.css

# Generate JSON token dump
python3 generate_tokens.py --format json --output design-tokens.json

# Print to stdout (no file)
python3 generate_tokens.py --format tailwind
```

**Formats:**
- `tailwind` — TypeScript config (dark mode, color aliases)
- `css` — CSS custom properties (`:root` + `@media (prefers-color-scheme: dark)`)
- `json` — Structured token export (colors, spacing, typography, radius, shadows)

---

### `generate_component.sh`

Creates a new component boilerplate with design system compliance built-in.

```bash
# Generate Angular component
./generate_component.sh user-profile angular
# Creates: user-profile.component.ts, user-profile.component.html

# Generate Next.js component
./generate_component.sh user-profile nextjs
# Creates: UserProfile.tsx
```

**Output includes:**
- Correct imports (Zard or shadcn/ui)
- Loading skeleton state
- Signal/state management (Angular/Next.js)
- Design system checklist (comment)
- Semantic tokens, focus rings, correct spacing, etc.

---

## Typical Workflow

1. **Create a new feature**
   ```bash
   ./generate_component.sh invoice-list angular
   ```

2. **Develop the component** (follow design system patterns)

3. **Validate compliance**
   ```bash
   ./validate.sh src/app
   ```

4. **Generate tokens** (if you modified the design system)
   ```bash
   python3 generate_tokens.py --format tailwind --output tailwind.config.ts
   ```

5. **Test dark mode** — toggle system theme, verify all components

---

## Design System Rules (TL;DR)

✅ **DO**
- Use semantic tokens: `bg-primary`, `text-muted-foreground`, `border-border`
- Use spacing scale: `p-4`, `gap-6`, `mb-8` (never `p-[13px]`)
- Use `font-mono tabular-nums text-end` for all numbers
- Use `rounded-md` for inputs/buttons, `rounded-2xl` for cards
- Use `ring-2 ring-ring ring-offset-2` for focus states
- Have ONE primary (`default`) button per view
- Show skeleton screens during loading

❌ **DON'T**
- Don't use raw colors: `bg-cyan-500`, `#06B6D4`, `style="color: red"`
- Don't use arbitrary spacing: `p-[7px]`, `gap-[13px]`
- Don't put body text below 14px (`text-sm` minimum)
- Don't use modals for simple confirmations
- Don't mix multiple font weights in a line
- Don't animate transitions > 200ms

---

## Integration with CI/CD

Add to your pre-commit or CI pipeline:

```yaml
# .github/workflows/design-system-check.yml
- name: Design System Compliance
  run: ./skills/design-system/scripts/validate.sh src/
  if: contains(github.event.head_commit.modified, '*.html')
```

---

## Questions?

Refer to:
- [`SKILL.md`](../SKILL.md) — Full skill documentation
- [`references/component-map.md`](../references/component-map.md) — Angular ↔ Next.js mapping
- [`DESIGN_SYSTEM (1).md`](../../../DESIGN_SYSTEM%20(1).md) — Complete spec (root)
