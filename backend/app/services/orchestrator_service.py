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
    async def resume(
        cls,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
        review_id: uuid.UUID,
        requested_action: str | None,
        request_content: str | None,
        action_payload: dict[str, Any] | None,
        reviewed_by: uuid.UUID | None,
        reviewed_at: Any,
        reviewer_feedback: str | None,
    ) -> OrchestratorResult:
        initial_state = cls._build_resume_state(
            conversation_id=conversation_id,
            user_id=user_id,
            history=history,
            review_id=review_id,
            requested_action=requested_action,
            request_content=request_content,
            action_payload=action_payload,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            reviewer_feedback=reviewer_feedback,
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

        async for event in cls._stream_state(
            initial_state=initial_state,
            conversation_id=conversation_id,
            resumed=False,
        ):
            yield event

    @classmethod
    async def stream_resume(
        cls,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
        review_id: uuid.UUID,
        requested_action: str | None,
        request_content: str | None,
        action_payload: dict[str, Any] | None,
        reviewed_by: uuid.UUID | None,
        reviewed_at: Any,
        reviewer_feedback: str | None,
    ) -> AsyncIterator[dict[str, Any]]:
        initial_state = cls._build_resume_state(
            conversation_id=conversation_id,
            user_id=user_id,
            history=history,
            review_id=review_id,
            requested_action=requested_action,
            request_content=request_content,
            action_payload=action_payload,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            reviewer_feedback=reviewer_feedback,
        )

        async for event in cls._stream_state(
            initial_state=initial_state,
            conversation_id=conversation_id,
            resumed=True,
        ):
            yield event

    @classmethod
    async def _stream_state(
        cls,
        *,
        initial_state: dict[str, Any],
        conversation_id: uuid.UUID,
        resumed: bool,
    ) -> AsyncIterator[dict[str, Any]]:
        accumulated_state: dict[str, Any] = {
            **initial_state,
        }

        yield {
            "event": (
                "workflow_resume_started"
                if resumed
                else "workflow_started"
            ),
            "data": {
                "conversation_id": str(
                    conversation_id,
                ),
                "resumed": resumed,
                "approved_review_id": (
                    initial_state.get(
                        "approved_review_id",
                    )
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
            if not isinstance(
                stream_chunk,
                dict,
            ):
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
                        accumulated_state=accumulated_state,
                    )
                ):
                    yield update_event

        result = cls._build_result(
            accumulated_state,
        )

        yield {
            "event": (
                "workflow_resume_completed"
                if resumed
                else "workflow_completed"
            ),
            "data": {
                **cls._build_result_event_data(
                    result,
                ),
                "resumed": resumed,
                "approval_granted": bool(
                    accumulated_state.get(
                        "approval_granted",
                        False,
                    )
                ),
                "approved_review_id": (
                    cls._optional_string(
                        accumulated_state.get(
                            "approved_review_id",
                        )
                    )
                ),
            },
        }

    @staticmethod
    async def _handle_custom_chunk(
        chunk_data: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        if not isinstance(
            chunk_data,
            dict,
        ):
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
        if not isinstance(
            chunk_data,
            dict,
        ):
            return

        for node_name, node_update in chunk_data.items():
            if not isinstance(
                node_update,
                dict,
            ):
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
                        "planner_confidence": (
                            OrchestratorService._safe_float(
                                node_update.get(
                                    "planner_confidence",
                                    0.0,
                                ),
                                minimum=0.0,
                                maximum=1.0,
                            )
                        ),
                        "planner_provider": (
                            OrchestratorService._optional_string(
                                node_update.get(
                                    "planner_provider",
                                )
                            )
                        ),
                        "planner_model": (
                            OrchestratorService._optional_string(
                                node_update.get(
                                    "planner_model",
                                )
                            )
                        ),
                        "planner_fallback": bool(
                            node_update.get(
                                "planner_fallback",
                                False,
                            )
                        ),
                        "planner_error": (
                            OrchestratorService._optional_string(
                                node_update.get(
                                    "planner_error",
                                )
                            )
                        ),
                        "planner_latency_ms": (
                            OrchestratorService._safe_float(
                                node_update.get(
                                    "planner_latency_ms",
                                    0.0,
                                ),
                                minimum=0.0,
                            )
                        ),
                        "planner_signals": (
                            OrchestratorService._normalize_string_list(
                                node_update.get(
                                    "planner_signals",
                                    [],
                                )
                            )
                        ),
                        "approval_granted": bool(
                            node_update.get(
                                "approval_granted",
                                False,
                            )
                        ),
                        "approved_review_id": (
                            OrchestratorService._optional_string(
                                node_update.get(
                                    "approved_review_id",
                                )
                            )
                        ),
                    },
                }

            if node_name == "human_review":
                yield {
                    "event": "human_review_required",
                    "data": {
                        "status": str(
                            node_update.get(
                                "review_status",
                                "pending",
                            )
                            or "pending"
                        ),
                        "reason": str(
                            node_update.get(
                                "review_reason",
                                "",
                            )
                            or ""
                        ),
                        "requested_action": (
                            node_update.get(
                                "requested_action",
                            )
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
        messages = OrchestratorService._build_messages(
            history,
        )

        return {
            "conversation_id": str(
                conversation_id,
            ),
            "user_id": str(
                user_id,
            ),
            "messages": messages,
            "route": None,
            "planner_reason": None,
            "planner_confidence": 0.0,
            "planner_provider": None,
            "planner_model": None,
            "planner_fallback": False,
            "planner_error": None,
            "planner_latency_ms": 0.0,
            "planner_signals": [],
            "requires_human_review": False,
            "review_status": None,
            "review_reason": None,
            "review_id": None,
            "approval_granted": False,
            "approved_review_id": None,
            "requested_action": None,
            "request_content": None,
            "action_payload": None,
            "reviewed_by": None,
            "reviewed_at": None,
            "reviewer_feedback": None,
            "completed": False,
            "error": None,
        }

    @staticmethod
    def _build_resume_state(
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        history: list[Message],
        review_id: uuid.UUID,
        requested_action: str | None,
        request_content: str | None,
        action_payload: dict[str, Any] | None,
        reviewed_by: uuid.UUID | None,
        reviewed_at: Any,
        reviewer_feedback: str | None,
    ) -> dict[str, Any]:
        messages = OrchestratorService._build_messages(
            history,
        )

        normalized_action_payload = (
            {
                **action_payload,
            }
            if isinstance(
                action_payload,
                dict,
            )
            else {}
        )

        normalized_request_content = (
            OrchestratorService._optional_string(
                request_content,
            )
        )

        if normalized_request_content:
            latest_user_content = (
                OrchestratorService
                ._get_latest_user_message_content(
                    messages,
                )
            )

            if latest_user_content != normalized_request_content:
                messages.append(
                    {
                        "role": MessageRole.USER.value,
                        "content": normalized_request_content,
                    }
                )

        normalized_action_payload.update(
            {
                "approval_required": False,
                "approval_granted": True,
                "approved_review_id": str(
                    review_id,
                ),
            }
        )

        resume_route = (
            OrchestratorService._optional_string(
                normalized_action_payload.get(
                    "resume_route",
                )
            )
            or OrchestratorService._optional_string(
                normalized_action_payload.get(
                    "original_route",
                )
            )
        )

        return {
            "conversation_id": str(
                conversation_id,
            ),
            "user_id": str(
                user_id,
            ),
            "messages": messages,
            "route": resume_route,
            "planner_reason": (
                "The workflow is being resumed after human "
                f"approval for review '{review_id}'."
            ),
            "planner_confidence": 1.0,
            "planner_provider": "resume",
            "planner_model": None,
            "planner_fallback": False,
            "planner_error": None,
            "planner_latency_ms": 0.0,
            "planner_signals": [
                "human review approved",
                "workflow resumed",
            ],
            "requires_human_review": False,
            "review_status": "approved",
            "review_reason": None,
            "review_id": str(
                review_id,
            ),
            "approval_granted": True,
            "approved_review_id": str(
                review_id,
            ),
            "requested_action": (
                OrchestratorService._optional_string(
                    requested_action,
                )
            ),
            "request_content": (
                normalized_request_content
            ),
            "action_payload": (
                normalized_action_payload
            ),
            "reviewed_by": (
                str(
                    reviewed_by,
                )
                if reviewed_by is not None
                else None
            ),
            "reviewed_at": (
                OrchestratorService._serialize_datetime(
                    reviewed_at,
                )
            ),
            "reviewer_feedback": (
                OrchestratorService._optional_string(
                    reviewer_feedback,
                )
            ),
            "completed": False,
            "error": None,
        }

    @staticmethod
    def _build_messages(
        history: list[Message],
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {
                "role": MessageRole.SYSTEM.value,
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

            content = str(
                message.content,
            ).strip()

            if not content:
                continue

            messages.append(
                {
                    "role": message.role,
                    "content": content,
                }
            )

        return messages

    @staticmethod
    def _get_latest_user_message_content(
        messages: list[dict[str, str]],
    ) -> str | None:
        for message in reversed(
            messages,
        ):
            if message.get(
                "role",
            ) != MessageRole.USER.value:
                continue

            content = str(
                message.get(
                    "content",
                    "",
                )
                or ""
            ).strip()

            if content:
                return content

        return None

    @staticmethod
    def _build_result_event_data(
        result: OrchestratorResult,
    ) -> dict[str, Any]:
        return {
            "response_content": result.response_content,
            "model": result.model,
            "provider": result.provider,
            "route": result.route,
            "planner_reason": result.planner_reason,
            "planner_confidence": result.planner_confidence,
            "planner_provider": result.planner_provider,
            "planner_model": result.planner_model,
            "planner_fallback": result.planner_fallback,
            "planner_error": result.planner_error,
            "planner_latency_ms": result.planner_latency_ms,
            "planner_signals": result.planner_signals,
            "usage": result.usage,
            "requires_human_review": (
                result.requires_human_review
            ),
            "review_status": result.review_status,
            "review_reason": result.review_reason,
            "review_id": result.review_id,
            "requested_action": (
                result.requested_action
            ),
            "request_content": result.request_content,
            "action_payload": result.action_payload,
            "reviewed_by": result.reviewed_by,
            "reviewed_at": result.reviewed_at,
            "reviewer_feedback": (
                result.reviewer_feedback
            ),
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

        planner_confidence = (
            OrchestratorService._safe_float(
                final_state.get(
                    "planner_confidence",
                    0.0,
                ),
                minimum=0.0,
                maximum=1.0,
            )
        )

        planner_provider = (
            OrchestratorService._optional_string(
                final_state.get(
                    "planner_provider",
                )
            )
            or "unknown"
        )

        planner_model = (
            OrchestratorService._optional_string(
                final_state.get(
                    "planner_model",
                )
            )
        )

        planner_fallback = bool(
            final_state.get(
                "planner_fallback",
                False,
            )
        )

        planner_error = (
            OrchestratorService._optional_string(
                final_state.get(
                    "planner_error",
                )
            )
        )

        planner_latency_ms = (
            OrchestratorService._safe_float(
                final_state.get(
                    "planner_latency_ms",
                    0.0,
                ),
                minimum=0.0,
            )
        )

        planner_signals = (
            OrchestratorService._normalize_string_list(
                final_state.get(
                    "planner_signals",
                    [],
                )
            )
        )

        usage = final_state.get(
            "usage",
            {},
        )

        if not isinstance(
            usage,
            dict,
        ):
            usage = {}

        requires_human_review = bool(
            final_state.get(
                "requires_human_review",
                False,
            )
        )

        review_status = (
            OrchestratorService._optional_string(
                final_state.get(
                    "review_status",
                )
            )
        )

        review_reason = (
            OrchestratorService._optional_string(
                final_state.get(
                    "review_reason",
                )
            )
        )

        review_id = (
            OrchestratorService._optional_string(
                final_state.get(
                    "review_id",
                )
            )
        )

        requested_action = (
            OrchestratorService._optional_string(
                final_state.get(
                    "requested_action",
                )
            )
        )

        request_content = (
            OrchestratorService._optional_string(
                final_state.get(
                    "request_content",
                )
            )
        )

        action_payload = final_state.get(
            "action_payload",
        )

        if not isinstance(
            action_payload,
            dict,
        ):
            action_payload = None

        reviewed_by = (
            OrchestratorService._optional_string(
                final_state.get(
                    "reviewed_by",
                )
            )
        )

        reviewed_at = (
            OrchestratorService._optional_string(
                final_state.get(
                    "reviewed_at",
                )
            )
        )

        reviewer_feedback = (
            OrchestratorService._optional_string(
                final_state.get(
                    "reviewer_feedback",
                )
            )
        )

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

        if (
            requires_human_review
            and not review_reason
        ):
            review_reason = planner_reason

        if (
            requires_human_review
            and not review_status
        ):
            review_status = "pending"

        if bool(
            final_state.get(
                "approval_granted",
                False,
            )
        ):
            requires_human_review = False
            review_status = "approved"
            review_reason = None

            review_id = (
                OrchestratorService._optional_string(
                    final_state.get(
                        "approved_review_id",
                    )
                )
                or review_id
            )

        return OrchestratorResult(
            response_content=response_content,
            model=model,
            provider=provider,
            route=route,
            planner_reason=planner_reason,
            planner_confidence=planner_confidence,
            planner_provider=planner_provider,
            planner_model=planner_model,
            planner_fallback=planner_fallback,
            planner_error=planner_error,
            planner_latency_ms=planner_latency_ms,
            planner_signals=planner_signals,
            usage=usage,
            requires_human_review=requires_human_review,
            review_status=review_status,
            review_reason=review_reason,
            review_id=review_id,
            requested_action=requested_action,
            request_content=request_content,
            action_payload=action_payload,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            reviewer_feedback=reviewer_feedback,
        )

    @staticmethod
    def _safe_float(
        value: Any,
        *,
        minimum: float | None = None,
        maximum: float | None = None,
    ) -> float:
        try:
            numeric_value = float(
                value,
            )

        except (
            TypeError,
            ValueError,
        ):
            numeric_value = 0.0

        if minimum is not None:
            numeric_value = max(
                minimum,
                numeric_value,
            )

        if maximum is not None:
            numeric_value = min(
                maximum,
                numeric_value,
            )

        return numeric_value

    @staticmethod
    def _normalize_string_list(
        value: Any,
        *,
        limit: int = 10,
    ) -> list[str]:
        if not isinstance(
            value,
            list,
        ):
            return []

        normalized_values: list[str] = []

        for item in value:
            normalized_item = str(
                item,
            ).strip()

            if not normalized_item:
                continue

            if normalized_item in normalized_values:
                continue

            normalized_values.append(
                normalized_item,
            )

            if len(
                normalized_values,
            ) >= limit:
                break

        return normalized_values

    @staticmethod
    def _serialize_datetime(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        isoformat_method = getattr(
            value,
            "isoformat",
            None,
        )

        if callable(
            isoformat_method,
        ):
            serialized_value = str(
                isoformat_method(),
            ).strip()

            if serialized_value:
                return serialized_value

        return OrchestratorService._optional_string(
            value,
        )

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = str(
            value,
        ).strip()

        if not normalized_value:
            return None

        return normalized_value