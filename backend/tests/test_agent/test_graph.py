"""Tests for the agent graph (agent/graph.py)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from agentic_rpg.agent.graph import AgentState, build_agent_graph, should_execute_tools
from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.game_state import GameState


# ---------------------------------------------------------------------------
# Helpers: Fake LLM that cycles through predetermined responses
# ---------------------------------------------------------------------------
class FakeChatModel:
    """A fake chat model that returns predetermined AIMessage responses.

    Supports bind_tools() (no-op) and ainvoke() for use with LangGraph.
    """

    def __init__(self, responses: list[AIMessage]) -> None:
        self._responses = list(responses)
        self._idx = 0

    def bind_tools(self, tools: list, **kwargs: Any) -> "FakeChatModel":
        """No-op bind_tools — returns self."""
        return self

    async def ainvoke(self, messages: list[BaseMessage], **kwargs: Any) -> AIMessage:
        msg = self._responses[self._idx % len(self._responses)]
        self._idx += 1
        return msg


class FakeChatModelWithUniqueIds:
    """A fake model that always returns tool calls with unique IDs.

    Used to test recursion limit — without unique IDs, add_messages
    deduplicates and the graph terminates early.
    """

    def __init__(self, tool_name: str) -> None:
        self._tool_name = tool_name
        self._idx = 0

    def bind_tools(self, tools: list, **kwargs: Any) -> "FakeChatModelWithUniqueIds":
        return self

    async def ainvoke(self, messages: list[BaseMessage], **kwargs: Any) -> AIMessage:
        call_id = f"call_{self._idx}"
        self._idx += 1
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": self._tool_name,
                    "args": {},
                    "id": call_id,
                    "type": "tool_call",
                }
            ],
        )


# ---------------------------------------------------------------------------
# Helpers: Simple LangChain tools for testing
# ---------------------------------------------------------------------------
@tool
def get_character_name() -> str:
    """Return the character's name."""
    return "Aldric"


@tool
def get_location_name() -> str:
    """Return the current location name."""
    return "The Rusty Flagon"


# ---------------------------------------------------------------------------
# Tests: should_execute_tools routing function
# ---------------------------------------------------------------------------
class TestShouldExecuteTools:
    """Tests for the should_execute_tools routing function."""

    def test_returns_tools_when_tool_calls_present(self) -> None:
        """Routes to 'tools' when the last message has tool_calls."""
        state: AgentState = {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {"name": "get_character_name", "args": {}, "id": "call_1", "type": "tool_call"}
                    ],
                )
            ],
        }
        assert should_execute_tools(state) == "tools"

    def test_returns_respond_when_no_tool_calls(self) -> None:
        """Routes to 'respond' when the last message has no tool_calls."""
        state: AgentState = {
            "messages": [AIMessage(content="The tavern is quiet.")],
        }
        assert should_execute_tools(state) == "respond"

    def test_returns_respond_for_empty_tool_calls_list(self) -> None:
        """Routes to 'respond' when tool_calls is an empty list."""
        state: AgentState = {
            "messages": [AIMessage(content="Done.", tool_calls=[])],
        }
        assert should_execute_tools(state) == "respond"

    def test_returns_respond_when_last_message_is_not_ai(self) -> None:
        """Routes to 'respond' when the last message is a HumanMessage."""
        state: AgentState = {
            "messages": [HumanMessage(content="I look around.")],
        }
        assert should_execute_tools(state) == "respond"

    def test_returns_respond_when_last_message_is_tool_message(self) -> None:
        """Routes to 'respond' when the last message is a ToolMessage."""
        state: AgentState = {
            "messages": [ToolMessage(content="Aldric", tool_call_id="call_1")],
        }
        assert should_execute_tools(state) == "respond"


