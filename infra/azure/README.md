# RedPA AI on Azure with Pulumi

This directory is the Phase 15 Azure reference architecture.

## Azure resources

The baseline provisions:

- Resource Group
- Azure Container Registry
- Azure Container Apps Environment
- Backend Container App
- Frontend Container App
- Spring Boot Policy Service Container App
- Azure Database for PostgreSQL Flexible Server
- Azure Key Vault
- Log Analytics Workspace

Redis, Qdrant, and model inference remain explicit external endpoints in this
reference stack. This avoids pretending that a development container is a
production-grade stateful Azure service.

## Prerequisites

- Azure CLI
- Pulumi CLI
- Python
- an Azure subscription
- Docker images published to a registry accessible by Azure

## Setup

```powershell
cd infra\azure
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

az login
pulumi login
pulumi stack init dev
pulumi config set azure-native:location westeurope
pulumi config set redpa:environment dev
pulumi config set --secret redpa:postgresPassword "<strong-password>"
```

Optional external service endpoints:

```powershell
pulumi config set --secret redpa:redisUrl "rediss://..."
pulumi config set --secret redpa:qdrantUrl "https://..."
pulumi config set --secret redpa:ollamaBaseUrl "https://..."
```

Preview:

```powershell
pulumi preview
```

Deploy:

```powershell
pulumi up
```

Destroy when no longer required:

```powershell
pulumi destroy
```

## Important

`pulumi up` creates billable Azure resources.

The Phase 15 verification script does not deploy cloud resources by default.
A real Azure preview is opt-in through `REDPA_RUN_AZURE_PREVIEW=1`.
