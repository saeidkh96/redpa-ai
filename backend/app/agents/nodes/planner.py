from __future__ import annotations

import logging
import re
from typing import Any

from app.agents.state import (
    AgentRoute,
    AgentState,
)
from app.services.planner_service import PlannerService


logger = logging.getLogger(__name__)


RESUMABLE_ROUTES: tuple[AgentRoute, ...] = (
    "chat",
    "rag",
    "research",
    "a2a",
    "tool",
    "sql",
)


EXECUTION_VERBS: tuple[str, ...] = (
    "send",
    "create",
    "schedule",
    "execute",
    "run",
    "delete",
    "remove",
    "drop",
    "truncate",
    "transfer",
    "wire",
    "pay",
    "purchase",
    "buy",
    "refund",
    "approve",
    "update",
    "insert",
)


INFORMATIONAL_PREFIXES: tuple[str, ...] = (
    "what is",
    "what are",
    "how does",
    "how do",
    "how can",
    "how would",
    "why does",
    "why do",
    "explain",
    "describe",
    "tell me about",
    "give me an example",
    "show me an example",
    "write an example",
)


HIGH_RISK_ACTION_PATTERNS: tuple[
    tuple[str, str, AgentRoute],
    ...,
] = (
    (
        "drop_table",
        r"\bdrop\s+(the\s+)?table\b",
        "sql",
    ),
    (
        "truncate_table",
        r"\btruncate\s+(the\s+)?table\b",
        "sql",
    ),
    (
        "delete_database_records",
        r"\bdelete\s+(the\s+)?"
        r"(record|records|row|rows|data)\b",
        "sql",
    ),
    (
        "transfer_money",
        r"\btransfer\s+(the\s+)?money\b",
        "tool",
    ),
    (
        "wire_money",
        r"\bwire\s+(the\s+)?money\b",
        "tool",
    ),
    (
        "send_email",
        r"\bsend\s+(an?\s+)?email\b",
        "tool",
    ),
    (
        "approve_invoice",
        r"\bapprove\s+(the\s+|an?\s+)?invoice\b",
        "tool",
    ),
    (
        "execute_purchase",
        r"\b(purchase|buy)\s+(the\s+|an?\s+)?"
        r"(item|product|subscription|service)\b",
        "tool",
    ),
    (
        "execute_refund",
        r"\b(issue|process|execute|send)\s+"
        r"(the\s+|an?\s+)?refund\b",
        "tool",
    ),
    (
        "create_calendar_event",
        r"\bcreate\s+(the\s+|an?\s+)?"
        r"calendar\s+event\b",
        "tool",
    ),
    (
        "schedule_meeting",
        r"\bschedule\s+(the\s+|an?\s+)?meeting\b",
        "tool",
    ),
    (
        "create_github_issue",
        r"\bcreate\s+(the\s+|an?\s+)?"
        r"github\s+issue\b",
        "tool",
    ),
)


