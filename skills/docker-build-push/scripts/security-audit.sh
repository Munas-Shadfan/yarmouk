#!/bin/bash
# Security Audit — Pre-flight check before any git commit or docker push
# Usage: bash scripts/security-audit.sh [--strict]
# Exit code 0 = safe to proceed | Exit code 1 = BLOCKED (issues found)

set +e

STRICT="${1:-}"
ISSUES=0
WARNINGS=0

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

warn() { echo -e "${YELLOW}⚠️  WARNING: $1${NC}"; ((WARNINGS++)) || true; }
fail() { echo -e "${RED}❌ ISSUE: $1${NC}"; ((ISSUES++)) || true; }
pass() { echo -e "${GREEN}✅ $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

echo ""
echo "🔒 Security Audit"
echo "=================================="

# ── 1. Check .env is NOT tracked by git ──────────────────────────────────────
echo ""
echo "📄 Checking git-tracked secrets..."
for f in .env .env.local .env.production .env.staging; do
  if git ls-files --error-unmatch "$f" 2>/dev/null; then
    fail "$f is tracked by git — run: git rm --cached $f"
  fi
done

# Check if any file in git index contains known secret patterns
STAGED_SECRETS=$(git diff --cached --unified=0 2>/dev/null | grep -iE '^\+.*(api[_-]?key|github_token|secret|password|private_key)\s*[=:]\s*.{8,}' | grep -v '^\+\+\+' || true)
if [ -n "$STAGED_SECRETS" ]; then
  fail "Staged changes contain what looks like secrets — review before committing"
  echo "$STAGED_SECRETS" | head -5
else
  pass "No secrets detected in staged files"
fi

# ── 2. Scan working directory for exposed secrets ────────────────────────────
echo ""
echo "🔍 Scanning files for exposed secrets..."
SCAN_DIRS="."
EXCLUDE="--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build --exclude=*.lock --exclude=*.png --exclude=*.jpg"

HITS=$(grep -rniE $EXCLUDE \
  '(GITHUB_TOKEN|GEMINI_API_KEY|AWS_SECRET|STRIPE_SECRET|OPENAI_API_KEY)\s*=\s*.{8,}' \
  $SCAN_DIRS 2>/dev/null \
  | grep -v '\.env\.example\|your-key\|placeholder\|<.*>\|TODO\|#.*example' || true)

if [ -n "$HITS" ]; then
  warn "Possible hardcoded secrets found (verify these are not real keys):"
  echo "$HITS" | head -10
else
  pass "No hardcoded secrets detected"
fi

# ── 3. Check .gitignore covers sensitive files ───────────────────────────────
echo ""
echo "📋 Checking .gitignore..."
REQUIRED_IGNORES=(".env" ".credentials" "*.pem" "*.key" "*.p12")
if [ -f ".gitignore" ]; then
  for pattern in "${REQUIRED_IGNORES[@]}"; do
    if grep -qF "$pattern" ".gitignore"; then
      pass "$pattern is gitignored"
    else
      warn "$pattern is NOT in .gitignore"
    fi
  done
else
  fail "No .gitignore found"
fi

# ── 4. Check credential file permissions ─────────────────────────────────────
echo ""
echo "🔐 Checking credential file permissions..."
if [ -d ".credentials" ]; then
  for f in .credentials/*; do
    if [ -f "$f" ]; then
      perms=$(stat -f "%Op" "$f" 2>/dev/null | tail -c 4 || stat -c "%a" "$f" 2>/dev/null)
      if [ "$perms" = "600" ]; then
        pass "$f permissions OK (600)"
      else
        fail "$f has permissions $perms (should be 600) — run: chmod 600 $f"
      fi
    fi
  done
else
  info "No .credentials directory"
fi

# ── 5. Check GITHUB_TOKEN is set (required for push) ─────────────────────────
echo ""
echo "🔑 Checking required env vars..."
if [ -n "${GITHUB_TOKEN:-}" ]; then
  # Mask the token in output
  MASKED="${GITHUB_TOKEN:0:8}****"
  pass "GITHUB_TOKEN is set ($MASKED)"
else
  fail "GITHUB_TOKEN is not set — export it or add to .env"
fi

if [ -n "${GEMINI_API_KEY:-}" ]; then
  MASKED="${GEMINI_API_KEY:0:8}****"
  pass "GEMINI_API_KEY is set ($MASKED)"
else
  info "GEMINI_API_KEY not set (only needed for image generation)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "=================================="
echo "📊 Summary"
echo "=================================="

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}✅ All checks passed — safe to proceed${NC}"
  exit 0
elif [ $ISSUES -eq 0 ]; then
  echo -e "${YELLOW}⚠️  $WARNINGS warning(s), 0 blocking issues${NC}"
  if [ "$STRICT" = "--strict" ]; then
    echo -e "${RED}Strict mode: warnings treated as errors. Aborting.${NC}"
    exit 1
  fi
  exit 0
else
  echo -e "${RED}❌ $ISSUES issue(s), $WARNINGS warning(s) — BLOCKED${NC}"
  echo "Fix the issues above before committing or pushing."
  exit 1
fi
