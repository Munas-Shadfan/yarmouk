#!/usr/bin/env bash
# check-core-web-vitals.sh — Fetch PageSpeed Insights CWV data for a URL
# Usage: ./check-core-web-vitals.sh https://example.com [mobile|desktop]
# Requires: curl, jq
# Optional: set PAGESPEED_API_KEY env var for higher API quota

set -euo pipefail

URL="${1:-}"
STRATEGY="${2:-mobile}"

if [[ -z "$URL" ]]; then
  echo "Usage: $0 <url> [mobile|desktop]"
  echo "Example: $0 https://example.com mobile"
  exit 1
fi

if ! command -v jq &>/dev/null; then
  echo "❌ jq is required. Install with: brew install jq"
  exit 1
fi

API_KEY="${PAGESPEED_API_KEY:-}"
API_URL="https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PARAMS="url=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$URL")&strategy=$STRATEGY"
[[ -n "$API_KEY" ]] && PARAMS="$PARAMS&key=$API_KEY"

echo ""
echo "══════════════════════════════════════════"
echo "  Core Web Vitals: $URL"
echo "  Strategy: $STRATEGY"
echo "══════════════════════════════════════════"
echo "  Fetching PageSpeed Insights data..."

RESPONSE=$(curl -sL --max-time 30 "$API_URL?$PARAMS")

# Check for API error
if echo "$RESPONSE" | jq -e '.error' &>/dev/null; then
  ERROR=$(echo "$RESPONSE" | jq -r '.error.message')
  echo "  ❌ API Error: $ERROR"
  echo "  Tip: Set PAGESPEED_API_KEY env var to avoid quota limits"
  exit 1
fi

# Overall score
SCORE=$(echo "$RESPONSE" | jq -r '.lighthouseResult.categories.performance.score // "N/A"')
if [[ "$SCORE" != "N/A" ]]; then
  SCORE_PCT=$(echo "$SCORE * 100" | bc | cut -d. -f1)
  if   [[ "$SCORE_PCT" -ge 90 ]]; then SCORE_LABEL="✅ Good ($SCORE_PCT)"
  elif [[ "$SCORE_PCT" -ge 50 ]]; then SCORE_LABEL="⚠️  Needs Improvement ($SCORE_PCT)"
  else                                  SCORE_LABEL="❌ Poor ($SCORE_PCT)"
  fi
else
  SCORE_LABEL="N/A"
fi

echo ""
echo "── Performance Score ────────────────────"
echo "  $SCORE_LABEL / 100"

# Helper: rate a metric
rate_metric() {
  local label="$1" value="$2" unit="$3" good="$4" needs="$5"
  if [[ "$value" == "null" || "$value" == "" ]]; then
    echo "  $label : No data"
    return
  fi
  local val_int
  val_int=$(echo "$value" | cut -d. -f1)
  if   (( val_int <= good  )); then STATUS="✅ Good"
  elif (( val_int <= needs )); then STATUS="⚠️  Needs Improvement"
  else                              STATUS="❌ Poor"
  fi
  echo "  $label : ${value}${unit}  $STATUS"
}

echo ""
echo "── Core Web Vitals ──────────────────────"
echo "  (Field data — real user measurements)"

FCP=$(echo "$RESPONSE"  | jq -r '.loadingExperience.metrics.FIRST_CONTENTFUL_PAINT_MS.percentile // "null"')
LCP=$(echo "$RESPONSE"  | jq -r '.loadingExperience.metrics.LARGEST_CONTENTFUL_PAINT_MS.percentile // "null"')
FID=$(echo "$RESPONSE"  | jq -r '.loadingExperience.metrics.FIRST_INPUT_DELAY_MS.percentile // "null"')
INP=$(echo "$RESPONSE"  | jq -r '.loadingExperience.metrics.INTERACTION_TO_NEXT_PAINT.percentile // "null"')
CLS=$(echo "$RESPONSE"  | jq -r '.loadingExperience.metrics.CUMULATIVE_LAYOUT_SHIFT_SCORE.percentile // "null"')
TTFB=$(echo "$RESPONSE" | jq -r '.loadingExperience.metrics.EXPERIMENTAL_TIME_TO_FIRST_BYTE.percentile // "null"')

# Convert ms to s for display
ms_to_s() { echo "scale=2; $1 / 1000" | bc; }

[[ "$FCP"  != "null" ]] && FCP_S=$(ms_to_s "$FCP")   || FCP_S="null"
[[ "$LCP"  != "null" ]] && LCP_S=$(ms_to_s "$LCP")   || LCP_S="null"
[[ "$TTFB" != "null" ]] && TTFB_S=$(ms_to_s "$TTFB") || TTFB_S="null"

# LCP: good ≤ 2500ms, needs ≤ 4000ms
if [[ "$LCP" != "null" ]]; then
  if   (( LCP <= 2500 )); then LCP_STATUS="✅ Good"
  elif (( LCP <= 4000 )); then LCP_STATUS="⚠️  Needs Improvement"
  else                         LCP_STATUS="❌ Poor"
  fi
  echo "  LCP  (Largest Contentful Paint)  : ${LCP_S}s  $LCP_STATUS  (good: ≤2.5s)"
