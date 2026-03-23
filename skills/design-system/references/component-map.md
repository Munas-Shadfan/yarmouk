# Component Map — Angular ↔ Next.js

Maps every Zard component to its shadcn/ui equivalent.
Both sides use the same Tailwind CSS 4 token layer.

---

## Primitives

| Zard (Angular) | shadcn/ui (Next.js) | Notes |
|---|---|---|
| `z-button` | `Button` | Same variants: `default`, `outline`, `ghost`, `destructive`, `secondary`, `link` |
| `z-input` | `Input` | Add `font-mono tabular-nums text-right` for financial fields |
| `z-select` | `Select` | Use `SelectTrigger`, `SelectContent`, `SelectItem` |
| `z-combobox` | `Command` + `Popover` | shadcn command palette is equivalent |
| `z-alert` | `Alert` | Use `AlertTitle`, `AlertDescription`; `variant="destructive"` for errors |
| `z-badge` | `Badge` | Same variant names |
| `z-card` | `Card` | Use `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` |
| `z-dialog` | `Dialog` | Use `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogTitle` |
| `z-dropdown-menu` | `DropdownMenu` | Use `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem` |
| `z-table` | `Table` | Use `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell` |
| `z-tab-group` + `z-tab` | `Tabs` | Use `TabsList`, `TabsTrigger`, `TabsContent` |
| `z-toaster` (ngx-sonner) | `Toaster` (sonner) | `toast.success()`, `toast.error()`, etc. |
| `z-toggle` | `Toggle` | — |
| `z-skeleton` | `Skeleton` | Same `animate-pulse` base |
| `[zPopover]` | `Popover` | Use `PopoverTrigger`, `PopoverContent` |
| `z-sheet` | `Sheet` | `side="right"` or `side="bottom"` |
| `z-accordion` | `Accordion` | — |
| `z-calendar` | `Calendar` | — |
| `z-date-picker` | `Calendar` + `Popover` | shadcn docs have a date picker example |
| `z-checkbox` | `Checkbox` | — |
| `z-radio-group` + `z-radio` | `RadioGroup` + `RadioGroupItem` | — |
| `z-pagination` | `Pagination` | — |
| `z-icon` (lucide-angular) | `lucide-react` | Same icon names: `Plus`, `ArrowLeft`, `Search` |
| `z-divider` | `Separator` | — |
| `z-progress-bar` | `Progress` | — |
| `z-tooltip` | `Tooltip` | Use `TooltipProvider`, `TooltipTrigger`, `TooltipContent` |
| `z-avatar` | `Avatar` | Use `AvatarImage`, `AvatarFallback` |
| `z-switch` | `Switch` | — |
| `z-slider` | `Slider` | — |
| `z-textarea` | `Textarea` | — |

---

## Application-Specific Components

No shadcn equivalent — purpose-built.

| Component | Angular | Next.js |
|---|---|---|
| Account autocomplete | `app-account-autocomplete` | Build with `Command` + fixed-position popover |
| Sidebar | `app-sidebar` | Next.js layout + `Sheet` for mobile |
| Breadcrumbs | Inline `router-link` + back button | `next/link` + `useRouter().back()` |

---

## Status Badge Pattern

Built inline in both frameworks — not a component. Always use this anatomy:

```
inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold
+ colored dot (size-1.5 rounded-full)
+ ring-1 ring-inset
```

| State | Background | Text | Dot | Ring |
|---|---|---|---|---|
| Draft | `bg-zinc-100` | `text-zinc-600` | `bg-zinc-400` | `ring-zinc-500/20` |
| Posted | `bg-cyan-50` | `text-cyan-700` | `bg-cyan-500` | `ring-cyan-500/20` |
| Canceled | `bg-red-50` | `text-red-700` | `bg-red-500` | `ring-red-500/20` |
| Warning/Pending | `bg-amber-50` | `text-amber-700` | `bg-amber-400` | `ring-amber-500/20` |
| Success | `bg-emerald-50` | `text-emerald-700` | `bg-emerald-500` | `ring-emerald-500/20` |

---

## Keyboard Shortcuts

| Action | Key |
|---|---|
| Global search / command menu | `Cmd+K` / `Ctrl+K` |
| Save draft | `Cmd+S` / `Ctrl+S` |
| Post / submit | `Cmd+Enter` / `Ctrl+Enter` |
| Close modal / cancel | `Esc` |
| Navigate table cells | `Tab` / `Shift+Tab` |
| Navigate list rows | Arrow Up / Arrow Down |
| Select option | `Enter` |
| Show shortcuts overlay | `?` |

---

## CSS Token Setup

Both frameworks share identical CSS custom properties (see main SKILL.md for full `:root` block).

---

## RTL Support

Use logical CSS classes — Tailwind handles all `ms-`/`me-`/`ps-`/`pe-` automatically.

| Avoid | Use |
|---|---|
| `ml-4` | `ms-4` |
| `pl-3` | `ps-3` |
| `text-left` | `text-start` |
| `float-right` | `float-end` |

Font stack: `'Inter', 'Cairo', ui-sans-serif` — Cairo auto-selected for Arabic.
