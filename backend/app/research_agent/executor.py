from __future__ import annotations

import json
import uuid

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
)
from a2a.server.agent_execution import (
    AgentExecutor,
    RequestContext,
)
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Part,
    TaskState,
)

from app.research_agent.service import (
    ResearchAgentError,
    ResearchAgentService,
)


class RedPAResearchAgentExecutor(AgentExecutor):
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

        task = new_task_from_user_message(
            user_message,
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

        query = get_message_text(
            user_message,
        ).strip()

        try:
            result = await ResearchAgentService.research(
                query=query,
                max_results=8,
            )

            payload = json.dumps(
                result.model_dump(
                    mode="json",
                ),
                ensure_ascii=False,
                indent=2,
            )

            await updater.add_artifact(
                parts=[
                    Part(
                        text=payload,
                        media_type="application/json",
                    )
                ],
                artifact_id=str(uuid.uuid4()),
            )

            await updater.complete(
                message=None,
            )

        except (
            ResearchAgentError,
            ValueError,
        ) as exception:
            await updater.failed(
                message=None,
            )

            await updater.add_artifact(
                parts=[
                    Part(
                        text=json.dumps(
                            {
                                "success": False,
                                "query": query,
                                "error": str(exception),
                            },
                            ensure_ascii=False,
                            indent=2,
                        ),
                        media_type="application/json",
                    )
                ],
                artifact_id=str(uuid.uuid4()),
            )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise NotImplementedError(
            "Research Agent cancellation is not implemented."
        )