async def planner_node(
    state: AgentState,
) -> dict[str, object]:
    approval_granted = bool(
        state.get(
            "approval_granted",
            False,
        )
    )

    approved_review_id = _optional_string(
        state.get(
            "approved_review_id",
        )
    )

    if approval_granted and approved_review_id:
        return _build_approved_plan(
            state=state,
            approved_review_id=approved_review_id,
        )

    latest_user_message = _get_latest_user_message(
        state,
    )

    if latest_user_message is None:
        return _build_default_chat_plan()

    normalized_message = _normalize_text(
        latest_user_message,
    )

    high_risk_action = _detect_high_risk_action(
        normalized_message,
    )

    if high_risk_action is not None:
        (
            requested_action,
            resume_route,
            matched_signal,
        ) = high_risk_action

        reason = (
            "Selected the 'human_review' route because "
            "the request explicitly asks the system to "
            f"execute the sensitive action "
            f"'{requested_action}'."
        )

        return {
            "route": "human_review",
            "planner_reason": reason,
            "planner_confidence": 1.0,
            "planner_provider": "rule_based",
            "planner_model": "safety-gate-v1",
            "planner_fallback": False,
            "planner_error": None,
            "planner_latency_ms": 0.0,
            "planner_signals": [
                matched_signal,
            ],
            "requires_human_review": True,
            "review_status": "pending",
            "review_reason": reason,
            "review_id": None,
            "approval_granted": False,
            "approved_review_id": None,
            "requested_action": requested_action,
            "request_content": latest_user_message,
            "action_payload": {
                "original_route": resume_route,
                "resume_route": resume_route,
                "requested_action": requested_action,
                "request_content": latest_user_message,
                "approval_required": True,
                "safety_gate": "deterministic",
                "matched_signal": matched_signal,
            },
        }

    planner_result = await PlannerService.create_plan(
        latest_user_message,
    )

    await record_runtime_event(
        event_type="planner.decision",
        stage="planner",
        payload={
            "route": planner_result.plan.route,
            "confidence": planner_result.plan.confidence,
            "provider": planner_result.provider,
            "fallback_used": planner_result.fallback_used,
        },
    )

    route = planner_result.plan.route
    reason = planner_result.plan.reasoning
    requires_human_review = route == "human_review"

    logger.info(
        "Planner selected route | route=%s "
        "confidence=%.2f provider=%s fallback=%s",
        route,
        planner_result.plan.confidence,
        planner_result.provider,
        planner_result.fallback_used,
    )

    return {
        "route": route,
        "planner_reason": reason,
        "planner_confidence": (
            planner_result.plan.confidence
        ),
        "planner_provider": (
            planner_result.provider
        ),
        "planner_model": planner_result.model,
        "planner_fallback": (
            planner_result.fallback_used
        ),
        "planner_error": planner_result.error,
        "planner_latency_ms": (
            planner_result.latency_ms
        ),
        "planner_signals": (
            planner_result.plan.signals
        ),
        "requires_human_review": (
            requires_human_review
        ),
        "review_status": (
            "pending"
            if requires_human_review
            else None
        ),
        "review_reason": (
            reason
            if requires_human_review
            else None
        ),
        "review_id": None,
        "approval_granted": False,
        "approved_review_id": None,
        "requested_action": (
            "manual_human_review"
            if requires_human_review
            else None
        ),
        "request_content": (
            latest_user_message
            if requires_human_review
            else None
        ),
        "action_payload": (
            {
                "original_route": "chat",
                "resume_route": "chat",
                "requested_action": (
                    "manual_human_review"
                ),
                "request_content": latest_user_message,
                "approval_required": True,
                "planner_provider": (
                    planner_result.provider
                ),
                "planner_confidence": (
                    planner_result.plan.confidence
                ),
            }
            if requires_human_review
            else None
        ),
    }


def _build_default_chat_plan() -> dict[str, object]:
    return {
        "route": "chat",
        "planner_reason": (
            "Selected the 'chat' route because no valid "
            "user message was available."
        ),
        "planner_confidence": 1.0,
        "planner_provider": "rule_based",
        "planner_model": "deterministic-router-v1",
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
    }


def _build_approved_plan(
    *,
    state: AgentState,
    approved_review_id: str,
) -> dict[str, object]:
    action_payload = state.get(
        "action_payload",
    )

    if not isinstance(
        action_payload,
        dict,
    ):
        action_payload = {}

    resume_route = _resolve_resume_route(
        state=state,
        action_payload=action_payload,
    )

    requested_action = (
        _optional_string(
            state.get(
                "requested_action",
            )
        )
        or _optional_string(
            action_payload.get(
                "requested_action",
            )
        )
        or "approved_workflow_execution"
    )

    request_content = (
        _optional_string(
            state.get(
                "request_content",
            )
        )
        or _optional_string(
            action_payload.get(
                "request_content",
            )
        )
        or _get_latest_user_message(
            state,
        )
    )

    updated_action_payload = {
        **action_payload,
        "resume_route": resume_route,
        "approval_required": False,
        "approval_granted": True,
        "approved_review_id": approved_review_id,
    }

    return {
        "route": resume_route,
        "planner_reason": (
            f"Resuming approved human review "
            f"'{approved_review_id}' through the "
            f"'{resume_route}' route."
        ),
        "planner_confidence": 1.0,
        "planner_provider": "resume",
        "planner_model": None,
        "planner_fallback": False,
        "planner_error": None,
        "planner_latency_ms": 0.0,
        "planner_signals": [
            "approved human review",
        ],
        "requires_human_review": False,
        "review_status": "approved",
        "review_reason": None,
        "review_id": approved_review_id,
        "approval_granted": True,
        "approved_review_id": approved_review_id,
        "requested_action": requested_action,
        "request_content": request_content,
        "action_payload": updated_action_payload,
    }


