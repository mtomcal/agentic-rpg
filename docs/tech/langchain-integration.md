# Technology Choice: LangChain / LangGraph / LangSmith

## Decision

Use LangChain for LLM abstraction and tool definitions, LangGraph for agent workflow orchestration, and LangSmith for observability, tracing, and evaluation.

## Rationale

- **Learning goal**: This project exists to deeply learn LangChain and LangGraph by building a real, complex agent system — not toy examples.
- **Structured agent workflows**: LangGraph provides explicit state machines for agent control flow, making complex multi-step interactions (tool calls, retries, branching) clear and debuggable.
- **Tool ecosystem**: LangChain's `@tool` decorator and `BaseTool` class provide a clean, typed interface for defining game tools with automatic schema generation from Pydantic models.
- **Observability built-in**: LangSmith gives us full traces of every agent run — prompts, tool calls, latencies, token usage — with zero custom instrumentation.
- **Provider flexibility**: LangChain's `ChatModel` abstraction makes switching between Anthropic, OpenAI, or other providers a configuration change.

## Core Components

### LangChain — LLM Abstraction & Tools

LangChain provides:

- **Chat models**: `ChatAnthropic` (primary), `ChatOpenAI` (future). Uniform interface for message passing, streaming, and tool binding.
- **Tool definitions**: `@tool` for simple function tools, `BaseTool` subclass for tools that need complex setup (state access, event emission).
- **Prompt templates**: `ChatPromptTemplate` for composing system prompts, context injection, and few-shot examples.
- **Structured output**: `.with_structured_output(PydanticModel)` for guaranteed schema-conforming responses (story outlines, world state).
- **Memory**: `ConversationBufferMemory` and `ConversationSummaryMemory` for managing conversation history and context window limits.

### LangGraph — Agent Workflow

LangGraph defines the agent as an explicit state graph:

```
                ┌───────────┐
                │  Receive   │
                │   Input    │
                └─────┬─────┘
                      │
                ┌─────▼─────┐
                │  Assemble  │
                │  Context   │
                └─────┬─────┘
                      │
                ┌─────▼─────┐
                │  Call LLM  │◄────────────┐
                └─────┬─────┘              │
                      │                    │
               ┌──────▼──────┐             │
               │  Tool calls? │             │
               └──┬───────┬──┘             │
              yes │       │ no             │
           ┌──────▼────┐  │               │
           │  Execute   │  │               │
           │   Tools    │──┘               │
           └──────┬─────┘                  │
                  │ (tool results added    │
                  │  to messages)          │
                  └────────────────────────┘

                      │ no tool calls
                ┌─────▼─────┐
                │  Return    │
                │  Response  │
                └────────────┘
```

**Nodes**:
- `context_assembly` — Loads game state from DB, builds system prompt with character/location/inventory context, assembles conversation history within token limits
- `call_model` — Invokes the bound chat model (with tools) using assembled messages
- `execute_tools` — Runs tool calls via LangGraph's `ToolNode`, returns `ToolMessage` results
- `deliver_response` — Extracts final narrative text, persists updated game state to DB

**Edges**:
- `context_assembly` → `call_model`
- `call_model` → conditional: if tool calls → `execute_tools`, else → `deliver_response`
- `execute_tools` → `call_model` (loop back with tool results)
- `deliver_response` → `END`

**State schema** (Pydantic model):
```python
from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages

class AgentState(BaseModel):
    """Typed state flowing through every node of the agent graph."""
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)
    session_id: str = ""
    game_state: dict = Field(default_factory=dict)
    system_prompt: str = ""
    tool_call_count: int = 0
    token_usage: int = 0
```

**Graph construction**:
```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

def build_agent_graph(tools: list, chat_model) -> CompiledGraph:
    model_with_tools = chat_model.bind_tools(tools)

    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("context_assembly", context_assembly_node)
    graph.add_node("call_model", call_model_node)
    graph.add_node("execute_tools", ToolNode(tools))
    graph.add_node("deliver_response", deliver_response_node)

    # Define flow
    graph.set_entry_point("context_assembly")
    graph.add_edge("context_assembly", "call_model")
    graph.add_conditional_edges(
        "call_model",
        should_execute_tools,  # returns "tools" or "respond"
        {"tools": "execute_tools", "respond": "deliver_response"},
    )
    graph.add_edge("execute_tools", "call_model")
    graph.add_edge("deliver_response", END)

    return graph.compile()

def should_execute_tools(state: AgentState) -> str:
    """Conditional edge: route to tools or final response."""
    last_message = state.messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "respond"
```

### LangSmith — Observability & Tracing

LangSmith is enabled by setting environment variables. Every LangGraph agent run is automatically traced:

- **Traces**: Full tree of LLM calls, tool executions, and state transitions for each player action
- **Token tracking**: Input/output tokens per call, per run, per session — feeds into cost monitoring
- **Latency**: Time spent in LLM calls vs. tool execution vs. context assembly
- **Debugging**: Replay any trace, inspect prompts and responses, spot issues
- **Evaluation**: Define test cases (player action → expected tool calls / narrative quality) and run evals

No custom instrumentation needed — LangGraph's integration reports everything automatically.

## Tool Definition Pattern

Tools are defined using LangChain's abstractions, with Pydantic models for input validation:

### Simple tools — `@tool` decorator

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class MoveCharacterInput(BaseModel):
    location_id: str = Field(description="ID of the target location")

@tool(args_schema=MoveCharacterInput)
def move_character(location_id: str) -> str:
    """Move the player character to a connected location."""
    # Access game state, validate move, emit event, return result
    ...
