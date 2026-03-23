# Troubleshooting · Design System Issues

## Dark Mode Not Working

**Problem:** Colors don't change when switching to dark mode

**Checklist:**
1. ✅ Using semantic tokens? Check for raw colors:
   ```bash
   grep -r "bg-cyan-500\|bg-red-400\|#06B6D4" src/
   ```
   Fix: Replace with `bg-primary`, `bg-destructive`, etc.

2. ✅ Is `<html>` element getting `class="dark"` or `dir="dark"`?
   ```tsx
   // Next.js
   <html className={isDark ? 'dark' : ''}>
   
   // Angular
   <html [class.dark]="isDark()">
   ```

3. ✅ Check Tailwind config has dark mode enabled:
   ```typescript
   export default {
     darkMode: ["class", "(prefers-color-scheme: dark)"],
     // ...
   };
   ```

4. ✅ Test with browser DevTools:
   - Open DevTools → **Rendering** tab
   - Check "Emulate CSS media feature prefers-color-scheme: dark"
   - Refresh page

5. ✅ CSS custom properties defined?
   ```css
   @media (prefers-color-scheme: dark) {
     :root {
       --primary: oklch(0.765 0.134 212); /* lighter cyan */
       --background: oklch(0.145 0 0); /* dark bg */
     }
   }
   ```

---

## Focus Ring Not Showing

**Problem:** Buttons/inputs don't show focus ring when tabbing

**Checklist:**
1. ✅ Is the element interactive?
   - Buttons, links, inputs need `ring-2 ring-ring ring-offset-2`
   
2. ✅ Check for override CSS:
   ```css
   /* Bad — removes focus */
   input:focus {
     outline: none;
     box-shadow: none; /* This removes the ring! */
   }
   ```
   Fix: Remove that CSS or use Tailwind's focus classes

3. ✅ Is `ring` token defined in Tailwind?
   ```typescript
   // tailwind.config.ts
   theme: {
     extend: {
       colors: {
         ring: 'oklch(0.704 0.135 217)', // primary color
       }
     }
   }
   ```

4. ✅ Test focus:
   ```bash
   # Press Tab in the browser
   # You should see a cyan ring around the focused element
   ```

---

## Numbers Not Aligning

**Problem:** Amounts in tables don't align in columns

**Checklist:**
1. ✅ Using `font-mono tabular-nums`? BOTH are required:
   ```html
   <!-- Bad — only mono, no tabular -->
   <td class="font-mono">{{ amount }}</td>
   
   <!-- Good -->
   <td class="font-mono tabular-nums">{{ amount }}</td>
   ```

2. ✅ Is text right-aligned?
   ```html
   <!-- Bad — left-aligned numbers -->
   <td class="font-mono tabular-nums">{{ amount }}</td>
   
   <!-- Good — right-aligned -->
   <td class="font-mono tabular-nums text-end">{{ amount }}</td>
   ```

3. ✅ Are all cells in the column the same?
   - Header, data rows, and total should all be `font-mono tabular-nums text-end`
   - Verify font is consistent (Inter or Cairo, not mixed)

4. ✅ Check browser rendering:
   - Open DevTools → **Elements** → inspect a cell
   - Verify `font-family` is monospace (Fira Code, Courier, etc.)
   - Verify no `-webkit-text-size-adjust` that breaks it

---

## Styles Not Applying

**Problem:** Tailwind classes not showing in the rendered output

**Checklist:**
1. ✅ Is Tailwind CSS loaded?
   ```bash
   # Check browser DevTools → Styles tab
   # You should see Tailwind CSS rules
   ```

2. ✅ Are all Tailwind classes in `purge` list? (Content configuration)
   ```typescript
   // tailwind.config.ts
   export default {
     content: [
       './src/**/*.{ts,tsx,html}',
       './app/**/*.{ts,tsx}',
     ],
   };
   ```

3. ✅ Is the element using a semantic class?
   ```tsx
   // Bad — 'primary' is not a default Tailwind class
   <div className="bg-primary">content</div>
   
   // Good — 'primary' is defined in Tailwind config
   // Check: theme.colors.primary in tailwind.config.ts
   ```

