#!/usr/bin/env bash
# Connect to the PostgreSQL server defined in .env
# Usage: bash connect.sh [database]
#   database defaults to $PGDATABASE from .env
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

find_env_file() {
  local dir="$1"

  while [[ "$dir" != "/" ]]; do
    if [[ -f "$dir/.env" ]]; then
      echo "$dir/.env"
      return 0
    fi

    dir="$(dirname "$dir")"
  done

  return 1
}

ENV_FILE="$(find_env_file "$SCRIPT_DIR" || true)"

if [[ -n "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi

: "${PGHOST:?PGHOST not set. Add it to .env}"
: "${PGUSER:?PGUSER not set. Add it to .env}"
: "${PGPASSWORD:?PGPASSWORD not set. Add it to .env}"
PGPORT="${PGPORT:-5432}"
TARGET_DB="${1:-${PGDATABASE:-postgres}}"

echo "Connecting to $PGHOST:$PGPORT as $PGUSER -> $TARGET_DB"
psql "host=$PGHOST port=$PGPORT user=$PGUSER dbname=$TARGET_DB sslmode=prefer"
