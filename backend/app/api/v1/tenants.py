from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.tenants import (
    TenantCreateRequest,
    TenantMemberCreateRequest,
    TenantMemberResponse,
    TenantResponse,
)
from app.security.rbac import Permission
from app.services.authorization_service import (
    AuthorizationService,
    ForbiddenError,
)
from app.services.tenant_service import (
    TenantMembershipNotFoundError,
    TenantService,
)


router = APIRouter(
    prefix="/tenants",
    tags=["Tenants"],
)


@router.post(
    "",
    response_model=TenantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_tenant(
    request: TenantCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TenantResponse:
    tenant = await TenantService.create(
        session=session,
        user_id=current_user.id,
        name=request.name,
    )

    return TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        role="owner",
        created_at=tenant.created_at,
    )


@router.get(
    "",
    response_model=list[TenantResponse],
)
async def list_tenants(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[TenantResponse]:
    rows = await TenantService.list_for_user(
        session=session,
        user_id=current_user.id,
    )

    return [
        TenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            role=membership.role,
            created_at=tenant.created_at,
        )
        for tenant, membership in rows
    ]


@router.post(
    "/{tenant_id}/members",
    response_model=TenantMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    tenant_id: uuid.UUID,
    request: TenantMemberCreateRequest,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> TenantMemberResponse:
    try:
        await AuthorizationService.require(
            session=session,
            tenant_id=tenant_id,
            user_id=current_user.id,
            permission=Permission.MEMBER_WRITE,
        )
    except (ForbiddenError, TenantMembershipNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    membership = await TenantService.add_member(
        session=session,
        tenant_id=tenant_id,
        user_id=request.user_id,
        role=request.role,
    )

    return TenantMemberResponse(
        id=membership.id,
        tenant_id=membership.tenant_id,
        user_id=membership.user_id,
        role=membership.role,
        created_at=membership.created_at,
    )
