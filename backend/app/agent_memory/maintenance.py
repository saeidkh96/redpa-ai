from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID

from app.agent_memory.repository import AgentMemoryRepository
from app.agent_memory.schemas import (
    MemoryCreate,
    MemoryRecord,
    MemoryUpdate,
)
from app.agent_memory.semantic import MemorySemanticStore


class AgentMemoryMaintenanceService:
    @classmethod
    async def summarize(
        cls,
        *,
        agent_id: str,
        memory_ids: list[UUID],
        workflow_id: UUID | None = None,
        user_id: UUID | None = None,
        importance: float = 0.8,
    ) -> MemoryRecord:
        memories = [
            await AgentMemoryRepository.get(memory_id)
            for memory_id in memory_ids
        ]

        if not memories:
            raise ValueError(
                "At least one memory is required for summarization."
            )

        summary = cls._build_summary(memories)

        result = await AgentMemoryRepository.create(
            MemoryCreate(
                agent_id=agent_id,
                content=summary,
                scope=(
                    "workflow"
                    if workflow_id is not None
                    else "user"
                    if user_id is not None
                    else "private"
                ),
                kind="summary",
                user_id=user_id,
                workflow_id=workflow_id,
                importance=importance,
                metadata={
                    "source_memory_ids": [
                        str(memory.id)
                        for memory in memories
                    ],
                    "source_count": len(memories),
                    "compression": "extractive",
                },
                embed=True,
            )
        )

        await MemorySemanticStore.upsert(result)

        for memory in memories:
            await AgentMemoryRepository.update(
                memory.id,
                MemoryUpdate(
                    metadata={
                        **memory.metadata,
                        "summarized_into": str(result.id),
                    },
                    is_active=False,
                    reembed=False,
                ),
            )

        return await AgentMemoryRepository.get(result.id)

    @classmethod
    async def deduplicate(
        cls,
        *,
        agent_id: str | None = None,
        user_id: UUID | None = None,
        workflow_id: UUID | None = None,
        similarity_threshold: float = 0.92,
        limit: int = 500,
    ) -> dict[str, int]:
        memories = await AgentMemoryRepository.list(
            agent_id=agent_id,
            user_id=user_id,
            workflow_id=workflow_id,
            active_only=True,
            limit=limit,
        )

        groups: dict[str, list[MemoryRecord]] = defaultdict(list)

        for memory in memories:
            groups[
                cls._fingerprint(memory.content)
            ].append(memory)

        duplicate_groups = 0
        deactivated = 0

        for group in groups.values():
            if len(group) < 2:
                continue

            duplicate_groups += 1

            group.sort(
                key=lambda item: (
                    -item.importance,
                    item.created_at,
                )
            )

            canonical = group[0]

            for duplicate in group[1:]:
                similarity = cls._token_similarity(
                    canonical.content,
                    duplicate.content,
                )

                if similarity < similarity_threshold:
                    continue

                await AgentMemoryRepository.update(
                    duplicate.id,
                    MemoryUpdate(
                        metadata={
                            **duplicate.metadata,
                            "duplicate_of": str(canonical.id),
                            "similarity": round(similarity, 4),
                        },
                        is_active=False,
                        reembed=False,
                    ),
                )

                deactivated += 1

        return {
            "duplicate_groups": duplicate_groups,
            "deactivated_memories": deactivated,
        }

    @classmethod
    async def apply_retention(
        cls,
        *,
        max_age_days: int = 180,
        minimum_importance: float = 0.35,
        preserve_kinds: set[str] | None = None,
        limit: int = 1000,
    ) -> dict[str, int]:
        preserve_kinds = preserve_kinds or {
            "preference",
            "decision",
            "summary",
        }

        memories = await AgentMemoryRepository.list(
            active_only=True,
            limit=limit,
        )

        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(days=max_age_days)
        )

        deactivated = 0
        preserved = 0

        for memory in memories:
            if memory.kind in preserve_kinds:
                preserved += 1
                continue

            if (
                memory.created_at < cutoff
                and memory.importance < minimum_importance
            ):
                await AgentMemoryRepository.update(
                    memory.id,
                    MemoryUpdate(
                        metadata={
                            **memory.metadata,
                            "retention_deactivated_at": (
                                datetime.now(
                                    timezone.utc,
                                ).isoformat()
                            ),
                            "retention_policy": {
                                "max_age_days": max_age_days,
                                "minimum_importance": minimum_importance,
                            },
                        },
                        is_active=False,
                        reembed=False,
                    ),
                )
                deactivated += 1

        return {
            "deactivated_memories": deactivated,
            "preserved_memories": preserved,
        }

    @staticmethod
    def _build_summary(
        memories: Iterable[MemoryRecord],
    ) -> str:
        lines = [
            "Agent memory summary:",
            "",
        ]

        for index, memory in enumerate(
            memories,
            start=1,
        ):
            content = re.sub(
                r"\s+",
                " ",
                memory.content,
            ).strip()

            lines.append(
                f"{index}. [{memory.kind}] {content[:500]}"
            )

        return "\n".join(lines)

    @staticmethod
    def _fingerprint(
        content: str,
    ) -> str:
        normalized = re.sub(
            r"\s+",
            " ",
            str(content or "").casefold(),
        ).strip()

        return hashlib.sha256(
            normalized.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _token_similarity(
        left: str,
        right: str,
    ) -> float:
        left_tokens = set(
            re.findall(
                r"[a-z0-9_]{2,}",
                left.casefold(),
            )
        )
        right_tokens = set(
            re.findall(
                r"[a-z0-9_]{2,}",
                right.casefold(),
            )
        )

        if not left_tokens and not right_tokens:
            return 1.0

        union = left_tokens | right_tokens

        if not union:
            return 0.0

        return len(
            left_tokens & right_tokens
        ) / len(union)
