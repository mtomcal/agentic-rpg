# Schema Registry Specification

## Overview

The schema registry is the single source of truth for all data structures in the system. Schemas are defined as **Pydantic v2 models** in Python — the models themselves ARE the schema. They define validation, serialization, documentation, and generate both OpenAPI specs (via FastAPI) and TypeScript types (via code generation). This eliminates type drift between layers and provides a contract that both sides must honor.

## What Gets a Schema

Every data structure that crosses a boundary gets a Pydantic model:

- **API request/response bodies**: All HTTP and WebSocket message payloads
- **Game state**: The full game state structure and all its sub-structures
- **Events**: Every event type's payload
- **Tool parameters and return values**: Input/output for every agent tool
- **Story outline structures**: Beats, outlines, adaptation records

Internal-only structures (e.g., database query helpers, internal caches) do not need Pydantic models — plain dataclasses or dicts are fine.

## Schema Organization

Schemas are organized as Python modules in a `models/` package within the backend:

```
backend/src/agentic_rpg/models/
  __init__.py
  game_state.py       # GameState, Session, Character, StatusEffect, etc.
  character.py         # Character-related models
  inventory.py         # Inventory, Item models
  world.py             # World, Location models
  story.py             # StoryState, StoryOutline, StoryBeat, AdaptationRecord
  events.py            # GameEvent, event payload models
  api.py               # API request/response models
```

Each file defines one or more related Pydantic models. All models are re-exported from `__init__.py` files for convenient imports.

## Schema Conventions

All Pydantic models follow these conventions:

```python
from pydantic import BaseModel, Field
from enum import StrEnum

class ItemType(StrEnum):
    """Fixed value sets use StrEnum."""
    weapon = "weapon"
    armor = "armor"
    consumable = "consumable"
    quest = "quest"

class Item(BaseModel):
    """Every model has a docstring for documentation."""

    id: UUID = Field(..., description="Unique item identifier")
    name: str = Field(..., description="Display name of the item")
    item_type: ItemType = Field(..., description="Category of the item")
    quantity: int = Field(default=1, ge=1, description="Stack count")
    description: str = Field(default="", description="Flavor text for the item")
```

- **Field descriptions**: Every field uses `Field(description=...)` for documentation
- **Defaults**: Optional fields use `Field(default=...)` — explicit about what's optional
- **Constraints**: Use Pydantic validators (`ge`, `le`, `min_length`, `pattern`, etc.)
- **Enums**: Use `StrEnum` for fixed value sets (status effects, item types, event types)
- **Composition**: Models reference each other directly — Pydantic handles nested validation

## TypeScript Type Generation

TypeScript types are generated from Pydantic models for the frontend. The generated code:

- Lives at `frontend/types/generated.ts` in the frontend project
- Includes type definitions (interfaces and enums)
- Is regenerated on every schema change via a build step

### Generation Workflow

```
backend/src/agentic_rpg/models/**/*.py (Pydantic models)
    │
    └──→ [FastAPI] ──→ OpenAPI spec (automatic, at /openapi.json)
                           │
                           └──→ [openapi-typescript] ──→ frontend/types/generated.ts
```

The generation step runs:
- As a pre-commit hook (optional, for safety)
- As part of CI (required, to catch drift)
- Manually via a script during development (`make generate-types`)

If the generated TypeScript doesn't match the Pydantic models, CI fails.

### Generation Tools

**openapi-typescript**: generates TypeScript types from the OpenAPI JSON that FastAPI produces. Run via `make generate-types`, which first exports the OpenAPI schema from the running backend and then runs `openapi-ts` to emit `frontend/types/generated.ts`.

## Validation

Pydantic models serve dual purpose:

1. **Static typing**: Type checkers (mypy, pyright) enforce structure in Python. Generated TypeScript types enforce structure in the frontend.
2. **Runtime validation**: FastAPI automatically validates all request bodies against Pydantic models. The event system validates event payloads by constructing Pydantic model instances before emission.

Runtime validation is built into Pydantic — no separate validation library needed. Invalid data raises `ValidationError` with detailed error messages.

```python
# FastAPI validates automatically — just declare the type
@app.post("/api/v1/sessions")
async def create_session(request: SessionCreateRequest) -> SessionCreateResponse:
    ...  # request is already validated

# Manual validation where needed
try:
    event = CharacterStatChanged(**payload)
except ValidationError as e:
    logger.error(f"Invalid event payload: {e}")
```

## Schema Evolution

When a schema changes:

1. Update the Pydantic model
2. Run the TypeScript generation script
3. Fix any type errors in Python and TypeScript (the types changed)
4. Update any tests that depend on the old structure
5. If the change is backwards-incompatible, write a state migration (see [Game State](game-state.md))

Adding new optional fields with defaults is always safe. Removing fields, renaming fields, or changing types is a breaking change.

### Model Versioning

For breaking changes that need to coexist, use versioned models:

```python
class CharacterV1(BaseModel):
    name: str
    health: int

class CharacterV2(BaseModel):
    name: str
    stats: CharacterStats  # Replaces flat health field
```

The API version (`/api/v1/`, `/api/v2/`) determines which model version is used for serialization.

## Future Extensions

- **Schema diffing**: Automated detection of breaking vs. non-breaking changes by comparing Pydantic model JSON schemas across versions
- **Mock data generation**: Auto-generate test fixtures from model examples and Pydantic's `model_construct()`
- **Schema documentation site**: Auto-generated docs from FastAPI's built-in OpenAPI/Swagger UI (available for free at `/docs`)
