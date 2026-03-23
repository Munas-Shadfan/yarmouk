---
name: design-system
description: >
  Use when the user asks to build, style, review, redesign, or implement any UI component,
  page layout, animation, or visual pattern in Angular or Next.js. Triggers on: "build X",
  "style this", "implement a table/form/modal/card/sidebar", "design system", "dark mode",
  "accessibility", "animation", "motion", "framer motion", "make it look premium",
  "Apple style", "clean modern design", "shadcn", "Zard component", "review my UI",
  "redesign this", "make it less generic", "loading state", "skeleton", "empty state",
  "hover effect", "micro-interaction", "glass effect", or any frontend design question.
  Also triggers when pasting UI code for review.
metadata:
  version: 2.1.0
---

# Design System Skill

Premium, Apple-style design system for **Angular 19** (Zard) and **Next.js** (shadcn/ui).
Keyboard-first, bilingual (LTR/RTL), dark-mode native, built on **Tailwind CSS 4 + semantic tokens**.

**References bundled with this skill:**
- `references/component-map.md` — Zard ↔ shadcn/ui equivalents
- `references/premium-patterns.md` — Animation, motion, glassmorphism, anti-generic rules
- `references/redesign-audit.md` — Checklist for upgrading existing projects
- `references/quick-reference.md` — 30-second token/component lookup
- `references/troubleshooting.md` — Common issues with fixes

---

## Step 1 — Detect the Framework

Before writing any code:
1. Check the open file — `.component.ts` / `.html` = Angular, `.tsx` = Next.js
2. Ask if it cannot be determined

Design tokens are identical across both frameworks. Only component syntax differs.

**Dependency check:** Before importing ANY library (`framer-motion`, `lucide-react`, etc.), check `package.json`. If missing, output the install command first.

---

## Semantic Token System (Both Frameworks)

**Never use raw values.** Every color reference MUST go through semantic tokens — they automatically adapt to dark mode.

```
BANNED                          USE INSTEAD
bg-cyan-500                     bg-primary
style="color: #06B6D4"         text-primary
border-radius: 8px              rounded-md
bg-zinc-100                     bg-muted
bg-white                        bg-card
text-gray-500                   text-muted-foreground
border-gray-200                 border-border
text-emerald-500                text-success
text-amber-500                  text-warning
bg-red-500                      bg-destructive
shadow-lg (untinted)            shadow-lg shadow-black/[0.08]
```

### Token Reference

| Purpose | Token / Class |
|---|---|
| Primary action | `bg-primary text-primary-foreground` |
| Page background | `bg-background text-foreground` |
| Card / surface | `bg-card text-card-foreground` |
| Muted / secondary bg | `bg-muted text-muted-foreground` |
| Destructive / error | `bg-destructive text-destructive-foreground` |
| Success | `bg-success text-success-foreground` · text-only: `text-success` |
| Warning | `bg-warning text-warning-foreground` · text-only: `text-warning` |
| Standard border | `border-border` |
| Form field border | `border-input` |
| Focus ring | `ring-2 ring-ring ring-offset-2` |
| Popover / dropdown | `bg-popover text-popover-foreground` |
| Vibrancy surface | `backdrop-blur-xl bg-background/80 border-border/50` |

### Opacity Variants (prefer over raw shades)

```
bg-primary/10    → subtle tint (chip backgrounds, hover zones)
bg-primary/20    → light tint (active states)
bg-success/10    → positive indicator backgrounds
bg-destructive/10 → error / danger backgrounds
text-foreground/60  → secondary body text
text-foreground/40  → placeholder / hint text
border-border/50    → subtle dividers
bg-background/80    → frosted vibrancy surfaces (with backdrop-blur)
```

### CSS Variables Setup

Both frameworks share the same CSS custom properties:

```css
:root {
  --primary: oklch(0.704 0.135 217);
  --primary-foreground: oklch(1 0 0);
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --card: oklch(1 0 0);
  --card-foreground: oklch(0.145 0 0);
  --muted: oklch(0.97 0 0);
  --muted-foreground: oklch(0.45 0 0);
  --border: oklch(0.9 0 0);
  --input: oklch(0.9 0 0);
  --ring: oklch(0.704 0.135 217);
  --destructive: oklch(0.577 0.245 27);
  --destructive-foreground: oklch(1 0 0);
  --success: oklch(0.62 0.17 155);
  --success-foreground: oklch(1 0 0);
  --warning: oklch(0.75 0.16 75);
  --warning-foreground: oklch(0.2 0 0);
  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.145 0 0);
  --radius: 0.5rem;
}

.dark {
  --primary: oklch(0.765 0.134 212);
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --card: oklch(0.205 0 0);
  --muted: oklch(0.269 0 0);
  --border: oklch(1 0 0 / 10%);
  --destructive: oklch(0.65 0.21 25);
  --destructive-foreground: oklch(1 0 0);
  --success: oklch(0.7 0.17 155);
  --success-foreground: oklch(1 0 0);
  --warning: oklch(0.8 0.14 75);
  --warning-foreground: oklch(0.2 0 0);
  --popover: oklch(0.205 0 0);
  --popover-foreground: oklch(0.985 0 0);
}
```

