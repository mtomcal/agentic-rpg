# Agent System Specification

## Overview

The agent system is the core intelligence of the game. It receives player input, reasons about the current game state, invokes tools to modify that state, and produces narrative output. The agent operates as a single decision loop that processes one player action at a time.

## Core Concepts

### The Agent Loop

The agent follows a standard tool-use loop:

1. **Receive** player input (text command or action)
2. **Gather context** — current game state, recent event history, story outline, conversation history
3. **Send to LLM** with system prompt, context, player input, and available tools
4. **Process LLM response**:
   - If the LLM returns tool calls, execute them and loop back to step 3 with the results
   - If the LLM returns a text response, deliver it to the player
5. **Emit events** for any state changes that occurred

This is a synchronous loop — the agent processes one player action to completion before accepting the next.

### Context Assembly

Before each LLM call, the agent assembles a context window containing:

- **System prompt**: Defines the agent's role, the current genre/setting, tone guidelines, and behavioral rules
- **Story outline**: The current story arc (see [Story Engine](story-engine.md))
- **Game state summary**: Character stats, inventory, location, active status effects
- **Recent events**: Last N events from the event bus relevant to the current scene
- **Conversation history**: Recent player/agent exchanges (windowed to fit context limits)
- **Available tools**: The set of tools the agent can invoke, with their schemas

### Context Window Management

The context window has a finite size. The agent must manage what goes in:

- **Story outline**: Always included, but kept concise (summary form)
- **Game state**: Always included as structured data
- **Conversation history**: Sliding window, most recent N turns. Older history is summarized.
- **Events**: Only recent, relevant events. Filtered by location and recency.

When the context approaches the limit, the agent should:
1. Summarize older conversation history into a condensed form
2. Drop irrelevant events
3. Never drop the story outline or current game state

## Tools

The agent interacts with the game world exclusively through tools. It cannot modify game state directly — it must call a tool.

### Tool Interface

Every tool has:

- **Name**: Unique identifier (e.g., `move_character`, `update_health`)
- **Description**: What the tool does (included in LLM context so the agent knows when to use it)
- **Parameter schema**: JSON Schema defining the tool's input parameters
- **Return schema**: JSON Schema defining the tool's output
- **Validation**: Parameter validation before execution
- **Side effects**: What events the tool emits and what state it modifies

### Tool Categories

Tools are organized into categories:

- **Character**: Modify character stats, status effects, level up
- **Inventory**: Add/remove items, equip/unequip, use consumables
- **World**: Move between locations, inspect environment, interact with objects
- **Combat**: Attack, defend, use abilities, flee (later phase)
- **Narrative**: Update story outline, create story events, introduce NPCs
- **Meta**: Save game, load game, get help

### Tool Execution

When the agent calls a tool:

1. Validate parameters against the tool's schema
2. Check preconditions (e.g., player must be alive to move)
3. Execute the state change
4. Emit relevant events to the event bus
5. Return the result to the agent (success/failure + any output data)

Tool execution is atomic — either all state changes succeed or none do.

## System Prompt Design

The system prompt is built dynamically based on:

- **Genre/setting**: Injected from the session configuration (e.g., "You are a Game Master for a dark fantasy RPG set in a dying world")
- **Tone guidelines**: How the agent should narrate (gritty, humorous, epic, etc.)
- **Behavioral rules**: Always respect player agency, never kill the player without warning, maintain narrative consistency
- **Current scene context**: What's happening right now (combat, exploration, dialogue)

The system prompt should be modular — composed of reusable blocks that can be assembled based on the current game situation.

## Error Handling

- If a tool call fails validation, the error is returned to the agent and it can retry or adapt
- If the LLM returns an invalid tool call (wrong name, bad params), log it and ask the LLM to try again (up to 3 retries)
- If the LLM gets stuck in a loop (calling the same tool repeatedly), break the loop and return a fallback narrative response
- All errors are logged as events for debugging

## Future Extensions

- **Multi-agent**: Specialized agents for combat, NPC dialogue, world events — each with their own tool sets and system prompts. A router decides which agent handles each player action.
- **Agent memory**: Long-term memory store that persists across sessions for NPC relationships, world changes, player preferences.
- **Parallel tool calls**: Allow the LLM to call multiple tools in one turn for efficiency.
