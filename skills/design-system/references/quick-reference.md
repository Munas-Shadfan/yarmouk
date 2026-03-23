# Quick Reference · Ovovex Design System

## When to Use This Skill

**Trigger phrases:**
- "How do I build a [button/form/table/dialog]?"
- "What's the correct styling for..."
- "Does this component follow the design system?"
- "Style this component"
- "Dark mode not working"
- "How do I implement keyboard navigation?"

**Frameworks supported:** Angular 19, Next.js 15+

---

## 30-Second Token Rules

| Need | Token | Example |
|------|-------|---------|
| Primary button | `bg-primary text-primary-foreground` | `<z-button zType="default">` |
| Secondary button | `bg-secondary text-secondary-foreground` | `<z-button zType="outline">` |
| Error/destructive | `bg-destructive text-destructive-foreground` | `<z-button zType="destructive">` |
| Page background | `bg-background text-foreground` | `<div class="bg-background">` |
| Card background | `bg-card text-card-foreground` | `<z-card>` |
| Muted/secondary | `bg-muted text-muted-foreground` | Disabled states, secondary UI |
| Input border | `border-input` | `<input z-input>` |
| Focus ring | `ring-2 ring-ring ring-offset-2` | On all interactive elements |
| Popover | `bg-popover text-popover-foreground` | Dropdowns, tooltips |

---

## Component Quick Pick

**Need a...**

| What | Angular | Next.js |
|------|---------|---------|
| Button | `<z-button zType="default">` | `<Button>` |
| Input field | `<input z-input>` | `<Input />` |
| Dropdown | `<z-select>` | `<Select />` |
| Search/combo | `<z-combobox>` | `<Command />` + `<Popover />` |
| Modal dialog | `ZardDialogService.open()` | `<Dialog />` |
| Data table | `<table z-table>` | `<Table />` |
| Card box | `<z-card>` | `<Card />` |
| Alert/error | `<z-alert>` | `<Alert />` |
| Badge label | `<z-badge>` | `<Badge />` |
| Tabs | `<z-tab-group>` | `<Tabs />` |
| Loading | `<z-skeleton>` | `<Skeleton />` |
| Notification | `toast('msg')` | `toast('msg')` |

---

## Spacing Quick Pick

| Use | Tailwind Class | Value |
|-----|---|---|
| Inline gap (buttons) | `gap-2` | 8px |
| Component padding | `p-4` | 16px |
| Card padding (desktop) | `p-6` | 24px |
| Between sections | `gap-8` | 32px |
| Page padding | `p-8` | 32px |
| Large spacing | `gap-12` | 48px |
| **Never** | `p-[7px]`, arbitrary | ❌ |

---

## Financial UI Patterns

### Journal Entry Table

```html
<table z-table class="w-full">
  <thead>
    <tr>
      <th>Account</th>
      <th class="text-end">Debit</th>
      <th class="text-end">Credit</th>
    </tr>
  </thead>
  <tbody>
    @for (line of lines(); track line.id) {
      <tr>
        <td>{{ line.account }}</td>
        <td class="font-mono tabular-nums text-end">{{ line.debit | currency }}</td>
        <td class="font-mono tabular-nums text-end">{{ line.credit | currency }}</td>
      </tr>
    }
  </tbody>
</table>
```

**Rules:**
- ✅ Numbers always `font-mono tabular-nums text-end`
- ✅ Account column uses account autocomplete
- ✅ Tab navigation: auto-advance cells → rows → auto-add new row
- ✅ Total row in `<tfoot>` with bold + `bg-zinc-50/50`

### Status Badge

```html
<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full 
             text-[11px] font-semibold bg-cyan-50 text-cyan-700 ring-1 ring-inset ring-cyan-500/20">
  <span class="size-1.5 rounded-full bg-cyan-500"></span>
  Posted
</span>
```

**Variants:**
- Draft: `bg-zinc-100 text-zinc-600` + gray dot
- Posted: `bg-cyan-50 text-cyan-700` + cyan dot + shield icon
- Canceled: `bg-red-50 text-red-700` + red dot

### Form with Errors

```html
<!-- Show ALL errors at top, never hide them -->
@if (errors().length > 0) {
  <z-alert zType="destructive">
    <p class="font-medium">Please fix the following:</p>
    <ul class="mt-2 list-disc list-inside">
      @for (error of errors(); track error) {
        <li class="text-sm">{{ error }}</li>
      }
    </ul>
  </z-alert>
}

<!-- Inline error indicators on fields -->
<div>
  <label class="text-sm font-medium">Amount</label>
  <input z-input type="number" class="w-full" 
    [class.border-destructive]="hasError('amount')"
    [class.ring-destructive/20]="hasError('amount')" />
  @if (hasError('amount')) {
    <p class="text-xs text-destructive mt-1">{{ getError('amount') }}</p>
  }
</div>
```

