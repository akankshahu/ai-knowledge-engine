# Components Design — AI Knowledge Engine

Overview: high-level responsibilities for each system component.

- Frontend (Next.js + TypeScript + Tailwind + shadcn/ui):
  - File upload UI with drag-and-drop, progress, and resumable uploads.
  - Document list, processing status, and streaming chat interface.
  - Authentication flows and role-based UI elements.

- API Gateway (FastAPI + Pydantic):
  - REST and streaming endpoints for uploads, status, document metadata, and chat.
  - Input validation, rate limiting, and centralized auth enforcement.
  - Correlation IDs and request tracing headers.

- Background Workers (Celery + Redis or FastAPI BackgroundTasks for MVP):
  - Asynchronous ingestion pipeline: extract -> normalize -> chunk -> embed -> store.
  - Task orchestration, retries, idempotency, and DLQ handling.
  - Periodic re-indexing and cleanup jobs.

- Vector Database (Postgres + pgvector):
  - Store chunk text, provenance metadata, and embedding vectors.
  - Use HNSW or IVFFlat indexes for ANN searches.
  - Row-level security (RLS) or tenant partitioning for isolation.

- Object Storage (S3 or MinIO):
  - Source file storage for uploaded documents and extracted assets.
  - Lifecycle rules for retention and archival.

- Models & Inference (Cloud-hosted or Self-hosted LLMs):
  - Embedding provider (batchable, low-latency) and generation model (streaming-capable).
  - Routing rules for cost/quality (fast small model vs. high-quality model).

- Auth & IAM:
  - OAuth2 / JWT, refresh tokens, RBAC for admin vs. user operations.
  - Audit logs for data access and model calls.

- Observability & Ops:
  - Prometheus metrics, Grafana dashboards, structured logs, and distributed tracing.
  - CI/CD pipelines, Helm charts / Docker Compose for environments.

- Security & Compliance:
  - TLS, at-rest encryption, PII redaction options, and audit trails.
  - Data residency and tenant isolation patterns.

Notes:
- Keep ingestion idempotent and chunk-level to reduce retry blast radius.
- Batch embeddings and use caching to control cost.
- Prefer streaming APIs (SSE/WS) for chat UX and backpressure handling.
