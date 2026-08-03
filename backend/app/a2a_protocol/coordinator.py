from __future__ import annotations

import json

from app.a2a.service import AgentService


class RedPACoordinatorAgent:
    async def invoke(self, user_request: str) -> str:
        query = str(user_request or "").strip()

        if not query:
            return (
                "No text input was provided. Ask me to discover a RedPA "
                "agent capability or show agent-platform health."
            )

        lowered = query.casefold()

        if any(
            signal in lowered
            for signal in (
                "health",
                "status",
                "available agents",
                "list agents",
                "agent registry",
            )
        ):
            health = await AgentService.health()
            agents = await AgentService.list_agents()

            return json.dumps(
                {
                    "status": health.status,
                    "total_agents": health.total_agents,
                    "active_agents": health.active_agents,
                    "degraded_agents": health.degraded_agents,
                    "offline_agents": health.offline_agents,
                    "agents": [
                        {
                            "id": item.id,
                            "name": item.name,
                            "status": item.status.value,
                            "capabilities": item.capability_names,
                            "routes": item.supported_routes,
                        }
                        for item in agents.items
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )

        discovery = await AgentService.discover(
            query,
            limit=10,
        )

        payload = {
            "query": discovery.query,
            "total": discovery.total,
            "matches": [
                {
                    "agent_id": item.agent_id,
                    "agent_name": item.agent_name,
                    "capability": item.capability_name,
                    "description": item.capability_description,
                    "matched_terms": item.matched_tags,
                    "score": item.score,
                }
                for item in discovery.matches
            ],
        }

        if not discovery.matches:
            payload["message"] = (
                "No matching active RedPA capability was found."
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
