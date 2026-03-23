---
name: postgres
description: "PostgreSQL assistant for the self-hosted server at 31.97.217.73. Use when writing queries, designing tables, optimizing performance, reviewing schema, debugging slow queries, or managing the database. Also triggers for: SQL help, database design, migrations, indexing strategy, JSONB, pg_stat, explain analyze, connection issues."
metadata:
  version: 1.0.0
---

# PostgreSQL — Self-Hosted Server

**Server:** `31.97.217.73` (default port `5432`)
Credentials live in `.env` — never hardcoded anywhere.

## Setup

Add to your project root `.env`:

```env
PGHOST=31.97.217.73
PGPORT=5432
PGUSER=husain
PGPASSWORD=<password>
PGDATABASE=<your-database-name>
```

All scripts source the nearest parent `.env` automatically.

## Scripts

```bash
# Connect to the server
bash aqlaanskills/skills/postgres/scripts/connect.sh [database]

# Create a database if it doesn't exist, then update PGDATABASE in .env
bash aqlaanskills/skills/postgres/scripts/create-db.sh <database-name>

# Health check: version, size, connections, large tables, dead tuples, unused indexes
bash aqlaanskills/skills/postgres/scripts/health-check.sh [database]
```

---

## Data Types — Use These

| Use | Instead of |
|---|---|
| `BIGINT GENERATED ALWAYS AS IDENTITY` | `SERIAL` |
| `TIMESTAMPTZ` | `TIMESTAMP` |
| `TEXT` | `VARCHAR(n)` / `CHAR(n)` |
| `NUMERIC(p,s)` | `MONEY` / `FLOAT` for money |
| `BOOLEAN NOT NULL` | nullable booleans for true/false |
| `JSONB` | `JSON` |
| `UUID` (only for distributed/federated) | UUID as default PK |

---

## Table Design Rules

- Always define a `PRIMARY KEY` for reference tables (`users`, `orders`, etc.).
- Prefer `BIGINT GENERATED ALWAYS AS IDENTITY` as PK; use `UUID` only when global uniqueness is required.
- Add `NOT NULL` everywhere semantically required; use `DEFAULT` for common values.
- Normalize to 3NF first; denormalize only with measured evidence.
- PostgreSQL does **not** auto-index FK columns — always add them manually:
  ```sql
  CREATE INDEX ON orders (user_id);
  ```

### Standard Table Template

```sql
CREATE TABLE example (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON example (created_at);
```

---

## Indexing Strategy

| Index type | Use for |
|---|---|
| B-tree (default) | equality, range, ORDER BY |
| GIN | JSONB (`@>`, `?`), arrays, full-text search |
| GiST | ranges, geometry, exclusion constraints |
| BRIN | very large time-series tables (natural insert order) |

```sql
-- Composite: most selective/filtered column first
CREATE INDEX ON orders (user_id, created_at);

-- Partial: hot subset
CREATE INDEX ON users (email) WHERE status = 'active';

-- Expression: computed search key
CREATE INDEX ON users (LOWER(email));

-- Covering: avoid table lookup
CREATE INDEX ON orders (user_id, status) INCLUDE (total, created_at);

-- JSONB
CREATE INDEX ON events USING GIN (data);

-- Concurrent (non-blocking, cannot run in transaction)
CREATE INDEX CONCURRENTLY ON large_table (column);
```

---

## Query Optimization

Always use `EXPLAIN (ANALYZE, BUFFERS)` to diagnose slow queries:

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.name, COUNT(o.id)
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id, u.name;
```

### Pagination — cursor-based, not OFFSET

```sql
-- BAD
SELECT * FROM products ORDER BY id OFFSET 10000 LIMIT 20;

-- GOOD
SELECT * FROM products WHERE id > $last_id ORDER BY id LIMIT 20;
```

### Upserts

```sql
INSERT INTO users (email, name)
VALUES ($1, $2)
ON CONFLICT (email) DO UPDATE
SET name = EXCLUDED.name, updated_at = now()
WHERE users.name IS DISTINCT FROM EXCLUDED.name;
```

---

## JSONB Guidance

```sql
-- Index for containment + key existence
CREATE INDEX ON tbl USING GIN (data);

-- Containment query (uses GIN)
SELECT * FROM events WHERE data @> '{"type": "login"}';

-- BAD: no index support
SELECT * FROM events WHERE data->>'type' = 'login';

-- Extract a scalar for B-tree indexing
ALTER TABLE tbl ADD COLUMN status TEXT GENERATED ALWAYS AS (data->>'status') STORED;
CREATE INDEX ON tbl (status);
```

---

## Monitoring (run on your server)

```sql
-- Slow queries (requires pg_stat_statements extension)
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

-- Unused indexes
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- Table & index sizes
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 20;

-- Bloat / dead tuples
SELECT relname, n_dead_tup, n_live_tup, last_vacuum, last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 10;
```

---

## Security

```sql
-- Granular permissions (never GRANT ALL to app users)
GRANT SELECT, INSERT, UPDATE ON orders TO app_user;
GRANT USAGE ON SEQUENCE orders_id_seq TO app_user;

-- Row-Level Security
ALTER TABLE sensitive_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_policy ON sensitive_data
    FOR ALL TO app_role
    USING (user_id = current_setting('app.current_user_id')::BIGINT);
```

- Use **parameterized queries** exclusively — never interpolate user input into SQL.
- Never store passwords in plain text — use `pgcrypto`: `crypt($password, gen_salt('bf'))`.
- Use SSL connections to the server: `psql "sslmode=require host=31.97.217.73 ..."`

---

## Common Anti-Patterns

| Anti-pattern | Fix |
|---|---|
| `SELECT *` in production queries | Select only needed columns |
| OFFSET pagination on large tables | Cursor-based pagination |
| Querying `data->>'field'` without index | Use `@>` containment with GIN index |
| `TIMESTAMP` (no timezone) | `TIMESTAMPTZ` |
| `VARCHAR(n)` | `TEXT` with `CHECK (LENGTH(col) <= n)` |
| `SERIAL` / `BIGSERIAL` | `BIGINT GENERATED ALWAYS AS IDENTITY` |
| No index on FK columns | `CREATE INDEX ON child(parent_id)` |
| `UPDATE` without `WHERE` | Always filter; use transactions |

---

## Safe Schema Changes

```sql
-- Test DDL in a transaction (rollback if wrong)
BEGIN;
ALTER TABLE users ADD COLUMN phone TEXT;
-- inspect...
ROLLBACK; -- or COMMIT

-- Non-blocking index creation
CREATE INDEX CONCURRENTLY ON users (phone);

-- Add NOT NULL with a default (avoids full table rewrite in PG11+)
ALTER TABLE users ADD COLUMN verified BOOLEAN NOT NULL DEFAULT false;
```

---

## Useful Extensions

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;    -- password hashing, UUIDs
CREATE EXTENSION IF NOT EXISTS pg_trgm;     -- fuzzy text search
CREATE EXTENSION IF NOT EXISTS uuid-ossp;   -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS unaccent;    -- accent-insensitive search
CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- query stats (add to postgresql.conf)
```
