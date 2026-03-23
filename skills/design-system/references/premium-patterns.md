# Premium Design Patterns

Advanced patterns for building interfaces that look like $150k agency work, not generic AI output.
Load this reference when building marketing pages, dashboards, or any UI that needs to feel premium.

---

## The Creative Arsenal

### Navigation

| Pattern | Description |
|---|---|
| Floating pill nav | Detached from top edge (`mt-6 mx-auto w-max rounded-full`), glass effect |
| Mac dock magnification | Icons scale fluidly on hover using spring physics |
| Dynamic island | Pill-shaped component that morphs to show status/alerts |
| Mega menu reveal | Full-screen dropdown with stagger-faded content |
| Contextual radial menu | Circular menu expanding at click coordinates |

### Layout Archetypes

| Pattern | When to use |
|---|---|
| Bento grid | Asymmetric tiles (Apple Control Center style). `grid-template-columns: 2fr 1fr 1fr` |
| Z-axis cascade | Cards stacked with slight overlaps and rotation for depth |
| Editorial split | Massive typography left, interactive content right (`grid-cols-2`) |
| Split-screen scroll | Two halves sliding in opposite directions on scroll |
| Curtain reveal | Hero parting in the middle on scroll |
| Sticky scroll stack | Cards that stick to top and physically stack over each other |

**Mobile override (all layouts):** Collapse to `w-full px-4 py-8` single-column below `768px`.

### Card Patterns

| Pattern | Implementation |
|---|---|
| Double-bezel (Doppelrand) | Outer shell (`bg-muted/50 p-1.5 rounded-[2rem] ring-1 ring-border`) + inner core (`bg-card rounded-[calc(2rem-0.375rem)]`) |
| Parallax tilt | 3D tilt tracking mouse via `useMotionValue` + `useTransform` |
| Spotlight border | Border illuminates dynamically under cursor position |
| Glassmorphism panel | `backdrop-blur-xl` + `border-white/10` + `shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]` |
| Morphing modal | Button seamlessly expands into its own full-screen dialog |

### Scroll Animations

| Pattern | Implementation |
|---|---|
| Horizontal scroll hijack | Vertical scroll → smooth horizontal pan via `useTransform(scrollY, ...)` |
| Scroll progress path | SVG line draws itself tied to scroll position |
| Zoom parallax | Background image zooms tied to scroll progress |
| Fade-up entry | `translate-y-16 blur-sm opacity-0` → `translate-y-0 blur-0 opacity-100` over 600ms+ |

**Critical:** Use `IntersectionObserver` or Framer Motion `whileInView` for scroll triggers. Never use `window.addEventListener('scroll')`.

### Typography Effects

| Pattern | Implementation |
|---|---|
| Kinetic marquee | Endless text bands reversing on scroll direction |
| Text mask reveal | Large type as transparent window to video background |
| Text scramble | Matrix-style character decode on load/hover |
| Gradient stroke | Outlined text with animated gradient along stroke |

### Micro-Interactions

| Pattern | Implementation |
|---|---|
| Particle explosion | CTA shatters into particles on success |
| Directional hover | Fill enters from exact mouse-entry side |
| Ripple click | Visual wave from click coordinates |
| Skeleton shimmer | Light reflection shifting across placeholder boxes |
| Mesh gradient | Organic lava-lamp color blobs as background |

---

## The Bento Dashboard Paradigm

Modern SaaS dashboards and feature sections. "Vercel-core meets Dribbble-clean."

### Surface Rules

- Background: `bg-muted/30` or `#f9fafb`
- Cards: `bg-card` with `border-border/50` and diffused shadow: `shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]`
- Radius: `rounded-[2rem]` on major containers
- Internal padding: `p-8` or `p-10`
- Labels/descriptions placed **outside and below** cards for gallery-style presentation

### 5 Card Archetypes

1. **Intelligent List** — Vertical stack with infinite auto-sort loop. Items swap via `layoutId` simulating AI prioritization.
2. **Command Input** — Search/AI bar with multi-step typewriter effect cycling through prompts + blinking cursor + shimmer loading state.
3. **Live Status** — Scheduling interface with breathing status dots. Pop-up badge with overshoot spring, stays 3s, vanishes.
4. **Wide Data Stream** — Horizontal infinite carousel of metrics. Seamless loop via `x: ["0%", "-100%"]`.
5. **Contextual UI** — Document view with staggered text highlight + float-in action toolbar.

### Animation Engine

- Spring physics on everything: `type: "spring", stiffness: 100, damping: 20`
- Heavy use of `layout` and `layoutId` for smooth transitions
- Every card has an infinite "alive" state (pulse, typewriter, float, carousel)
- Wrap dynamic lists in `<AnimatePresence>`
- **Performance:** Memoize perpetual motion components with `React.memo`. Isolate in microscopic `'use client'` leaf components.

---

## Vibe Archetypes (pick one per project)

### 1. Ethereal Glass (SaaS / AI / Tech)
- Deep OLED black (`#050505`)
- Radial mesh gradients (subtle glowing orbs)
- Cards with `backdrop-blur-2xl` + `border-white/10`
- Wide geometric grotesk typography

### 2. Editorial Luxury (Lifestyle / Agency)
- Warm cream (`#FDFBF7`), muted sage, deep espresso
- Variable serif for massive headings
- CSS noise/film-grain overlay (`opacity-[0.03]`)

### 3. Soft Structuralism (Consumer / Portfolio)
- Silver-grey or white backgrounds
- Massive bold grotesk typography
- Ultra-diffused ambient shadows

---

## Performance Guardrails

| Rule | Why |
|---|---|
| Only animate `transform` + `opacity` | Other properties trigger layout recalculation |
| `will-change: transform` sparingly | Overuse wastes GPU memory |
| `backdrop-blur` on fixed/sticky only | Causes continuous repaints on scroll containers |
| Noise/grain on `fixed pointer-events-none` | Prevents repaint on scroll |
| No `z-[9999]` | Use structured z-index scale: nav → modals → overlays |
| `min-h-[100dvh]` not `h-screen` | iOS Safari viewport bug |
| `useEffect` cleanup for animations | Prevents memory leaks |
| Memoize perpetual motion | Prevents re-render cascade |

---

## Pre-Flight Checklist

Before shipping any premium UI:

- [ ] No banned patterns (generic 3-card rows, centered heroes, linear easing)
- [ ] A vibe archetype was consciously chosen and applied consistently
- [ ] All major containers use double-bezel or intentional surface treatment
- [ ] Section padding is minimum `py-16` — the layout breathes
- [ ] All transitions use spring/cubic-bezier — no `linear` or `ease-in-out`
- [ ] Scroll entry animations present — no element appears statically
- [ ] Layout collapses gracefully below 768px
- [ ] All animations use only `transform` and `opacity`
- [ ] `backdrop-blur` only on fixed/sticky elements
- [ ] Loading, empty, and error states all present
- [ ] Content uses realistic data, not "John Doe" or "99.99%"
