from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.security.rbac import Role


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    role: Role
    created_at: datetime


class TenantMemberCreateRequest(BaseModel):
    user_id: uuid.UUID
    role: Role


class TenantMemberResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: Role
    created_at: datetime
