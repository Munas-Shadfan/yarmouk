"""
Database schema and initialization for the admin system.
Tables: admin_users, unanswered_questions, chat_analytics
"""

SCHEMA_SQL = """
-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base: pre-indexed chunks from all yu.edu.jo pages and PDFs
CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_url   TEXT NOT NULL,
    source_type  TEXT NOT NULL DEFAULT 'page',  -- 'page' or 'pdf'
    content      TEXT NOT NULL,
    embedding    vector(1536),                  -- OpenAI text-embedding-3-small
    indexed_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
    ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_knowledge_url
    ON knowledge_chunks (source_url);

-- Admin users table (OAuth2 / JWT auth)
CREATE TABLE IF NOT EXISTS admin_users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Questions the agent could not answer (flagged by the agent tool)
CREATE TABLE IF NOT EXISTS unanswered_questions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    question TEXT NOT NULL,
    thread_id TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT 'ar',
    admin_answer TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'answered', 'dismissed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    answered_at TIMESTAMPTZ
);

-- Simple chat analytics (one row per chat message)
CREATE TABLE IF NOT EXISTS chat_analytics (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id TEXT NOT NULL,
    user_query TEXT NOT NULL,
    response_length INT NOT NULL DEFAULT 0,
    tools_used TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_analytics_created ON chat_analytics (created_at);
CREATE INDEX IF NOT EXISTS idx_unanswered_status ON unanswered_questions (status);
"""


async def init_admin_schema(pool):
    """Run schema migration using an existing connection pool."""
    async with pool.connection() as conn:
        await conn.execute(SCHEMA_SQL)
