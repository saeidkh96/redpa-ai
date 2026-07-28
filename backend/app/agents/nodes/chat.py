from app.agents.state import AgentState
from app.clients.ollama_client import ollama_client
from app.core.exceptions import LLMInvalidResponseError
from app.schemas.ollama import OllamaChatMessage


ALLOWED_LLM_ROLES = {
    "system",
    "user",
    "assistant",
    "tool",
}


async def chat_node(
    state: AgentState,
) -> dict[str, object]:
    raw_messages = state.get("messages", [])

    if not raw_messages:
        raise LLMInvalidResponseError(
            "The orchestrator received no messages."
        )

    ollama_messages: list[OllamaChatMessage] = []

    for raw_message in raw_messages:
        role = raw_message.get("role")
        content = raw_message.get("content", "").strip()

        if role not in ALLOWED_LLM_ROLES:
            continue

        if not content:
            continue

        ollama_messages.append(
            OllamaChatMessage(
                role=role,
                content=content,
            )
        )

    if not ollama_messages:
        raise LLMInvalidResponseError(
            "The orchestrator could not build a valid LLM request."
        )

    ollama_response = await ollama_client.chat(
        messages=ollama_messages,
    )

    response_content = (
        ollama_response.message.content.strip()
    )

    if not response_content:
        raise LLMInvalidResponseError(
            "The chat agent returned an empty response."
        )

    return {
        "response_content": response_content,
        "model": ollama_response.model,
        "provider": "ollama",
        "usage": {
            "prompt_eval_count": (
                ollama_response.prompt_eval_count
            ),
            "eval_count": ollama_response.eval_count,
            "total_duration": (
                ollama_response.total_duration
            ),
            "load_duration": (
                ollama_response.load_duration
            ),
            "prompt_eval_duration": (
                ollama_response.prompt_eval_duration
            ),
            "eval_duration": (
                ollama_response.eval_duration
            ),
        },
    }