def _detect_high_risk_action(
    normalized_message: str,
) -> tuple[str, AgentRoute, str] | None:
    if _is_informational_request(
        normalized_message,
    ):
        return None

    if not _contains_execution_intent(
        normalized_message,
    ):
        return None

    for (
        requested_action,
        pattern,
        resume_route,
    ) in HIGH_RISK_ACTION_PATTERNS:
        match = re.search(
            pattern,
            normalized_message,
            flags=re.IGNORECASE,
        )

        if match is None:
            continue

        return (
            requested_action,
            resume_route,
            match.group(0).strip(),
        )

    return None


def _is_informational_request(
    normalized_message: str,
) -> bool:
    return any(
        normalized_message.startswith(
            prefix,
        )
        for prefix in INFORMATIONAL_PREFIXES
    )


def _contains_execution_intent(
    normalized_message: str,
) -> bool:
    for verb in EXECUTION_VERBS:
        if re.search(
            rf"\b{re.escape(verb)}\b",
            normalized_message,
        ):
            return True

    return False


def _resolve_resume_route(
    *,
    state: AgentState,
    action_payload: dict[str, Any],
) -> AgentRoute:
    route_candidates: tuple[Any, ...] = (
        action_payload.get(
            "resume_route",
        ),
        action_payload.get(
            "original_route",
        ),
        action_payload.get(
            "route",
        ),
        state.get(
            "route",
        ),
    )

    for candidate in route_candidates:
        normalized_route = _normalize_route(
            candidate,
        )

        if normalized_route in RESUMABLE_ROUTES:
            return normalized_route

    requested_action = (
        _optional_string(
            state.get(
                "requested_action",
            )
        )
        or _optional_string(
            action_payload.get(
                "requested_action",
            )
        )
    )

    if requested_action:
        normalized_action = _normalize_text(
            requested_action,
        )

        if any(
            database_signal in normalized_action
            for database_signal in (
                "table",
                "database",
                "record",
                "row",
                "sql",
            )
        ):
            return "sql"

        return "tool"

    return "chat"


def _get_latest_user_message(
    state: AgentState,
) -> str | None:
    messages = state.get(
        "messages",
        [],
    )

    for message in reversed(
        messages,
    ):
        if not isinstance(
            message,
            dict,
        ):
            continue

        if message.get(
            "role",
        ) != "user":
            continue

        content = message.get(
            "content",
            "",
        )

        if not isinstance(
            content,
            str,
        ):
            continue

        normalized_content = content.strip()

        if normalized_content:
            return normalized_content

    return None


def _normalize_route(
    value: Any,
) -> AgentRoute | None:
    if value is None:
        return None

    normalized_value = str(
        value,
    ).strip().casefold()

    route_aliases: dict[str, AgentRoute] = {
        "chat": "chat",
        "conversation": "chat",
        "general_chat": "chat",
        "rag": "rag",
        "retrieval": "rag",
        "document_search": "rag",
        "knowledge_base": "rag",
        "research": "research",
        "web_research": "research",
        "web_search": "research",
        "tool": "tool",
        "tool_execution": "tool",
        "execute_tool": "tool",
        "sql": "sql",
        "database": "sql",
        "database_query": "sql",
        "human_review": "human_review",
        "review": "human_review",
        "manual_approval": "human_review",
    }

    return route_aliases.get(
        normalized_value,
    )


def _normalize_text(
    text: str,
) -> str:
    normalized = text.casefold()

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


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