---

## Typography

| Role | Classes | Min Size |
|---|---|---|
| Page display title | `text-4xl font-extrabold tracking-tight` | — |
| Page / section headline | `text-2xl font-bold tracking-tight` | — |
| Card / subsection title | `text-xl font-semibold` | — |
| Body text | `text-sm` | **14px — never go below** |
| Body strong | `text-sm font-semibold` | — |
| Column headers / sub-labels | `text-xs font-bold uppercase tracking-widest text-muted-foreground` | 12px |
| Financial numbers | `font-mono tabular-nums` | **ALWAYS for amounts** |
| Status badges | `text-[11px] font-semibold` | 10px floor |

**Premium typography rules:**
- Use negative `tracking-tighter` on large display text for presence
- Limit paragraph width to ~65 characters (`max-w-[65ch]`)
- Use `text-wrap: balance` on headlines to prevent orphaned words
- Introduce Medium (500) and SemiBold (600) weights — don't rely only on 400/700

---

## Spacing

- Card internal padding: `p-6` (desktop) · `p-4` (mobile)
- Page padding: `p-8`
- Between components: `gap-4` – `gap-8`
- Between page sections: `gap-8` – `gap-12`
- **Never** arbitrary values like `p-[13px]` or `mt-[7px]`

## Radius

| Element | Class |
|---|---|
| Inputs, buttons | `rounded-md` (6px) |
| Dropdowns, menus | `rounded-md` |
| Cards, page sections | `rounded-2xl` (16px) |
| Modals | `rounded-xl` (12px) |
| Floating sheets | `rounded-3xl` (24px) |
| Badges, avatars, pills | `rounded-full` |

## Shadows (Apple-style depth)

Apple uses layered shadows — a soft diffuse shadow for ambient depth plus a tight contact shadow for grounding. Never use generic black shadows.

| Element | Classes |
|---|---|
| Card resting | `shadow-sm shadow-black/[0.04] dark:shadow-black/[0.2]` |
| Card hover / elevated | `shadow-md shadow-black/[0.06] dark:shadow-black/[0.25]` |
| Dropdown / popover | `shadow-lg shadow-black/[0.08] dark:shadow-black/[0.3]` |
| Modal / dialog | `shadow-xl shadow-black/[0.1] dark:shadow-black/[0.4]` |
| Floating sheet | `shadow-2xl shadow-black/[0.12] dark:shadow-black/[0.5]` |

**Rules:**
- Tint shadows using `shadow-primary/5` for branded surfaces (e.g. primary CTA cards)
- Use `ring-1 ring-border/50` as a secondary depth cue alongside shadows in dark mode — shadows alone disappear on dark backgrounds
- Never apply `shadow-2xl` to inline content — reserve heavy shadows for overlays and floating surfaces

## Vibrancy / Frosted Surfaces

Apple's signature translucent material for navigation bars, sidebars, and sheets:

```
/* Navigation bar / sticky header */
backdrop-blur-xl bg-background/80 border-b border-border/50

/* Floating panel / command palette */
backdrop-blur-2xl bg-card/70 ring-1 ring-border/50 shadow-2xl shadow-black/[0.12]

/* Sidebar */
backdrop-blur-xl bg-muted/60 border-e border-border/50
```

**Performance:** Only apply `backdrop-blur` to `fixed` or `sticky` elements. Never blur scrolling containers — causes GPU repaint on every frame.

---

## Angular 19 — Zard Components

### Buttons

```html
<!-- Primary — only ONE per view -->
<z-button zType="default">Save Entry</z-button>

<!-- Secondary -->
<z-button zType="outline">Cancel</z-button>

<!-- Destructive — irreversible actions only -->
<z-button zType="destructive">Delete</z-button>

<!-- Ghost — toolbar / tertiary -->
<z-button zType="ghost" zSize="icon" aria-label="Add row">
  <z-icon zType="plus" />
</z-button>

<!-- Loading state -->
<z-button zType="default" [zLoading]="saving()">Save</z-button>
```