# ---------------------------------------------------------------------------
# Tests: build_agent_graph
# ---------------------------------------------------------------------------
class TestBuildAgentGraph:
    """Tests for the build_agent_graph function."""

    def test_graph_compiles_with_no_tools(self) -> None:
        """build_agent_graph returns a compiled graph with expected nodes."""
        from langgraph.graph.state import CompiledStateGraph

        model = FakeChatModel([AIMessage(content="Hello")])
        graph = build_agent_graph(tools=[], chat_model=model)
        assert isinstance(graph, CompiledStateGraph)
        # Should have call_model and deliver_response nodes (plus __start__, __end__)
        node_names = set(graph.nodes.keys())
        assert "call_model" in node_names
        assert "deliver_response" in node_names
        # No execute_tools node when no tools given
        assert "execute_tools" not in node_names

    def test_graph_compiles_with_tools(self) -> None:
        """build_agent_graph returns a compiled graph with tool execution node."""
        from langgraph.graph.state import CompiledStateGraph

        model = FakeChatModel([AIMessage(content="Hello")])
        graph = build_agent_graph(
            tools=[get_character_name, get_location_name],
            chat_model=model,
        )
        assert isinstance(graph, CompiledStateGraph)
        node_names = set(graph.nodes.keys())
        assert "call_model" in node_names
        assert "deliver_response" in node_names
        assert "execute_tools" in node_names

    def test_bind_tools_not_implemented_fallback(self) -> None:
        """Graph still works when model's bind_tools raises NotImplementedError."""

        class NoBind:
            def bind_tools(self, tools: list, **kwargs: Any) -> Any:
                raise NotImplementedError

            async def ainvoke(self, messages: list, **kwargs: Any) -> AIMessage:
                return AIMessage(content="Fallback response")

        graph = build_agent_graph(
            tools=[get_character_name],
            chat_model=NoBind(),
        )
        assert "call_model" in graph.nodes

    def test_default_recursion_limit(self) -> None:
        """Default recursion_limit is 25 when not specified."""
        model = FakeChatModel([AIMessage(content="Hello")])
        graph = build_agent_graph(tools=[], chat_model=model)
        assert graph.recursion_limit == 25


# ---------------------------------------------------------------------------
# Tests: Graph execution — simple action (no tool calls)
# ---------------------------------------------------------------------------
class TestGraphSimpleAction:
    """Tests for graph execution with no tool calls."""

    @pytest.fixture
    def simple_graph(self) -> Any:
        """A graph where the LLM responds with plain text (no tool calls)."""
        model = FakeChatModel([AIMessage(content="The tavern is dimly lit.")])
        return build_agent_graph(tools=[], chat_model=model)

    async def test_simple_action_returns_messages(self, simple_graph: Any) -> None:
        """Graph produces messages including the LLM response."""
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="I look around."),
            ],
        }
        result = await simple_graph.ainvoke(initial_state)
        messages = result["messages"]
        # Should have: system + human + AI response
        assert len(messages) >= 3
        # Last message should be from the AI
        last_msg = messages[-1]
        assert isinstance(last_msg, AIMessage)
        assert last_msg.content == "The tavern is dimly lit."

    async def test_simple_action_preserves_input_messages(self, simple_graph: Any) -> None:
        """Input messages (system, human) are preserved in the output."""
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="I look around."),
            ],
        }
        result = await simple_graph.ainvoke(initial_state)
        messages = result["messages"]
        assert isinstance(messages[0], SystemMessage)
        assert messages[0].content == "You are a Game Master."
        assert isinstance(messages[1], HumanMessage)
        assert messages[1].content == "I look around."


class TestGraphWithToolsButNoToolCalls:
    """Tests for graph with tools bound but LLM returns plain text."""

    async def test_tools_bound_but_llm_responds_directly(self) -> None:
        """Graph works when tools are available but LLM chooses not to use them."""
        model = FakeChatModel([AIMessage(content="You see a tavern.")])
        graph = build_agent_graph(
            tools=[get_character_name, get_location_name],
            chat_model=model,
        )
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="I look around."),
            ],
        }
        result = await graph.ainvoke(initial_state)
        messages = result["messages"]
        last_msg = messages[-1]
        assert isinstance(last_msg, AIMessage)
        assert last_msg.content == "You see a tavern."
        # No tool messages should be present
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 0


# ---------------------------------------------------------------------------
# Tests: Graph execution — single tool call
# ---------------------------------------------------------------------------
class TestGraphWithToolCalls:
    """Tests for graph execution involving tool calls."""

    @pytest.fixture
    def tool_then_respond_graph(self) -> Any:
        """Graph where LLM first calls a tool, then responds with text."""
        responses = [
            # First call: LLM wants to call get_character_name
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_character_name",
                        "args": {},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            ),
            # Second call: after tool result, LLM gives final narrative
            AIMessage(content="Aldric surveys the room."),
        ]
        model = FakeChatModel(responses)
        return build_agent_graph(
            tools=[get_character_name, get_location_name],
            chat_model=model,
        )

    async def test_tool_call_followed_by_response(self, tool_then_respond_graph: Any) -> None:
        """LLM calls a tool, gets result, then produces narrative."""
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="What is my name?"),
            ],
        }
        result = await tool_then_respond_graph.ainvoke(initial_state)
        messages = result["messages"]
        # Should contain: system, human, AI(tool_call), tool_result, AI(narrative)
        assert len(messages) >= 5
        # Final message should be narrative
        last_msg = messages[-1]
        assert isinstance(last_msg, AIMessage)
        assert last_msg.content == "Aldric surveys the room."

    async def test_tool_result_in_messages(self, tool_then_respond_graph: Any) -> None:
        """Tool execution result appears as a ToolMessage in the message list."""
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="What is my name?"),
            ],
        }
        result = await tool_then_respond_graph.ainvoke(initial_state)
        messages = result["messages"]
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 1
        assert "Aldric" in tool_msgs[0].content


