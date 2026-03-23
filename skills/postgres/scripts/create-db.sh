#!/usr/bin/env bash
# Create a PostgreSQL database if it does not already exist.
# Credentials are read from .env — never hardcoded.
# Usage: bash create-db.sh <database-name>
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
TARGET_DB="${1:?Usage: bash create-db.sh <database-name>}"

CONN="host=$PGHOST port=$PGPORT user=$PGUSER dbname=postgres sslmode=prefer"

echo "Checking if database '$TARGET_DB' exists on $PGHOST..."

EXISTS=$(psql "$CONN" -tAc "SELECT 1 FROM pg_database WHERE datname = '$TARGET_DB';")

if [[ "$EXISTS" == "1" ]]; then
  echo "Database '$TARGET_DB' already exists. Nothing to do."
else
  echo "Database '$TARGET_DB' not found. Creating..."
  psql "$CONN" -c "CREATE DATABASE \"$TARGET_DB\" OWNER \"$PGUSER\";"
  echo "Database '$TARGET_DB' created successfully."
  echo ""
  echo "Update your project .env with:"
  echo "  PGDATABASE=$TARGET_DB"
fi
