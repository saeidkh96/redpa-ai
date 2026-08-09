# RedPA AI v3 Threat Model

## Assets

- user identities and JWTs;
- tenant data;
- agent workflow state;
- prompts and retrieved knowledge;
- tool credentials;
- policy decisions;
- audit trails;
- model-provider credentials;
- infrastructure secrets.

## Trust Boundaries

```text
Browser
  -> FastAPI
      -> PostgreSQL / Redis / Qdrant
      -> MCP services
      -> Spring Boot Policy Service
      -> Model providers
      -> external integrations
```

## Main Threats

### Broken tenant isolation
Mitigation: explicit tenant membership and tenant-scope validation.

### Excessive tool privileges
Mitigation: RBAC, policy enforcement, Human Review, least privilege.

### Prompt-driven destructive action
Mitigation: tool boundary + Policy Engine `ALLOW / REVIEW / DENY`.

### Secret leakage
Mitigation: managed secrets, repository scanning, production configuration
checks, no real credentials in examples.

### Event loss
Mitigation: transactional outbox before Redis Streams publication.

### Event duplication
Mitigation: stable event IDs and idempotent consumers.

### Sensitive error leakage
Mitigation: `EXPOSE_ERROR_DETAILS=false` in production.

### Insecure transport
Mitigation: production HTTPS requirement and TLS external dependencies.

### Supply-chain compromise
Mitigation: CI dependency auditing, container scanning, locked release review.

## Residual Risk

RedPA remains a portfolio/open-source platform. Production use requires
organization-specific security review, penetration testing, secret management,
backup/restore validation, IAM design, network configuration, and incident
response.
