# Schema Registry Specification

## Overview

The schema registry is the single source of truth for all data structures in the system. Schemas are defined as JSON Schema files, and both the server (Go structs) and client (TypeScript types) are generated from them. This eliminates type drift between layers and provides a contract that both sides must honor.

## What Gets a Schema

Every data structure that crosses a boundary gets a JSON Schema:

- **API request/response bodies**: All HTTP and WebSocket message payloads
- **Game state**: The full game state structure and all its sub-structures
- **Events**: Every event type's payload
- **Tool parameters and return values**: Input/output for every agent tool
- **Story outline structures**: Beats, outlines, adaptation records

Internal-only structures (e.g., database query helpers, internal caches) do not need schemas.

## Schema Organization

Schemas are organized in a `schemas/` directory at the project root:

```
schemas/
  game-state/
    game-state.json         # Top-level game state
    character.json          # Character model
    character-stats.json    # Character stats
    inventory.json          # Inventory model
    item.json               # Item model
    world.json              # World state
    location.json           # Location model
    conversation.json       # Conversation history
    message.json            # Single message
  story/
    story-outline.json      # Full story outline
    story-beat.json         # Single story beat
    adaptation-record.json  # Outline adaptation log entry
  events/
    base-event.json         # Base event envelope
    character-events.json   # Character event payloads
    inventory-events.json   # Inventory event payloads
    world-events.json       # World event payloads
    story-events.json       # Story event payloads
    session-events.json     # Session event payloads
    agent-events.json       # Agent event payloads
  api/
    session-create.json     # POST /sessions request/response
    session-list.json       # GET /sessions response
    player-action.json      # WebSocket player action
    agent-response.json     # WebSocket agent response
    state-update.json       # WebSocket state update
    error.json              # Error response
  tools/
    character-tools.json    # Character tool params/returns
    inventory-tools.json    # Inventory tool params/returns
    world-tools.json        # World tool params/returns
    narrative-tools.json    # Narrative tool params/returns
```

Each file defines one or more related schemas using standard JSON Schema (draft 2020-12).

## Schema Conventions

- **$id**: Every schema has a unique `$id` (e.g., `"https://agentic-rpg/schemas/game-state/character.json"`)
- **$ref**: Schemas reference each other using `$ref` for composition
- **Required fields**: Explicitly listed. Optional fields use `default` values.
- **Descriptions**: Every field has a `description` for documentation
- **Examples**: Schemas include `examples` for clarity and test data generation
- **Enums**: Use `enum` for fixed value sets (status effects, item types, event types)
- **Versioning**: Schemas include a `$schema` version field. Schema evolution follows the rules in [Game State](game-state.md) schema versioning.

## Code Generation

### Go Structs

Generate Go structs from JSON Schema. The generated code:

- Lives in a `generated/` package (not hand-edited)
- Includes JSON tags for serialization
- Includes validation methods (generated from schema constraints)
- Is regenerated on every schema change via a build step

### TypeScript Types

Generate TypeScript interfaces from JSON Schema. The generated code:

- Lives in a `generated/` directory in the frontend project
- Includes type definitions (interfaces and enums)
- Is regenerated on every schema change via a build step

### Generation Workflow

```
schemas/*.json
    │
    ├──→ [Go codegen tool] ──→ backend/generated/*.go
    │
    └──→ [TS codegen tool] ──→ frontend/src/generated/*.ts
```

The generation step runs:
- As a pre-commit hook (optional, for safety)
- As part of CI (required, to catch drift)
- Manually via a script during development

If the generated code doesn't match the schemas, CI fails.

## Validation

Schemas serve dual purpose:

1. **Compile-time**: Generated types enforce structure in Go and TypeScript
2. **Runtime**: The event system validates event payloads against their schemas before emission. API requests are validated against their schemas before processing.

Runtime validation uses the same JSON Schema files, loaded at startup.

## Schema Evolution

When a schema changes:

1. Update the JSON Schema file
2. Run the generation script
3. Fix any compile errors in Go and TypeScript (the generated types changed)
4. Update any tests that depend on the old structure
5. If the change is backwards-incompatible, write a state migration (see [Game State](game-state.md))

Adding new optional fields with defaults is always safe. Removing fields, renaming fields, or changing types is a breaking change.

## Future Extensions

- **Schema diffing**: Automated detection of breaking vs. non-breaking changes
- **OpenAPI generation**: Generate an OpenAPI spec from the schemas for API documentation
- **Mock data generation**: Auto-generate test fixtures from schema examples
- **Schema documentation site**: Auto-generated docs from schema descriptions
