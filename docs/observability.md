# Observability & Testing

## Goals
- Track request volume, latency, and errors.
- Verify key API paths with automated tests.
- Keep the implementation lightweight for MVP and easy to swap for Prometheus/Grafana later.

## Metrics

### Exposed endpoint
- `GET /metrics` returns plain text metrics.
- Counters are collected in-memory for now.

### Current metric names
- `app_requests_total{path="..."}` — count of requests per path.
- `app_request_latency_seconds_total{path="..."}` — cumulative latency per path.

## Logging

- Use structured log lines for request handling, uploads, task starts, task completion, and failures.
- Include `request_id`, `tenant_id`, `document_id`, and status code where available.
- Prefer JSON logs in production so they can be indexed in Loki/ELK.

## Testing Strategy

### Unit tests
- Validate metrics collection.
- Validate response rendering from `/metrics`.
- Validate helper functions such as chunking and prompt construction.

### Integration tests
- `GET /` returns health payload.
- `GET /test-db` succeeds against a test DB.
- `POST /upload` creates a document record.
- `POST /chat` streams SSE output.

### End-to-end tests
- Upload a sample document.
- Wait for background processing.
- Query via chat and confirm streamed output.

## Load Testing

- Use Locust or k6.
- Scenarios:
  - Upload burst
  - Status polling
  - Chat query load
- Track P95 latency, error rates, and queue depth.

## CI Checks

- Run tests on every PR.
- Lint code and fail builds on import/runtime errors.
- Smoke test Docker Compose startup.

## Next
- Add Prometheus exporter and Grafana dashboard when moving beyond MVP.
