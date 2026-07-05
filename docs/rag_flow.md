# Retrieval & RAG Flow

## Overview

The RAG (Retrieval-Augmented Generation) pipeline retrieves relevant document chunks from the vector database and uses them as context for an LLM to generate accurate, grounded responses.

## Retriever Strategy

### Semantic Similarity Search

1. **Query embedding:** Convert user query to embedding vector (same dimensions as stored vectors).
2. **ANN search:** Use pgvector `<#>` (distance operator) or cosine similarity to find top-k closest chunks.
3. **Filtering:** Filter by `tenant_id` and optionally document_id.

Query example (SQL):
```sql
SELECT v.chunk_id, c.text, d.id as document_id, d.name
FROM vectors v
JOIN chunks c ON c.id = v.chunk_id
JOIN documents d ON d.id = c.document_id
WHERE v.tenant_id = :tenant_id
ORDER BY v.embedding <#> :query_embedding
LIMIT 10;
```

### Hybrid Retrieval (Optional Advanced)

Combine semantic + keyword (BM25):
- Score each result: `alpha * semantic_score + (1 - alpha) * bm25_score`
- Better precision for rare terms and technical queries.

### Re-ranking (Optional)

Use a lightweight cross-encoder model to re-rank top-k results before passing to LLM.

## Prompt Construction

### System Prompt
```
You are a helpful assistant answering questions about internal documents.
Use only the provided context and be concise.
If you cannot answer from the context, say so.
```

### Context Formatting
```
Context:
---
[Document: {doc_name}]
{chunk_text}

[Document: {doc_name}]
{chunk_text}
---

User Question: {query}
```

## Context Windowing

- **Token budget:** Reserve tokens for query + response; allocate remainder to context.
- **Strategy:** Select longest/highest-relevance chunks first, up to budget.
- **Example:** Model context 4096 tokens; reserve 500 for query/response; ~3000 for context ≈ 5–10 chunks.

## Streaming Responses

- **SSE (Server-Sent Events):** FastAPI `StreamingResponse` with `text/event-stream`.
- **Token-level streaming:** Stream LLM output token-by-token to provide immediate feedback.
- **Backpressure:** Slow client reads naturally slow LLM processing.

## Implementation Patterns

### 1. Embedding Generation (Query Time)
- Cache frequent query embeddings (Redis).
- Use same embedding provider as ingestion.

### 2. Batch Optimization
- Group multiple queries into single embedding call if async.
- Useful for analytics/bulk operations.

### 3. Fallback & Error Handling
- If semantic search returns no results, return empty context and let LLM say "no information".
- If LLM fails, return cached/default response or inform user.

## Cost Control

- Limit context chunks to reduce token usage.
- Use cheaper embedding model for queries; expensive model for documents if needed.
- Cache embeddings and responses aggressively.

## Security & Privacy

- Enforce tenant_id filtering on all retrieval queries.
- Mask sensitive data (PII) in chunks before retrieval or in prompt.
- Audit all LLM calls: who, what context, cost.

Next: Implementation in `retriever.py`, `llm.py`, and `/chat` endpoint.
