import re

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
    "delete",
    "remove",
    "drop table",
    "truncate",
    "transfer money",
    "wire money",
    "payment",
    "bank account",
    "send email",
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


def _normalize_text(text: str) -> str:
    normalized = text.casefold()

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()


def _get_latest_user_message(
    state: AgentState,
) -> str | None:
    messages = state.get(
        "messages",
        [],
    )

    for message in reversed(messages):
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


def _detect_high_risk_action(
    normalized_message: str,
) -> str | None:
    for pattern in HIGH_RISK_PATTERNS:
        if pattern in normalized_message:
            return pattern

    return None


def _detect_route(
    user_message: str,
) -> tuple[AgentRoute, str]:
    normalized_message = _normalize_text(
        user_message,
    )

    high_risk_action = _detect_high_risk_action(
        normalized_message,
    )

    if high_risk_action is not None:
        return (
            "human_review",
            (
                "Selected the 'human_review' route because "
                "the request contains the high-risk action "
                f"'{high_risk_action}'."
            ),
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


async def planner_node(
    state: AgentState,
) -> dict[str, object]:
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
    }