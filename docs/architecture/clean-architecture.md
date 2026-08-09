# Clean Architecture

## Dependency Rule

Dependencies should point inward:

```text
API / Frameworks
      |
      v
Application Services
      |
      v
Domain
```

Infrastructure implements interfaces owned by inner layers.

## Rules

1. Domain code must not depend on FastAPI.
2. Domain code must not depend on SQLAlchemy sessions.
3. Application services may orchestrate domain objects and ports.
4. API routers translate HTTP requests into application calls.
5. Infrastructure adapters implement persistence or remote-service concerns.
6. Cross-context communication should use explicit interfaces/contracts.
7. Framework models should not become the only representation of domain rules.
8. External integrations must be replaceable behind adapters.

## Existing RedPA Examples

Good existing architectural patterns include:

- Model Gateway provider abstractions;
- Adapter / Factory / Registry patterns;
- Policy Service domain/application/infrastructure split;
- Guardrail contracts;
- service-layer workflow orchestration.

## Evolution Rule

Phase 14 does not perform a large risky rewrite. Instead it creates explicit
architecture boundaries and verification so future code follows the intended
structure.
