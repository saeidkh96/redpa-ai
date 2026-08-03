from typing import Any, Literal, TypedDict


AgentRoute = Literal[
    "chat",
    "rag",
    "research",
    "a2a",
    "tool",
    "sql",
    "human_review",
]


PlannerProvider = Literal[
    "ollama",
    "rule_based",
    "resume",
]


ReviewStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "cancelled",
]


class AgentState(TypedDict, total=False):
    conversation_id: str
    user_id: str

    messages: list[dict[str, str]]

    route: AgentRoute

    planner_reason: str
    planner_confidence: float
    planner_provider: PlannerProvider
    planner_model: str | None
    planner_fallback: bool
    planner_error: str | None
    planner_latency_ms: float
    planner_signals: list[str]

    response_content: str
    model: str
    provider: str

    usage: dict[str, Any]

    requires_human_review: bool
    review_status: ReviewStatus | None
    review_reason: str | None
    review_id: str | None

    approval_granted: bool
    approved_review_id: str | None

    requested_action: str | None
    request_content: str | None
    action_payload: dict[str, Any] | None

    reviewed_by: str | None
    reviewed_at: str | None
    reviewer_feedback: str | None

    selected_tool: str | None
    tool_arguments: dict[str, Any] | None
    tool_result: Any | None
    tool_success: bool
    tool_error: str | None
    tool_execution_time_ms: float
    tool_metadata: dict[str, Any] | None

    research_query: str | None
    research_evidence: list[dict[str, Any]]
    research_sources: list[dict[str, Any]]
    research_summary: str | None
    research_provider: str | None
    research_error: str | None
    research_execution_time_ms: float

    completed: bool
    error: str | None