### Inputs

```html
<input z-input placeholder="Account name" class="w-full" />

<!-- Financial amount — always right-align + mono -->
<input z-input type="number" class="w-full font-mono tabular-nums text-end" />

<!-- Error state -->
<input z-input class="w-full border-destructive ring-destructive/20" />
```

### Status Badges

```html
<!-- Draft — muted semantic tokens -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold
             bg-muted text-muted-foreground ring-1 ring-inset ring-border">
  <span class="size-1.5 rounded-full bg-muted-foreground/40"></span>
  Draft
</span>

<!-- Posted — primary semantic tokens -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold
             bg-primary/10 text-primary ring-1 ring-inset ring-primary/20">
  <span class="size-1.5 rounded-full bg-primary"></span>
  Posted
</span>

<!-- Success — e.g. Balanced, Approved -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold
             bg-success/10 text-success ring-1 ring-inset ring-success/20">
  <span class="size-1.5 rounded-full bg-success"></span>
  Balanced
</span>

<!-- Destructive — e.g. Overdue, Rejected -->
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold
             bg-destructive/10 text-destructive ring-1 ring-inset ring-destructive/20">
  <span class="size-1.5 rounded-full bg-destructive"></span>
  Overdue
</span>
```

### Cards & Tables

```html
<z-card zTitle="Journal Entries" zDescription="Current period">
  <!-- body -->
</z-card>

<table z-table zVariant="default" zSize="default" class="w-full">
  <thead z-table-header>
    <tr>
      <th class="text-xs font-bold uppercase tracking-widest text-muted-foreground">Account</th>
      <th class="text-xs font-bold uppercase tracking-widest text-muted-foreground text-end">Debit</th>
    </tr>
  </thead>
  <tbody>
    @for (line of lines(); track line.id) {
      <tr>
        <td>{{ line.account }}</td>
        <td class="font-mono tabular-nums text-end">{{ line.debit | number:'1.2-2' }}</td>
      </tr>
    }
  </tbody>
</table>
```

### Loading / Skeletons

```html
@if (loading()) {
  <div class="space-y-3">
    <z-skeleton class="h-9 w-full rounded-md" />
    <z-skeleton class="h-9 w-3/4 rounded-md" />
    <z-skeleton class="h-9 w-1/2 rounded-md" />
  </div>
} @else {
  <!-- actual content -->
}
```

Skeletons must mirror the **exact** layout of final content.

### Toasts

```typescript
import { toast } from 'ngx-sonner';

toast.success('Entry posted');
toast.error('Failed to save — check your connection');
toast.warning('Entry is unbalanced');
```

Use toasts for **transient feedback only**. Use `z-alert` (inline) for form validation errors.

### Component Boilerplate

```typescript
@Component({
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, ZardButtonComponent, ZardIconComponent],
})
export class MyComponent {
  private myService = inject(MyService);
  loading = signal(true);
  data = signal<MyType[]>([]);
}
```

Rules: always `OnPush`, always `standalone: true`, use `signal()` / `computed()`, use `inject()`.

---

## Next.js — shadcn/ui Components

### Buttons

```tsx
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

<Button>Save Entry</Button>                           {/* Primary — ONE per view */}
<Button variant="outline">Cancel</Button>              {/* Secondary */}
<Button variant="destructive">Delete</Button>          {/* Destructive */}
<Button variant="ghost" size="icon" aria-label="Add">  {/* Ghost icon */}
  <Plus className="size-4" />
</Button>
```

### Inputs & Cards

```tsx
import { Input } from "@/components/ui/input"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"

<Input placeholder="Account name" />
<Input type="number" className="font-mono tabular-nums text-right" />

<Card className="rounded-2xl">
  <CardHeader>
    <CardTitle>Journal Entries</CardTitle>
    <CardDescription>Current period</CardDescription>
  </CardHeader>
  <CardContent>{/* body */}</CardContent>
</Card>
```

### Loading / Skeletons

```tsx
import { Skeleton } from "@/components/ui/skeleton"

{isLoading ? (
  <div className="space-y-3">
    <Skeleton className="h-9 w-full rounded-md" />
    <Skeleton className="h-9 w-3/4 rounded-md" />
  </div>
) : (
  <ActualContent />
)}
```

### Toasts

```tsx
import { toast } from "sonner"
toast.success("Entry posted")
toast.error("Failed to save")
```

### RSC Safety (Next.js specific)

