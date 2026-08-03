from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


MemoryScope = Literal[
    "private",
    "shared",
    "workflow",
    "user",
]

MemoryKind = Literal[
    "fact",
    "preference",
    "summary",
    "observation",
    "decision",
    "result",
]


class MemoryCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    agent_id: str = Field(
        min_length=1,
        max_length=100,
    )
    content: str = Field(
        min_length=1,
        max_length=50_000,
    )
    scope: MemoryScope = "private"
    kind: MemoryKind = "observation"
    user_id: UUID | None = None
    workflow_id: UUID | None = None
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )
    embed: bool = True


class MemoryUpdate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    content: str | None = Field(
        default=None,
        min_length=1,
        max_length=50_000,
    )
    scope: MemoryScope | None = None
    kind: MemoryKind | None = None
    importance: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None
    reembed: bool = True


class MemoryRecord(BaseModel):
    id: UUID
    agent_id: str
    content: str
    scope: MemoryScope
    kind: MemoryKind
    user_id: UUID | None
    workflow_id: UUID | None
    importance: float
    metadata: dict[str, Any]
    is_active: bool
    embedding_status: str
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None


class MemorySearchRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    query: str = Field(
        min_length=1,
        max_length=10_000,
    )
    agent_id: str | None = Field(
        default=None,
        max_length=100,
    )
    user_id: UUID | None = None
    workflow_id: UUID | None = None
    scopes: list[MemoryScope] = Field(
        default_factory=lambda: [
            "private",
            "shared",
            "workflow",
            "user",
        ],
    )
    kinds: list[MemoryKind] = Field(
        default_factory=list,
    )
    limit: int = Field(
        default=8,
        ge=1,
        le=50,
    )
    min_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
    )
    include_shared: bool = True


class MemorySearchResult(BaseModel):
    memory: MemoryRecord
    score: float
    semantic_score: float
    importance_score: float
    recency_score: float


class SharedMemoryPublishRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    source_agent_id: str = Field(
        min_length=1,
        max_length=100,
    )
    content: str = Field(
        min_length=1,
        max_length=50_000,
    )
    kind: MemoryKind = "observation"
    user_id: UUID | None = None
    workflow_id: UUID | None = None
    importance: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )
    visible_to_agents: list[str] = Field(
        default_factory=list,
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class SharedMemoryContextRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    requesting_agent_id: str = Field(
        min_length=1,
        max_length=100,
    )
    query: str = Field(
        min_length=1,
        max_length=10_000,
    )
    user_id: UUID | None = None
    workflow_id: UUID | None = None
    limit: int = Field(
        default=8,
        ge=1,
        le=50,
    )
    min_score: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
    )
