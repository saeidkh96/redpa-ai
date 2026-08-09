from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: str


class TenantScopeError(PermissionError):
    pass


def assert_same_tenant(
    *,
    context: TenantContext,
    resource_tenant_id: uuid.UUID,
) -> None:
    if context.tenant_id != resource_tenant_id:
        raise TenantScopeError(
            "Cross-tenant resource access is not allowed.",
        )
