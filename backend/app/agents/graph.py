from langgraph.graph import END, START, StateGraph

from app.agents.nodes.chat import chat_node
from app.agents.nodes.planner import planner_node
from app.agents.nodes.response import response_node
from app.agents.state import AgentState


def create_agent_graph():
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
        "response",
        response_node,
    )

    graph_builder.add_edge(
        START,
        "planner",
    )

    graph_builder.add_edge(
        "planner",
        "chat",
    )

    graph_builder.add_edge(
        "chat",
        "response",
    )

    graph_builder.add_edge(
        "response",
        END,
    )

    return graph_builder.compile()


agent_graph = create_agent_graph()