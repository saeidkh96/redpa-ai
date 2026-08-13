# RBAC

Phase 16 introduces tenant-scoped RBAC.

Roles:

- owner
- admin
- operator
- reviewer
- viewer

Authorization is expressed through explicit permissions rather than scattered
role-name checks.

Examples:

- `review:decide`
- `policy:enforce`
- `model-gateway:invoke`
- `mcp:execute`
- `member:write`

The owner role receives all permissions. Other roles receive least-privilege
sets appropriate to their responsibilities.
