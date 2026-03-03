# Agent System Specification

## Overview

The agent system is the core intelligence of the game. It receives player input, reasons about the current game state, invokes tools to modify that state, and produces narrative output. The agent is implemented as a **LangGraph StateGraph** that processes one player action at a time through a series of graph nodes.

## Core Concepts

### The Agent Graph (LangGraph StateGraph)

The agent is a LangGraph `StateGraph` with the following nodes and edges:

```
[context_assembly] -> [llm_call] -> [tool_execution] -> [llm_call] (loop)
                                  \-> [response_delivery] (when no tool calls)
```

**Nodes:**

1. **`context_assembly`** — Builds the full prompt from game state, conversation history, and player input
2. **`llm_call`** — Sends the assembled messages to the LLM via LangChain's `ChatAnthropic` or `ChatOpenAI`
3. **`tool_execution`** — Executes tool calls using LangGraph's `ToolNode` and returns results
4. **`response_delivery`** — Extracts the final narrative text and emits state-change events

**Conditional edges:**

- After `llm_call`: route to `tool_execution` if the response contains tool calls, otherwise route to `response_delivery`
- After `tool_execution`: always route back to `llm_call` with the tool results appended

**Graph state** is defined as a `TypedDict`:

```python
from typing import Annotated
from langgraph.graph import MessagesState

class AgentState(MessagesState):
    """Extends MessagesState with game-specific fields."""
    game_state: dict          # current character, inventory, location, etc.
    session_id: str           # session identifier
    events: list[dict]        # events emitted during this turn
```

This is a synchronous graph invocation — the agent processes one player action to completion before accepting the next. LangSmith traces every graph invocation end-to-end.

### Context Assembly (LangChain Prompt Templates)

The `context_assembly` node builds the message list sent to the LLM. It uses **LangChain `ChatPromptTemplate`** to compose the system prompt and **LangChain message types** (`SystemMessage`, `HumanMessage`, `AIMessage`, `ToolMessage`) for the conversation.

The assembled context includes:

- **System prompt**: Built with `ChatPromptTemplate.from_messages()` using template variables for genre, tone, scene context, and behavioral rules
- **Story outline**: Injected as a `SystemMessage` block (always included, summary form)
- **Game state summary**: Character stats, inventory, location, active status effects — formatted as a `SystemMessage` block
- **Recent events**: Last N events from the event bus relevant to the current scene — formatted as a `SystemMessage` block
- **Conversation history**: Recent player/agent exchanges from LangChain memory (see below)
- **Player input**: The current player action as a `HumanMessage`
- **Available tools**: Bound to the LLM via `llm.bind_tools(tools)` (not in the message list directly)

### Context Window Management (LangChain Memory)

The context window has a finite size. LangChain memory modules manage what fits:

- **`ConversationBufferWindowMemory`**: Keeps the most recent N turns of conversation. Older messages are dropped automatically.
- **`ConversationSummaryMemory`**: When older history is dropped, it's first summarized into a condensed form by an LLM call and retained as a summary message.

**Priority rules** (same as before, enforced in `context_assembly`):

- Story outline: Always included, never dropped
- Game state: Always included as structured data, never dropped
- Conversation history: Sliding window via `ConversationBufferWindowMemory`, oldest summarized via `ConversationSummaryMemory`
- Events: Only recent, relevant events; filtered by location and recency

When the context approaches the token limit:

1. Summarize older conversation history (handled by `ConversationSummaryMemory`)
2. Drop irrelevant events
3. Never drop the story outline or current game state

## Tools

The agent interacts with the game world exclusively through tools. It cannot modify game state directly — it must call a tool. Tools use **LangChain's `@tool` decorator or `BaseTool` class** and are executed by **LangGraph's `ToolNode`**.

### Tool Interface (LangChain Tools)

Every tool is defined using LangChain's tool system:

