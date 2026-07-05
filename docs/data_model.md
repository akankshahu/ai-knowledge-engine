# Data Model & pgvector Schema

This document defines the relational schema and vector storage patterns for the AI Knowledge Engine.

Goals:
- Fast, accurate semantic retrieval via `pgvector`.
- Provenance for chunk-level citations.
- Tenant isolation and idempotent ingestion.
- Support efficient indexing and re-indexing.

Embedding parameters (recommended):
- Dimension: 1536 (match provider) — store in `vector(1536)`.
- Normalization: store raw floats; compute cosine via `ivfflat`/`hnsw` helpers.

Tables (core)

1) `users`
- `id` UUID PK
- `email` TEXT UNIQUE
- `hashed_password` TEXT
- `tenant_id` UUID
- `role` TEXT
- `created_at` timestamptz

2) `documents`
- `id` UUID PK
- `tenant_id` UUID
- `user_id` UUID FK -> `users(id)`
- `name` TEXT
- `storage_path` TEXT (S3/MinIO)
- `mime` TEXT
- `pages` INT
- `status` TEXT (uploaded, processing, completed, failed)
- `uploaded_at` timestamptz
- `metadata` JSONB

3) `chunks`
- `id` UUID PK
- `document_id` UUID FK -> `documents(id)`
- `chunk_index` INT
- `text` TEXT
- `token_count` INT
- `offset_start` INT
- `offset_end` INT
- `page_number` INT NULLABLE
- `content_hash` TEXT (SHA256) — for dedupe
- `created_at` timestamptz

4) `vectors`
- `id` UUID PK (same as chunk id or separate PK referencing `chunks.id`)
- `chunk_id` UUID UNIQUE FK -> `chunks(id)`
- `embedding` vector(1536)
- `tenant_id` UUID
- `metadata` JSONB (score hints, source offsets)
- `inserted_at` timestamptz

Design notes:
- Use `chunk_id` FK for easy lookups: join `vectors` -> `chunks` -> `documents` for provenance.
- Consider co-locating `embedding` in the `chunks` table to avoid joins for small deployments.

Indexes & pgvector configuration

- Enable extension:
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

- Table `vectors` column:
  ```sql
  ALTER TABLE vectors
  ADD COLUMN embedding vector(1536);
  ```

- HNSW index (good default):
  ```sql
  CREATE INDEX ON vectors USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
  -- or for hnsw (pgvector >= v0.5.0 supports hnsw):
  CREATE INDEX ON vectors USING hnsw (embedding vector_l2_ops);
  ```

- Use `IVFFlat` when you need lower memory and are willing to train the index; use `HNSW` for high recall and easier maintenance.

- Add filtering indexes:
  ```sql
  CREATE INDEX ON vectors (tenant_id);
  CREATE INDEX ON chunks (document_id);
  CREATE INDEX ON documents (tenant_id);
  ```

Tenant isolation

- Option 1: Row-Level Security (RLS)
  - Add `tenant_id` to `documents`, `chunks`, `vectors`.
  - Enable RLS and policies that restrict access to `current_setting('app.tenant')` or via session role.

- Option 2: Schemas per tenant or DB per tenant (stronger isolation) — higher ops cost.

Idempotency & Upserts

- Use `content_hash` for chunks and `chunk_id` or hash uniqueness to avoid duplicates.
- Insert embedding upserts:
  ```sql
  INSERT INTO chunks (id, document_id, chunk_index, text, content_hash, token_count)
  VALUES (...) ON CONFLICT (content_hash) DO NOTHING;

  INSERT INTO vectors (chunk_id, embedding, tenant_id)
  VALUES (...) ON CONFLICT (chunk_id) DO UPDATE SET embedding = EXCLUDED.embedding, inserted_at = now();
  ```

Similarity queries (example, cosine similarity via normalized vectors)

- Compute embedding for query in app, then run:
  ```sql
  SELECT v.chunk_id, c.text, d.id as document_id, 1 - (v.embedding <#> query_embedding) AS similarity
  FROM vectors v
  JOIN chunks c ON c.id = v.chunk_id
  JOIN documents d ON d.id = c.document_id
  WHERE v.tenant_id = :tenant_id
  ORDER BY v.embedding <#> query_embedding
  LIMIT 10;
  ```
- `pgvector` operator `<#>` is distance; use appropriate operator for cosine or L2 depending on storage.

Storage & cleanup

- Keep original documents in S3/MinIO; keep pointers in `documents.storage_path`.
- Implement lifecycle jobs to delete old vectors or archive documents.

Operational considerations

- Batch embedding writes (e.g., 100–500 chunks) for throughput.
- Use a dedicated DB connection pool (pgbouncer) for many worker processes.
- Monitor `vectors` table size; consider partitioning by `tenant_id` or time.

Migration & example (alembic)

- Create alembic migration adding `vector` column and extension creation.

Security

- Encrypt DB at rest; use TLS for DB connections.
- Enforce RBAC and use `tenant_id` checks on all queries.

Next: I can generate SQL migration files (Alembic) and a SQLAlchemy ORM model mapping for `chunks`/`vectors`.