```

### Complex tools — `BaseTool` subclass

```python
from langchain_core.tools import BaseTool

class GetCharacterTool(BaseTool):
    name: str = "get_character"
    description: str = "Get the current character's full state"
    state_manager: StateManager  # injected dependency

    def _run(self, **kwargs) -> str:
        return self.state_manager.get_character(kwargs["session_id"])
```

Tools are collected into a list and bound to the chat model via `model.bind_tools(tools)`. LangGraph's `ToolNode` handles execution automatically.

## Streaming with `astream_events`

Agent responses stream to the frontend via WebSocket using LangGraph's `astream_events` API, which provides fine-grained events for every step of the graph execution:

```python
async def stream_agent_response(agent_graph, state, websocket):
    """Stream agent response events to the WebSocket."""
    async for event in agent_graph.astream_events(state, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            # Text chunks — forward immediately for typewriter effect
            chunk = event["data"]["chunk"]
            if chunk.content:
                await websocket.send_json({
                    "type": "agent_response",
                    "data": {"chunk": chunk.content, "done": False},
                })

        elif kind == "on_tool_start":
            # Tool execution started — notify the player
            await websocket.send_json({
                "type": "state_update",
                "data": {"tool": event["name"], "status": "executing"},
            })

        elif kind == "on_tool_end":
            # Tool finished — state may have changed
            await websocket.send_json({
                "type": "state_update",
                "data": {"tool": event["name"], "status": "completed"},
            })

    # Signal that the full response is complete
    await websocket.send_json({
        "type": "agent_response",
        "data": {"chunk": "", "done": True},
    })
```

Key event types from `astream_events(version="v2")`:
- `on_chat_model_stream` — individual text token chunks from the LLM
- `on_chat_model_end` — full LLM response (including tool calls)
- `on_tool_start` / `on_tool_end` — tool execution lifecycle
- `on_chain_start` / `on_chain_end` — node entry/exit in the graph

LangGraph handles the complexity of streaming through a multi-step graph with tool call loops — the stream pauses during tool execution and resumes when the model generates its next response.

## Memory Management

### Conversation History

LangGraph's `add_messages` annotation on the state handles message accumulation. Each turn appends the player's `HumanMessage`, the model's `AIMessage` (with optional tool calls), any `ToolMessage` results, and the final `AIMessage` response.

### Context Window Trimming

The `context_assembly` node trims conversation history to fit within the model's context window:

```python
from langchain_core.messages import trim_messages

async def context_assembly_node(state: AgentState) -> dict:
    game_state = await state_manager.load(state.session_id)
    system_prompt = build_system_prompt(game_state)

    # Trim messages to fit context window, keeping most recent messages
    trimmed = trim_messages(
        state.messages,
        max_tokens=4000,
        strategy="last",
        token_counter=chat_model,
        include_system=True,
    )

    return {
        "messages": trimmed,
        "game_state": game_state.model_dump(),
        "system_prompt": system_prompt,
    }
```

### Session Persistence

Conversation history is stored in PostgreSQL as part of the session's game state JSONB. When a session resumes, messages are deserialized from the database and loaded into the `AgentState`. LangGraph checkpointing can optionally be used for more granular state persistence across turns.

## Cost and Token Management

- LangSmith automatically tracks token usage for every LLM call
- Custom callback handler accumulates per-session token totals
- Per-session token budget (configurable, with sensible default)
- Warn the player when approaching the budget
- Hard stop at the budget limit
- LangSmith dashboard shows cost trends across sessions

## Error Handling

- **Rate limiting (429)**: LangChain's built-in retry with exponential backoff (configurable `max_retries`)
- **Server errors (500, 503)**: Retry once via LangChain retry config, then return error to the agent
- **Timeout**: Configurable timeout on LLM calls via `request_timeout`. On timeout, return error to agent.
- **Invalid tool calls**: LangGraph's `ToolNode` catches exceptions, returns error message as tool result, lets the LLM retry
- **Content filtering**: If the LLM refuses a request, the refusal text becomes the agent response

## Configuration

Environment variables and Python settings:

- **`LANGSMITH_API_KEY`**: LangSmith API key for tracing
- **`LANGSMITH_PROJECT`**: LangSmith project name (e.g., `agentic-rpg-dev`)
- **`LANGSMITH_TRACING`**: Enable/disable tracing (`true` / `false`)
- **`ANTHROPIC_API_KEY`**: Anthropic API key
- **`OPENAI_API_KEY`**: OpenAI API key (future)

Application config (Pydantic settings):

- **`llm_provider`**: Which provider (`anthropic`, `openai`)
- **`llm_model`**: Which model (`claude-sonnet-4-20250514`, `gpt-4o`, etc.)
- **`temperature`**: Default 0.7 for narrative, 0.2 for structured output
- **`max_tokens`**: Per-request output token limit
- **`token_budget`**: Per-session total token budget
- **`request_timeout`**: Timeout for LLM calls (default 60s)
- **`max_retries`**: Retry count for transient failures (default 3)

## Future Extensions

- **Multiple providers**: Fall back to a secondary provider if the primary is down
- **Model routing**: Use cheaper/faster models for simple tasks (inventory checks), expensive models for narrative
- **Prompt caching**: Leverage Anthropic prompt caching via LangChain's cache support
- **LangSmith evaluations**: Automated test suites that score agent behavior (narrative quality, tool accuracy)
- **Multi-agent graphs**: LangGraph sub-graphs for specialized agents (combat, NPC dialogue) composed into the main agent graph
- **Human-in-the-loop**: LangGraph interrupt nodes for player confirmation on high-stakes actions
