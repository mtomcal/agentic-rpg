# Tool Registry Specification

## Overview

The tool registry is a central catalog of all tools available to the agent. Tools are the only way the agent can interact with the game world. The registry is implemented using **LangChain's tool system** (`@tool` decorator and `BaseTool` class) with **Pydantic models** for input/output schemas, and tools are executed by **LangGraph's `ToolNode`**.

## Core Concepts

### Tools (LangChain @tool / BaseTool)

A tool is a LangChain tool — either a decorated function or a `BaseTool` subclass — that the agent can invoke to inspect or modify game state. Every tool has:

- **Name**: Unique string identifier derived from the function name or `BaseTool.name` (e.g., `move_character`, `add_item`, `attack_target`)
- **Description**: Docstring or `BaseTool.description` — included in the LLM prompt so the agent knows when to use it
- **Category**: Logical grouping (character, inventory, world, combat, narrative, meta) — tracked by the registry, not a LangChain concept
- **Parameter schema (`args_schema`)**: A **Pydantic model** defining input parameters. LangChain automatically converts this to the LLM's expected tool format.
- **Return type**: Pydantic model or primitive. LangChain serializes the return as a `ToolMessage`.
- **Preconditions**: Conditions checked in the tool's `_run` method (e.g., character must be alive, must be in the right location). Failures return error results.
- **Events emitted**: List of event types this tool emits on success (documented and enforced in the tool implementation)

### Registration

Tools register with the registry at application startup. The registry is a Python module that collects all LangChain tools and provides them to the agent graph.

Registration requires:

1. A unique name (duplicate names are rejected)
2. A valid Pydantic `args_schema`
3. A category assignment
4. The tool function or `BaseTool` instance

```python
from app.tools.registry import ToolRegistry

registry = ToolRegistry()

# Register decorated functions
registry.register(move_character, category="world")
registry.register(update_health, category="character")

# Register BaseTool instances
registry.register(MoveCharacterTool(game_state=state), category="world")
```

Registration is explicit — tools don't auto-discover. Each tool module registers its tools during initialization.

### Discovery

The registry provides discovery methods:

- **`list_tools()`**: Returns all registered tool names and descriptions
- **`list_by_category(category)`**: Returns tools in a specific category
- **`get_tool(name)`**: Returns the full LangChain tool object by name
- **`get_tools_for_binding()`**: Returns the list of tools ready for `llm.bind_tools(tools)` — this is the primary method the agent graph uses

The agent system uses discovery to build the tool list for each LLM call. The available tools may vary by context (e.g., combat tools are only available during combat).

```python
# In the agent graph's context_assembly node:
tools = registry.get_tools_for_context(
    categories=["character", "inventory", "world", "narrative", "meta"],
    game_state=current_state,
)
llm_with_tools = llm.bind_tools(tools)
```

### Execution (LangGraph ToolNode)

Tool execution is handled by **LangGraph's `ToolNode`**, which processes `AIMessage` tool calls automatically. The pipeline:

1. **Lookup**: `ToolNode` finds the tool by name from the bound tool list
2. **Validate**: Pydantic validates parameters against the tool's `args_schema` — invalid params return a validation error as a `ToolMessage`
3. **Preconditions**: Checked inside the tool's `_run` method using the injected game state
4. **Execute**: `ToolNode` calls the tool function with validated parameters
5. **Emit events**: The tool emits events via the injected event emitter during execution
6. **Return**: `ToolNode` wraps the result as a `ToolMessage` and appends it to the message list

If any step fails, the pipeline returns an error `ToolMessage`. The error includes what failed and why, so the LLM can adapt on the next iteration.

```python
from langgraph.prebuilt import ToolNode

# In the agent graph definition:
tool_node = ToolNode(tools=registry.get_tools_for_binding())
graph.add_node("tool_execution", tool_node)
```

### Tool Context (Dependency Injection)

Every tool that needs game state uses LangChain's `BaseTool` with injected dependencies:

- **Parameters**: Pydantic-validated input from the LLM's tool call
- **Game state**: Injected at tool construction time (read access)
- **State updater**: Injected function to apply state changes (write access)
- **Event emitter**: Injected function to emit events

