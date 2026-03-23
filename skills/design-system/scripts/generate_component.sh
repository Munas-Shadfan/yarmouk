#!/bin/bash

# Design System Boilerplate Generator
# Creates a new Angular component with design system compliance

set -e

if [ -z "$1" ]; then
    echo "Usage: ./generate_component.sh <component-name> [angular|nextjs]"
    echo "Example: ./generate_component.sh user-profile angular"
    exit 1
fi

COMPONENT_NAME="$1"
FRAMEWORK="${2:-angular}"
KEBAB_NAME=$(echo "$COMPONENT_NAME" | tr '[:upper:]' '[:lower:]')
PASCAL_NAME=$(echo "$KEBAB_NAME" | sed 's/-\([a-z]\)/\U\1/g' | sed 's/^[a-z]/\U&/')

echo "🎨 Generating $FRAMEWORK component: $COMPONENT_NAME"
echo ""

if [ "$FRAMEWORK" = "angular" ]; then
    # Angular template
    cat > "${KEBAB_NAME}.component.ts" << EOF
import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { signal, computed } from '@angular/core';

// Zard components
import { ZardButtonComponent } from '@/shared/components/z-button';
import { ZardIconComponent } from '@/shared/components/z-icon';
import { ZardSkeletonComponent } from '@/shared/components/z-skeleton';

@Component({
  selector: 'app-$KEBAB_NAME',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    ZardButtonComponent,
    ZardIconComponent,
    ZardSkeletonComponent,
  ],
  template: \`
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold tracking-tight">$PASCAL_NAME</h1>
          <p class="text-sm text-muted-foreground mt-0.5">Description here</p>
        </div>
        <z-button zType="default">Action</z-button>
      </div>

      <!-- Loading state -->
      @if (loading()) {
        <div class="space-y-3">
          <z-skeleton class="h-9 w-full rounded-md" />
          <z-skeleton class="h-9 w-3/4 rounded-md" />
        </div>
      } @else {
        <!-- Content here -->
      }
    </div>
  \`,
  styles: [],
})
export class ${PASCAL_NAME}Component implements OnInit {
  loading = signal(true);

  ngOnInit() {
    // Load data
    this.loadData();
  }

  loadData() {
    // API call here
    this.loading.set(false);
  }
}
EOF

    cat > "${KEBAB_NAME}.component.html" << EOF
<!-- Template (optional) -->
<div class="space-y-6">
  <h1 class="text-2xl font-bold tracking-tight">$PASCAL_NAME</h1>
</div>
EOF

    echo "✅ Created Angular component:"
    echo "   - ${KEBAB_NAME}.component.ts"
    echo "   - ${KEBAB_NAME}.component.html"

elif [ "$FRAMEWORK" = "nextjs" ]; then
    # Next.js component
    cat > "${PASCAL_NAME}.tsx" << EOF
'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';

export function ${PASCAL_NAME}() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load data
    loadData();
  }, []);

  const loadData = async () => {
    try {
      // API call here
      setLoading(false);
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-9 w-full rounded-md" />
        <Skeleton className="h-9 w-3/4 rounded-md" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">$PASCAL_NAME</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Description here</p>
        </div>
        <Button>Action</Button>
      </div>
      {/* Content here */}
    </div>
  );
}
EOF

    echo "✅ Created Next.js component:"
    echo "   - ${PASCAL_NAME}.tsx"

fi

cat << 'EOF'

📋 Design System Checklist:
  ☐ Use semantic tokens (bg-primary, text-muted-foreground, etc.)
  ☐ Body text ≥ 14px (use text-sm minimum)
  ☐ Financial fields: font-mono tabular-nums text-end
  ☐ Spacing from scale: p-4, gap-6, etc. (never arbitrary)
  ☐ Focus rings: ring-2 ring-ring ring-offset-2
  ☐ One primary button per view (zType="default")
  ☐ Cards use rounded-2xl, inputs use rounded-md
  ☐ Dark mode support (test with prefers-color-scheme)
  ☐ Keyboard navigation (Tab, Arrow keys, Enter, Esc)
  ☐ Loading states with skeleton screens

EOF
