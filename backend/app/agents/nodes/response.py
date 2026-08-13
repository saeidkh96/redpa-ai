from app.agents.state import AgentState
from app.core.exceptions import LLMInvalidResponseError


async def response_node(
    state: AgentState,
) -> dict[str, object]:
    response_content = state.get(
        "response_content",
        "",
    ).strip()

    if not response_content:
        raise LLMInvalidResponseError(
            "The workflow completed without generating a response."
        )

    model = state.get("model", "").strip()
    provider = state.get("provider", "").strip()

    if not model:
        raise LLMInvalidResponseError(
            "The workflow did not return the model name."
        )

    if not provider:
        raise LLMInvalidResponseError(
            "The workflow did not return the provider name."
        )

    return {
        "response_content": response_content,
        "model": model,
        "provider": provider,
        "completed": True,
        "error": None,
    }