from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.nodes.a2a import a2a_node
from app.agents.nodes.capability_unavailable import (
    capability_unavailable_node,
)
from app.agents.nodes.chat import chat_node
from app.agents.nodes.human_review import (
    human_review_node,
)
from app.agents.nodes.planner import planner_node
from app.agents.nodes.rag import rag_node
from app.agents.nodes.research import research_node
from app.agents.nodes.response import response_node
from app.agents.nodes.tool import tool_node
from app.agents.router import route_after_planner
from app.agents.state import AgentState


def create_agent_graph() -> CompiledStateGraph:
    graph_builder = StateGraph(
        AgentState,
    )

    graph_builder.add_node(
        "planner",
        planner_node,
    )

    graph_builder.add_node(
        "chat",
        chat_node,
    )

    graph_builder.add_node(
        "rag",
        rag_node,
    )

    graph_builder.add_node(
        "research",
        research_node,
    )

    graph_builder.add_node(
        "a2a",
        a2a_node,
    )

    graph_builder.add_node(
        "tool",
        tool_node,
    )

    graph_builder.add_node(
        "human_review",
        human_review_node,
    )

    graph_builder.add_node(
        "capability_unavailable",
        capability_unavailable_node,
    )

    graph_builder.add_node(
        "response",
        response_node,
    )

    graph_builder.add_edge(
        START,
        "planner",
    )

    graph_builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "chat": "chat",
            "rag": "rag",
            "research": "research",
            "a2a": "a2a",
            "tool": "tool",
            "human_review": "human_review",
            "capability_unavailable": (
                "capability_unavailable"
            ),
        },
    )

    graph_builder.add_edge(
        "chat",
        "response",
    )

    graph_builder.add_edge(
        "rag",
        "response",
    )

    graph_builder.add_edge(
        "research",
        "response",
    )

    graph_builder.add_edge(
        "a2a",
        "response",
    )

    graph_builder.add_edge(
        "tool",
        "response",
    )

    graph_builder.add_edge(
        "human_review",
        "response",
    )

    graph_builder.add_edge(
        "capability_unavailable",
        "response",
    )

    graph_builder.add_edge(
        "response",
        END,
    )

    return graph_builder.compile()


agent_graph = create_agent_graph()