# Technology Choice: Pydantic v2 Models

## Decision

Use Pydantic v2 models as the single source of truth for all data structures. Generate TypeScript types from these models for the frontend.

## Rationale

- **Single source of truth**: Pydantic models define the schema once. TypeScript types are generated from them. No manual synchronization.
- **Runtime validation**: Pydantic validates data at runtime automatically — API requests, event payloads, game state, LLM structured output. No separate validation step needed.
- **LangChain integration**: LangChain uses Pydantic natively for tool input schemas, structured output, and agent state. Pydantic models flow directly into the LLM tool definitions.
- **FastAPI integration**: FastAPI uses Pydantic for request/response models, automatic OpenAPI docs, and serialization. The same models serve the API layer and the game logic.
- **Rich type system**: Pydantic v2 supports discriminated unions, computed fields, custom validators, JSON Schema export, and serialization hooks — covering every data modeling need.

## Pydantic Version

Use Pydantic v2 (2.x). It's a ground-up rewrite with a Rust core (`pydantic-core`) that's significantly faster than v1.

## Model Organization

Models are organized by domain in a Python package:

```
backend/src/agentic_rpg/
  models/
    __init__.py
    game_state.py     # GameState, SessionState
    character.py      # Character, CharacterStats, StatusEffect
    inventory.py      # Item, Inventory, EquipmentSlot
    world.py          # Location, Connection, WorldState, WorldFlag
    story.py          # StoryOutline, StoryBeat, BeatStatus
    events.py         # GameEvent, EventType, event payload models
    api.py            # API request/response models
```

Each module exports its models. The `__init__.py` re-exports the public API.

## Model Conventions

### Field Descriptions

Every field includes a `description` for documentation and LLM tool schema generation:

```python
class Character(BaseModel):
    name: str = Field(description="Character's display name")
    health: int = Field(default=100, ge=0, le=100, description="Current health points")
    energy: int = Field(default=100, ge=0, le=100, description="Current energy points")
    status_effects: list[StatusEffect] = Field(
        default_factory=list,
        description="Active status effects on the character"
    )
```

### Validators

Use Pydantic validators for domain rules:

```python
from pydantic import field_validator

class Location(BaseModel):
    id: str
    name: str
    connections: list[str] = Field(description="IDs of connected locations")

    @field_validator("id")
    @classmethod
    def id_must_be_slug(cls, v: str) -> str:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Location ID must be alphanumeric with hyphens/underscores")
        return v
```

### Discriminated Unions

Use discriminated unions for event payloads and polymorphic types:

```python
from typing import Annotated, Literal, Union
from pydantic import Discriminator

class MoveEvent(BaseModel):
    type: Literal["move"] = "move"
    location_id: str

class ItemEvent(BaseModel):
    type: Literal["item"] = "item"
    item_id: str
    action: Literal["add", "remove", "use"]

GameEvent = Annotated[Union[MoveEvent, ItemEvent], Discriminator("type")]
```

### Serialization

Use `model_config` for consistent JSON serialization:

```python
class GameState(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        ser_json_timedelta="float",
        json_schema_extra={"examples": [...]},
    )
```

## TypeScript Generation

### Tool: `datamodel-code-generator` or `pydantic-to-typescript`

Generate TypeScript interfaces from Pydantic models via their JSON Schema export:

```bash
#!/bin/bash
# scripts/generate-types.sh

set -e

MODELS_DIR="server/models"
TS_OUT="frontend/src/generated"

rm -rf "$TS_OUT"
mkdir -p "$TS_OUT"

# Export JSON Schema from Pydantic models, then generate TypeScript
python -m scripts.export_schemas --output schemas/
npx json-schema-to-typescript \
  --input schemas/ \
  --output "$TS_OUT" \
  --cwd schemas/

echo "Done."
```

The Python export script uses `Model.model_json_schema()` to produce JSON Schema files, which are then fed to the TypeScript generator.

### Generation Workflow

#### During Development

1. Edit a Pydantic model in `backend/src/agentic_rpg/models/`
2. Run `./scripts/generate-types.sh`
3. Fix any TypeScript compile errors (the types changed)
4. Commit the model change AND the generated TypeScript together

#### In CI

1. Run `./scripts/generate-types.sh`
2. Check that the generated code matches what's committed (`git diff --exit-code`)
3. If they differ, the build fails (someone forgot to regenerate)

#### Adding a New Model

1. Create the Pydantic model in the appropriate `backend/src/agentic_rpg/models/` module
2. Add it to the schema export script
3. Run the generation script
4. Import the generated TypeScript type in the frontend
5. Write tests that use the model

## Pydantic → TypeScript Mapping

| Pydantic | TypeScript |
|---|---|
| `BaseModel` | `interface` |
| `str` | `string` |
| `int` | `number` |
| `float` | `number` |
| `bool` | `boolean` |
| `list[T]` | `T[]` |
| `dict[str, T]` | `Record<string, T>` |
| `Literal["a", "b"]` | `"a" \| "b"` |
| `T \| None` | `T \| null` |
| `Annotated[Union[...], Discriminator]` | discriminated union |
| `datetime` | `string` (ISO 8601) |
| `UUID` | `string` |

## Model Versioning

For schema evolution (game state stored as JSONB):

- Add a `schema_version: int` field to versioned models
- Write migration functions: `migrate_v1_to_v2(data: dict) -> dict`
- On load, check version and apply migrations as needed
- Pydantic's `model_validator(mode="before")` can handle version detection and migration transparently

## Generated Code Rules

- Generated TypeScript lives in `frontend/src/generated/`
- Generated files have a header comment: `// Generated from Pydantic models. DO NOT EDIT.`
- Generated code is committed to git (so frontend builds don't require the Python environment)
- Never hand-edit generated files

## Future Extensions

- **OpenAPI generation**: FastAPI generates OpenAPI specs automatically from Pydantic models — use for API docs
- **Mock data generation**: Generate test fixtures from model `examples` and `json_schema_extra`
- **Model documentation**: Generate human-readable docs from field `description` values
- **Database model integration**: Explore SQLModel for unified Pydantic + SQLAlchemy models
