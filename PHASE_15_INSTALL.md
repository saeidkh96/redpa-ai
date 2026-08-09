# RedPA AI v3 — Phase 15 Complete

Phase 15 covers:

- 15.1 Azure architecture
- 15.2 Pulumi foundation
- 15.3 Azure Container Registry
- 15.4 Azure Container Apps
- 15.5 PostgreSQL + Key Vault
- 15.6 cloud observability
- 15.7 cloud security / OIDC
- 15.8 IaC CI and tests
- 15.9 final verification

## Install

Extract into the repository root.

```powershell
powershell -ExecutionPolicy Bypass -File .\APPLY_V3_PHASE_15.ps1
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASE_15.ps1
```

The verifier is deliberately safe: it does not create billable Azure
resources.

## Optional real Azure preview

First install the IaC dependencies:

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
cd ..\..
```

Then:

```powershell
$env:REDPA_RUN_AZURE_PREVIEW = "1"
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASE_15.ps1
```

Only run `pulumi up` when you intentionally want to create Azure resources.
