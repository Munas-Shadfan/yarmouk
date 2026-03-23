#!/bin/bash
# Example script to generate TypeScript/Angular client from a spec without relying on skills
# Uses orval CLI if installed, or openapi-generator-cli as a fallback.
# Usage: ./generate_client.sh <spec-path> <output-dir>

SPEC=$1
OUTDIR=$2

if [ -z "$SPEC" ] || [ -z "$OUTDIR" ]; then
  echo "Usage: $0 <spec-path> <output-dir>"
  exit 1
fi

# try orval first
if command -v orval >/dev/null 2>&1; then
  echo "using orval to generate client"
  orval --input "$SPEC" --output "$OUTDIR" || exit 1
else
  echo "orval not found, falling back to openapi-generator-cli"
  if ! command -v openapi-generator-cli >/dev/null 2>&1; then
    echo "please install orval (npm i -g orval) or openapi-generator-cli"
    exit 1
  fi
  openapi-generator-cli generate -i "$SPEC" -g typescript-angular -o "$OUTDIR" || exit 1
fi

echo "client generated in $OUTDIR"
