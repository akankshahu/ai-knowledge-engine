# Security & Compliance

## Authentication & Authorization

### JWT Tokens

- **Issuance:** `/login` endpoint returns JWT with `sub` (user_id) and `tenant_id`.
- **Storage:** Client stores in secure httpOnly cookie (frontend).
- **Validation:** Every request includes token in `Authorization: Bearer <token>` header.
- **Expiry:** 30 minutes default; refresh token can extend session.

Example payload:
```json
{
  "sub": "user-123",
  "tenant_id": "tenant-456",
  "exp": 1720...
}
```

### Role-Based Access Control (RBAC)

- **Roles:** `admin`, `user`, `viewer`.
- **Permissions:** Enforce at endpoint level using middleware.
  - `admin`: full access (manage users, documents, settings).
  - `user`: upload, chat, view own documents.
  - `viewer`: read-only access.

### Password Security

- **Hashing:** bcrypt with salt (never store plaintext).
- **Requirements:** Min 12 chars, uppercase, lowercase, numbers, special chars (enforce on signup).

## Tenant Isolation

### Row-Level Security (RLS)

- Add `tenant_id` to all user-facing tables.
- Enable Postgres RLS policies:

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON documents
  USING (tenant_id = current_setting('app.tenant_id'));
```

- Set tenant context per request:
  ```python
  db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, false)"))
  ```

### Multi-Tenant Enforcement

- Every query filters by `tenant_id`.
- No cross-tenant data access.
- Example:
  ```python
  docs = db.query(models.Document).filter(
      models.Document.tenant_id == current_tenant_id
  ).all()
  ```

## Encryption

### In Transit (TLS/SSL)

- All API traffic over HTTPS (cert via Let's Encrypt or managed service).
- Postgres connection pool uses SSL (`sslmode=require`).
- Redis secured via AUTH and network ACLs.

### At Rest

- **Database:** Transparent Data Encryption (TDE) in Postgres (pgcrypto extension).
  ```sql
  CREATE EXTENSION pgcrypto;
  CREATE TABLE sensitive_data (
    id UUID PRIMARY KEY,
    data BYTEA
  );
  INSERT INTO sensitive_data VALUES (gen_random_uuid(), pgp_sym_encrypt('secret', 'password'));
  ```
- **Object Storage (S3):** Enable SSE-S3 or SSE-KMS.
- **Secrets (API keys):** Use HashiCorp Vault or AWS Secrets Manager, never commit to git.

## PII Handling & Data Redaction

### Detection

- Use regex or NLP models to identify PII patterns (SSN, email, phone, credit card).

### Redaction

- On ingestion:
  ```python
  chunk_text = redact_pii(chunk_text)  # Replace with [REDACTED]
  ```
- Optional flag per tenant: redact_sensitive=True.

### Audit Trail

- Log all PII access and redaction events.

## Audit Logging & Compliance

### Audit Events

- **User login/logout:** timestamp, user_id, tenant_id, IP.
- **Document upload/delete:** who, what, when, size, hash.
- **Query execution:** user, query text, results returned, latency, cost.
- **Access to sensitive docs:** document_id, user, timestamp.

### Log Storage

- Append-only table or immutable log storage (S3, CloudWatch, Splunk).
- Retention policy: 7 years for financial, 1 year for operational.

Example audit entry:
```json
{
  "timestamp": "2026-07-05T10:30:00Z",
  "user_id": "user-123",
  "tenant_id": "tenant-456",
  "action": "UPLOAD",
  "resource": "document-789",
  "details": {
    "filename": "report.pdf",
    "size_bytes": 2048000,
    "hash": "sha256:abc123..."
  }
}
```

## Secrets Management

### API Keys

- Generate using strong random generator (`secrets.token_urlsafe`).
- Store hashed in DB (`argon2id`), never plaintext.
- Rotate regularly (quarterly).

### Environment Variables

- Never commit `.env` to git.
- Use GitHub Secrets for CI/CD.
- Use Vault or cloud secret managers for production.

Example `.env`:
```
SECRET_KEY=...
DATABASE_URL=postgresql://...
LLM_API_KEY=sk-...
```

## GDPR & Compliance

### Data Subject Rights

- **Access:** User can request export of their data.
- **Deletion:** User can request account and all data deletion.
- **Portability:** Export data in standardized format (JSON/CSV).

### Data Retention

- User deletions: soft delete + hard delete after 30 days.
- Audit logs: retain per legal hold and jurisdiction.
- Backups: follow same retention policy.

### Data Residency

- Allow tenant to choose region (EU, US, APAC).
- Ensure data stays within region (no cross-region replication without consent).

## Threat Modeling & Mitigation

| Threat | Mitigation |
|--------|-----------|
| SQL Injection | Use parameterized queries (SQLAlchemy ORM) |
| XSS (Frontend) | Sanitize user input, use CSP headers |
| CSRF | SameSite=Strict cookies, CSRF tokens |
| Rate Limiting | Implement rate limiter (FastAPI, Redis-backed) |
| DDoS | Use cloud WAF (CloudFlare, AWS WAF) |
| Broken Auth | Strong JWT, HTTPS, secure cookie storage |
| Privilege Escalation | RBAC, tenant isolation, audit logging |

## Security Checklist

- [ ] TLS/HTTPS on all endpoints
- [ ] Password hashing (bcrypt/argon2)
- [ ] JWT validation on every request
- [ ] Tenant isolation + RLS enabled
- [ ] Secrets in Vault (not git)
- [ ] Audit logging to append-only store
- [ ] Rate limiting + DDoS protection
- [ ] Regular security updates (dependencies)
- [ ] Incident response plan
- [ ] Annual penetration testing

## Next: Implement in `auth.py`, `audit.py`, and middleware.
