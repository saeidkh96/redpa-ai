from __future__ import annotations

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
)
from a2a.types import Part, TaskState

from app.a2a_protocol.coordinator import RedPACoordinatorAgent


class RedPACoordinatorExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agent = RedPACoordinatorAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message(
                "RedPA Coordinator is processing the request."
            ),
        )

        result = await self.agent.invoke(
            get_message_text(context.message) or ""
        )

        await updater.add_artifact(
            parts=[
                Part(
                    text=result,
                    media_type="application/json",
                )
            ]
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message(
                "RedPA Coordinator completed the request."
            ),
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task = context.current_task

        if task is None:
            return

        updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        await updater.update_status(
            state=TaskState.TASK_STATE_CANCELED,
            message=new_text_message(
                "The RedPA A2A task was canceled."
            ),
        )