```python
class MoveCharacterTool(BaseTool):
    name: str = "move_character"
    description: str = "Move the character to a connected location."
    args_schema: type = MoveCharacterInput

    # Injected dependencies
    game_state: GameState
    state_updater: StateUpdater
    event_emitter: EventEmitter

    def _run(self, location_id: str) -> dict:
        # Check preconditions
        connections = self.game_state.get_connections()
        if location_id not in connections:
            return {"success": False, "error": "Location not connected"}

        # Execute state change
        self.state_updater.move_character(location_id)

        # Emit events
        self.event_emitter.emit("character_moved", {"location_id": location_id})

        return {"success": True, "location": self.game_state.get_location(location_id)}
```

For simple tools that don't need game state, the `@tool` decorator is preferred for brevity:

```python
@tool(args_schema=GetRecentEventsInput)
def get_recent_events(count: int = 10, type: str | None = None) -> list[dict]:
    """Get recent game events, optionally filtered by type."""
    ...
```

Tools should not access the database directly. They work through the state and event abstractions.

## Standard Tools

These are the core tools available from the start. Each is implemented as a LangChain tool with a Pydantic `args_schema`.

### Character Tools

| Tool | Description | Parameters (Pydantic fields) |
|------|-------------|------------------------------|
| `get_character` | Get current character state | — |
| `update_health` | Modify character health | `amount: int, reason: str` |
| `update_energy` | Modify character energy | `amount: int, reason: str` |
| `add_status_effect` | Apply a status effect | `effect: str, duration: int \| None` |
| `remove_status_effect` | Remove a status effect | `effect: str` |
| `update_money` | Add or remove money | `amount: int, reason: str` |

### Inventory Tools

| Tool | Description | Parameters (Pydantic fields) |
|------|-------------|------------------------------|
| `get_inventory` | List current inventory | — |
| `add_item` | Add an item to inventory | `item: ItemModel` |
| `remove_item` | Remove an item | `item_id: str, quantity: int \| None` |
| `equip_item` | Equip an item to a slot | `item_id: str, slot: str` |
| `unequip_item` | Unequip from a slot | `slot: str` |
| `use_item` | Use a consumable item | `item_id: str, target: str \| None` |

### World Tools

| Tool | Description | Parameters (Pydantic fields) |
|------|-------------|------------------------------|
| `get_current_location` | Get current location details | — |
| `get_connections` | List connected locations | — |
| `move_character` | Move to a connected location | `location_id: str` |
| `inspect_environment` | Get detailed location description | `focus: str \| None` |
| `add_location` | Create a new location in the world | `location: LocationModel` |
| `set_world_flag` | Set a world state flag | `key: str, value: Any` |

### Narrative Tools

| Tool | Description | Parameters (Pydantic fields) |
|------|-------------|------------------------------|
| `get_story_outline` | Get current story outline | — |
| `resolve_beat` | Mark current beat as resolved | `outcome: str` |
| `adapt_outline` | Request story outline adaptation | `reason: str, changes: str` |
| `advance_beat` | Move to the next story beat | — |
| `add_beat` | Insert a new beat (side quest, etc.) | `beat: BeatModel, position: int \| None` |
| `update_story_summary` | Update the running story summary | `summary: str` |

### Meta Tools

| Tool | Description | Parameters (Pydantic fields) |
|------|-------------|------------------------------|
| `get_game_state` | Get full game state summary | — |
| `get_recent_events` | Get recent events | `count: int \| None, type: str \| None` |

## Contextual Tool Availability

Not all tools are available at all times. The registry supports filtering before binding tools to the LLM:

- **By category**: Only include certain categories (e.g., during combat, include combat + character but not world movement)
- **By precondition**: Only include tools whose preconditions can be met in the current state
- **By feature flag**: Tools behind feature flags are only registered if the flag is enabled

The agent system calls `registry.get_tools_for_context()` to select the appropriate tool set, then binds them with `llm.bind_tools(tools)` for each LLM call.

```python
# During combat: restrict available tools
combat_tools = registry.get_tools_for_context(
    categories=["combat", "character", "inventory", "meta"],
    game_state=current_state,
)

# During exploration: full tool set minus combat
explore_tools = registry.get_tools_for_context(
    categories=["character", "inventory", "world", "narrative", "meta"],
    game_state=current_state,
)
```

## Future Extensions

- **Custom tool creation**: Allow the agent to define new tools at runtime using LangChain's dynamic tool creation (e.g., a spell the player invented)
- **Tool chaining**: Define composite tools using LangGraph sub-graphs that execute a sequence of atomic tools
- **Tool permissions**: Different agent roles (sub-graphs) have access to different tool sets via separate `ToolNode` instances
- **Tool versioning**: Support multiple versions of a tool using LangChain's tool naming conventions
