from __future__ import annotations

import os

import uvicorn
from a2a.server.request_handlers import (
    DefaultRequestHandler,
)
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import (
    InMemoryTaskStore,
)
from fastapi import FastAPI

from app.research_agent.card import (
    build_research_agent_card,
)
from app.research_agent.executor import (
    RedPAResearchAgentExecutor,
)


def create_research_agent_application() -> FastAPI:
    agent_card = build_research_agent_card()

    request_handler = DefaultRequestHandler(
        agent_executor=RedPAResearchAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    routes = []

    routes.extend(
        create_agent_card_routes(
            agent_card,
        )
    )

    routes.extend(
        create_jsonrpc_routes(
            request_handler,
            rpc_url="/",
        )
    )

    application = FastAPI(
        title="RedPA Research Agent",
        version="0.6.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        routes=routes,
    )

    @application.get("/health")
    async def health() -> dict[str, object]:
        return {
            "status": "healthy",
            "service": "RedPA Research Agent",
            "protocol_version": "1.0",
            "agent_card": "/.well-known/agent-card.json",
            "capabilities": [
                "web_research",
                "evidence_collection",
                "evidence_ranking",
            ],
        }

    return application


app = create_research_agent_application()


def main() -> None:
    uvicorn.run(
        "app.research_agent.server:app",
        host=os.getenv(
            "RESEARCH_AGENT_HOST",
            "0.0.0.0",
        ),
        port=int(
            os.getenv(
                "RESEARCH_AGENT_PORT",
                "8061",
            )
        ),
        reload=False,
    )


if __name__ == "__main__":
    main()
