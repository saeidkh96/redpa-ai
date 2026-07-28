import uuid

from app.agents.graph import agent_graph
from app.agents.prompts import REDPA_SYSTEM_PROMPT
from app.core.exceptions import LLMInvalidResponseError
from app.models.message import (
    Message,
    MessageRole,
)
from app.schemas.orchestrator import (
    OrchestratorResult,
)


class OrchestratorService:
    @staticmethod
    async def run(
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
    ) -> OrchestratorResult:
        messages = [
            {
                "role": "system",
                "content": REDPA_SYSTEM_PROMPT,
            }
        ]

        for message in history:
            if message.role not in {
                MessageRole.USER.value,
                MessageRole.ASSISTANT.value,
                MessageRole.SYSTEM.value,
            }:
                continue

            content = message.content.strip()

            if not content:
                continue

            messages.append(
                {
                    "role": message.role,
                    "content": content,
                }
            )

        initial_state = {
            "conversation_id": str(
                conversation_id,
            ),
            "user_id": str(
                user_id,
            ),
            "messages": messages,
            "completed": False,
            "error": None,
        }

        final_state = await agent_graph.ainvoke(
            initial_state,
        )

        if not final_state.get("completed"):
            raise LLMInvalidResponseError(
                "The agent workflow did not complete successfully."
            )

        response_content = final_state.get(
            "response_content",
            "",
        ).strip()

        model = final_state.get(
            "model",
            "",
        ).strip()

        provider = final_state.get(
            "provider",
            "",
        ).strip()

        route = final_state.get(
            "route",
            "",
        ).strip()

        planner_reason = final_state.get(
            "planner_reason",
            "",
        ).strip()

        if not response_content:
            raise LLMInvalidResponseError(
                "The agent workflow returned an empty response."
            )

        if not model:
            raise LLMInvalidResponseError(
                "The agent workflow returned no model name."
            )

        if not provider:
            raise LLMInvalidResponseError(
                "The agent workflow returned no provider name."
            )

        if not route:
            raise LLMInvalidResponseError(
                "The planner returned no workflow route."
            )

        if not planner_reason:
            raise LLMInvalidResponseError(
                "The planner returned no routing reason."
            )

        return OrchestratorResult(
            response_content=response_content,
            model=model,
            provider=provider,
            route=route,
            planner_reason=planner_reason,
            usage=final_state.get(
                "usage",
                {},
            ),
        )