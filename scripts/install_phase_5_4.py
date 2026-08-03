from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def patch(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")

    if new in text:
        print(f"{label}: already installed")
        return

    if old not in text:
        raise SystemExit(f"Could not patch {label} in {path}")

    path.write_text(
        text.replace(old, new, 1),
        encoding="utf-8",
    )

    print(f"{label}: installed")


def main() -> None:
    state = ROOT / "backend/app/agents/state.py"
    router = ROOT / "backend/app/agents/router.py"
    graph = ROOT / "backend/app/agents/graph.py"
    planner_service = ROOT / "backend/app/services/planner_service.py"
    planner_node = ROOT / "backend/app/agents/nodes/planner.py"

    patch(
        state,
        '    "research",\n    "tool",\n',
        '    "research",\n    "a2a",\n    "tool",\n',
        "AgentRoute",
    )

    patch(
        router,
        '    "research",\n    "tool",\n',
        '    "research",\n    "a2a",\n    "tool",\n',
        "GraphDestination",
    )

    patch(
        router,
        '    "research": "research",\n    "tool": "tool",\n',
        '    "research": "research",\n    "a2a": "a2a",\n    "tool": "tool",\n',
        "route mapping",
    )

    patch(
        router,
        '        "web_research": "research",\n        "web_search": "research",\n',
        (
            '        "web_research": "research",\n'
            '        "web_search": "research",\n'
            '        "a2a": "a2a",\n'
            '        "remote_agent": "a2a",\n'
            '        "remote_delegation": "a2a",\n'
        ),
        "route aliases",
    )

    patch(
        graph,
        'from app.agents.nodes.capability_unavailable import (\n',
        (
            'from app.agents.nodes.a2a import a2a_node\n'
            'from app.agents.nodes.capability_unavailable import (\n'
        ),
        "a2a node import",
    )

    patch(
        graph,
        '    graph_builder.add_node(\n        "tool",\n        tool_node,\n    )\n',
        (
            '    graph_builder.add_node(\n'
            '        "a2a",\n'
            '        a2a_node,\n'
            '    )\n\n'
            '    graph_builder.add_node(\n'
            '        "tool",\n'
            '        tool_node,\n'
            '    )\n'
        ),
        "a2a graph node",
    )

    patch(
        graph,
        '            "research": "research",\n            "tool": "tool",\n',
        (
            '            "research": "research",\n'
            '            "a2a": "a2a",\n'
            '            "tool": "tool",\n'
        ),
        "a2a conditional edge",
    )

    patch(
        graph,
        '    graph_builder.add_edge(\n        "tool",\n        "response",\n    )\n',
        (
            '    graph_builder.add_edge(\n'
            '        "a2a",\n'
            '        "response",\n'
            '    )\n\n'
            '    graph_builder.add_edge(\n'
            '        "tool",\n'
            '        "response",\n'
            '    )\n'
        ),
        "a2a response edge",
    )

    patch(
        planner_service,
        '                "research",\n                "tool",\n',
        (
            '                "research",\n'
            '                "a2a",\n'
            '                "tool",\n'
        ),
        "planner JSON route",
    )

    patch(
        planner_service,
        '    "research": (\n        r"^\\s*research\\b",\n',
        (
            '    "a2a": (\n'
            '        r"\\bvia\\s+a2a\\b",\n'
            '        r"\\buse\\s+(the\\s+)?remote\\s+agent\\b",\n'
            '        r"\\bask\\s+(the\\s+)?remote\\s+(agent|coordinator)\\b",\n'
            '        r"\\bdelegate\\s+.+\\s+to\\s+(the\\s+)?remote\\s+agent\\b",\n'
            '        r"\\bremote\\s+a2a\\b",\n'
            '    ),\n'
            '    "research": (\n'
            '        r"^\\s*research\\b",\n'
        ),
        "planner route patterns",
    )

    patch(
        planner_service,
        'ROUTE_PRIORITY: tuple[AgentRoute, ...] = (\n    "human_review",\n',
        (
            'ROUTE_PRIORITY: tuple[AgentRoute, ...] = (\n'
            '    "human_review",\n'
            '    "a2a",\n'
        ),
        "planner route priority",
    )

    patch(
        planner_service,
        'DETERMINISTIC_RESEARCH_PATTERNS: tuple[str, ...] = (\n',
        (
            'DETERMINISTIC_A2A_PATTERNS: tuple[str, ...] = (\n'
            '    r"\\bvia\\s+a2a\\b",\n'
            '    r"\\buse\\s+(the\\s+)?remote\\s+agent\\b",\n'
            '    r"\\bask\\s+(the\\s+)?remote\\s+(agent|coordinator)\\b",\n'
            '    r"\\bdelegate\\s+.+\\s+to\\s+(the\\s+)?remote\\s+agent\\b",\n'
            '    r"\\bremote\\s+a2a\\b",\n'
            ')\n\n\n'
            'DETERMINISTIC_RESEARCH_PATTERNS: tuple[str, ...] = (\n'
        ),
        "deterministic a2a patterns",
    )

    patch(
        planner_service,
        '        research_signal = cls._match_first_pattern(\n',
        (
            '        a2a_signal = cls._match_first_pattern(\n'
            '            value=normalized_message,\n'
            '            patterns=DETERMINISTIC_A2A_PATTERNS,\n'
            '        )\n\n'
            '        if a2a_signal is not None:\n'
            '            return PlannerResult(\n'
            '                route="a2a",\n'
            '                confidence=1.0,\n'
            '                reasoning=(\n'
            '                    "Selected the a2a route because the "\n'
            '                    "request explicitly asks for remote A2A "\n'
            '                    "delegation."\n'
            '                ),\n'
            '                signals=[\n'
            '                    a2a_signal,\n'
            '                    "a2a",\n'
            '                    "remote delegation",\n'
            '                ],\n'
            '            )\n\n'
            '        research_signal = cls._match_first_pattern(\n'
        ),
        "deterministic a2a planning",
    )

    patch(
        planner_node,
        '    "research",\n    "tool",\n',
        '    "research",\n    "a2a",\n    "tool",\n',
        "resumable a2a route",
    )

    print("Phase 5.4 installed successfully")


if __name__ == "__main__":
    main()
