from __future__ import annotations

import re
from typing import Any

from app.agents.state import AgentRoute, AgentState


ROUTE_KEYWORDS: dict[AgentRoute, tuple[str, ...]] = {
    "rag": (
        "document",
        "documents",
        "pdf",
        "file",
        "files",
        "knowledge base",
        "knowledge-base",
        "uploaded document",
        "uploaded file",
        "search my document",
        "search the document",
        "retrieve from",
        "retrieval",
        "vector database",
        "vector store",
        "embedding",
        "embeddings",
    ),
    "sql": (
        "sql",
        "database query",
        "query the database",
        "query database",
        "database table",
        "database tables",
        "postgresql",
        "postgres",
        "mysql",
        "select from",
        "insert into",
        "update table",
        "delete from",
        "drop table",
        "truncate table",
    ),
    "tool": (
        "send an email",
        "send email",
        "email someone",
        "create calendar event",
        "calendar event",
        "schedule a meeting",
        "call an api",
        "call api",
        "use a tool",
        "execute tool",
        "github issue",
        "create github",
        "transfer money",
        "wire money",
        "approve invoice",
        "purchase",
        "buy",
        "refund",
    ),
    "research": (
        "research",
        "web search",
        "search the web",
        "search online",
        "browse the web",
        "find online",
        "latest news",
        "current information",
        "external sources",
    ),
    "human_review": (
        "human review",
        "human approval",
        "manual approval",
        "manager approval",
        "review by a human",
        "ask a human",
        "escalate to human",
        "human in the loop",
        "human-in-the-loop",
    ),
}


HIGH_RISK_PATTERNS: tuple[str, ...] = (
    "drop table",
    "truncate table",
    "delete from",
    "delete",
    "remove",
    "transfer money",
    "wire money",
    "payment",
    "bank account",
    "send email",
    "send an email",
    "email someone",
    "approve invoice",
    "purchase",
    "buy",
    "refund",
    "create calendar event",
    "schedule a meeting",
    "create github issue",
)


ROUTE_PRIORITIES: tuple[AgentRoute, ...] = (
    "human_review",
    "tool",
    "sql",
    "rag",
    "research",
)


RESUMABLE_ROUTES: tuple[AgentRoute, ...] = (
    "chat",
    "rag",
    "research",
    "tool",
    "sql",
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
        return {
            "route": "chat",
            "planner_reason": (
                "Selected the 'chat' route because no valid "
                "user message was available."
            ),
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

    normalized_message = _normalize_text(
        latest_user_message,
    )

    high_risk_action = _detect_high_risk_action(
        normalized_message,
    )

    if high_risk_action is not None:
        resume_route = _detect_resume_route(
            normalized_message=normalized_message,
            high_risk_action=high_risk_action,
        )

        reason = (
            "Selected the 'human_review' route because "
            "the request contains the high-risk action "
            f"'{high_risk_action}'."
        )

        return {
            "route": "human_review",
            "planner_reason": reason,
            "requires_human_review": True,
            "review_status": "pending",
            "review_reason": reason,
            "review_id": None,
            "approval_granted": False,
            "approved_review_id": None,
            "requested_action": high_risk_action,
            "request_content": latest_user_message,
            "action_payload": {
                "original_route": resume_route,
                "resume_route": resume_route,
                "requested_action": high_risk_action,
                "request_content": latest_user_message,
                "approval_required": True,
            },
        }

    route, reason = _detect_route(
        latest_user_message,
    )

    requires_human_review = route == "human_review"

    return {
        "route": route,
        "planner_reason": reason,
        "requires_human_review": requires_human_review,
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
            }
            if requires_human_review
            else None
        ),
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
        return _route_from_requested_action(
            requested_action,
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

    if request_content:
        normalized_content = _normalize_text(
            request_content,
        )

        return _detect_resume_route(
            normalized_message=normalized_content,
            high_risk_action="approved_action",
        )

    return "chat"


def _detect_route(
    user_message: str,
) -> tuple[AgentRoute, str]:
    normalized_message = _normalize_text(
        user_message,
    )

    for route in ROUTE_PRIORITIES:
        keywords = ROUTE_KEYWORDS.get(
            route,
            (),
        )

        matched_keyword = next(
            (
                keyword
                for keyword in keywords
                if keyword in normalized_message
            ),
            None,
        )

        if matched_keyword is None:
            continue

        return (
            route,
            (
                f"Selected the '{route}' route because "
                "the request matched the routing signal "
                f"'{matched_keyword}'."
            ),
        )

    return (
        "chat",
        (
            "Selected the 'chat' route because no specialized "
            "workflow signals were detected."
        ),
    )


def _detect_resume_route(
    *,
    normalized_message: str,
    high_risk_action: str,
) -> AgentRoute:
    sql_keywords = ROUTE_KEYWORDS[
        "sql"
    ]

    if any(
        keyword in normalized_message
        for keyword in sql_keywords
    ):
        return "sql"

    tool_keywords = ROUTE_KEYWORDS[
        "tool"
    ]

    if any(
        keyword in normalized_message
        for keyword in tool_keywords
    ):
        return "tool"

    if high_risk_action in {
        "transfer money",
        "wire money",
        "payment",
        "bank account",
        "send email",
        "send an email",
        "email someone",
        "approve invoice",
        "purchase",
        "buy",
        "refund",
        "create calendar event",
        "schedule a meeting",
        "create github issue",
    }:
        return "tool"

    if high_risk_action in {
        "drop table",
        "truncate table",
        "delete from",
    }:
        return "sql"

    return "chat"


def _route_from_requested_action(
    requested_action: str,
) -> AgentRoute:
    normalized_action = _normalize_text(
        requested_action,
    )

    return _detect_resume_route(
        normalized_message=normalized_action,
        high_risk_action=normalized_action,
    )


def _detect_high_risk_action(
    normalized_message: str,
) -> str | None:
    for pattern in HIGH_RISK_PATTERNS:
        if pattern in normalized_message:
            return pattern

    return None


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