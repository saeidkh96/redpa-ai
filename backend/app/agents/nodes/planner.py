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
    messages = state.get("messages", [])

    for message in reversed(messages):
        if message.get("role") != "user":
            continue

        content = message.get("content", "")

        if not isinstance(content, str):
            continue

        normalized_content = content.strip()

        if normalized_content:
            return normalized_content

    return None


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

        matched_keywords = [
            keyword
            for keyword in keywords
            if keyword in normalized_message
        ]

        if matched_keywords:
            matched_keyword = matched_keywords[0]

            return (
                route,
                (
                    f"Selected the '{route}' route because "
                    f"the request matched the routing signal "
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
        }

    route, reason = _detect_route(
        latest_user_message,
    )

    return {
        "route": route,
        "planner_reason": reason,
    }