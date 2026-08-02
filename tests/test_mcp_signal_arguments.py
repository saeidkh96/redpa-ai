from app.agents.nodes.tool import (
    _extract_signal_arguments,
)


def test_extracts_tool_arguments_from_signal() -> None:
    arguments = _extract_signal_arguments(
        [
            "dynamic mcp selection",
            (
                'tool_arguments_json:'
                '{"query":"LangGraph","limit":5}'
            ),
        ]
    )

    assert arguments == {
        "query": "LangGraph",
        "limit": 5,
    }