else
  echo "  LCP  : No field data"
fi

# INP: good ≤ 200ms, needs ≤ 500ms
if [[ "$INP" != "null" ]]; then
  if   (( INP <= 200 )); then INP_STATUS="✅ Good"
  elif (( INP <= 500 )); then INP_STATUS="⚠️  Needs Improvement"
  else                        INP_STATUS="❌ Poor"
  fi
  echo "  INP  (Interaction to Next Paint)  : ${INP}ms  $INP_STATUS  (good: ≤200ms)"
else
  echo "  INP  : No field data"
fi

# CLS: good ≤ 0.1, needs ≤ 0.25 (percentile is * 100 in API)
if [[ "$CLS" != "null" ]]; then
  CLS_REAL=$(echo "scale=3; $CLS / 100" | bc)
  if   (( CLS <= 10  )); then CLS_STATUS="✅ Good"
  elif (( CLS <= 25  )); then CLS_STATUS="⚠️  Needs Improvement"
  else                        CLS_STATUS="❌ Poor"
  fi
  echo "  CLS  (Cumulative Layout Shift)    : $CLS_REAL  $CLS_STATUS  (good: ≤0.1)"
else
  echo "  CLS  : No field data"
fi

# FCP
if [[ "$FCP" != "null" ]]; then
  if   (( FCP <= 1800 )); then FCP_STATUS="✅ Good"
  elif (( FCP <= 3000 )); then FCP_STATUS="⚠️  Needs Improvement"
  else                         FCP_STATUS="❌ Poor"
  fi
  echo "  FCP  (First Contentful Paint)     : ${FCP_S}s  $FCP_STATUS  (good: ≤1.8s)"
fi

# TTFB
if [[ "$TTFB" != "null" ]]; then
  if   (( TTFB <= 800  )); then TTFB_STATUS="✅ Good"
  elif (( TTFB <= 1800 )); then TTFB_STATUS="⚠️  Needs Improvement"
  else                          TTFB_STATUS="❌ Poor"
  fi
  echo "  TTFB (Time to First Byte)         : ${TTFB_S}s  $TTFB_STATUS  (good: ≤0.8s)"
fi

echo ""
echo "── Lab Data (Lighthouse) ────────────────"
LAB_LCP=$(echo "$RESPONSE"  | jq -r '.lighthouseResult.audits["largest-contentful-paint"].displayValue // "N/A"')
LAB_TBT=$(echo "$RESPONSE"  | jq -r '.lighthouseResult.audits["total-blocking-time"].displayValue // "N/A"')
LAB_CLS=$(echo "$RESPONSE"  | jq -r '.lighthouseResult.audits["cumulative-layout-shift"].displayValue // "N/A"')
LAB_SI=$(echo "$RESPONSE"   | jq -r '.lighthouseResult.audits["speed-index"].displayValue // "N/A"')
LAB_TTI=$(echo "$RESPONSE"  | jq -r '.lighthouseResult.audits["interactive"].displayValue // "N/A"')
LAB_FCP=$(echo "$RESPONSE"  | jq -r '.lighthouseResult.audits["first-contentful-paint"].displayValue // "N/A"')

echo "  LCP          : $LAB_LCP"
echo "  TBT          : $LAB_TBT"
echo "  CLS          : $LAB_CLS"
echo "  Speed Index  : $LAB_SI"
echo "  TTI          : $LAB_TTI"
echo "  FCP          : $LAB_FCP"

echo ""
echo "── Top Opportunities ────────────────────"
echo "$RESPONSE" | jq -r '
  .lighthouseResult.audits
  | to_entries
  | map(select(.value.details.type == "opportunity" and (.value.details.overallSavingsMs // 0) > 200))
  | sort_by(-.value.details.overallSavingsMs)
  | .[0:5]
  | .[]
  | "  ⚡ \(.value.title) — save ~\(.value.details.overallSavingsMs | . / 1000 | . * 10 | round / 10)s"
' 2>/dev/null || echo "  No major opportunities detected"

echo ""
echo "── Diagnostics ──────────────────────────"
echo "$RESPONSE" | jq -r '
  .lighthouseResult.audits
  | to_entries
  | map(select(.value.score != null and .value.score < 0.9 and .value.scoreDisplayMode == "binary"))
  | .[0:6]
  | .[]
  | "  ⚠️  \(.value.title)"
' 2>/dev/null || echo "  No critical diagnostics"

echo ""
echo "── Full Report ──────────────────────────"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$URL")
echo "  https://pagespeed.web.dev/report?url=$ENCODED&form_factor=$STRATEGY"

echo ""
echo "══════════════════════════════════════════"
echo "  CWV check complete."
echo "══════════════════════════════════════════"
echo ""
