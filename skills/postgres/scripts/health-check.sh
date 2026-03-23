#!/usr/bin/env bash
# Quick health check for the PostgreSQL server defined in .env
# Usage: bash health-check.sh [database]
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

run_sql() {
  psql "host=$PGHOST port=$PGPORT user=$PGUSER dbname=$TARGET_DB sslmode=prefer" "$@"
}

echo "=== PostgreSQL Health Check: $PGHOST ==="

echo ""
echo "--- Server version ---"
run_sql -tAc "SELECT version();"

echo ""
echo "--- Database size ($TARGET_DB) ---"
run_sql -tAc "SELECT pg_size_pretty(pg_database_size(current_database()));"

echo ""
echo "--- Active connections ---"
run_sql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state ORDER BY count DESC;"

echo ""
echo "--- Top 5 largest tables ---"
run_sql -c "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 5;"

echo ""
echo "--- Tables with high dead tuples (needs VACUUM) ---"
run_sql -c "
SELECT relname, n_dead_tup, last_autovacuum
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 5;"

echo ""
echo "--- Unused indexes ---"
run_sql -c "
SELECT indexname, tablename, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY tablename
LIMIT 10;"

echo ""
echo "Done."
