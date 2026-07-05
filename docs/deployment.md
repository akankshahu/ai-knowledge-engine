# Scalability & Deployment

## Docker Compose (Local Dev & Single-Node Prod)

The `docker-compose.yml` orchestrates all services locally:
- **Postgres + pgvector:** Database with vector indexing.
- **Redis:** Broker for Celery and caching.
- **API:** FastAPI server (port 8000).
- **Celery Worker:** Background task processor.

### Quick Start

```bash
docker-compose up -d
```

Services are health-checked and auto-restart. Logs:

```bash
docker-compose logs -f api
docker-compose logs -f celery_worker
```

Teardown:

```bash
docker-compose down -v
```

## Kubernetes (Multi-Node, High Availability)

For production, use Helm charts or raw manifests:

### Example: API Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: knowledge-api
  template:
    metadata:
      labels:
        app: knowledge-api
    spec:
      containers:
      - name: api
        image: knowledge-engine/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: CELERY_BROKER
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

### Autoscaling (HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: knowledge-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: knowledge-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Postgres Connection Pooling (pgBouncer)

For many workers, use pgBouncer to reduce DB connection overhead:

```ini
[databases]
knowledge_engine = host=postgres port=5432 dbname=knowledge_engine

[pgbouncer]
listen_port = 6432
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
```

In services, set `DATABASE_URL="postgresql://user:pass@pgbouncer:6432/knowledge_engine"`.

## Secrets Management (Vault / K8s Secrets)

Store sensitive data (API keys, DB credentials):

```bash
# Kubernetes Secret
kubectl create secret generic db-secret \
  --from-literal=url="postgresql://user:pass@postgres:5432/knowledge_engine" \
  --from-literal=api-key="sk-..."
```

Reference in deployments:

```yaml
env:
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: url
```

## Load Balancing & Ingress

Use Nginx or cloud LB to route traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: knowledge-ingress
spec:
  ingressClassName: nginx
  rules:
  - host: api.knowledge.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: knowledge-api
            port:
              number: 8000
  tls:
  - hosts:
    - api.knowledge.com
    secretName: tls-cert
```

## CI/CD Pipeline

Example GitHub Actions workflow:

```yaml
name: Build & Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: docker build -t knowledge-engine:${{ github.sha }} -f backend/Dockerfile .
    - name: Push to registry
      run: docker push knowledge-engine:${{ github.sha }}
    - name: Deploy to k8s
      run: |
        kubectl set image deployment/knowledge-api \
          api=knowledge-engine:${{ github.sha }} \
          --namespace production
```

## Monitoring & Health

- **Liveness probe:** Check `/` endpoint.
- **Readiness probe:** Check `/test-db` endpoint.
- **Metrics:** Expose `/metrics` via Prometheus.

## Cost Optimization

- Use spot instances for workers (non-critical).
- Auto-scale down during off-peak.
- Cache frequently accessed embeddings in Redis.
- Batch embedding calls.
- Archive old documents to S3 Glacier.

## Summary

- **Dev:** Docker Compose for fast iteration.
- **Prod:** Kubernetes with HPA, pgBouncer, Vault, and monitoring.
- **Scaling:** Stateless API pods + pooled DB connections + distributed cache.
