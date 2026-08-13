# RedPA AI v3.0.0 Release Notes

RedPA AI v3 expands the platform from an agentic runtime into a broader
enterprise AI engineering reference platform.

## Major additions

### Evaluation
- evaluation engine;
- model/agent metrics;
- benchmark runs;
- evaluation dashboard and telemetry.

### Model Gateway
- provider-neutral model contract;
- adapters, registry, factory, routing;
- retry, timeout, fallback, circuit breaker;
- Model Gateway Control Center.

### Governance
- Java 21 / Spring Boot Policy Service;
- ALLOW / REVIEW / DENY;
- policy-to-Human-Review bridge;
- policy audit and metrics;
- Policy Control Center;
- Cucumber BDD.

### Architecture
- DDD bounded contexts;
- Clean Architecture rules;
- ADRs;
- C4;
- arc42.

### Cloud
- Azure reference architecture;
- Pulumi Azure Native IaC;
- Container Apps;
- PostgreSQL Flexible Server;
- Key Vault;
- ACR;
- cloud CI/security baseline.

### Identity and tenancy
- tenant domain;
- membership model;
- RBAC permissions;
- tenant-isolation contracts;
- OAuth Authorization Code + PKCE foundation;
- Access & Tenancy Control Center.

### Event-driven integration
- transactional outbox;
- Redis Streams event bus;
- durable publication attempts;
- Event & Integration Control Center.

### Security
- production configuration guard;
- threat model;
- secret scan;
- CI dependency audit;
- Kubernetes network-policy baseline.

## Important limitations

- Azure resources are defined as IaC but are not claimed as deployed unless
  `pulumi up` has actually been run.
- OAuth token exchange/account linking remains intentionally incomplete until
  real provider credentials and server-side state/verifier persistence are
  configured.
- Production deployment still requires environment-specific security review.
