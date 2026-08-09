# Multi-tenancy

Phase 16 introduces explicit tenants and tenant memberships.

Core entities:

```text
Tenant
TenantMembership
```

Each membership binds:

```text
tenant_id + user_id + role
```

The initial implementation establishes tenant ownership, listing, membership
creation, and tenant-scope contracts.

Important architectural rule:

> A tenant-scoped resource must never be accessed only by user identity. The
> tenant context must also be validated.

Future phases can progressively add `tenant_id` to conversations, workflows,
documents, evaluations, audit events, and other resources.