4. ✅ Build/dev server running?
   ```bash
   npm run dev  # Next.js
   ng serve    # Angular
   ```
   Restart if styles still not applying.

---

## Button Has Two Types

**Problem:** View has two `zType="default"` buttons (primary)

**Problem:** Users confused about which button to click

**Fix:** Demote ONE to secondary:
```tsx
// Bad
<z-button zType="default">Save</z-button>
<z-button zType="default">Cancel</z-button>

// Good
<z-button zType="default">Save</z-button>
<z-button zType="outline">Cancel</z-button>
```

**Rule:** Only ONE primary action per view. Everything else is `outline`, `ghost`, or `secondary`.

---

## Text Too Small

**Problem:** Body text is hard to read (below 14px)

**Checklist:**
1. ✅ Minimum body text is `text-sm` (14px)
   ```tsx
   // Bad
   <p class="text-xs">This is important</p>
   
   // Good
   <p class="text-sm">This is important</p>
   ```

2. ✅ For captions/labels only:
   - Subheadings: `text-xs` (12px) OK if `font-bold uppercase`
   - Badges: `text-[11px]` OK for status labels
   - Footnotes: `text-[10px]` only as last resort

3. ✅ Mobile/tablet breakpoints?
   ```tsx
   <p class="text-sm sm:text-base">Responsive text</p>
   ```

---

## Keyboard Navigation Broken

**Problem:** Tab key doesn't navigate, or Enter doesn't work

**Checklist:**
1. ✅ Is the element focusable?
   ```html
   <!-- Bad — div is not focusable by default -->
   <div onclick="doSomething()">Click me</div>
   
   <!-- Good — button is focusable -->
   <button onclick="doSomething()">Click me</button>
   ```

2. ✅ Is `tabindex` correct?
   ```html
   <!-- Bad — negative tabindex removes from tab order -->
   <button tabindex="-1">Hidden</button>
   
   <!-- Good — tabindex="0" (or omitted) means normal tab order -->
   <button tabindex="0">Normal</button>
   ```

3. ✅ Is focus being managed?
   ```typescript
   // Angular
   @ViewChild('input') input!: ElementRef;
   
   ngAfterViewInit() {
     this.input.nativeElement.focus();
   }
   ```

4. ✅ Test with keyboard ONLY:
   - Unplug mouse or disable trackpad
   - Use Tab, Shift+Tab, Arrow keys, Enter, Esc
   - Every action must work

---

## Colors Look Wrong in Dark Mode

**Problem:** Primary cyan is too dark/light in dark mode

**Root cause:** OKLCH tokens not adjusted for dark mode

**Fix:**
```css
:root {
  /* Light mode — Cyan 500 */
  --primary: oklch(0.704 0.135 217);
}

@media (prefers-color-scheme: dark) {
  :root {
    /* Dark mode — Cyan 400 (lighter!) */
    --primary: oklch(0.765 0.134 212);
  }
}
```

**Remember:** In dark mode, you lighten the color by 1 step to maintain visual weight.

---

## Component Looks Different in Next.js vs Angular

**Problem:** Same component rendered differently

**Checklist:**
1. ✅ Are both using identical Tailwind classes?
   ```html
   <!-- Angular -->
   <div class="bg-card rounded-2xl border shadow-sm p-6">
   
   <!-- Next.js (identical) -->
   <div className="bg-card rounded-2xl border shadow-sm p-6">
   ```

2. ✅ Are tokens defined identically?
   - Both should read from `tailwind.config.ts` or CSS custom properties
   - Both should have dark mode support

3. ✅ Are fonts the same?
   - Check `font-sans` in Tailwind config (Inter, Cairo, system-ui)
   - Both frameworks should have same font stack

4. ✅ Browser differences?
   - Clear browser cache (`Cmd+Shift+R` on Mac)
   - Test in same browser (Chrome, Firefox, Safari)

---

## Spacing Looks Off

**Problem:** Gaps are too small/large, padding inconsistent

