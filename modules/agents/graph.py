"""LangGraph wiring: router -> tool calls -> end.

The tools are injected as a dict of callables that take the question. The adapters that
turn a question into tool arguments (KPI name, year, keys) are not part of this version.
Requires langgraph (see requirements.txt).
"""
from typing import Callable, TypedDict

from langgraph.graph import END, StateGraph

from .router import MAX_TOOL_CALLS, route


class AgentState(TypedDict):
    question: str
    pending: list[str]
    results: dict
    calls: int


def build_graph(tools: dict[str, Callable[[str], object]]):
    """Compile the agent graph. Every name returned by route() must be a key of tools."""

    def router_node(state: AgentState) -> dict:
        return {"pending": route(state["question"]), "results": {}, "calls": 0}

    def tool_node(state: AgentState) -> dict:
        if not state["pending"] or state["calls"] >= MAX_TOOL_CALLS:
            return {"pending": []}
        name, rest = state["pending"][0], state["pending"][1:]
        result = tools[name](state["question"])
        return {
            "pending": rest,
            "results": {**state["results"], name: result},
            "calls": state["calls"] + 1,
        }

    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("tool", tool_node)
    graph.set_entry_point("router")
    graph.add_edge("router", "tool")
    graph.add_conditional_edges("tool", lambda s: "tool" if s["pending"] else END)
    return graph.compile()