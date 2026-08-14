# RedPA AI V8 Azure Production Runbook

V8 adds a production deployment path without claiming that the repository is already live in Azure.

## Prerequisites

- Azure subscription and authenticated Azure CLI
- Pulumi CLI and a configured backend
- container images published to an accessible registry
- production secrets configured with Pulumi secret values

## Preview

```bash
cd infra/azure
python -m pip install -r requirements.txt
pulumi stack select prod
pulumi config set --secret redpa:postgresPassword '<value>'
pulumi config set --secret redpa:secretKey '<value>'
pulumi config set --secret redpa:apiKeyPepper '<value>'
pulumi preview
```

## Deploy

```bash
pulumi up
pulumi stack output backendUrl
pulumi stack output frontendUrl
```

After deployment, run the V8 load smoke against the exported backend URL and store the JSON output as release evidence.

```bash
python scripts/reliability/load_test.py \
  --base-url "$(pulumi stack output backendUrl)" \
  --requests 500 \
  --concurrency 25 \
  --output artifacts/azure-load-test-v8.json
```

A successful Pulumi configuration is deployment automation; only a completed `pulumi up` plus runtime checks count as a live deployment claim.