- Default to Server Components. Only use `'use client'` when state/interactivity is needed.
- Interactive components (animations, hover effects) MUST be isolated leaf `'use client'` components.
- Global state (providers, context) MUST be wrapped in a `'use client'` component.

---

## Page Layout Patterns

### Page Header

```html
<div class="flex items-center justify-between">
  <div class="flex items-center gap-3">
    <button class="p-2 rounded-full hover:bg-muted" aria-label="Go back">
      <z-icon zType="arrow-left" class="size-5" />
    </button>
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Journal Entry</h1>
      <p class="text-sm text-muted-foreground">Draft · Created today</p>
    </div>
  </div>
  <div class="flex items-center gap-2">
    <!-- status badge + action buttons -->
  </div>
</div>
```

### KPI Stat Card

```html
<div class="bg-card rounded-2xl border border-border shadow-sm p-6">
  <p class="text-xs font-bold uppercase tracking-widest text-muted-foreground">Total Revenue</p>
  <p class="text-2xl font-bold tracking-tight font-mono tabular-nums mt-2">$12,450.00</p>
  <p class="text-xs text-success mt-1">+8.2% from last month</p>
</div>
```

### Empty State

```html
<div class="px-4 py-16 text-center">
  <div class="mx-auto size-12 rounded-full bg-muted flex items-center justify-center mb-4">
    <SearchIcon class="size-5 text-muted-foreground" />
  </div>
  <p class="text-sm font-medium text-foreground">No results found</p>
  <p class="text-xs text-muted-foreground mt-1">Try a different search term</p>
</div>
```

---

## Interactive States (Mandatory)

Every component MUST implement these states — not just the happy path:

1. **Loading** — Skeleton loaders matching the final layout. Never use a generic spinner alone.
2. **Empty** — Composed empty state explaining how to populate data. Not just blank space.
3. **Error** — Clear inline error messages. Use `z-alert` / `Alert`, not toast, for actionable errors.
4. **Hover** — Background shift, subtle scale, or translate. Never a bare color swap.
5. **Active/Pressed** — `active:scale-[0.98]` or `-translate-y-[1px]` to simulate physical push.
6. **Focus** — Visible `ring-2 ring-ring ring-offset-2` on ALL interactive elements.
7. **Disabled** — `opacity-50 pointer-events-none` with `text-muted-foreground`.

---

## Animation & Motion

### Performance Rules (non-negotiable)

- **Only animate** `transform` and `opacity` — never `top`, `left`, `width`, `height`
- **Max duration:** 200ms for UI transitions, 300ms for page transitions
- **Spring physics** over linear easing: `type: "spring", stiffness: 100, damping: 20`
- **Respect** `prefers-reduced-motion` — disable non-essential animations
- Apply `backdrop-blur` only to fixed/sticky elements — never to scrolling containers
- Apply grain/noise overlays to `fixed inset-0 pointer-events-none` elements only

### Framer Motion (Next.js)

```tsx
'use client';
import { motion } from "framer-motion"

// Fade-up entry
<motion.div
  initial={{ opacity: 0, y: 16 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ type: "spring", stiffness: 100, damping: 20 }}
>
  {children}
</motion.div>

// Staggered list
<motion.ul variants={{ show: { transition: { staggerChildren: 0.05 } } }}>
  {items.map(item => (
    <motion.li
      key={item.id}
      variants={{ hidden: { opacity: 0, y: 8 }, show: { opacity: 1, y: 0 } }}
    />
  ))}
</motion.ul>

// Layout transitions
<motion.div layout layoutId="shared-element" />
```

**Critical:** For magnetic hover or continuous animations, use `useMotionValue` + `useTransform` — never `useState` in the render cycle. Wrap perpetual animations in `React.memo` isolated client components.

### CSS Transitions (Angular)

```css
/* Standard transition — use cubic-bezier, not linear */
.element {
  transition: all 200ms cubic-bezier(0.16, 1, 0.3, 1);
}

/* Staggered entry via CSS */
.item {
  animation: fadeUp 200ms cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: calc(var(--index) * 50ms);
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## Premium Design Rules (Anti-Generic)

These rules combat the common "AI-generated" look:

### Layout

- **Ban centered hero sections** for marketing pages — use split-screen, asymmetric, or left-aligned layouts
- **Ban 3-equal-card rows** — use bento grids, zig-zag, asymmetric grids, or masonry
- **Contain layouts:** `max-w-7xl mx-auto` — content must not stretch edge-to-edge
- **Use CSS Grid** over complex flexbox math: `grid grid-cols-1 md:grid-cols-3 gap-6`
- **Use `min-h-[100dvh]`** not `h-screen` — prevents iOS Safari viewport jumping
- **Mobile override:** Any asymmetric layout above `md:` MUST collapse to `w-full px-4` below 768px

### Color

- Max 1 accent color. Keep saturation under 80%.
- Never use pure `#000000` — use off-black (`zinc-950`, `slate-950`)
- Tint shadows to match background hue — not generic black
- Stick to ONE gray family (warm or cool) throughout the project
- Ban the "AI purple/blue gradient" aesthetic

