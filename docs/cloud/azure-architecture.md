# Azure Reference Architecture

## Deployment view

```mermaid
flowchart TB
    User[User / Operator]
    Frontend[Azure Container App - Frontend]
    Backend[Azure Container App - FastAPI]
    Policy[Azure Container App - Spring Boot Policy]
    PG[(Azure PostgreSQL Flexible Server)]
    Redis[(External / Managed Redis)]
    Qdrant[(External / Managed Qdrant)]
    LLM[Model Provider Endpoint]
    KV[Azure Key Vault]
    ACR[Azure Container Registry]
    Logs[Log Analytics]

    User --> Frontend
    Frontend --> Backend
    Backend --> Policy
    Backend --> PG
    Backend --> Redis
    Backend --> Qdrant
    Backend --> LLM
    ACR --> Frontend
    ACR --> Backend
    ACR --> Policy
    Backend --> Logs
    Policy --> Logs
    KV -. secrets .-> Backend
```

## Design principles

- stateless application components run as Container Apps;
- PostgreSQL uses Azure Database for PostgreSQL Flexible Server;
- secrets are represented as Pulumi secrets and Key Vault is part of the
  target architecture;
- stateful vector/cache systems remain explicit service dependencies;
- cloud deployment is defined as code and reviewed through preview before
  deployment;
- dev and production use separate Pulumi stacks.
