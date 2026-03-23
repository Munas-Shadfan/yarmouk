---
name: i18n-localization
description: >
  Use this skill for ANY task touching internationalization, localization, translation, RTL, multi-region,
  multi-currency, hreflang, locale routing, or language switching in the Avoyzen storefront or admin.
  Triggers on: "localize", "translate", "Arabic", "RTL", "hreflang", "en-jo", "ar-sa", "currency formatting",
  "locale", "i18n", "multi-region", "language switcher", or any mention of a country+language pair.
metadata:
  version: 1.0.0
---

# i18n Localization Skill — Avoyzen Storefront

This skill encodes the full localization architecture for Avoyzen: a multi-tenant Next.js 16 + App Router storefront
targeting MENA + global markets with locale combos like `en-jo`, `ar-sa`, `ar-ae`, `en-ksa`, etc.

---

## Core Architecture

### URL Structure (Shopify Hydrogen pattern)

```
/{storeSlug}/                    → default locale (en-US)
/{storeSlug}/en-jo/              → English + Jordan
/{storeSlug}/ar-sa/              → Arabic + Saudi Arabia
/{storeSlug}/ar-ae/              → Arabic + UAE
/{storeSlug}/en-sa/              → English + Saudi Arabia
/{storeSlug}/ar-jo/              → Arabic + Jordan
```

**URL segment format:** `{language}-{country}` in lowercase — e.g. `ar-sa` for `ar-SA` (BCP-47).

The locale segment is **optional** — if missing, the middleware detects and redirects using:
1. Cookie (`NEXT_LOCALE`)
2. `Accept-Language` header
3. `req.geo.country` (Vercel/CF edge geolocation) → mapped to default locale for that country
4. Fallback: `en-us`

### Supported Locales (MENA-first)

| Locale | Language | Country | Currency | Dir |
|--------|----------|---------|----------|-----|
| `ar-sa` | Arabic | Saudi Arabia | SAR | rtl |
| `ar-ae` | Arabic | UAE | AED | rtl |
| `ar-jo` | Arabic | Jordan | JOD | rtl |
| `ar-kw` | Arabic | Kuwait | KWD | rtl |
| `ar-qa` | Arabic | Qatar | QAR | rtl |
| `ar-bh` | Arabic | Bahrain | BHD | rtl |
| `en-sa` | English | Saudi Arabia | SAR | ltr |
| `en-ae` | English | UAE | AED | ltr |
| `en-jo` | English | Jordan | JOD | ltr |
| `en-us` | English | United States | USD | ltr |
| `en-gb` | English | United Kingdom | GBP | ltr |

---

## Route Structure

All storefront pages live under `app/[storeSlug]/[locale]/`. The `[locale]` segment is optional via
Next.js catch-all or a dedicated optional segment `($locale)`.

```
app/
  [storeSlug]/
    [locale]/               ← NEW: optional locale segment
      layout.tsx            ← sets <html lang dir>, loads translations server-side
      page.tsx
      products/
        [handle]/page.tsx
      collections/
        [handle]/page.tsx
      checkout/page.tsx
      account/
        page.tsx
        ...
```

---

## Translation Loading (Server Components First)

**Never ship translation strings to the client unless the component is a Client Component.**

```ts
// lib/i18n/getTranslations.ts  (server-only)
import 'server-only'
import { Locale } from './config'

const translationCache = new Map<Locale, Record<string, unknown>>()

export async function getTranslations(locale: Locale) {
  if (translationCache.has(locale)) return translationCache.get(locale)!
  const lang = locale.split('-')[0] // 'ar-sa' → 'ar'
  const mod = await import(`@/lib/translations/${lang}`)
  translationCache.set(locale, mod.default)
  return mod.default
}
```

**Client Components** receive pre-translated strings as props from their Server Component parent.
Only interactive UI strings that change without navigation need client-side translation access.

---

## Locale Config (single source of truth)

