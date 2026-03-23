#!/bin/bash

# Design System Validator
# Checks Angular component template files for compliance with Ovovex Design System

set -e

TARGET="${1:-.}"

echo "🎨 Ovovex Design System Validator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Scanning: $TARGET"
echo ""

ISSUES=0

# 1. Check for raw hex colors
echo "📍 Scanning for raw hex colors..."
if grep -r --include="*.html" --include="*.component.ts" "style=.*#[0-9A-Fa-f]\{6\}\|class=.*bg-\[#\|text-\[#" "$TARGET" 2>/dev/null; then
    echo "  ⚠️  Found raw hex colors — use semantic tokens instead (bg-primary, text-primary, etc.)"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ No raw hex colors detected"
fi

# 2. Check for raw color names
echo ""
echo "📍 Scanning for raw Tailwind colors (bg-cyan-500, bg-red-400)..."
if grep -r --include="*.html" --include="*.component.ts" "bg-cyan-\|bg-red-\|text-cyan-\|text-red-\|bg-zinc-100\|border-zinc-200" "$TARGET" 2>/dev/null | grep -v "primary\|destructive\|muted"; then
    echo "  ⚠️  Found raw color names — use semantic tokens instead"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ No raw color names detected"
fi

# 3. Check for body text below 14px
echo ""
echo "📍 Scanning for text smaller than 14px..."
if grep -r --include="*.html" --include="*.component.ts" "text-\[1[0-3]px\]\|text-xs\|text-\[10px\]\|text-\[11px\]\|text-\[12px\]" "$TARGET" 2>/dev/null | grep -v "font-bold.*uppercase\|caption\|badge"; then
    echo "  ⚠️  Found text below 14px — body text minimum is text-sm (14px)"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ All body text >= 14px"
fi

# 4. Check for arbitrary spacing
echo ""
echo "📍 Scanning for arbitrary spacing (p-[7px], m-[13px], etc)..."
if grep -r --include="*.html" --include="*.component.ts" "p-\[\|m-\[\|gap-\[\|px-\[\|py-\[\|space-" "$TARGET" 2>/dev/null | grep -v "gap-\["; then
    echo "  ⚠️  Found arbitrary spacing — use the spacing scale (p-2, p-4, p-6, gap-4, etc.)"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ Using spacing scale"
fi

# 5. Check for multiple primary buttons
echo ""
echo "📍 Scanning for multiple 'default' type buttons per view..."
# This is a heuristic — count z-button zType="default" per component
if grep -r --include="*.html" "z-button.*zType=\"default\"" "$TARGET" 2>/dev/null | awk '{print FILENAME}' | sort | uniq -c | awk '$1 > 1' | wc -l | grep -q "^0$"; then
    echo "  ✅ Single primary button per view"
else
    echo "  ⚠️  Detected multiple primary (default) buttons — each view should have only one primary action"
    ISSUES=$((ISSUES + 1))
fi

# 6. Check for font-mono tabular-nums on financial fields
echo ""
echo "📍 Scanning for financial fields without font-mono tabular-nums..."
if grep -r --include="*.html" --include="*.component.ts" 'type="number"\|currency\|debit\|credit\|amount' "$TARGET" 2>/dev/null | grep -v "font-mono\|tabular-nums" | head -5; then
    echo "  ⚠️  Found number/currency fields without font-mono tabular-nums"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ Financial fields properly styled"
fi

# 7. Check for rounded-lg on cards
echo ""
echo "📍 Scanning for rounded-lg on cards (should be rounded-2xl)..."
if grep -r --include="*.html" "z-card.*rounded-lg\|rounded-lg.*z-card" "$TARGET" 2>/dev/null; then
    echo "  ⚠️  Found rounded-lg on card — use rounded-2xl for cards"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ Cards use correct radius"
fi

# 8. Check for missing focus rings
echo ""
echo "📍 Scanning for inputs/buttons without focus management..."
MISSING_FOCUS=$(grep -r --include="*.html" --include="*.component.ts" "<button\|<input" "$TARGET" 2>/dev/null | grep -v "ring-\|focus:" | wc -l)
if [ "$MISSING_FOCUS" -gt 0 ]; then
    echo "  ⚠️  Found $MISSING_FOCUS interactive elements that may be missing focus rings"
    ISSUES=$((ISSUES + 1))
else
    echo "  ✅ Focus management present"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ISSUES -eq 0 ]; then
    echo "✅ Design system compliance: PASS"
    exit 0
else
    echo "⚠️  Found $ISSUES issue(s) — review above"
    exit 1
fi