- **Name**: Derived from the function name or `BaseTool.name` (e.g., `move_character`, `update_health`)
- **Description**: Docstring or `BaseTool.description` — included in the LLM context so the agent knows when to use it
- **Parameter schema**: A **Pydantic model** used as the `args_schema` — LangChain converts this to the LLM's tool format automatically
- **Return type**: Pydantic model or primitive — LangChain serializes the return value as a `ToolMessage`
- **Validation**: Pydantic validates parameters before execution (built into LangChain's tool pipeline)
- **Side effects**: What events the tool emits and what state it modifies (documented in the tool and enforced in the execution context)

Example using `@tool`:

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class UpdateHealthInput(BaseModel):
    amount: int = Field(description="Health change amount, negative for damage")
    reason: str = Field(description="Why health is changing")

@tool(args_schema=UpdateHealthInput)
def update_health(amount: int, reason: str) -> dict:
    """Modify character health by the given amount."""
    ...
```

Example using `BaseTool` for tools needing game state access:

```python
from langchain_core.tools import BaseTool

class MoveCharacterTool(BaseTool):
    name: str = "move_character"
    description: str = "Move the character to a connected location."
    args_schema: type = MoveCharacterInput

    game_state: GameState  # injected at construction

    def _run(self, location_id: str) -> dict:
        ...
```

### Tool Categories

Tools are organized into categories (same groupings, now registered as LangChain tools):

- **Character**: Modify character stats, status effects, level up
- **Inventory**: Add/remove items, equip/unequip, use consumables
- **World**: Move between locations, inspect environment, interact with objects
- **Combat**: Attack, defend, use abilities, flee (later phase)
- **Narrative**: Update story outline, create story events, introduce NPCs
- **Meta**: Save game, load game, get help

### Tool Execution (LangGraph ToolNode)

When the LLM returns tool calls in its response:

1. The conditional edge routes to the `tool_execution` node
2. **LangGraph's `ToolNode`** receives the `AIMessage` with tool calls
3. For each tool call, `ToolNode`:
   a. Looks up the tool by name from the bound tool list
   b. **Pydantic validates** the parameters against the tool's `args_schema`
   c. Checks preconditions (enforced in the tool's `_run` method)
   d. Executes the tool function
   e. Returns a `ToolMessage` with the result
4. Tool results are appended to the message list and routed back to `llm_call`
5. Events emitted during tool execution are collected in the graph state

Tool execution is atomic — either all state changes within a single tool call succeed or none do.

## System Prompt Design (ChatPromptTemplate)

The system prompt is built dynamically using `ChatPromptTemplate`:

```python
from langchain_core.prompts import ChatPromptTemplate

system_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a Game Master for a {genre} RPG set in {setting}.

Tone: {tone_guidelines}

Rules:
{behavioral_rules}

Current scene: {scene_context}

Story outline:
{story_outline}

Game state:
{game_state_summary}

Recent events:
{recent_events}
"""),
])
```

Template variables are filled from:

- **Genre/setting**: Session configuration (e.g., "dark fantasy", "a dying world")
- **Tone guidelines**: How the agent should narrate (gritty, humorous, epic, etc.)
- **Behavioral rules**: Always respect player agency, never kill the player without warning, maintain narrative consistency
- **Scene context**: What's happening right now (combat, exploration, dialogue)
- **Story outline, game state, events**: Assembled from the game database

The prompt is modular — template variables allow reusable blocks to be assembled based on the current game situation.

## Error Handling

- If Pydantic validation fails on a tool call, LangChain returns the validation error as a `ToolMessage` and the LLM can retry or adapt
- If the LLM returns an invalid tool call (wrong name, bad params), the `ToolNode` returns an error message; the graph loops back to `llm_call` for retry (up to 3 iterations, enforced by a `recursion_limit` on the graph)
- If the LLM gets stuck in a loop (calling the same tool repeatedly), the graph's `recursion_limit` breaks the loop and the `response_delivery` node returns a fallback narrative response
- All errors are logged as events for debugging
- **LangSmith** traces capture the full graph execution including all errors, making debugging straightforward

## Observability (LangSmith)

Every agent graph invocation is traced by **LangSmith**:

- Full message history for each LLM call
- Tool call inputs and outputs
- Token usage per call
- Latency per node
- Error traces with full context

LangSmith is configured via environment variables (`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`). All LangChain and LangGraph calls are automatically instrumented — no manual tracing code required.

## Future Extensions

- **Multi-agent**: Specialized LangGraph sub-graphs for combat, NPC dialogue, world events — each with their own tool sets and system prompts. A LangGraph router node decides which sub-graph handles each player action.
- **Agent memory**: LangChain's long-term memory stores (vector stores, entity memory) that persist across sessions for NPC relationships, world changes, player preferences.
- **Parallel tool calls**: LangGraph's `ToolNode` already supports parallel tool execution when the LLM returns multiple tool calls in one response — enable this as models support it.
- **Streaming**: LangGraph supports streaming node outputs, enabling real-time narrative delivery to the player as the LLM generates text.
