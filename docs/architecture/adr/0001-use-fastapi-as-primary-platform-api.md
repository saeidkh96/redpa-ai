# ADR-0001: FastAPI as Primary Platform API

Status: Accepted

## Context

RedPA requires async APIs, typed request validation, OpenAPI generation, and
tight integration with Python AI libraries.

## Decision

FastAPI remains the primary platform API.

## Consequences

- Python AI integration remains straightforward.
- API contracts are generated automatically.
- CPU-heavy or independently scalable responsibilities may be moved into
  separate services when justified.
