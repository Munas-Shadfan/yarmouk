#!/bin/bash
# Docker Build & Push to GHCR
# Usage: bash scripts/build-and-push.sh [version] [--skip-audit]
# Requires: GITHUB_TOKEN env var with write:packages scope
set -euo pipefail

VERSION="${1:-}"
SKIP_AUDIT="${2:-}"

GREEN='\033[0;32m'; BLUE='\033[0;34m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Allow callers to override REPO_ROOT (e.g. when skill lives in a submodule)
REPO_ROOT="${REPO_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
cd "${REPO_ROOT}"

# ── Security audit ────────────────────────────────────────────────────────────
if [ "$SKIP_AUDIT" != "--skip-audit" ]; then
  echo -e "${BLUE}🔒 Running security audit...${NC}"
  if ! bash "${SCRIPT_DIR}/security-audit.sh"; then
    echo -e "${RED}❌ Security audit failed. Aborting build.${NC}"
    exit 1
  fi
  echo ""
fi

# ── Config (set by skill from project context) ────────────────────────────────
REGISTRY="ghcr.io"
GITHUB_USER="husainf4l"
PROJECT="${PROJECT_NAME:-$(basename "$REPO_ROOT")}"
# SERVICES is expected to be set externally or defaulted
IFS=',' read -ra SERVICES <<< "${SERVICES:-app}"

# ── Version ───────────────────────────────────────────────────────────────────
if [ -z "$VERSION" ]; then
  if [ -f "VERSION" ]; then
    VERSION=$(cat VERSION | tr -d '[:space:]')
  else
    VERSION="1.0.0"
    echo "$VERSION" > VERSION
    echo -e "${YELLOW}Created VERSION file: $VERSION${NC}"
  fi
fi

CREATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SOURCE="https://github.com/${GITHUB_USER}/${PROJECT}"

echo -e "${BLUE}🐳 Docker Build & Push — ${PROJECT} v${VERSION}${NC}"
echo "Registry : ${REGISTRY}/${GITHUB_USER}"
echo "Services : ${SERVICES[*]}"
echo ""

# ── Guard: GITHUB_TOKEN ───────────────────────────────────────────────────────
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo -e "${RED}❌ GITHUB_TOKEN not set${NC}"
  echo "   export GITHUB_TOKEN=ghp_..."
  exit 1
fi

# ── Login ─────────────────────────────────────────────────────────────────────
echo -e "${BLUE}🔑 Logging in to GHCR...${NC}"
echo "${GITHUB_TOKEN}" | docker login "${REGISTRY}" -u "${GITHUB_USER}" --password-stdin
echo -e "${GREEN}✅ Login successful${NC}"
echo ""

# ── Build & Push each service ─────────────────────────────────────────────────
for SERVICE in "${SERVICES[@]}"; do
  IMAGE="${REGISTRY}/${GITHUB_USER}/${PROJECT}-${SERVICE}"
  DOCKERFILE="docker/Dockerfile.${SERVICE}"

  if [ ! -f "$DOCKERFILE" ]; then
    echo -e "${RED}❌ Missing $DOCKERFILE${NC}"
    echo "   Create it or run the skill's first-time setup."
    exit 1
  fi

  echo -e "${BLUE}🏗️  Building ${SERVICE}...${NC}"
  docker build \
    --platform linux/amd64 \
    --file "$DOCKERFILE" \
    --tag "${IMAGE}:${VERSION}" \
    --tag "${IMAGE}:latest" \
    --label "org.opencontainers.image.version=${VERSION}" \
    --label "org.opencontainers.image.created=${CREATED}" \
    --label "org.opencontainers.image.source=${SOURCE}" \
    .
  echo -e "${GREEN}✅ Built ${SERVICE}${NC}"

  echo -e "${BLUE}📤 Pushing ${SERVICE}...${NC}"
  docker push "${IMAGE}:${VERSION}"
  docker push "${IMAGE}:latest"
  echo -e "${GREEN}✅ Pushed ${IMAGE}:${VERSION}${NC}"
  echo ""
done

echo "=================================="
echo -e "${GREEN}🎉 Released v${VERSION} to GHCR${NC}"
for SERVICE in "${SERVICES[@]}"; do
  echo "   ${REGISTRY}/${GITHUB_USER}/${PROJECT}-${SERVICE}:${VERSION}"
done
echo -e "${BLUE}🔗 ${SOURCE}/packages${NC}"
