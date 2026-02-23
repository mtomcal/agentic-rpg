# Tool Registry Specification

## Overview

The tool registry is a central catalog of all tools available to the agent. Tools are the only way the agent can interact with the game world. The registry enables dynamic tool discovery, validation, and execution.

## Core Concepts

### Tools

A tool is a callable function that the agent can invoke to inspect or modify game state. Every tool has:

- **Name**: Unique string identifier (e.g., `move_character`, `add_item`, `attack_target`)
- **Description**: Human-readable description of what the tool does. This is included in the LLM prompt so the agent knows when to use it.
- **Category**: Logical grouping (character, inventory, world, combat, narrative, meta)
- **Parameter schema**: JSON Schema defining input parameters
- **Return schema**: JSON Schema defining the output
- **Preconditions**: Conditions that must be true for the tool to execute (e.g., character must be alive, must be in the right location)
- **Events emitted**: List of event types this tool emits on success

### Registration

Tools register themselves with the registry at application startup. Registration requires:

1. A unique name (duplicate names are rejected)
2. A valid parameter schema
3. A valid return schema
4. A category assignment
5. The executable function

Registration is explicit — tools don't auto-discover. Each tool module registers its tools during initialization.

### Discovery

The registry provides discovery methods:

- **List all tools**: Returns all registered tool names and descriptions
- **List by category**: Returns tools in a specific category
- **Get tool**: Returns full tool metadata by name
- **Get LLM tool definitions**: Returns tools formatted for the LLM API's tool-use format (name, description, parameter schema)

The agent system uses discovery to build the tool list for each LLM call. The available tools may vary by context (e.g., combat tools are only available during combat).

### Execution

Tool execution follows a strict pipeline:

1. **Lookup**: Find the tool in the registry by name
2. **Validate**: Check parameters against the tool's JSON Schema
3. **Preconditions**: Check that all preconditions are met (given current game state)
4. **Execute**: Run the tool function with validated parameters and game state
5. **Emit events**: Publish any events produced by the tool
6. **Return**: Return the tool's result to the caller

If any step fails, the pipeline stops and returns an error result. The error includes which step failed and why, so the agent can adapt.

### Tool Context

Every tool receives:

- **Parameters**: The validated input parameters
- **Game state**: The current game state (read access)
- **State updater**: A function to apply state changes (write access)
- **Event emitter**: A function to emit events

Tools should not access the database directly. They work through the state and event abstractions.

## Standard Tools

These are the core tools available from the start:

### Character Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_character` | Get current character state | — |
| `update_health` | Modify character health | `amount: int, reason: string` |
| `update_energy` | Modify character energy | `amount: int, reason: string` |
| `add_status_effect` | Apply a status effect | `effect: string, duration: int?` |
| `remove_status_effect` | Remove a status effect | `effect: string` |
| `update_money` | Add or remove money | `amount: int, reason: string` |

### Inventory Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_inventory` | List current inventory | — |
| `add_item` | Add an item to inventory | `item: ItemDef` |
| `remove_item` | Remove an item | `item_id: string, quantity: int?` |
| `equip_item` | Equip an item to a slot | `item_id: string, slot: string` |
| `unequip_item` | Unequip from a slot | `slot: string` |
| `use_item` | Use a consumable item | `item_id: string, target: string?` |

### World Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_current_location` | Get current location details | — |
| `get_connections` | List connected locations | — |
| `move_character` | Move to a connected location | `location_id: string` |
| `inspect_environment` | Get detailed location description | `focus: string?` |
| `add_location` | Create a new location in the world | `location: LocationDef` |
| `set_world_flag` | Set a world state flag | `key: string, value: any` |

### Narrative Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_story_outline` | Get current story outline | — |
| `resolve_beat` | Mark current beat as resolved | `outcome: string` |
| `adapt_outline` | Request story outline adaptation | `reason: string, changes: string` |
| `advance_beat` | Move to the next story beat | — |
| `add_beat` | Insert a new beat (side quest, etc.) | `beat: BeatDef, position: int?` |
| `update_story_summary` | Update the running story summary | `summary: string` |

### Meta Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_game_state` | Get full game state summary | — |
| `get_recent_events` | Get recent events | `count: int?, type: string?` |

## Contextual Tool Availability

Not all tools are available at all times. The registry supports filtering:

- **By category**: Only include certain categories (e.g., during combat, include combat + character but not world movement)
- **By precondition**: Only include tools whose preconditions can be met in the current state
- **By feature flag**: Tools behind feature flags are only registered if the flag is enabled

The agent system is responsible for selecting the appropriate tool set for each LLM call.

## Future Extensions

- **Custom tool creation**: Allow the agent to define new tools at runtime (e.g., a spell the player invented)
- **Tool chaining**: Define composite tools that execute a sequence of atomic tools
- **Tool permissions**: Different agent roles have access to different tool sets
- **Tool versioning**: Support multiple versions of a tool for backwards compatibility