```ts
// lib/i18n/config.ts
export const LOCALES = [
  'ar-sa', 'ar-ae', 'ar-jo', 'ar-kw', 'ar-qa', 'ar-bh',
  'en-sa', 'en-ae', 'en-jo', 'en-us', 'en-gb',
] as const

export type Locale = typeof LOCALES[number]

export const DEFAULT_LOCALE: Locale = 'en-us'

export const LOCALE_META: Record<Locale, {
  lang: string       // BCP-47 language tag for <html lang>
  dir: 'ltr' | 'rtl'
  currency: string   // ISO 4217
  country: string    // ISO 3166-1 alpha-2
  label: string      // display name in that language
}> = {
  'ar-sa': { lang: 'ar-SA', dir: 'rtl', currency: 'SAR', country: 'SA', label: 'العربية (السعودية)' },
  'ar-ae': { lang: 'ar-AE', dir: 'rtl', currency: 'AED', country: 'AE', label: 'العربية (الإمارات)' },
  'ar-jo': { lang: 'ar-JO', dir: 'rtl', currency: 'JOD', country: 'JO', label: 'العربية (الأردن)' },
  'en-sa': { lang: 'en-SA', dir: 'ltr', currency: 'SAR', country: 'SA', label: 'English (Saudi Arabia)' },
  'en-ae': { lang: 'en-AE', dir: 'ltr', currency: 'AED', country: 'AE', label: 'English (UAE)' },
  'en-jo': { lang: 'en-JO', dir: 'ltr', currency: 'JOD', country: 'JO', label: 'English (Jordan)' },
  'en-us': { lang: 'en-US', dir: 'ltr', currency: 'USD', country: 'US', label: 'English (US)' },
  'en-gb': { lang: 'en-GB', dir: 'ltr', currency: 'GBP', country: 'GB', label: 'English (UK)' },
  'ar-kw': { lang: 'ar-KW', dir: 'rtl', currency: 'KWD', country: 'KW', label: 'العربية (الكويت)' },
  'ar-qa': { lang: 'ar-QA', dir: 'rtl', currency: 'QAR', country: 'QA', label: 'العربية (قطر)' },
  'ar-bh': { lang: 'ar-BH', dir: 'rtl', currency: 'BHD', country: 'BH', label: 'العربية (البحرين)' },
}
```

---

## Middleware Integration

The existing middleware already handles custom domain → storeSlug resolution. Locale detection
is layered on top **after** slug resolution, before the URL rewrite:

```ts
// PSEUDO — extend existing middleware.ts
const slug = await resolveSlug(request)    // existing
const locale = detectLocale(request)        // NEW
const pathnameWithoutSlug = ...             // existing
const newUrl = `/${slug}/${locale}${pathnameWithoutSlug}`
return NextResponse.rewrite(newUrl)
```

**Do not break the existing domain → slug logic.** Locale sits between slug and path.

---

## hreflang Generation

Use Next.js `generateMetadata` — it auto-renders `<link rel="alternate" hreflang>` tags:

```ts
// app/[storeSlug]/[locale]/products/[handle]/page.tsx
export async function generateMetadata({ params }) {
  const { storeSlug, locale, handle } = params
  const baseUrl = getStoreBaseUrl(storeSlug)
  return {
    alternates: {
      languages: Object.fromEntries(
        LOCALES.map(l => [
          LOCALE_META[l].lang,
          `${baseUrl}/${l}/products/${handle}`
        ])
      ),
    }
  }
}
```

**Mandatory hreflang rules:**
- Every locale variant must be self-referential (points to itself)
- Every variant must link to all others (reciprocal)
- Always include `x-default` pointing to the default locale or a language picker
- Use ISO 639-1 + ISO 3166-1 alpha-2 format: `en-JO` not `en-UK` (correct is `en-GB`)

---

## Currency Formatting

Use the browser/Node `Intl.NumberFormat` — zero extra libraries:

```ts
export function formatPrice(amount: number, locale: Locale): string {
  const { lang, currency } = LOCALE_META[locale]
  return new Intl.NumberFormat(lang, {
    style: 'currency',
    currency,
    minimumFractionDigits: currency === 'JOD' || currency === 'KWD' || currency === 'BHD' ? 3 : 2,
  }).format(amount)
}
```

**Currency rounding by region:**
- JOD, KWD, BHD → 3 decimal places (fils)
- SAR, AED, QAR → 2 decimal places, round to nearest 0.05 or whole number per merchant config
- USD, GBP, EUR → 2 decimal places

Pass `Accept-Currency` header (already implemented) when fetching prices from the API.

---

## RTL Support

### What changes for RTL

- `<html dir="rtl">` — set from LOCALE_META in server layout
- Tailwind CSS 4 logical properties: use `ms-*` / `me-*` instead of `ml-*` / `mr-*`
- Flex row direction flips automatically with `dir="rtl"` for most UI
- Icons/chevrons pointing left/right need to be mirrored: `class="rtl:rotate-180"`
- Text alignment: `text-start` (not `text-left`) so it flips correctly
- Number formatting: `Intl.NumberFormat('ar-SA')` produces Arabic-Indic numerals — use `en-SA` locale
  if you want Arabic locale + Western numerals: `new Intl.NumberFormat('en-SA', { currency: 'SAR' })`

