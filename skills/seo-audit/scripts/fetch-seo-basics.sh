#!/usr/bin/env bash
# fetch-seo-basics.sh — Pull key on-page SEO signals from a URL
# Usage: ./fetch-seo-basics.sh https://example.com
# Requires: curl (built-in macOS/Linux)

set -euo pipefail

URL="${1:-}"

if [[ -z "$URL" ]]; then
  echo "Usage: $0 <url>"
  echo "Example: $0 https://example.com/page"
  exit 1
fi

# Normalise — strip trailing slash
URL="${URL%/}"

echo ""
echo "══════════════════════════════════════════"
echo "  SEO Basics Fetch: $URL"
echo "══════════════════════════════════════════"

HTML=$(curl -sL --max-time 15 \
  -A "Mozilla/5.0 (compatible; SEO-Audit-Script/1.0)" \
  -w "\n###STATUS:%{http_code}###\nTTFB:%{time_starttransfer}s" \
  "$URL")

STATUS=$(echo "$HTML" | grep -o '###STATUS:[0-9]*###' | grep -o '[0-9]*')
TTFB=$(echo "$HTML"  | grep -o 'TTFB:[0-9.]*s' | head -1)
HTML_BODY=$(echo "$HTML" | sed '/###STATUS:/d' | sed '/TTFB:/d')

echo ""
echo "── HTTP ─────────────────────────────────"
echo "  Status code : $STATUS"
echo "  TTFB        : $TTFB"

