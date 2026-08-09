from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BoundedContext:
    name: str
    responsibility: str
    modules: tuple[str, ...]


CONTEXTS: tuple[BoundedContext, ...] = (
    BoundedContext(
        name="agent_orchestration",
        responsibility="Planning, routing, agents, and workflows.",
        modules=("agents", "workflows", "services"),
    ),
    BoundedContext(
        name="knowledge_retrieval",
        responsibility="Documents, embeddings, RAG, and semantic retrieval.",
        modules=("rag", "documents"),
    ),
    BoundedContext(
        name="human_oversight",
        responsibility="Human review, approval, rejection, and resume.",
        modules=("models.human_review", "services.human_review_service"),
    ),
    BoundedContext(
        name="tooling_integration",
        responsibility="Internal tools, unified tools, and MCP.",
        modules=("tools", "mcp"),
    ),
    BoundedContext(
        name="model_runtime",
        responsibility="Provider-neutral model execution.",
        modules=("model_gateway",),
    ),
    BoundedContext(
        name="policy_governance",
        responsibility="Policy, guardrails, risk, enforcement, and audit.",
        modules=("guardrails", "services.policy_enforcement_service"),
    ),
    BoundedContext(
        name="platform_operations",
        responsibility="Auth, jobs, observability, health, and runtime services.",
        modules=("middleware", "monitoring", "runtime"),
    ),
)


def context_names() -> tuple[str, ...]:
    return tuple(context.name for context in CONTEXTS)
