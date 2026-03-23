# Redesign Audit Checklist

Use this when upgrading an existing project. Work with the existing stack — improve what's there, don't rewrite from scratch.

## Process

1. **Scan** — Read the codebase. Identify framework, styling method, current patterns.
2. **Diagnose** — Run through checklist below. List every generic pattern and weak point.
3. **Fix** — Apply targeted upgrades in priority order (below).

---

## Fix Priority (maximum impact, minimum risk)

1. **Font swap** — biggest instant improvement, lowest risk
2. **Color palette cleanup** — remove clashing or oversaturated colors
3. **Hover and active states** — makes the interface feel alive
4. **Layout and spacing** — proper grid, max-width, consistent padding
5. **Replace generic components** — swap cliche patterns for modern alternatives
6. **Add loading, empty, error states** — makes it feel finished
7. **Polish typography scale** — the premium final touch

---

## Typography Audit

- [ ] Browser default fonts or Inter everywhere → Replace with `Geist`, `Outfit`, `Satoshi`, `Cabinet Grotesk`
- [ ] Headlines lack presence → Increase size, tighten letter-spacing, reduce line-height
- [ ] Body text too wide → Limit to ~65 characters (`max-w-[65ch]`)
- [ ] Only Regular/Bold weights → Introduce Medium (500) and SemiBold (600)
- [ ] Numbers in proportional font → `font-mono tabular-nums`
- [ ] Missing tracking adjustments → Negative tracking on large headers, positive on labels
- [ ] Orphaned words → `text-wrap: balance` or `text-wrap: pretty`

## Color & Surface Audit

- [ ] Pure `#000000` background → Off-black (`zinc-950`, `slate-950`)
- [ ] Oversaturated accents → Desaturate below 80%
- [ ] Multiple accent colors → Pick one, remove the rest
- [ ] Mixing warm and cool grays → One family throughout
- [ ] "AI purple/blue gradient" → Neutral bases + singular accent
- [ ] Generic `box-shadow` → Tint shadows to match background hue
- [ ] Zero texture → Subtle noise, grain, or micro-patterns
- [ ] Inconsistent lighting direction → Audit all shadows for single light source
- [ ] Random dark sections in light page → Consistent tone or commit to dark mode
- [ ] Empty flat sections → Add background imagery, patterns, or ambient gradients

## Layout Audit

- [ ] Everything centered and symmetrical → Break with offset margins, mixed aspect ratios
- [ ] Three equal card columns → Bento grid, zig-zag, asymmetric, or masonry
- [ ] `height: 100vh` → `min-height: 100dvh`
- [ ] Complex flexbox math → CSS Grid
- [ ] No max-width container → `max-w-7xl mx-auto`
- [ ] Uniform border-radius → Vary: tighter on inner elements, softer on containers
- [ ] No overlap or depth → Negative margins for layering
- [ ] Symmetrical padding → Adjust optically (bottom often needs more)
- [ ] Buttons not bottom-aligned in card groups → Pin to bottom
- [ ] Inconsistent vertical rhythm → Align shared elements across columns

## Interactivity Audit

- [ ] No hover states → Add background shift, scale, or translate
- [ ] No active/pressed feedback → `scale(0.98)` or `translateY(1px)`
- [ ] Zero-duration transitions → Add 150-200ms with cubic-bezier
- [ ] Missing focus ring → `ring-2 ring-ring ring-offset-2`
- [ ] No loading states → Skeleton loaders matching layout
- [ ] No empty states → Composed "getting started" view
- [ ] No error states → Clear inline messages, not `alert()`
- [ ] Dead `#` links → Link properly or visually disable
- [ ] No active nav indicator → Style current page link
- [ ] Instant scroll jumps → `scroll-behavior: smooth`
- [ ] Animations on `top`/`left`/`width` → Switch to `transform` + `opacity`

## Content Audit

- [ ] "John Doe", "Jane Smith" → Diverse, realistic names
- [ ] Round numbers "99.99%", "$100.00" → Organic data: "47.2%", "$12,847.23"
- [ ] "Acme Corp" → Contextual, believable brand names
- [ ] "Elevate", "Seamless", "Unleash" → Plain, specific language
- [ ] Exclamation marks in success messages → Confident, not loud
- [ ] "Oops!" error messages → Direct: "Connection failed"
- [ ] Lorem Ipsum → Real draft copy
- [ ] Title Case On Everything → Sentence case

## Component Audit

- [ ] Generic card (border + shadow + white bg) → Only use cards when elevation = hierarchy
- [ ] Always one filled + one ghost button → Add text links or tertiary styles
- [ ] Pill-shaped "New"/"Beta" badges → Square badges, flags, or plain text
- [ ] Accordion FAQ → Side-by-side list, searchable help, or progressive disclosure
- [ ] 3-card carousel testimonials → Masonry wall, embedded posts, or single quote
- [ ] Pricing table with 3 towers → Highlight recommended with emphasis, not height
- [ ] Modals for everything → Inline editing, slide-overs, expandable sections
- [ ] Avatar circles exclusively → Try squircles or rounded squares
- [ ] Footer link farm → Simplify to main paths + legal links

## Iconography Audit

- [ ] Default Lucide/Feather everywhere → Use Phosphor, Heroicons, or custom set
- [ ] Rocketship for "Launch" → Less cliche metaphors (bolt, spark, vault)
- [ ] Inconsistent stroke widths → Standardize to one weight
- [ ] Missing favicon → Always include branded favicon
- [ ] Stock "diverse team" photos → Real photos or consistent illustration style

## Code Quality Audit

- [ ] Div soup → Semantic HTML: `<nav>`, `<main>`, `<article>`, `<section>`
- [ ] Inline styles mixed with classes → Move all to styling system
- [ ] Hardcoded pixel widths → Relative units (`%`, `rem`, `max-width`)
- [ ] Missing alt text → Describe image content
- [ ] Arbitrary z-index `9999` → Structured z-index scale
- [ ] Dead commented-out code → Remove before shipping
- [ ] Import hallucinations → Verify every import exists in `package.json`
- [ ] Missing meta tags → `<title>`, `description`, `og:image`
- [ ] No skip-to-content link → Add for keyboard users
- [ ] No cookie consent (if needed) → Add compliant banner
- [ ] No custom 404 → Design branded "not found" page
