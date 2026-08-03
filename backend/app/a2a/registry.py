from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from app.a2a.schemas import (
    AgentCard,
    AgentCardSummary,
    AgentHealthItem,
    AgentHealthResponse,
    AgentListResponse,
    AgentStatus,
    CapabilityDiscoveryResponse,
    CapabilityMatch,
)


class AgentAlreadyRegisteredError(RuntimeError):
    pass


class AgentNotFoundError(LookupError):
    pass


class AgentRegistry:
    """
    In-process registry for RedPA agents.

    The registry is intentionally small and deterministic. Remote A2A agent
    discovery and persistence are added in later phases.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentCard] = {}
        self._lock = asyncio.Lock()

    async def register(
        self,
        card: AgentCard,
        *,
        replace: bool = False,
    ) -> AgentCard:
        normalized_id = card.id.casefold()

        async with self._lock:
            if (
                normalized_id in self._agents
                and not replace
            ):
                raise AgentAlreadyRegisteredError(
                    f"Agent '{card.id}' is already registered."
                )

            self._agents[normalized_id] = card

        return card

    async def unregister(
        self,
        agent_id: str,
    ) -> None:
        normalized_id = str(
            agent_id
            or "",
        ).casefold().strip()

        async with self._lock:
            if normalized_id not in self._agents:
                raise AgentNotFoundError(
                    f"Agent '{agent_id}' was not found."
                )

            del self._agents[normalized_id]

    async def get(
        self,
        agent_id: str,
    ) -> AgentCard:
        normalized_id = str(
            agent_id
            or "",
        ).casefold().strip()

        card = self._agents.get(
            normalized_id,
        )

        if card is None:
            raise AgentNotFoundError(
                f"Agent '{agent_id}' was not found."
            )

        return card

    async def list(
        self,
    ) -> AgentListResponse:
        cards = sorted(
            self._agents.values(),
            key=lambda item: item.id,
        )

        items = [
            AgentCardSummary(
                id=card.id,
                name=card.name,
                version=card.version,
                status=card.status,
                capability_names=[
                    capability.name
                    for capability in card.capabilities
                ],
                supported_routes=card.supported_routes,
            )
            for card in cards
        ]

        return AgentListResponse(
            items=items,
            total=len(
                items,
            ),
        )

    async def health(
        self,
    ) -> AgentHealthResponse:
        cards = sorted(
            self._agents.values(),
            key=lambda item: item.id,
        )

        active = sum(
            1
            for card in cards
            if card.status == AgentStatus.ACTIVE
        )

        degraded = sum(
            1
            for card in cards
            if card.status == AgentStatus.DEGRADED
        )

        offline = sum(
            1
            for card in cards
            if card.status == AgentStatus.OFFLINE
        )

        overall_status = (
            "healthy"
            if offline == 0 and degraded == 0
            else "degraded"
        )

        return AgentHealthResponse(
            status=overall_status,
            total_agents=len(
                cards,
            ),
            active_agents=active,
            degraded_agents=degraded,
            offline_agents=offline,
            checked_at=datetime.now(
                timezone.utc,
            ),
            agents=[
                AgentHealthItem(
                    id=card.id,
                    name=card.name,
                    status=card.status,
                    capability_count=len(
                        card.capabilities,
                    ),
                )
                for card in cards
            ],
        )

    async def discover(
        self,
        query: str,
        *,
        limit: int = 10,
    ) -> CapabilityDiscoveryResponse:
        normalized_query = str(
            query
            or "",
        ).strip()

        if not normalized_query:
            return CapabilityDiscoveryResponse(
                query="",
                matches=[],
                total=0,
            )

        query_terms = self._tokenize(
            normalized_query,
        )

        matches: list[CapabilityMatch] = []

        for card in self._agents.values():
            if card.status == AgentStatus.OFFLINE:
                continue

            for capability in card.capabilities:
                capability_terms = self._tokenize(
                    " ".join(
                        [
                            capability.name,
                            capability.description,
                            *capability.tags,
                            *capability.examples,
                        ]
                    )
                )

                matched_terms = sorted(
                    query_terms
                    & capability_terms,
                )

                if not matched_terms:
                    continue

                name_terms = self._tokenize(
                    capability.name,
                )

                tag_terms = self._tokenize(
                    " ".join(
                        capability.tags,
                    )
                )

                score = (
                    len(
                        query_terms
                        & name_terms
                    )
                    * 3.0
                    + len(
                        query_terms
                        & tag_terms
                    )
                    * 2.0
                    + len(
                        matched_terms
                    )
                    * 0.5
                )

                matches.append(
                    CapabilityMatch(
                        agent_id=card.id,
                        agent_name=card.name,
                        capability_name=capability.name,
                        capability_description=(
                            capability.description
                        ),
                        matched_tags=matched_terms,
                        score=score,
                    )
                )

        matches.sort(
            key=lambda item: (
                -item.score,
                item.agent_id,
                item.capability_name,
            )
        )

        limited_matches = matches[
            : max(
                1,
                min(
                    int(limit),
                    50,
                ),
            )
        ]

        return CapabilityDiscoveryResponse(
            query=normalized_query,
            matches=limited_matches,
            total=len(
                limited_matches,
            ),
        )

    @staticmethod
    def _tokenize(
        value: str,
    ) -> set[str]:
        stop_words = {
            "a",
            "an",
            "and",
            "for",
            "from",
            "in",
            "of",
            "on",
            "the",
            "to",
            "with",
        }

        return {
            token
            for token in re.findall(
                r"[a-z0-9_]{2,}",
                str(
                    value
                    or "",
                ).casefold(),
            )
            if token not in stop_words
        }


agent_registry = AgentRegistry()
