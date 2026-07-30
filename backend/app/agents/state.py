from typing import Any, Literal, TypedDict


AgentRoute = Literal[
    "chat",
    "rag",
    "research",
    "tool",
    "sql",
    "human_review",
]


ReviewStatus = Literal[
    "pending",
    "approved",
    "rejected",
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

    requires_human_review: bool
    review_status: ReviewStatus | None
    review_reason: str | None
    review_id: str | None
    reviewed_by: str | None
    reviewed_at: str | None
    reviewer_feedback: str | None

    completed: bool
    error: str | None