# Security Policy

## Current Controls

- JWT authentication
- user-scoped resources
- deterministic approval gates
- safe calculator parsing without `eval`
- structured tool registry
- blocked local and private network targets
- environment-based secrets
- no arbitrary shell-execution tool

## Production Requirements

Before production deployment, add:

- managed secrets;
- HTTPS;
- strict CORS;
- rate limiting;
- fine-grained authorization;
- encrypted backups;
- centralized logs;
- dependency scanning;
- container scanning;
- audit retention.
