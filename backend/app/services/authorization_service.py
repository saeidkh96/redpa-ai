from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.security.rbac import Permission, Role, authorize
from app.services.tenant_service import TenantService


class ForbiddenError(PermissionError):
    pass


class AuthorizationService:
    @staticmethod
    async def require(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        permission: Permission,
    ) -> Role:
        membership = await TenantService.get_membership(
            session=session,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        role = Role(membership.role)
        decision = authorize(role, permission)

        if not decision.allowed:
            raise ForbiddenError(
                f"Role {role.value!r} lacks permission "
                f"{permission.value!r}.",
            )

        return role