### Tailwind CSS 4 RTL utilities

```html
<!-- Margin -->
<div class="ms-4">     <!-- margin-inline-start: auto-flips for RTL -->

<!-- Padding -->
<div class="ps-6 pe-4"> <!-- padding-inline-start/end -->

<!-- Text align -->
<p class="text-start">  <!-- left in LTR, right in RTL -->

<!-- Arrow that flips -->
<ChevronRight class="rtl:rotate-180" />

<!-- Absolute position that flips -->
<div class="inset-s-0">   <!-- left:0 in LTR, right:0 in RTL -->
```

---

## Static Generation

To maintain maximum performance with multiple locales:

```ts
// app/[storeSlug]/[locale]/layout.tsx
export async function generateStaticParams() {
  const stores = await getAllStoreSlugs()
  return stores.flatMap(storeSlug =>
    LOCALES.map(locale => ({ storeSlug, locale }))
  )
}
```

**Performance tradeoff strategy:**
- Default locale (`en-us`) → fully static (ISR 60s)
- MENA locales → ISR with `revalidate: 300` (5 min) to reduce build time
- Admin i18n pages → always dynamic (`export const dynamic = 'force-dynamic'`)

---

## Translation File Structure

```ts
// lib/translations/ar.ts  (mirror of en.ts with Arabic strings)
const ar = {
  nav: {
    home: 'الرئيسية',
    products: 'المنتجات',
    collections: 'المجموعات',
    search: 'البحث',
    cart: 'السلة',
    account: 'الحساب',
  },
  product: {
    addToCart: 'أضف إلى السلة',
    outOfStock: 'نفد المخزون',
    lowStock: 'متبقي {{count}} فقط',
    // ...
  },
  // dir is used by the layout to set html[dir]
  dir: 'rtl',
} as const

export default ar
export type ArTranslations = typeof ar
```

**Template variables** use `{{variable}}` (already established in `en.ts`). Replace with:
```ts
function t(key: string, vars?: Record<string, string | number>) {
  let str = getString(key)
  if (vars) Object.entries(vars).forEach(([k, v]) => str = str.replace(`{{${k}}}`, String(v)))
  return str
}
```

---

## Performance Rules (zero regression)

1. **No i18n library in client bundle** — use server-only translation loading
2. **No dynamic imports for translations in hot path** — cache translation modules at module level
3. **Static params for known locales** — use `generateStaticParams` so pages are pre-rendered at build
4. **CDN-cacheable locale URLs** — each locale URL is a distinct cacheable path (no query params)
5. **`setRequestLocale` pattern** — if using `next-intl`, call in every layout + page to stay static
6. **Translation strings are never part of the JS bundle for Server Components**
7. **Intl.NumberFormat** — create once per locale and reuse via a module-level cache, not per-render

---

## Checklist Before Shipping Any i18n Change

- [ ] `<html lang>` and `<html dir>` set correctly from server
- [ ] hreflang tags present on all public pages
- [ ] Price displayed in locale currency with correct fraction digits
- [ ] RTL layout tested (flip `dir` in browser DevTools)
- [ ] `text-start` / `ms-*` / `me-*` used instead of directional equivalents
- [ ] Locale cookie set on user preference change
- [ ] `generateStaticParams` includes all locales
- [ ] `Accept-Currency` header sent to API
- [ ] Arabic translation strings reviewed (not machine-translated for launch)
- [ ] `x-default` hreflang present

---

## Related Files in Avoyzen

| File | Purpose |
|------|---------|
| `frontend/src/middleware.ts` | Add locale detection layer here |
| `frontend/src/lib/translations/en.ts` | English translation template |
| `frontend/src/lib/translations/ar.ts` | Arabic translations (create) |
| `frontend/src/store/language.ts` | Replace with URL-driven locale |
| `frontend/src/store/currency.ts` | Initialize from locale on server |
| `frontend/src/app/admin/stores/[storeId]/i18n/` | Admin locale/currency management UI |
| `frontend/src/lib/i18n/config.ts` | Create: LOCALES, LOCALE_META, DEFAULT_LOCALE |
| `frontend/src/lib/i18n/getTranslations.ts` | Create: server-only translation loader |
