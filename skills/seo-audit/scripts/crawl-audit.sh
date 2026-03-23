#!/usr/bin/env bash
# crawl-audit.sh — Crawl a site's sitemap and audit each URL for SEO issues
# Usage: ./crawl-audit.sh https://example.com [max_urls]
# Requires: curl, xmllint (brew install libxml2)
# Output: crawl-report.txt in current directory

set -euo pipefail

BASE_URL="${1:-}"
MAX_URLS="${2:-50}"

if [[ -z "$BASE_URL" ]]; then
  echo "Usage: $0 <base-url> [max_urls]"
  echo "Example: $0 https://example.com 20"
  exit 1
fi

# Strip trailing slash
BASE_URL="${BASE_URL%/}"
PROTO=$(echo "$BASE_URL" | awk -F/ '{print $1"//"$3}')
DOMAIN=$(echo "$BASE_URL" | awk -F/ '{print $3}')

REPORT="crawl-report-$(date +%Y%m%d-%H%M%S).txt"
ISSUES=0
PAGES_CHECKED=0

log() { echo "$1" | tee -a "$REPORT"; }

log ""
log "══════════════════════════════════════════"
log "  SEO Crawl Audit: $BASE_URL"
log "  Max URLs: $MAX_URLS"
log "  Report: $REPORT"
log "  Started: $(date)"
log "══════════════════════════════════════════"

# ── Discover URLs ──────────────────────────────────────────
log ""
log "── Discovering URLs from sitemap ────────"

SITEMAP_URLS=()

# Try sitemap.xml, sitemap_index.xml, /sitemap
for SITEMAP_PATH in sitemap.xml sitemap_index.xml sitemap; do
  SITEMAP_URL="$PROTO/$SITEMAP_PATH"
  STATUS=$(curl -sL --max-time 10 -o /dev/null -w "%{http_code}" "$SITEMAP_URL")
  if [[ "$STATUS" == "200" ]]; then
    log "  ✅ Sitemap found: $SITEMAP_URL"
    RAW=$(curl -sL --max-time 20 "$SITEMAP_URL")

    # Check if sitemap index (contains <sitemap> tags)
    if echo "$RAW" | grep -q '<sitemap>'; then
      log "  📑 Sitemap index detected — extracting child sitemaps"
      CHILD_SITEMAPS=$(echo "$RAW" | grep -oi '<loc>[^<]*</loc>' | sed 's/<loc>//;s|</loc>||')
      while IFS= read -r CHILD; do
        log "     Fetching: $CHILD"
        CHILD_RAW=$(curl -sL --max-time 20 "$CHILD" 2>/dev/null || true)
        while IFS= read -r U; do
          SITEMAP_URLS+=("$U")
        done < <(echo "$CHILD_RAW" | grep -oi '<loc>[^<]*</loc>' | sed 's/<loc>//;s|</loc>||')
      done <<< "$CHILD_SITEMAPS"
    else
      while IFS= read -r U; do
        SITEMAP_URLS+=("$U")
      done < <(echo "$RAW" | grep -oi '<loc>[^<]*</loc>' | sed 's/<loc>//;s|</loc>||')
    fi
    break
  fi
done

if [[ "${#SITEMAP_URLS[@]}" -eq 0 ]]; then
  log "  ⚠️  No URLs from sitemap — falling back to homepage only"
  SITEMAP_URLS=("$BASE_URL")
fi

TOTAL="${#SITEMAP_URLS[@]}"
log "  Total URLs in sitemap: $TOTAL"
[[ "$TOTAL" -gt "$MAX_URLS" ]] && log "  (Auditing first $MAX_URLS)"

# ── Crawl & Audit ──────────────────────────────────────────
log ""
log "── Page-by-Page Audit ───────────────────"

declare -A REDIRECT_URLS
declare -A NOINDEX_URLS
declare -A NO_TITLE_URLS
declare -A DUPE_TITLES
declare -A SHORT_TITLE_URLS
declare -A LONG_TITLE_URLS
declare -A NO_H1_URLS
declare -A MULTI_H1_URLS
declare -A NO_CANONICAL_URLS
declare -A NO_META_DESC_URLS
declare -a SEEN_TITLES

