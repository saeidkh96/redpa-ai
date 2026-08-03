from __future__ import annotations

import json
import os
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

import uvicorn
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
)
from a2a.server.agent_execution import (
    AgentExecutor,
    RequestContext,
)
from a2a.server.events import EventQueue
from a2a.server.request_handlers import (
    DefaultRequestHandler,
)
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import (
    InMemoryTaskStore,
    TaskUpdater,
)
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    Part,
    TaskState,
)
from fastapi import FastAPI


SpecialistHandler = Callable[
    [str],
    Awaitable[dict[str, Any]],
]


class SpecialistAgentExecutor(AgentExecutor):
    def __init__(
        self,
        *,
        handler: SpecialistHandler,
    ) -> None:
        self._handler = handler

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        user_message = context.message

        if user_message is None:
            raise ValueError(
                "A2A request did not contain a message."
            )

        task = (
            context.current_task
            or new_task_from_user_message(
                user_message,
            )
        )

        await event_queue.enqueue_event(
            task,
        )

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        await updater.update_status(
            TaskState.TASK_STATE_WORKING,
            message=None,
        )

        request_text = get_message_text(
            user_message,
        ).strip()

        try:
            result = await self._handler(
                request_text,
            )

            payload = json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

            await updater.add_artifact(
                parts=[
                    Part(
                        text=payload,
                        media_type="application/json",
                    )
                ],
                artifact_id=str(
                    uuid.uuid4(),
                ),
            )

            await updater.complete(
                message=None,
            )

        except Exception as exception:
            await updater.add_artifact(
                parts=[
                    Part(
                        text=json.dumps(
                            {
                                "success": False,
                                "request": request_text,
                                "error": str(
                                    exception,
                                ),
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        media_type="application/json",
                    )
                ],
                artifact_id=str(
                    uuid.uuid4(),
                ),
            )

            await updater.failed(
                message=None,
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError(
            "Specialist Agent cancellation is not implemented."
        )


def build_specialist_agent_card(
    *,
    name: str,
    description: str,
    public_url: str,
    version: str,
    skill_id: str,
    skill_name: str,
    skill_description: str,
    tags: list[str],
    examples: list[str],
) -> AgentCard:
    return AgentCard(
        name=name,
        description=description,
        supported_interfaces=[
            AgentInterface(
                url=public_url.rstrip(
                    "/",
                ),
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            )
        ],
        version=version,
        capabilities=AgentCapabilities(
            streaming=False,
            extended_agent_card=False,
        ),
        default_input_modes=[
            "text/plain",
        ],
        default_output_modes=[
            "application/json",
            "text/plain",
        ],
        skills=[
            AgentSkill(
                id=skill_id,
                name=skill_name,
                description=skill_description,
                tags=tags,
                examples=examples,
                input_modes=[
                    "text/plain",
                ],
                output_modes=[
                    "application/json",
                    "text/plain",
                ],
            )
        ],
    )


def create_specialist_application(
    *,
    service_name: str,
    version: str,
    card: AgentCard,
    handler: SpecialistHandler,
    capabilities: list[str],
) -> FastAPI:
    request_handler = DefaultRequestHandler(
        agent_executor=SpecialistAgentExecutor(
            handler=handler,
        ),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )

    routes = []

    routes.extend(
        create_agent_card_routes(
            card,
        )
    )

    routes.extend(
        create_jsonrpc_routes(
            request_handler,
            rpc_url="/",
        )
    )

    application = FastAPI(
        title=service_name,
        version=version,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        routes=routes,
    )

    @application.get("/health")
    async def health() -> dict[str, object]:
        return {
            "status": "healthy",
            "service": service_name,
            "protocol_version": "1.0",
            "agent_card": "/.well-known/agent-card.json",
            "capabilities": capabilities,
        }

    return application


def run_specialist(
    *,
    module_path: str,
    host_env: str,
    port_env: str,
    default_port: int,
) -> None:
    uvicorn.run(
        module_path,
        host=os.getenv(
            host_env,
            "0.0.0.0",
        ),
        port=int(
            os.getenv(
                port_env,
                str(
                    default_port,
                ),
            )
        ),
        reload=False,
    )
