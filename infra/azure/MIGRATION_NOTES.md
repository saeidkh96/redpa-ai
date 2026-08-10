# Migration notes

This ZIP is intended to replace the existing `infra/azure` directory.

Before replacing:
```powershell
Copy-Item .\infrazure .\infrazure-backup -Recurse
```

Main changes:
- Log Analytics wired to Container Apps Environment.
- `environment_id` used for Container Apps.
- Managed identity added.
- ACR pull RBAC added.
- Key Vault secret references added.
- Background worker/scheduler, research agent and A2A coordinator added.
- Redis/Qdrant/model endpoints stay explicit external dependencies.

First run only:
```powershell
python -m compileall .
pulumi preview
```