for ((i=0; i<TOTAL && i<MAX_URLS; i++)); do
  PAGE_URL="${SITEMAP_URLS[$i]}"
  PAGES_CHECKED=$((PAGES_CHECKED + 1))
  PAGE_ISSUES=0
  PAGE_LOG="  [$((i+1))/$([[ $TOTAL -lt $MAX_URLS ]] && echo $TOTAL || echo $MAX_URLS)] $PAGE_URL"

  # Fetch with redirect tracking
  RAW=$(curl -sL --max-time 15 \
    -A "Mozilla/5.0 (compatible; SEO-Audit/1.0)" \
    -w "\n###STATUS:%{http_code}###\n###FINAL_URL:%{url_effective}###" \
    "$PAGE_URL" 2>/dev/null || echo "###STATUS:000###\n###FINAL_URL:$PAGE_URL###")

  STATUS=$(echo "$RAW" | grep -o '###STATUS:[0-9]*###' | grep -o '[0-9]*')
  FINAL_URL=$(echo "$RAW" | grep -o '###FINAL_URL:[^#]*###' | sed 's/###FINAL_URL://;s/###//')
  HTML=$(echo "$RAW" | sed '/###STATUS:/d' | sed '/###FINAL_URL:/d')

  PAGE_RESULT=""

  # Status check
  if [[ "$STATUS" == "000" ]]; then
    PAGE_RESULT+="\n    ❌ TIMEOUT/ERROR — could not fetch"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  elif [[ "$STATUS" == "301" || "$STATUS" == "302" ]]; then
    REDIRECT_URLS["$PAGE_URL"]="→ $FINAL_URL"
    PAGE_RESULT+="\n    ⚠️  REDIRECT ($STATUS) → $FINAL_URL"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  elif [[ "$STATUS" != "200" ]]; then
    PAGE_RESULT+="\n    ❌ HTTP $STATUS"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  fi

  # Noindex
  ROBOTS_META=$(echo "$HTML" | grep -oi '<meta[^>]*name=["\x27]robots["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed 's/content="//;s/"//')
  if echo "$ROBOTS_META" | grep -qi 'noindex'; then
    NOINDEX_URLS["$PAGE_URL"]=1
    PAGE_RESULT+="\n    ❌ NOINDEX — in sitemap but set to noindex"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  fi

  # Title
  TITLE=$(echo "$HTML" | grep -oi '<title[^>]*>.*</title>' | sed 's/<[^>]*>//g' | head -1 | xargs)
  if [[ -z "$TITLE" ]]; then
    NO_TITLE_URLS["$PAGE_URL"]=1
    PAGE_RESULT+="\n    ❌ Missing title tag"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  else
    TITLE_LEN=${#TITLE}
    if [[ "$TITLE_LEN" -lt 30 ]]; then
      SHORT_TITLE_URLS["$PAGE_URL"]="$TITLE"
      PAGE_RESULT+="\n    ⚠️  Title too short (${TITLE_LEN} chars): $TITLE"
      PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
    elif [[ "$TITLE_LEN" -gt 60 ]]; then
      LONG_TITLE_URLS["$PAGE_URL"]="$TITLE"
      PAGE_RESULT+="\n    ⚠️  Title too long (${TITLE_LEN} chars): $TITLE"
      PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
    fi
    # Duplicate title check
    if printf '%s\n' "${SEEN_TITLES[@]:-}" | grep -qxF "$TITLE"; then
      DUPE_TITLES["$PAGE_URL"]="$TITLE"
      PAGE_RESULT+="\n    ❌ Duplicate title: $TITLE"
      PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
    else
      SEEN_TITLES+=("$TITLE")
    fi
  fi

  # H1
  H1_COUNT=$(echo "$HTML" | grep -oi '<h1[^>]*>.*</h1>' | wc -l | tr -d ' ')
  if [[ "$H1_COUNT" -eq 0 ]]; then
    NO_H1_URLS["$PAGE_URL"]=1
    PAGE_RESULT+="\n    ❌ No H1 tag"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  elif [[ "$H1_COUNT" -gt 1 ]]; then
    MULTI_H1_URLS["$PAGE_URL"]="$H1_COUNT"
    PAGE_RESULT+="\n    ⚠️  Multiple H1 tags ($H1_COUNT)"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  fi

  # Canonical
  CANONICAL=$(echo "$HTML" | grep -oi '<link[^>]*rel=["\x27]canonical["\x27][^>]*>' | grep -oi 'href="[^"]*"' | sed 's/href="//;s/"//')
  if [[ -z "$CANONICAL" ]]; then
    NO_CANONICAL_URLS["$PAGE_URL"]=1
    PAGE_RESULT+="\n    ⚠️  No canonical tag"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  fi

  # Meta description
  META_DESC=$(echo "$HTML" | grep -oi '<meta[^>]*name=["\x27]description["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed 's/content="//;s/"//')
  if [[ -z "$META_DESC" ]]; then
    NO_META_DESC_URLS["$PAGE_URL"]=1
    PAGE_RESULT+="\n    ⚠️  No meta description"
    PAGE_ISSUES=$((PAGE_ISSUES + 1)); ISSUES=$((ISSUES + 1))
  fi

  # Print result
  if [[ "$PAGE_ISSUES" -eq 0 ]]; then
    log "$PAGE_LOG  ✅"
  else
    log "$PAGE_LOG  ($PAGE_ISSUES issues)"
    echo -e "$PAGE_RESULT" | tee -a "$REPORT"
  fi
done

# ── Summary ────────────────────────────────────────────────
log ""
log "══════════════════════════════════════════"
log "  CRAWL SUMMARY"
log "══════════════════════════════════════════"
log "  Pages checked : $PAGES_CHECKED"
log "  Total issues  : $ISSUES"
log ""

if [[ "${#REDIRECT_URLS[@]:-0}" -gt 0 ]]; then
  log "── Redirects in Sitemap (${#REDIRECT_URLS[@]}) ──────────"
  for U in "${!REDIRECT_URLS[@]}"; do log "  $U ${REDIRECT_URLS[$U]}"; done
  log ""
fi
if [[ "${#NOINDEX_URLS[@]:-0}" -gt 0 ]]; then
  log "── Noindex Pages in Sitemap (${#NOINDEX_URLS[@]}) ──────"
  for U in "${!NOINDEX_URLS[@]}"; do log "  $U"; done
  log ""
fi
if [[ "${#DUPE_TITLES[@]:-0}" -gt 0 ]]; then
  log "── Duplicate Titles (${#DUPE_TITLES[@]}) ────────────────"
  for U in "${!DUPE_TITLES[@]}"; do log "  $U → \"${DUPE_TITLES[$U]}\""; done
  log ""
fi
if [[ "${#NO_H1_URLS[@]:-0}" -gt 0 ]]; then
  log "── Missing H1 (${#NO_H1_URLS[@]}) ──────────────────────"
  for U in "${!NO_H1_URLS[@]}"; do log "  $U"; done
  log ""
fi
if [[ "${#NO_CANONICAL_URLS[@]:-0}" -gt 0 ]]; then
  log "── Missing Canonical (${#NO_CANONICAL_URLS[@]}) ─────────"
  for U in "${!NO_CANONICAL_URLS[@]}"; do log "  $U"; done
  log ""
fi
if [[ "${#NO_META_DESC_URLS[@]:-0}" -gt 0 ]]; then
  log "── Missing Meta Description (${#NO_META_DESC_URLS[@]}) ─"
  for U in "${!NO_META_DESC_URLS[@]}"; do log "  $U"; done
  log ""
fi

log "── Next Steps ───────────────────────────"
log "  1. Fix ❌ critical issues first (noindex in sitemap, missing titles, HTTP errors)"
log "  2. Fix ⚠️  warnings (duplicate titles, missing canonicals)"
log "  3. Run: ./check-core-web-vitals.sh $BASE_URL"
log "  4. Run: ./fetch-seo-basics.sh $BASE_URL  (on key landing pages)"
log ""
log "  Full report saved to: $REPORT"
log "══════════════════════════════════════════"
log ""
