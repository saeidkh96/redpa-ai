# API Guide

## Interactive Documentation

After starting the backend:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

The generated OpenAPI document is the authoritative source because endpoint paths and schemas can change during development.

## Authentication

Protected endpoints expect a JWT access token:

```http
Authorization: Bearer <token>
```

A typical client flow is:

1. register a user if registration is enabled;
2. log in using the OAuth2-compatible login endpoint;
3. copy the returned access token;
4. send it as a Bearer token.

## Main API Domains

Based on the current application structure, the API is organized around:

- health and service status;
- authentication and users;
- conversations;
- messages and chat;
- Ollama / LLM status;
- planner and orchestrator execution;
- document upload and retrieval;
- human-review decisions;
- monitoring metrics.

## Example Health Request

```bash
curl http://localhost:8000/api/v1/health
```

## Example Authenticated Request

```bash
curl \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/conversations
```

## Error Model

Clients should expect standard HTTP status codes:

| Code | Meaning |
|---|---|
| 200 | Successful read or operation |
| 201 | Resource created |
| 400 | Invalid operation |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | State conflict |
| 422 | Request validation failed |
| 500 | Unexpected server error |
| 503 | External dependency unavailable |

## Request Tracing

Responses may expose:

```text
X-Request-ID
X-Process-Time-Ms
```

Log the request ID on the client side when reporting backend failures.

## Streaming

Streaming chat endpoints should be consumed incrementally rather than buffered until completion. The exact media type and event schema should be taken from Swagger/OpenAPI and the route implementation.

## Human Review

Human-review endpoints should enforce:

- ownership or reviewer authorization;
- valid state transitions;
- idempotent decision behavior;
- conflict responses when a review was already decided;
- audit-friendly storage of decisions and timestamps.