---

## Keyboard Shortcuts (All Apps)

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Navigate between inputs, cells |
| `Enter` | Confirm selection, submit form |
| `Esc` | Close dialog/dropdown |
| `↑` / `↓` | Navigate list options or table rows |
| `⌘S` / `Ctrl+S` | Save (as Draft) |
| `⌘Enter` / `Ctrl+Enter` | Post/Submit |
| `Delete` | Remove row (with confirmation) |
| `⌘K` / `Ctrl+K` | Global search |

---

## Dark Mode Checklist

- [ ] Test with system theme toggle
- [ ] Text colors update automatically (semantic tokens)
- [ ] Card backgrounds lighten (zinc-900 in dark)
- [ ] Primary color lightens by one stop (500→400)
- [ ] No hardcoded colors (`bg-[#fff]`, `style="color: #000"`)

**To test in Chrome DevTools:**
1. Open DevTools → **Rendering** → **Emulate CSS media feature prefers-color-scheme**
2. Select **dark**
3. Refresh

---

## Code Review Checklist

When you see a component, quickly check:

- [ ] Uses semantic tokens (no `bg-cyan-500`)
- [ ] No arbitrary spacing (`p-[7px]`)
- [ ] Body text ≥ 14px minimum
- [ ] Financial fields have `font-mono tabular-nums text-end`
- [ ] Interactive elements have focus ring
- [ ] ONE primary button per view (at most)
- [ ] Cards use `rounded-2xl`, inputs use `rounded-md`
- [ ] Skeletons mirror the final layout
- [ ] Dark mode supported
- [ ] Keyboard accessible (Tab, Arrow keys, Enter, Esc)

---

## Common Mistakes (Fix Immediately)

| ❌ Wrong | ✅ Right | Why |
|---------|---------|-----|
| `bg-cyan-500` | `bg-primary` | Automatic dark mode support |
| `style="color: #06B6D4"` | `class="text-primary"` | Semantic, maintainable |
| `text-[11px]` | `text-xs` (if necessary) | Respects scale |
| `p-[13px]` | `p-3` or `p-4` | Uses spacing system |
| `rounded-lg` on card | `rounded-2xl` | Correct hierarchy |
| No focus ring | `ring-2 ring-ring ring-offset-2` | Accessibility |
| 2 `default` buttons | Demote one to `outline` | Clear primary action |
| Raw number in table | `font-mono tabular-nums` | Alignment |
| Toast for errors | `<z-alert>` inline | Error clarity |
| Long animation | `duration-200` max | Snappiness |

---

## File Locations

| What | Path |
|------|------|
| Full spec | `DESIGN_SYSTEM (1).md` (root) |
| This skill | `skills/design-system/SKILL.md` |
| Component map | `skills/design-system/references/component-map.md` |
| Validation script | `skills/design-system/scripts/validate.sh` |
| Token generator | `skills/design-system/scripts/generate_tokens.py` |
| Component boilerplate | `skills/design-system/scripts/generate_component.sh` |

---

## Scripts

### Validate a component
```bash
./skills/design-system/scripts/validate.sh src/
```

### Generate a new component
```bash
./skills/design-system/scripts/generate_component.sh my-component angular
```

### Generate tokens
```bash
python3 skills/design-system/scripts/generate_tokens.py --format tailwind --output tailwind.config.ts
```

---

## When in Doubt

1. **Check the component reference** — Is this a standard Zard component?
2. **Look at similar code** — How did we style the last [button/form/table]?
3. **Use semantic tokens** — Always use `bg-primary` not `bg-cyan-500`
4. **Test dark mode** — Every change must work in both light and dark
5. **Run the validator** — `./scripts/validate.sh` catches most issues

---

## Quick Links

- **Angular 19 Docs:** https://angular.io
- **Next.js 15 Docs:** https://nextjs.org
- **Tailwind CSS 4:** https://tailwindcss.com
- **WCAG 2.1 (Accessibility):** https://www.w3.org/WAI/WCAG21/quickref
- **CVA (Class Variance Authority):** https://cva.style

---

**Last updated:** 2026-03-12  
**Design System Version:** 1.0  
**Framework Support:** Angular 19, Next.js 15+
