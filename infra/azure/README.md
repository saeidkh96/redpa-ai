# RedPA AI — Azure Deployment Pack

Replacement for the current `infra/azure` baseline.

## Provisions
- Resource Group
- ACR
- User Assigned Managed Identity + AcrPull
- Key Vault + Key Vault Secrets User
- Log Analytics
- Container Apps Environment connected to Log Analytics
- PostgreSQL Flexible Server + `redpa_ai`
- Backend
- Frontend
- Spring Boot Policy Service
- Background Worker
- Background Scheduler
- Research Agent
- A2A Coordinator

## External by design
Redis, Qdrant, and Ollama/model inference remain configurable external endpoints. This avoids silently choosing expensive/stateful Azure replacements before the architecture is decided.

## Setup
```powershell
cd infrazure
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
az login
pulumi login
pulumi stack init dev
pulumi config set azure-native:location westeurope
pulumi config set redpa:environment dev
pulumi config set redpa:location westeurope
pulumi config set redpa:projectName redpa
pulumi config set --secret redpa:postgresPassword "<strong-password>"
pulumi config set --secret redpa:secretKey "<long-random-secret>"
pulumi config set --secret redpa:apiKeyPepper "<long-random-pepper>"
python -m compileall .
pulumi preview
```

Do not run `pulumi up` until preview is clean.

## Important production note
The included PostgreSQL baseline enables public network access. Before real production traffic, move PostgreSQL and Container Apps to private/VNet-integrated networking and disable public database access.
