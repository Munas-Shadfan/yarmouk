---
name: image-optimizer
description: Optimize images in a directory — converts PNG/JPG/WebP to WebP, resizes to a max width, and reduces file size. Uses cwebp + ffmpeg. Use when the user says "optimize images", "compress images", "images are too heavy", or "reduce image size". argument-hint: "[directory]  (default: public/images)"
allowed-tools: Bash(bash *), Bash(ls *), Bash(du *), Bash(which *), Bash(find *), Bash(rm *)
---

# Image Optimizer

Converts all PNG/JPG/WebP images in a target directory to optimized WebP using `cwebp` + `ffmpeg` (for resizing). Reduces file sizes by 80–95% with no visible quality loss.

## Requirements

Check tools are available:
```bash
which cwebp ffmpeg
```

- `cwebp` — install via `brew install webp`
- `ffmpeg` — install via `brew install ffmpeg`

---

## Step 1 — Detect target directory

Default: `public/images/` relative to project root. Accept user override.

---

## Step 2 — Scan & report current sizes

```bash
du -sh <dir>/*
```

Show the user what's large before doing anything.

---

## Step 3 — Run the optimizer script

```bash
bash <skill_dir>/scripts/optimize.sh <target_dir> [max_width] [quality]
```

**Defaults:**
| Param | Default | Notes |
|---|---|---|
| `target_dir` | `public/images` | Relative to cwd |
| `max_width` | `1920` | Hero images; use `1600` for content images |
| `quality` | `82` | 80–85 is visually lossless for WebP |

The script:
1. Iterates all `*.png`, `*.jpg`, `*.jpeg`, `*.webp` in the directory
2. Uses `ffmpeg` to resize to `max_width` (only downscales, never upscales)
3. Uses `cwebp` to encode at the given quality
4. Overwrites the original file in-place

---

## Step 4 — Report savings

After the script, print a before/after size comparison.

---

## Error Handling

| Error | Action |
|---|---|
| `cwebp` not found | Stop, print `brew install webp` |
| `ffmpeg` not found | Stop, print `brew install ffmpeg` |
| No images found | Print warning, exit cleanly |
| File is already tiny (<50KB) | Skip it |

---

## Examples

```
/image-optimizer                        → optimize public/images/ at 1920px q82
/image-optimizer src/assets 1600 80     → custom dir, 1600px wide, quality 80
/image-optimizer public/images 1920 85  → hero images, higher quality
```
