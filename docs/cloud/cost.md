# Azure Cost Guardrails

Cloud resources can incur real costs.

Phase 15 defaults are intentionally small:

- Container Apps min replicas: 1
- Container Apps max replicas: 2
- PostgreSQL SKU: Burstable `Standard_B1ms`
- PostgreSQL storage: 32 GB
- Log Analytics retention: 30 days
- ACR: Basic

Before deployment:

- run `pulumi preview`;
- review Azure regional pricing;
- deploy to a dedicated dev resource group;
- destroy temporary stacks when testing is complete;
- never run production-sized replicas for a portfolio demo without a reason.
