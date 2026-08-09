from __future__ import annotations

import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant, TenantMembership
from app.security.rbac import Role


class TenantNotFoundError(LookupError):
    pass


class TenantMembershipNotFoundError(LookupError):
    pass


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("Tenant name must contain letters or numbers.")
    return slug[:120]


class TenantService:
    @staticmethod
    async def create(
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
        name: str,
        commit: bool = True,
    ) -> Tenant:
        tenant = Tenant(
            name=name.strip(),
            slug=slugify(name),
            created_by=user_id,
        )
        session.add(tenant)
        await session.flush()

        membership = TenantMembership(
            tenant_id=tenant.id,
            user_id=user_id,
            role=Role.OWNER.value,
        )
        session.add(membership)

        if commit:
            await session.commit()
            await session.refresh(tenant)

        return tenant

    @staticmethod
    async def list_for_user(
        *,
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[tuple[Tenant, TenantMembership]]:
        result = await session.execute(
            select(Tenant, TenantMembership)
            .join(
                TenantMembership,
                TenantMembership.tenant_id == Tenant.id,
            )
            .where(TenantMembership.user_id == user_id)
            .order_by(Tenant.created_at.asc())
        )
        return list(result.all())

    @staticmethod
    async def get_membership(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TenantMembership:
        result = await session.execute(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.user_id == user_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise TenantMembershipNotFoundError(
                "User is not a member of the tenant.",
            )
        return membership

    @staticmethod
    async def add_member(
        *,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: Role,
        commit: bool = True,
    ) -> TenantMembership:
        membership = TenantMembership(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role.value,
        )
        session.add(membership)

        if commit:
            await session.commit()
            await session.refresh(membership)

        return membership
