from typing import Any, Literal, TypedDict


AgentRoute = Literal[
    "chat",
    "rag",
    "research",
    "tool",
    "sql",
    "human_review",
]


class AgentState(TypedDict, total=False):
    conversation_id: str
    user_id: str

    messages: list[dict[str, str]]

    route: AgentRoute
    planner_reason: str

    response_content: str
    model: str
    provider: str

    usage: dict[str, Any]

    completed: bool
    error: str | None