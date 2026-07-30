from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.agents.graph import agent_graph
from app.agents.prompts import REDPA_SYSTEM_PROMPT
from app.core.exceptions import LLMInvalidResponseError
from app.models.message import (
    Message,
    MessageRole,
)
from app.schemas.orchestrator import OrchestratorResult


class OrchestratorService:
    @classmethod
    async def run(
        cls,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
    ) -> OrchestratorResult:
        initial_state = cls._build_initial_state(
            conversation_id=conversation_id,
            user_id=user_id,
            history=history,
        )

        final_state = await agent_graph.ainvoke(
            initial_state,
        )

        return cls._build_result(
            final_state,
        )

    @classmethod
    async def stream(
        cls,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
    ) -> AsyncIterator[dict[str, Any]]:
        initial_state = cls._build_initial_state(
            conversation_id=conversation_id,
            user_id=user_id,
            history=history,
        )

        accumulated_state: dict[str, Any] = {
            **initial_state,
        }

        yield {
            "event": "workflow_started",
            "data": {
                "conversation_id": str(
                    conversation_id,
                ),
            },
        }

        async for stream_chunk in agent_graph.astream(
            initial_state,
            stream_mode=[
                "updates",
                "custom",
            ],
            version="v2",
        ):
            if not isinstance(stream_chunk, dict):
                continue

            chunk_type = str(
                stream_chunk.get(
                    "type",
                    "",
                )
                or ""
            ).strip()

            chunk_data = stream_chunk.get(
                "data",
            )

            if chunk_type == "custom":
                async for custom_event in (
                    cls._handle_custom_chunk(
                        chunk_data,
                    )
                ):
                    yield custom_event

                continue

            if chunk_type == "updates":
                async for update_event in (
                    cls._handle_update_chunk(
                        chunk_data=chunk_data,
                        accumulated_state=(
                            accumulated_state
                        ),
                    )
                ):
                    yield update_event

        result = cls._build_result(
            accumulated_state,
        )

        yield {
            "event": "workflow_completed",
            "data": {
                "response_content": (
                    result.response_content
                ),
                "model": result.model,
                "provider": result.provider,
                "route": result.route,
                "planner_reason": (
                    result.planner_reason
                ),
                "usage": result.usage,
            },
        }

    @staticmethod
    async def _handle_custom_chunk(
        chunk_data: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        if not isinstance(chunk_data, dict):
            return

        event_type = str(
            chunk_data.get(
                "type",
                "",
            )
            or ""
        ).strip()

        if event_type == "token":
            token = str(
                chunk_data.get(
                    "content",
                    "",
                )
                or ""
            )

            if not token:
                return

            yield {
                "event": "token",
                "data": {
                    "content": token,
                    "node": str(
                        chunk_data.get(
                            "node",
                            "",
                        )
                        or ""
                    ),
                },
            }

            return

        if event_type == "stream_completed":
            yield {
                "event": "token_stream_completed",
                "data": {
                    "node": str(
                        chunk_data.get(
                            "node",
                            "",
                        )
                        or ""
                    ),
                },
            }

            return

        yield {
            "event": "custom",
            "data": chunk_data,
        }

    @staticmethod
    async def _handle_update_chunk(
        *,
        chunk_data: Any,
        accumulated_state: dict[str, Any],
    ) -> AsyncIterator[dict[str, Any]]:
        if not isinstance(chunk_data, dict):
            return

        for node_name, node_update in chunk_data.items():
            if not isinstance(node_update, dict):
                continue

            accumulated_state.update(
                node_update,
            )

            if node_name == "planner":
                yield {
                    "event": "route_selected",
                    "data": {
                        "route": str(
                            node_update.get(
                                "route",
                                "",
                            )
                            or ""
                        ),
                        "planner_reason": str(
                            node_update.get(
                                "planner_reason",
                                "",
                            )
                            or ""
                        ),
                    },
                }

            yield {
                "event": "node_completed",
                "data": {
                    "node": str(
                        node_name,
                    ),
                },
            }

    @staticmethod
    def _build_initial_state(
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
    ) -> dict[str, Any]:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": REDPA_SYSTEM_PROMPT,
            }
        ]

        allowed_roles = {
            MessageRole.USER.value,
            MessageRole.ASSISTANT.value,
            MessageRole.SYSTEM.value,
        }

        for message in history:
            if message.role not in allowed_roles:
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

        return {
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

    @staticmethod
    def _build_result(
        final_state: dict[str, Any],
    ) -> OrchestratorResult:
        if not final_state.get(
            "completed",
        ):
            error = final_state.get(
                "error",
            )

            if error:
                raise LLMInvalidResponseError(
                    f"The agent workflow failed: {error}"
                )

            raise LLMInvalidResponseError(
                "The agent workflow did not complete "
                "successfully."
            )

        response_content = str(
            final_state.get(
                "response_content",
                "",
            )
            or ""
        ).strip()

        model = str(
            final_state.get(
                "model",
                "",
            )
            or ""
        ).strip()

        provider = str(
            final_state.get(
                "provider",
                "",
            )
            or ""
        ).strip()

        route = str(
            final_state.get(
                "route",
                "",
            )
            or ""
        ).strip()

        planner_reason = str(
            final_state.get(
                "planner_reason",
                "",
            )
            or ""
        ).strip()

        usage = final_state.get(
            "usage",
            {},
        )

        if not isinstance(
            usage,
            dict,
        ):
            usage = {}

        if not response_content:
            raise LLMInvalidResponseError(
                "The agent workflow returned an empty "
                "response."
            )

        if not model:
            raise LLMInvalidResponseError(
                "The agent workflow returned no model name."
            )

        if not provider:
            raise LLMInvalidResponseError(
                "The agent workflow returned no provider "
                "name."
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
            usage=usage,
        )