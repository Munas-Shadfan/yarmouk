#!/usr/bin/env python3

"""
Design System Token Generator
Converts design tokens from the DESIGN_SYSTEM spec into framework-specific config files.

Usage:
    python3 generate_tokens.py --format tailwind --output tailwind.config.ts
    python3 generate_tokens.py --format css --output tokens.css
    python3 generate_tokens.py --format json --output design-tokens.json
"""

import json
import sys
from typing import Dict, Any
from pathlib import Path

# OKLCH Color System (from DESIGN_SYSTEM.md)
COLORS = {
    "primary": {"light": "oklch(0.704 0.135 217)", "dark": "oklch(0.765 0.134 212)"},  # Cyan
    "destructive": {"light": "oklch(0.577 0.245 27)", "dark": "oklch(0.704 0.191 22)"},  # Red
    "success": {"light": "oklch(0.644 0.189 142)", "dark": "oklch(0.732 0.156 142)"},  # Emerald
    "warning": {"light": "oklch(0.659 0.191 70)", "dark": "oklch(0.742 0.161 70)"},  # Amber
    "muted": {"light": "oklch(0.97 0 0)", "dark": "oklch(0.205 0 0)"},  # Zinc
    "background": {"light": "oklch(1 0 0)", "dark": "oklch(0.145 0 0)"},  # White / Zinc-950
    "foreground": {"light": "oklch(0.145 0 0)", "dark": "oklch(0.985 0 0)"},  # Zinc-950 / Zinc-50
    "card": {"light": "oklch(1 0 0)", "dark": "oklch(0.205 0 0)"},  # White / Zinc-900
    "border": {"light": "oklch(0.85 0 0)", "dark": "oklch(0.25 0 0)"},  # Zinc-200 / Zinc-800
}

# Spacing system (8px base)
SPACING = {
    "0.5": "2px",
    "1": "4px",
    "1.5": "6px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "12": "48px",
    "16": "64px",
    "24": "96px",
}

# Typography
TYPOGRAPHY = {
    "display": {"size": "36px", "weight": 800, "lineHeight": 1.1, "letterSpacing": "-0.025em"},
    "headline": {"size": "24px", "weight": 700, "lineHeight": 1.2, "letterSpacing": "-0.02em"},
    "title": {"size": "20px", "weight": 600, "lineHeight": 1.3, "letterSpacing": "-0.015em"},
    "body": {"size": "14px", "weight": 400, "lineHeight": 1.6, "letterSpacing": "0"},
    "body-strong": {"size": "14px", "weight": 600, "lineHeight": 1.6, "letterSpacing": "0"},
    "callout": {"size": "13px", "weight": 500, "lineHeight": 1.5, "letterSpacing": "0"},
    "subheadline": {"size": "12px", "weight": 700, "lineHeight": 1.4, "letterSpacing": "0.05em"},
    "footnote": {"size": "11px", "weight": 500, "lineHeight": 1.4, "letterSpacing": "0"},
    "caption": {"size": "10px", "weight": 700, "lineHeight": 1.3, "letterSpacing": "0.08em"},
}

# Border radius
RADIUS = {
    "sm": "4px",
    "md": "6px",
    "lg": "8px",
    "xl": "12px",
    "2xl": "16px",
    "3xl": "24px",
    "full": "9999px",
}

# Shadows
SHADOWS = {
    "sm": "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    "lg": "0 10px 15px -3px rgb(0 0 0 / 0.1)",
    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
}


def generate_tailwind_config() -> str:
    """Generate Tailwind CSS config (TypeScript)"""
    return '''// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  theme: {
    extend: {
      colors: {
        // Semantic tokens
        primary: {
          DEFAULT: "oklch(0.704 0.135 217)",
          foreground: "white",
        },
        destructive: {
          DEFAULT: "oklch(0.577 0.245 27)",
          foreground: "white",
        },
        success: {
          DEFAULT: "oklch(0.644 0.189 142)",
          foreground: "white",
        },
        warning: {
          DEFAULT: "oklch(0.659 0.191 70)",
          foreground: "white",
        },
        muted: {
          DEFAULT: "oklch(0.97 0 0)",
          foreground: "oklch(0.62 0 0)", // text-muted-foreground
        },
        background: "oklch(1 0 0)",
        foreground: "oklch(0.145 0 0)",
        card: "oklch(1 0 0)",
        "card-foreground": "oklch(0.145 0 0)",
        popover: "oklch(1 0 0)",
        "popover-foreground": "oklch(0.145 0 0)",
        border: "oklch(0.85 0 0)",
        input: "oklch(0.85 0 0)",
        ring: "oklch(0.704 0.135 217)", // primary
      },
      fontFamily: {
        sans: ["Inter", "Cairo", "system-ui", "sans-serif"],
        mono: ["Fira Code", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "6px",
        lg: "8px",
        xl: "12px",
      },
      boxShadow: {
        sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        lg: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
      },
    },
  },
  darkMode: ["class", "(prefers-color-scheme: dark)"],
  plugins: [],
};

export default config;
'''


def generate_css_tokens() -> str:
    """Generate CSS custom properties"""
    light_css = ":root {\n"
    dark_css = "@media (prefers-color-scheme: dark) {\n  :root {\n"

    for token, values in COLORS.items():
        light_css += f"  --color-{token}: {values['light']};\n"
        dark_css += f"    --color-{token}: {values['dark']};\n"

    for space, value in SPACING.items():
        light_css += f"  --spacing-{space}: {value};\n"

    for size, props in TYPOGRAPHY.items():
        light_css += f"  --text-{size}: {props['size']};\n"

    for rad, value in RADIUS.items():
        light_css += f"  --radius-{rad}: {value};\n"

    light_css += "}\n\n"
    dark_css += "  }\n}\n"

    return light_css + dark_css


def generate_json_tokens() -> Dict[str, Any]:
    """Generate JSON token export"""
    return {
        "version": "1.0.0",
        "colors": COLORS,
        "spacing": SPACING,
        "typography": TYPOGRAPHY,
        "radius": RADIUS,
        "shadows": SHADOWS,
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 generate_tokens.py --format [tailwind|css|json] --output [file]")
        sys.exit(1)

    format_type = sys.argv[2]
    output_file = sys.argv[4] if len(sys.argv) > 4 else None

    if format_type == "tailwind":
        content = generate_tailwind_config()
    elif format_type == "css":
        content = generate_css_tokens()
    elif format_type == "json":
        content = json.dumps(generate_json_tokens(), indent=2)
    else:
        print(f"Unknown format: {format_type}")
        sys.exit(1)

    if output_file:
        Path(output_file).write_text(content)
        print(f"✅ Generated: {output_file}")
    else:
        print(content)


if __name__ == "__main__":
    main()
