"""
Run once to initialize the database schema.
Usage: python scripts/init_db.py
"""
import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

RAW_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")

SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          UUID PRIMARY KEY,
    file_name   TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    file_size   INTEGER NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    chunk_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS chunks (
    id           UUID PRIMARY KEY,
    document_id  UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    text         TEXT NOT NULL,
    embedding    VECTOR(1024),
    file_name    TEXT NOT NULL,
    file_type    TEXT NOT NULL,
    -- source location (nullable depending on file type)
    page_number  INTEGER,
    slide_number INTEGER,
    sheet_name   TEXT,
    row_start    INTEGER,
    row_end      INTEGER,
    chunk_index  INTEGER NOT NULL DEFAULT 0
);

-- IVFFlat index for fast approximate nearest neighbor search
-- Lists: sqrt(num_chunks) is a good rule of thumb; 100 works for < 100k chunks
CREATE INDEX IF NOT EXISTS chunks_embedding_idx
    ON chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS chunks_document_id_idx ON chunks (document_id);
"""
async def main():
    print(f"Connecting to: {RAW_URL[:40]}...")
    conn = await asyncpg.connect(RAW_URL)
    await conn.execute(SQL)
    await conn.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    asyncio.run(main())