# Azure Deployment Runbook

## 1. Validate locally

```powershell
powershell -ExecutionPolicy Bypass -File .\VERIFY_V3_PHASE_15.ps1
```

## 2. Authenticate

```powershell
az login
az account show
pulumi login
```

## 3. Create stack

```powershell
cd infra\azure
pulumi stack init dev
pulumi config set azure-native:location westeurope
pulumi config set redpa:environment dev
pulumi config set --secret redpa:postgresPassword "<strong-password>"
```

## 4. Preview

```powershell
pulumi preview
```

## 5. Deploy

```powershell
pulumi up
```

## 6. Inspect outputs

```powershell
pulumi stack output
```

## 7. Destroy dev stack when finished

```powershell
pulumi destroy
```
