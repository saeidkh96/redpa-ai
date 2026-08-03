from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from app.a2a_remote.client import RemoteA2AClient
from app.a2a_remote.registry import RemoteAgentRecord


@dataclass(frozen=True, slots=True)
class SpecialistTarget:
    name: str
    base_url: str
    patterns: tuple[str, ...]


class CoordinatorSpecialistRouter:
    @classmethod
    def targets(cls) -> tuple[SpecialistTarget, ...]:
        return (
            SpecialistTarget(
                name="research-agent",
                base_url=os.getenv("RESEARCH_AGENT_URL", "http://research-agent:8061"),
                patterns=(r"\bresearch\b", r"\bweb\s+search\b", r"\bevidence\b", r"\bsources?\b", r"\blatest\b"),
            ),
            SpecialistTarget(
                name="postgres-agent",
                base_url=os.getenv("POSTGRES_AGENT_URL", "http://postgres-agent:8062"),
                patterns=(r"\bpostgres\b", r"\bpostgresql\b", r"\bsql\b", r"\bdatabase\b", r"\btables?\b"),
            ),
            SpecialistTarget(
                name="docker-agent",
                base_url=os.getenv("DOCKER_AGENT_URL", "http://docker-agent:8063"),
                patterns=(r"\bdocker\b", r"\bcontainers?\b", r"\bimages?\b", r"\blogs?\b"),
            ),
            SpecialistTarget(
                name="filesystem-agent",
                base_url=os.getenv("FILESYSTEM_AGENT_URL", "http://filesystem-agent:8064"),
                patterns=(r"\bfilesystem\b", r"\bfiles?\b", r"\bdirector(?:y|ies)\b", r"\bbackend/\b", r"\bdocs/\b"),
            ),
            SpecialistTarget(
                name="github-agent",
                base_url=os.getenv("GITHUB_AGENT_URL", "http://github-agent:8065"),
                patterns=(r"\bgithub\b", r"\brepositor(?:y|ies)\b", r"\bcommits?\b", r"\bissues?\b", r"\bpull\s+requests?\b"),
            ),
        )

    @classmethod
    def select(cls, request: str) -> SpecialistTarget | None:
        normalized = str(request or "").casefold()
        ranked = []

        for target in cls.targets():
            score = sum(
                1
                for pattern in target.patterns
                if re.search(pattern, normalized, flags=re.IGNORECASE)
            )
            if score > 0:
                ranked.append((score, target.name, target))

        if not ranked:
            return None

        ranked.sort(key=lambda item: (-item[0], item[1]))
        return ranked[0][2]

    @classmethod
    async def delegate(cls, request: str) -> dict[str, Any]:
        target = cls.select(request)
        if target is None:
            return {"delegated": False, "reason": "No matching specialist Agent was found."}

        record = RemoteAgentRecord(
            name=target.name,
            base_url=target.base_url,
            enabled=True,
            timeout_seconds=60.0,
        )

        await RemoteA2AClient.resolve_card(record)
        response = await RemoteA2AClient.delegate(record, request, timeout_seconds=90.0)

        return {
            "delegated": True,
            "specialist": target.name,
            "base_url": target.base_url,
            "success": response.success,
            "final_response": response.final_response,
            "event_count": response.event_count,
            "execution_time_ms": response.execution_time_ms,
            "error": response.error,
        }