**Checklist:**
1. ✅ Using spacing scale?
   ```tsx
   // Bad — arbitrary
   <div className="mb-[7px] p-[13px]">
   
   // Good — uses scale
   <div className="mb-2 p-3">
   ```

2. ✅ Hierarchy is correct?
   - Component internal: `p-4` (16px)
   - Between components: `gap-4` to `gap-8`
   - Between page sections: `gap-8` to `gap-12`

3. ✅ Is parent spacing interfering?
   ```tsx
   // Bad — child spacing overridden by parent
   <div className="space-y-4">  {/* adds margin-bottom to ALL children */}
     <div className="mb-8">This margin is ignored!</div>
   </div>
   
   // Good — use gap in flex/grid instead
   <div className="flex flex-col gap-8">
     <div>Content</div>
   </div>
   ```

---

## Animation Too Fast/Slow

**Problem:** Transitions feel janky or sluggish

**Rule:** All animations should complete in **200ms or less**

```tsx
// Bad — feels slow
<div className="transition-all duration-500">

// Good — snappy
<div className="transition-all duration-200">
```

**Transitions to support:**
- Hover states: 150ms
- Modals opening: 200ms
- Dropdowns: 100ms (instant)
- Focus rings: 0ms (instant)

---

## Toast Messages Not Appearing

**Problem:** `toast()` called but no notification shows

**Checklist:**
1. ✅ Is the Toaster component rendered at app root?
   ```typescript
   // Angular
   import { ZardToasterComponent } from '@zard/toaster';
   
   @Component({
     imports: [ZardToasterComponent],
   })
   
   // Next.js (sonner)
   import { Toaster } from 'sonner';
   
   export default function RootLayout() {
     return (
       <html>
         <body>
           <Toaster />
         </body>
       </html>
     );
   }
   ```

2. ✅ Are you using the correct import?
   ```typescript
   // Angular (ngx-sonner)
   import { toast } from 'ngx-sonner';
   toast.success('Success!');
   
   // Next.js (sonner)
   import { toast } from 'sonner';
   toast.success('Success!');
   ```

3. ✅ Check browser console for errors

---

## Modal/Dialog Not Closing

**Problem:** `Esc` key doesn't close dialog, or Click-outside doesn't work

**Checklist:**
1. ✅ Is the dialog component set up correctly?
   ```typescript
   // Angular
   ZardDialogService.open({
     title: 'Confirm',
     showClose: true, // X button
     closeOnBackdropClick: true, // Click-outside
   });
   ```

2. ✅ Is focus being trapped?
   - Dialog should trap focus inside
   - When you press Tab repeatedly, focus cycles within the dialog
   - `Esc` should close and return focus to the trigger

3. ✅ Check for `event.stopPropagation()` blocking Esc

---

## Performance Issues

**Problem:** Component is slow, renders lag

**Checklist:**
1. ✅ Change detection strategy (Angular)
   ```typescript
   @Component({
     changeDetection: ChangeDetectionStrategy.OnPush, // Much faster
   })
   ```

2. ✅ Using signals (Angular)
   ```typescript
   data = signal([...]); // Better than Observable
   ```

3. ✅ Memoizing computations (React)
   ```tsx
   const memoizedValue = useMemo(() => expensiveComputation(), []);
   ```

4. ✅ Remove `*ngFor` tracking issues (Angular)
   ```html
   <!-- Bad — no trackBy -->
   @for (item of items) {
   
   <!-- Good — trackBy function -->
   @for (item of items; track item.id) {
   ```

5. ✅ Check bundle size
   ```bash
   # Next.js
   npm run build
   
   # Angular
   ng build --stats-json
   ```

---

## Still Stuck?

1. **Check the full spec:** `DESIGN_SYSTEM (1).md` in workspace root
2. **Run the validator:** `./skills/design-system/scripts/validate.sh src/`
3. **Review similar code:** How was this solved elsewhere in the codebase?
4. **Test in isolation:** Create a minimal example to reproduce the issue

---

**Last updated:** 2026-03-12
