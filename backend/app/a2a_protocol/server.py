from __future__ import annotations

import os

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.a2a_protocol.card import build_public_agent_card
from app.a2a_protocol.specialist_executor import RedPACoordinatorDelegatingExecutor


public_agent_card = build_public_agent_card()

request_handler = DefaultRequestHandler(
    agent_executor=RedPACoordinatorDelegatingExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=public_agent_card,
)


async def health(request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "healthy",
            "service": "RedPA A2A Coordinator",
            "protocol_version": "1.0",
            "agent_card": "/.well-known/agent-card.json",
        }
    )


routes = [
    Route(
        "/health",
        health,
        methods=["GET"],
    )
]
routes.extend(
    create_agent_card_routes(public_agent_card)
)
routes.extend(
    create_jsonrpc_routes(
        request_handler,
        "/",
    )
)

app = Starlette(routes=routes)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("A2A_HOST", "0.0.0.0"),
        port=int(os.getenv("A2A_PORT", "8050")),
    )
