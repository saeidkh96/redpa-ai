from app.agents.state import AgentState


async def planner_node(
    state: AgentState,
) -> dict[str, object]:
    messages = state.get("messages", [])

    if not messages:
        return {
            "route": "chat",
            "planner_reason": (
                "No message history was supplied. "
                "Using the default chat workflow."
            ),
        }

    latest_user_message = next(
        (
            message
            for message in reversed(messages)
            if message.get("role") == "user"
        ),
        None,
    )

    if latest_user_message is None:
        return {
            "route": "chat",
            "planner_reason": (
                "No user message was found. "
                "Using the default chat workflow."
            ),
        }

    return {
        "route": "chat",
        "planner_reason": (
            "The chat workflow is currently the only enabled route."
        ),
    }