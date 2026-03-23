#!/bin/bash
# image-optimizer — convert PNG/JPG/WebP to optimized WebP in-place
# Usage: bash optimize.sh [target_dir] [max_width] [quality]
set -e

TARGET_DIR="${1:-public/images}"
MAX_WIDTH="${2:-1920}"
QUALITY="${3:-82}"

GREEN='\033[0;32m'; BLUE='\033[0;34m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo -e "${BLUE}🖼  Image Optimizer${NC}"
echo "Directory : $TARGET_DIR"
echo "Max width : ${MAX_WIDTH}px"
echo "Quality   : $QUALITY"
echo ""

# ── Guard: tools ──────────────────────────────────────────────────────────────
if ! command -v cwebp &>/dev/null; then
  echo -e "${RED}❌ cwebp not found. Install with: brew install webp${NC}"
  exit 1
fi
if ! command -v ffmpeg &>/dev/null; then
  echo -e "${RED}❌ ffmpeg not found. Install with: brew install ffmpeg${NC}"
  exit 1
fi

# ── Guard: directory ──────────────────────────────────────────────────────────
if [ ! -d "$TARGET_DIR" ]; then
  echo -e "${RED}❌ Directory not found: $TARGET_DIR${NC}"
  exit 1
fi

# ── Process images ────────────────────────────────────────────────────────────
TMP="__img_opt_tmp.png"
TOTAL_BEFORE=0
TOTAL_AFTER=0
COUNT=0
SKIPPED=0

process_image() {
  local file="$1"
  local before_bytes
  before_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")

  # Skip already tiny images (< 50KB)
  if [ "$before_bytes" -lt 51200 ]; then
    echo -e "  ${YELLOW}⏭  skip${NC} $file ($(( before_bytes / 1024 ))KB — already small)"
    SKIPPED=$(( SKIPPED + 1 ))
    return
  fi

  TOTAL_BEFORE=$(( TOTAL_BEFORE + before_bytes ))

  # Resize via ffmpeg → tmp PNG, then encode to WebP via cwebp
  ffmpeg -y -i "$file" \
    -vf "scale='if(gt(iw,${MAX_WIDTH}),${MAX_WIDTH},iw)':-2" \
    -f image2 -vframes 1 "$TMP" 2>/dev/null

  cwebp -q "$QUALITY" -m 6 "$TMP" -o "$file" 2>/dev/null
  rm -f "$TMP"

  local after_bytes
  after_bytes=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
  TOTAL_AFTER=$(( TOTAL_AFTER + after_bytes ))

  local before_kb=$(( before_bytes / 1024 ))
  local after_kb=$(( after_bytes / 1024 ))
  local saved=$(( before_kb - after_kb ))
  local pct=$(( saved * 100 / before_kb ))

  echo -e "  ${GREEN}✅${NC} $file  ${before_kb}KB → ${after_kb}KB  (-${pct}%)"
  COUNT=$(( COUNT + 1 ))
}

shopt -s nullglob
images=("$TARGET_DIR"/*.png "$TARGET_DIR"/*.jpg "$TARGET_DIR"/*.jpeg "$TARGET_DIR"/*.webp)

if [ ${#images[@]} -eq 0 ]; then
  echo -e "${YELLOW}⚠️  No images found in $TARGET_DIR${NC}"
  exit 0
fi

for img in "${images[@]}"; do
  process_image "$img"
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=================================="
BEFORE_MB=$(echo "scale=1; $TOTAL_BEFORE / 1048576" | bc)
AFTER_MB=$(echo "scale=1; $TOTAL_AFTER / 1048576" | bc)
SAVED_MB=$(echo "scale=1; ($TOTAL_BEFORE - $TOTAL_AFTER) / 1048576" | bc)

echo -e "${GREEN}🎉 Done — $COUNT image(s) optimized, $SKIPPED skipped${NC}"
echo "   Before : ${BEFORE_MB}MB"
echo "   After  : ${AFTER_MB}MB"
echo "   Saved  : ${SAVED_MB}MB"
