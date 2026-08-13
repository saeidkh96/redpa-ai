# Deployment Guide

## Local Docker Compose

```powershell
docker compose config
docker compose up -d --build
docker compose ps
```

## Core URLs

```text
API docs:     http://localhost:8000/docs
Health:       http://localhost:8000/api/v1/platform/health
Readiness:    http://localhost:8000/api/v1/platform/ready
Liveness:     http://localhost:8000/api/v1/platform/live
Metrics:      http://localhost:8000/api/v1/metrics
Grafana:      http://localhost:3000
Prometheus:   http://localhost:9090
Tempo:        http://localhost:3200
Qdrant:       http://localhost:6333
```

## Kubernetes

Validate:

```powershell
helm lint deploy/helm/redpa
```

Install:

```powershell
helm upgrade --install redpa deploy/helm/redpa `
  --namespace redpa `
  --create-namespace `
  --set secretEnv.DATABASE_URL="..." `
  --set secretEnv.SECRET_KEY="..." `
  --set secretEnv.API_KEY_PEPPER="..."
```

## Production Variables

```env
ENVIRONMENT=production
DEBUG=false
JSON_LOGS=true
EXPOSE_ERROR_DETAILS=false
REQUIRE_HTTPS=true
ALLOWED_HOSTS=redpa.example.com

DATABASE_URL=...
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333

SECRET_KEY=...
API_KEY_PEPPER=...

OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318

SLOW_REQUEST_THRESHOLD_MS=1000
SLOW_QUERY_THRESHOLD_MS=500
```
