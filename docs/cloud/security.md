# Azure Security Baseline

Phase 15 establishes these cloud security expectations:

1. use Pulumi secret configuration for sensitive values;
2. use Azure Key Vault as the cloud secret-management boundary;
3. keep ACR admin credentials disabled;
4. prefer workload identity / OIDC for CI instead of long-lived credentials;
5. use separate stacks for dev, staging, and production;
6. do not expose PostgreSQL directly unless explicitly required;
7. use TLS endpoints for external Redis, Qdrant, and model services;
8. run `pulumi preview` in CI before infrastructure changes;
9. require human approval for production deployment;
10. treat resource deletion as a controlled change.

The included stack is a reference baseline, not a claim of production
certification.
