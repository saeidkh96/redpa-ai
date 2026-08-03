from __future__ import annotations

import json
import uuid

from a2a.helpers import get_message_text, new_task_from_user_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import Part, TaskState

from app.a2a_protocol.specialist_router import CoordinatorSpecialistRouter


class RedPACoordinatorDelegatingExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        user_message = context.message
        if user_message is None:
            raise ValueError("A2A request did not contain a message.")

        task = new_task_from_user_message(user_message)
        await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )
        await updater.update_status(TaskState.TASK_STATE_WORKING, message=None)

        request_text = get_message_text(user_message).strip()
        result = await CoordinatorSpecialistRouter.delegate(request_text)

        await updater.add_artifact(
            parts=[Part(
                text=json.dumps(result, ensure_ascii=False, indent=2, default=str),
                media_type="application/json",
            )],
            artifact_id=str(uuid.uuid4()),
        )

        if result.get("success", result.get("delegated", False)):
            await updater.complete(message=None)
        else:
            await updater.failed(message=None)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Coordinator cancellation is not implemented.")
