# API Guide

## Interactive Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI schema: `http://localhost:8000/openapi.json`

The generated OpenAPI document is the authoritative source.

## Authentication

Protected endpoints expect:

```http
Authorization: Bearer <token>
```

Typical flow:

1. register a user when registration is enabled;
2. log in;
3. copy the access token;
4. send it as a Bearer token.

## Main API Domains

- health and service status;
- authentication and users;
- conversations;
- messages and chat;
- Ollama / LLM status;
- documents and retrieval;
- human reviews;
- tool discovery;
- metrics.

## Tool Discovery

```http
GET /api/v1/tools
GET /api/v1/tools/{tool_name}
```

Example:

```json
{
  "items": [
    {
      "name": "calculator",
      "description": "Safely evaluates basic mathematical expressions.",
      "version": "1.0.0",
      "requires_approval": false
    }
  ],
  "total": 1
}
```

## Chat Request

```json
{
  "conversation_id": "YOUR_CONVERSATION_UUID",
  "content": "What is the weather in Munich?"
}
```

The response may include:

- user message;
- assistant message;
- route;
- planner reasoning;
- provider;
- model;
- tool name;
- usage;
- review metadata.

## Human Review

Typical operations:

```text
GET    /api/v1/reviews
GET    /api/v1/reviews/{review_id}
POST   /api/v1/reviews/{review_id}/decision
POST   /api/v1/reviews/{review_id}/resume
```

## Error Model

| Code | Meaning |
|---|---|
| 200 | Successful operation |
| 201 | Resource created |
| 400 | Invalid operation |
| 401 | Missing or invalid authentication |
| 403 | Not authorized |
| 404 | Resource not found |
| 409 | State conflict |
| 422 | Validation failure |
| 500 | Unexpected error |
| 503 | Dependency unavailable |

## Request Tracing

Responses may expose:

```text
X-Request-ID
X-Process-Time-Ms
```