### Surfaces & Depth

- **Cards** exist only when elevation communicates hierarchy. For data-dense UIs, prefer `border-t`, `divide-y`, or negative space.
- **Glassmorphism done right:** `backdrop-blur` + 1px inner border (`border-white/10`) + inner shadow (`shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]`)
- **Tinted shadows:** Use colored shadows (`shadow-primary/10`) instead of generic black
- **Double-bezel pattern:** Outer shell (`bg-muted/50 rounded-[2rem] p-1.5 ring-1 ring-border`) containing inner core with its own background and smaller radius

### Content (Anti-Slop)

- Never use "John Doe", "Acme Corp", "99.99%" — use realistic, messy data
- Ban AI copywriting cliches: "Elevate", "Seamless", "Unleash", "Next-Gen", "Delve"
- Use sentence case for headers, not Title Case On Everything
- No emojis in production UI — use proper icons (Lucide, Phosphor, Radix)

---

## Accessibility Checklist

Every component must pass:
- [ ] Visible focus ring: `ring-2 ring-ring ring-offset-2`
- [ ] Fully keyboard operable — no mouse-only actions
- [ ] Icon-only buttons have `aria-label`
- [ ] Status conveyed by color + text/icon (never color alone)
- [ ] Touch targets >= 44x44px on mobile
- [ ] `prefers-reduced-motion` respected
- [ ] Dialogs trap focus; `Esc` closes
- [ ] Tables use semantic `<thead>`, `<th scope>`, `<tbody>`
- [ ] Skip-to-content link present on pages
- [ ] Alt text on all meaningful images

---

## RTL Support

Set `dir="rtl"` on `<html>`. Use logical CSS classes:

| Avoid | Use |
|---|---|
| `ml-4` | `ms-4` |
| `pl-3` | `ps-3` |
| `text-left` | `text-start` |
| `float-right` | `float-end` |

Font stack: `'SF Pro Display', 'Inter', 'Cairo', ui-sans-serif, system-ui` — SF Pro loads on Apple devices natively, Inter is the web fallback (matching metrics), Cairo auto-selects for Arabic script.

---

## Code Review — Flag These Immediately

| Issue | Fix |
|---|---|
| Raw hex or `bg-cyan-500` | Use `bg-primary` |
| Body text below 14px | Use `text-sm` minimum |
| Numbers without `font-mono tabular-nums` | Add both classes |
| Missing focus ring | Add `ring-2 ring-ring ring-offset-2` |
| Two primary buttons on same view | Demote one to `outline` |
| `rounded-lg` on a card | Use `rounded-2xl` |
| Arbitrary spacing `p-[13px]` | Use scale: `p-3` or `p-4` |
| Toast used for form error | Use inline alert |
| Animation > 200ms | Reduce for snappiness |
| `text-zinc-500` for disabled | Use `text-muted-foreground` |
| `h-screen` for full height | Use `min-h-[100dvh]` |
| Generic centered 3-card layout | Use bento/asymmetric grid |
| No loading/empty/error states | Implement all three |
| `bg-white` / `bg-black` | Use `bg-background` / `bg-card` |
| Linear easing on animations | Use spring or cubic-bezier |
| `window.addEventListener('scroll')` | Use IntersectionObserver |
| `text-emerald-*` / `text-green-*` | Use `text-success` |
| `text-amber-*` / `text-yellow-*` | Use `text-warning` |
| `shadow-lg` without tint | Use `shadow-lg shadow-black/[0.08]` or `shadow-primary/5` |
| `backdrop-blur` on scrolling container | Move blur to `fixed`/`sticky` element only |

---

## Scripts

```bash
# Validate design system compliance
./skills/design-system/scripts/validate.sh src/

# Generate a new component (angular or nextjs)
./skills/design-system/scripts/generate_component.sh my-component angular
./skills/design-system/scripts/generate_component.sh my-component nextjs

# Generate design tokens
python3 skills/design-system/scripts/generate_tokens.py --format tailwind --output tailwind.config.ts
```