# ---------------------------------------------------------------------------
# Tests: Graph execution — multiple tool calls in sequence
# ---------------------------------------------------------------------------
class TestGraphMultipleToolCalls:
    """Tests for graph execution with multiple sequential tool calls."""

    @pytest.fixture
    def multi_tool_graph(self) -> Any:
        """Graph where LLM calls two tools sequentially then responds."""
        responses = [
            # First call: ask for character name
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_character_name",
                        "args": {},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            ),
            # Second call: ask for location name
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_location_name",
                        "args": {},
                        "id": "call_2",
                        "type": "tool_call",
                    }
                ],
            ),
            # Third call: final narrative
            AIMessage(content="Aldric sits in The Rusty Flagon."),
        ]
        model = FakeChatModel(responses)
        return build_agent_graph(
            tools=[get_character_name, get_location_name],
            chat_model=model,
        )

    async def test_multiple_tool_calls_produce_final_narrative(
        self, multi_tool_graph: Any
    ) -> None:
        """LLM calls two tools sequentially, then produces final narrative."""
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="Where am I and who am I?"),
            ],
        }
        result = await multi_tool_graph.ainvoke(initial_state)
        messages = result["messages"]
        # Final message is narrative
        last_msg = messages[-1]
        assert isinstance(last_msg, AIMessage)
        assert last_msg.content == "Aldric sits in The Rusty Flagon."
        # Should have two ToolMessages
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        assert len(tool_msgs) == 2

    async def test_both_tool_results_present(self, multi_tool_graph: Any) -> None:
        """Both tool results are present in the message history."""
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="Where am I and who am I?"),
            ],
        }
        result = await multi_tool_graph.ainvoke(initial_state)
        messages = result["messages"]
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        tool_contents = [m.content for m in tool_msgs]
        assert any("Aldric" in c for c in tool_contents)
        assert any("Rusty Flagon" in c for c in tool_contents)


# ---------------------------------------------------------------------------
# Tests: Recursion limit
# ---------------------------------------------------------------------------
class TestGraphRecursionLimit:
    """Tests for recursion limit enforcement."""

    async def test_recursion_limit_stops_infinite_tool_loop(self) -> None:
        """Graph stops after hitting recursion limit instead of looping forever."""
        # LLM always returns a tool call with unique IDs — would loop forever
        model = FakeChatModelWithUniqueIds("get_character_name")
        graph = build_agent_graph(
            tools=[get_character_name],
            chat_model=model,
            recursion_limit=5,
        )
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="Loop forever."),
            ],
        }
        # Should raise a recursion limit error from langgraph
        from langgraph.errors import GraphRecursionError

        with pytest.raises(GraphRecursionError):
            await graph.ainvoke(initial_state, config={"recursion_limit": 5})

    async def test_recursion_limit_stored_on_graph(self) -> None:
        """The recursion_limit parameter is stored on the compiled graph."""
        model = FakeChatModel([AIMessage(content="Hello")])
        graph = build_agent_graph(
            tools=[],
            chat_model=model,
            recursion_limit=10,
        )
        assert graph.recursion_limit == 10


# ---------------------------------------------------------------------------
# Tests: Parallel tool calls (multiple tool_calls in one AIMessage)
# ---------------------------------------------------------------------------
class TestGraphParallelToolCalls:
    """Tests for parallel tool calls within a single AI message."""

    async def test_parallel_tool_calls_both_executed(self) -> None:
        """When LLM returns multiple tool_calls in one message, both are executed."""
        responses = [
            # Single message with two tool calls
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_character_name",
                        "args": {},
                        "id": "call_a",
                        "type": "tool_call",
                    },
                    {
                        "name": "get_location_name",
                        "args": {},
                        "id": "call_b",
                        "type": "tool_call",
                    },
                ],
            ),
            # After both tool results, final narrative
            AIMessage(content="Aldric is at The Rusty Flagon."),
        ]
        model = FakeChatModel(responses)
        graph = build_agent_graph(
            tools=[get_character_name, get_location_name],
            chat_model=model,
        )
        initial_state: AgentState = {
            "messages": [
                SystemMessage(content="You are a Game Master."),
                HumanMessage(content="Tell me about myself and where I am."),
            ],
        }
        result = await graph.ainvoke(initial_state)
        messages = result["messages"]
        tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
        # Both tools should be called
        assert len(tool_msgs) == 2
        last_msg = messages[-1]
        assert isinstance(last_msg, AIMessage)
        assert last_msg.content == "Aldric is at The Rusty Flagon."
