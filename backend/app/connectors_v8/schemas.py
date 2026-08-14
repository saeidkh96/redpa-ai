from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

ConnectorKind = Literal["webhook", "slack_webhook", "github_dispatch", "n8n_webhook"]


class ConnectorCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    kind: ConnectorKind
    endpoint_url: AnyHttpUrl
    secret_env_var: str | None = Field(default=None, max_length=120)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConnectorRecord(BaseModel):
    id: UUID
    name: str
    kind: ConnectorKind
    endpoint_url: str
    secret_env_var: str | None
    enabled: bool
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ConnectorExecuteRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_granted: bool = False
    dry_run: bool = True


class ConnectorDelivery(BaseModel):
    id: UUID
    connector_id: UUID
    status: str
    attempt_count: int
    response_status: int | None = None
    error: str | None = None
    dry_run: bool
    created_at: datetime
    completed_at: datetime | None = None


class ConnectorExecuteResponse(BaseModel):
    connector: ConnectorRecord
    delivery: ConnectorDelivery