# HTTPS check
if [[ "$URL" == https://* ]]; then
  echo "  HTTPS       : ✅"
else
  echo "  HTTPS       : ❌ Not HTTPS"
fi

echo ""
echo "── Title Tag ────────────────────────────"
TITLE=$(echo "$HTML_BODY" | grep -oi '<title[^>]*>.*</title>' | sed 's/<[^>]*>//g' | head -1)
if [[ -n "$TITLE" ]]; then
  LEN=${#TITLE}
  echo "  Content : $TITLE"
  echo "  Length  : $LEN chars $([ "$LEN" -le 60 ] && echo '✅' || echo '⚠️  Over 60')"
else
  echo "  ❌ No title tag found"
fi

echo ""
echo "── Meta Description ─────────────────────"
META_DESC=$(echo "$HTML_BODY" | grep -oi '<meta[^>]*name=["\x27]description["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed 's/content="//;s/"//')
if [[ -z "$META_DESC" ]]; then
  META_DESC=$(echo "$HTML_BODY" | grep -oi '<meta[^>]*content="[^"]*"[^>]*name=["\x27]description["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed 's/content="//;s/"//')
fi
if [[ -n "$META_DESC" ]]; then
  LEN=${#META_DESC}
  echo "  Content : $META_DESC"
  echo "  Length  : $LEN chars $([ "$LEN" -le 160 ] && echo '✅' || echo '⚠️  Over 160')"
else
  echo "  ❌ No meta description found"
fi

echo ""
echo "── Canonical ────────────────────────────"
CANONICAL=$(echo "$HTML_BODY" | grep -oi '<link[^>]*rel=["\x27]canonical["\x27][^>]*>' | grep -oi 'href="[^"]*"' | sed 's/href="//;s/"//' || true)
if [[ -n "$CANONICAL" ]]; then
  echo "  ✅ $CANONICAL"
  if [[ "$CANONICAL" != "$URL" && "$CANONICAL" != "$URL/" ]]; then
    echo "  ⚠️  Canonical differs from requested URL"
  fi
else
  echo "  ❌ No canonical tag found"
fi

echo ""
echo "── H1 Tags ──────────────────────────────"
H1_COUNT=$(echo "$HTML_BODY" | grep -oi '<h1[^>]*>.*</h1>' | wc -l | tr -d ' ' || true)
H1_TEXT=$(echo "$HTML_BODY"  | grep -oi '<h1[^>]*>.*</h1>' | sed 's/<[^>]*>//g' | head -3 || true)
echo "  Count : $H1_COUNT $([ "$H1_COUNT" -eq 1 ] && echo '✅' || echo '⚠️  Should be exactly 1')"
if [[ -n "$H1_TEXT" ]]; then
  echo "  Text  : $H1_TEXT"
fi

echo ""
echo "── Robots Meta ──────────────────────────"
ROBOTS_META=$(echo "$HTML_BODY" | grep -oi '<meta[^>]*name=["\x27]robots["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed 's/content="//;s/"//') || true
if [[ -n "$ROBOTS_META" ]]; then
  echo "  $ROBOTS_META"
  if echo "$ROBOTS_META" | grep -qi 'noindex'; then
    echo "  ❌ Page is set to NOINDEX — will not be indexed"
  else
    echo "  ✅ Indexable"
  fi
else
  echo "  ✅ No robots meta (indexable by default)"
fi

echo ""
echo "── Open Graph ───────────────────────────"
OG_TITLE=$(echo "$HTML_BODY" | grep -oi '<meta[^>]*property=["\x27]og:title["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed "s/content=\"//;s/\"//" | head -1 || true)
OG_DESC=$(echo "$HTML_BODY"  | grep -oi '<meta[^>]*property=["\x27]og:description["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed "s/content=\"//;s/\"//" | head -1 || true)
OG_IMG=$(echo "$HTML_BODY"   | grep -oi '<meta[^>]*property=["\x27]og:image["\x27][^>]*>' | grep -oi 'content="[^"]*"' | sed "s/content=\"//;s/\"//" | head -1 || true)
[[ -n "$OG_TITLE" ]] && echo "  og:title       : $OG_TITLE" || echo "  ❌ og:title missing"
[[ -n "$OG_DESC"  ]] && echo "  og:description : $OG_DESC"  || echo "  ❌ og:description missing"
[[ -n "$OG_IMG"   ]] && echo "  og:image       : $OG_IMG"   || echo "  ❌ og:image missing"

echo ""
echo "── Images Without Alt ───────────────────"
IMG_TOTAL=$(echo "$HTML_BODY"  | grep -oi '<img [^>]*>' | wc -l | tr -d ' ')
IMG_NO_ALT=$(echo "$HTML_BODY" | grep -oi '<img [^>]*>' | grep -v 'alt="[^"]*[a-zA-Z]' | wc -l | tr -d ' ')
echo "  Total images : $IMG_TOTAL"
echo "  Missing alt  : $IMG_NO_ALT $([ "$IMG_NO_ALT" -eq 0 ] && echo '✅' || echo '⚠️')"

echo ""
echo "── Internal vs External Links ───────────────"
DOMAIN=$(echo "$URL" | awk -F/ '{print $3}')
ALL_LINKS=$(echo "$HTML_BODY" | grep -oi 'href="[^"#]*"' | sed 's/href="//;s/"//' | grep -v '^$' | grep -v '^#')
INT_LINKS=$(echo "$ALL_LINKS" | grep -c "$DOMAIN" || true)
EXT_LINKS=$(echo "$ALL_LINKS" | grep -vc "$DOMAIN" || true)
echo "  Internal : $INT_LINKS"
echo "  External : $EXT_LINKS"

echo ""
echo "── robots.txt ───────────────────────────"
ROBOTS_URL="${URL%/*}/robots.txt"
PROTO=$(echo "$URL" | awk -F/ '{print $1"//"$3}')
ROBOTS_URL="$PROTO/robots.txt"
ROBOTS_STATUS=$(curl -sL --max-time 10 -o /dev/null -w "%{http_code}" "$ROBOTS_URL")
if [[ "$ROBOTS_STATUS" == "200" ]]; then
  echo "  ✅ Found at $ROBOTS_URL"
  ROBOTS_CONTENT=$(curl -sL --max-time 10 "$ROBOTS_URL")
  if echo "$ROBOTS_CONTENT" | grep -qi "sitemap"; then
    SITEMAP_LINE=$(echo "$ROBOTS_CONTENT" | grep -i "sitemap" | head -1)
    echo "  Sitemap declared: $SITEMAP_LINE"
  else
    echo "  ⚠️  No Sitemap declared in robots.txt"
  fi
  if echo "$ROBOTS_CONTENT" | grep -qi "disallow: /"; then
    echo "  ⚠️  Contains 'Disallow: /' — check for accidental full block"
  fi
else
  echo "  ❌ robots.txt not found (HTTP $ROBOTS_STATUS)"
fi

echo ""
echo "── XML Sitemap ──────────────────────────"
SITEMAP_URL="$PROTO/sitemap.xml"
SITEMAP_STATUS=$(curl -sL --max-time 10 -o /dev/null -w "%{http_code}" "$SITEMAP_URL")
if [[ "$SITEMAP_STATUS" == "200" ]]; then
  URL_COUNT=$(curl -sL --max-time 15 "$SITEMAP_URL" | grep -c '<loc>' || true)
  echo "  ✅ Found at $SITEMAP_URL"
  echo "  URL count: $URL_COUNT"
else
  echo "  ⚠️  Not found at $SITEMAP_URL (HTTP $SITEMAP_STATUS)"
  echo "     Try sitemap_index.xml or check robots.txt for custom path"
fi

echo ""
echo "══════════════════════════════════════════"
echo "  Fetch complete. Review findings above."
echo "  For Core Web Vitals run: ./check-core-web-vitals.sh $URL"
echo "══════════════════════════════════════════"
echo ""
