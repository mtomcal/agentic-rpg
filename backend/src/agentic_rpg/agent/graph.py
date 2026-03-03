"""LangGraph agent graph for processing player actions."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


class AgentState(dict):
    """Typed state flowing through every node of the agent graph.

    Keys:
        messages: List of LangChain messages, auto-merged via add_messages.
    """

    messages: Annotated[list[BaseMessage], add_messages]


def should_execute_tools(state: AgentState) -> Literal["tools", "respond"]:
    """Route based on whether the last message contains tool calls.

    Returns:
        "tools" if the last message has tool_calls, else "respond".
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "respond"


def build_agent_graph(
    tools: list[Any],
    chat_model: Any,
    recursion_limit: int = 25,
) -> Any:
    """Construct the LangGraph state graph for the RPG agent.

    The recursion_limit is stored as default config on the compiled graph.
    It limits how many node steps the graph can take before raising
    GraphRecursionError.

    Args:
        tools: List of LangChain tool objects for binding to the model.
        chat_model: A LangChain chat model (or fake) supporting ainvoke.
        recursion_limit: Max graph steps before raising GraphRecursionError.

    Returns:
        A compiled LangGraph StateGraph.
    """
    # Bind tools to model if tools are provided
    if tools:
        try:
            model = chat_model.bind_tools(tools)
        except NotImplementedError:
            model = chat_model
    else:
        model = chat_model

    # -- Node: call the LLM ---
    async def call_model(state: AgentState) -> dict:
        response = await model.ainvoke(state["messages"])
        return {"messages": [response]}

    # -- Node: deliver final response (terminal) ---
    async def deliver_response(state: AgentState) -> dict:
        # No-op pass-through — the last AI message is the response
        return {}

    # -- Build the graph ---
    graph = StateGraph(AgentState)

    graph.add_node("call_model", call_model)
    graph.add_node("deliver_response", deliver_response)

    if tools:
        tool_node = ToolNode(tools)
        graph.add_node("execute_tools", tool_node)
        graph.add_edge("execute_tools", "call_model")

    graph.set_entry_point("call_model")
    graph.add_conditional_edges(
        "call_model",
        should_execute_tools,
        {"tools": "execute_tools" if tools else "deliver_response", "respond": "deliver_response"},
    )
    graph.add_edge("deliver_response", END)

    compiled = graph.compile()
    # Attach recursion_limit as default config so callers don't need to pass it
    compiled.recursion_limit = recursion_limit
    return compiled
