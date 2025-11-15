# Initial Project Setup Implementation Plan

## Overview

This plan covers Phase 0: Foundation Setup for the Agentic RPG project. We'll establish the complete development infrastructure, project structure, and contracts needed to enable parallel development across multiple teams. This is the critical foundation that allows 6+ developers to work independently with minimal merge conflicts.

## Current State Analysis

**What exists now:**
- PRD document with comprehensive architecture specifications
- Empty project directory (only PRD.md exists)
- Clear team structure and ownership model defined
- Well-documented architectural patterns (Tool Registry, Event Bus, Feature Flags, DI)

**Key constraints discovered:**
- Must support parallel development from day one
- Need to establish contracts before teams can work independently
- Type generation must be automated to prevent drift
- Feature flag system required for incomplete feature shipping

## Desired End State

A fully initialized, working project with:

### Backend:
- Python project with Poetry dependency management
- Complete directory structure matching PRD specifications
- Core data models with Pydantic validation
- Service interfaces (StateManager, AgentService) defined
- Tool Registry and Event Bus implementations
- FastAPI app with health check endpoints
- OpenAPI spec generation working
- Contract test framework in place

### Frontend:
- Next.js 14+ project with App Router
- TypeScript configured with strict mode
- Tailwind CSS set up and configured
- Basic layout components
- Type generation from OpenAPI working
- API client stubs for development

### Infrastructure:
- Git repository with CODEOWNERS
- GitHub Actions CI/CD pipeline
- Docker Compose for local development
- Shared-types directory for contracts
- Documentation structure

### Verification:
- All developers can clone and run locally
- `poe test` passes on backend
- `npm run dev` works on frontend
- Type generation script works end-to-end
- CI pipeline runs successfully
- Contract tests framework validates all interfaces

## What We're NOT Doing

- No actual agent logic or LLM integration (Phase 1)
- No real game mechanics or tools (Phase 2)
- No WebSocket implementation (Phase 4)
- No production deployment setup (Phase 6)
- No database migrations (using JSON state only for now)
- No authentication or authorization
- No actual UI components beyond layout
- No Redis caching layer

## Implementation Approach

We'll work in sequential phases to establish the foundation:
1. **Backend skeleton** - Project structure, models, interfaces
2. **Frontend skeleton** - Next.js setup, basic structure
3. **Type generation pipeline** - Connect backend → frontend types
4. **Contract tests** - Validate all interfaces
5. **CI/CD** - Automate testing and validation
6. **Documentation** - Onboarding and architecture docs

Each phase builds on the previous, ensuring a working state at all times.

---

## Phase 1: Backend Python Project Setup

### Overview
Initialize the Python project with Poetry, create the complete directory structure, and set up basic configurations. This establishes the backend foundation.

### Changes Required:

#### 1. Initialize Poetry Project

**Location**: `/home/mtomcal/code/agentic-rpg/backend/`

**Actions**:
```bash
# Create backend directory
mkdir -p backend
cd backend

# Initialize Poetry project
poetry init \
  --name agentic-rpg \
  --description "Agentic RPG - Dynamic AI-driven RPG game" \
  --author "Your Team" \
  --python "^3.11" \
  --no-interaction
```

**Dependencies to add**:
```bash
# Core dependencies
poetry add fastapi uvicorn pydantic pydantic-settings
poetry add langchain langgraph langchain-anthropic
poetry add python-multipart websockets

# Development dependencies
poetry add --group dev pytest pytest-cov pytest-asyncio
poetry add --group dev ruff mypy
poetry add --group dev httpx  # For testing FastAPI
poetry add --group dev poethepoet  # Task runner
```

#### 2. Create Directory Structure

**Create all directories**:
```bash
mkdir -p src/agentic_rpg/{api,agents,models,services,utils}
mkdir -p src/agentic_rpg/api/routes
mkdir -p src/agentic_rpg/agents/{tools,prompts}
mkdir -p tests/{unit,integration,contracts,e2e}
mkdir -p tests/unit/{test_models,test_tools,test_services,test_utils}
mkdir -p tests/integration/{test_api,test_agents,test_state}
mkdir -p tests/e2e/test_gameplay
mkdir -p scripts
mkdir -p gamestate/sessions
mkdir -p shared-types
mkdir -p docs/ADR
```

**Create __init__.py files**:
```bash
touch src/agentic_rpg/__init__.py
touch src/agentic_rpg/{api,agents,models,services,utils}/__init__.py
touch src/agentic_rpg/agents/tools/__init__.py
touch tests/__init__.py
```

#### 3. Configuration Files

**File**: `backend/pyproject.toml` (add to Poetry-generated file)

```toml
[tool.poe.tasks]
# Testing
test = {cmd = "pytest tests/ -v --cov=src/agentic_rpg --cov-report=term-missing", help = "Run all tests with coverage"}
test-unit = {cmd = "pytest tests/unit/ -v", help = "Run unit tests only"}
test-integration = {cmd = "pytest tests/integration/ -v", help = "Run integration tests"}
test-contracts = {cmd = "pytest tests/contracts/ -v -m contract", help = "Run contract tests"}
test-fast = {cmd = "pytest tests/ -v -m 'not slow'", help = "Run fast tests only"}

# Code quality
lint = {cmd = "ruff check src tests", help = "Run linter"}
format = {cmd = "ruff format src tests", help = "Format code"}
format-check = {cmd = "ruff format --check src tests", help = "Check formatting"}
typecheck = {cmd = "mypy src", help = "Run type checking"}

# Combined checks
check-all = ["format-check", "lint", "typecheck", "test-contracts", "test-unit"]

# Generate types
generate-types = {shell = "bash scripts/generate-types.sh", help = "Generate TypeScript types from OpenAPI"}
generate-schemas = {cmd = "python scripts/generate_schemas.py", help = "Generate JSON schemas"}

# Development
dev = {cmd = "uvicorn agentic_rpg.api.main:app --reload", help = "Start dev server"}

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]  # Line length handled by formatter

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers"
markers = [
    "contract: Contract tests for interface validation",
    "integration: Integration tests requiring multiple components",
    "slow: Slow-running tests (LLM calls, etc.)",
    "requires_llm: Tests that require LLM API access",
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**File**: `backend/.env.example`

```bash
# Application
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# LLM Configuration
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_API_KEY=your-api-key-here
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4000

# State Storage
STATE_STORAGE_TYPE=json
STATE_STORAGE_PATH=./gamestate

# Feature Flags
FEATURE_COMBAT_SYSTEM=false
FEATURE_NPC_PERSONALITIES=false
FEATURE_WORLD_PERSISTENCE=true
FEATURE_WEBSOCKET_UPDATES=false

# Development
USE_MOCKS=false
ENABLE_DEBUG_ENDPOINTS=false

# Observability
ENABLE_TRACING=true
ENABLE_METRICS=true
TRACE_AGENT_REASONING=true
```

**File**: `backend/.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# Poetry
poetry.lock

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# Game state
gamestate/sessions/
*.db

# Logs
*.log
```

### Success Criteria:

#### Automated Verification:
- [ ] Poetry project initializes: `poetry install` completes successfully
- [ ] All dependencies install without conflicts
- [ ] Python version check passes: `python --version` shows 3.11+
- [ ] Linting passes: `poetry run poe lint` (will have no files yet, but command works)
- [ ] Directory structure exists: `ls -R src/agentic_rpg` shows all directories

#### Manual Verification:
- [ ] Project structure matches PRD specifications
- [ ] All configuration files are properly formatted
- [ ] Poetry commands work (`poetry run poe --help` shows all tasks)

---

## Phase 2: Core Data Models

### Overview
Implement all Pydantic data models that serve as the single source of truth for the entire system. These models will generate OpenAPI specs for the frontend.

### Changes Required:

#### 1. Base Models and Versioning

**File**: `backend/src/agentic_rpg/models/versioning.py`

```python
"""Schema version management and migrations."""
from typing import Dict, Callable, Any
from functools import wraps


class SchemaVersion:
    """Schema version management and migrations."""

    CURRENT = "1.0.0"
    MINIMUM_COMPATIBLE = "1.0.0"

    _migrations: Dict[tuple[str, str], Callable] = {}

    @classmethod
    def register_migration(cls, from_version: str, to_version: str):
        """Decorator to register schema migrations."""
        def decorator(func: Callable) -> Callable:
            cls._migrations[(from_version, to_version)] = func
            return func
        return decorator

    @classmethod
    def migrate(cls, state: dict, from_version: str, to_version: str) -> dict:
        """Apply migrations to bring state to target version."""
        # Simple implementation for now - extend as needed
        if from_version == to_version:
            return state

        # Will implement migration logic in future phases
        state["schema_version"] = to_version
        return state
```

#### 2. Character Models

**File**: `backend/src/agentic_rpg/models/character.py`

```python
"""Character-related data models."""
from pydantic import BaseModel, Field


class CharacterStats(BaseModel):
    """Character statistics."""

    health: int = Field(..., ge=0, description="Current health points")
    max_health: int = Field(..., ge=1, description="Maximum health points")
    energy: int = Field(..., ge=0, description="Current energy points")
    max_energy: int = Field(..., ge=1, description="Maximum energy points")
    money: int = Field(default=0, ge=0, description="Currency amount")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "health": 100,
                "max_health": 100,
                "energy": 50,
                "max_energy": 50,
                "money": 1000
            }]
        }
    }


class Character(BaseModel):
    """Player character model - source of truth for all layers."""

    id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., min_length=1, max_length=50, description="Character name")
    profession: str = Field(..., description="Character's profession")
    stats: CharacterStats
    location: str = Field(..., description="Current location ID")
    status: list[str] = Field(default_factory=list, description="Active status effects")

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "char_123",
                "name": "Jax",
                "profession": "Space Pirate",
                "stats": {
                    "health": 100,
                    "max_health": 100,
                    "energy": 50,
                    "max_energy": 50,
                    "money": 1000
                },
                "location": "cantina_001",
                "status": ["well_rested"]
            }]
        }
    }
```

#### 3. Inventory Models

**File**: `backend/src/agentic_rpg/models/inventory.py`

```python
"""Inventory-related data models."""
from pydantic import BaseModel, Field
from typing import Dict, Any


class InventoryItem(BaseModel):
    """Item in inventory."""

    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: str = Field(default="", description="Item description")
    quantity: int = Field(default=1, ge=1, description="Quantity of item")
    weight: float = Field(default=1.0, ge=0, description="Weight per item")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Item-specific properties"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "item_sword_001",
                "name": "Plasma Sword",
                "description": "A glowing blade of pure energy",
                "quantity": 1,
                "weight": 2.5,
                "properties": {
                    "damage": 15,
                    "type": "weapon",
                    "rarity": "rare"
                }
            }]
        }
    }


class Inventory(BaseModel):
    """Character inventory."""

    items: list[InventoryItem] = Field(default_factory=list)
    capacity: int = Field(default=20, ge=1, description="Max number of item stacks")
    max_weight: float = Field(default=100.0, ge=0, description="Maximum carry weight")

    @property
    def current_weight(self) -> float:
        """Calculate current total weight."""
        return sum(item.weight * item.quantity for item in self.items)

    @property
    def is_full(self) -> bool:
        """Check if inventory is at capacity."""
        return len(self.items) >= self.capacity

    def can_add(self, item: InventoryItem) -> tuple[bool, str]:
        """Check if item can be added to inventory."""
        if self.is_full:
            return False, "Inventory is full"

        new_weight = self.current_weight + (item.weight * item.quantity)
        if new_weight > self.max_weight:
            return False, f"Too heavy (would be {new_weight}/{self.max_weight})"

        return True, ""
```

#### 4. World Models

**File**: `backend/src/agentic_rpg/models/world.py`

```python
"""World-related data models."""
from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime


class NPC(BaseModel):
    """Non-player character."""

    id: str = Field(..., description="Unique NPC identifier")
    name: str = Field(..., description="NPC name")
    description: str = Field(..., description="NPC description")
    personality: str = Field(default="neutral", description="NPC personality type")
    dialogue_state: Dict[str, Any] = Field(
        default_factory=dict,
        description="NPC dialogue state"
    )


class Location(BaseModel):
    """Game location."""

    id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., min_length=1, description="Location name")
    description: str = Field(..., min_length=10, description="Location description")
    type: str = Field(..., description="Location type: city, wilderness, dungeon, etc.")
    connections: list[str] = Field(
        default_factory=list,
        description="Connected location IDs"
    )
    npcs: list[NPC] = Field(default_factory=list, description="NPCs at this location")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Location-specific properties"
    )


class WorldState(BaseModel):
    """Current world state."""

    current_location: Location
    available_locations: list[Location] = Field(default_factory=list)
    time_of_day: str = Field(default="day", description="Current time of day")
    weather: str = Field(default="clear", description="Current weather")
    discovered_locations: list[str] = Field(
        default_factory=list,
        description="Location IDs discovered by player"
    )
```

#### 5. Conversation Models

**File**: `backend/src/agentic_rpg/models/conversation.py`

```python
"""Conversation-related data models."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Dict, Any, Optional


class Message(BaseModel):
    """Chat message."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional message metadata"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "role": "user",
                "content": "I want to explore the ancient ruins.",
                "timestamp": "2025-01-01T12:00:00Z",
                "metadata": {"session_id": "session_123"}
            }]
        }
    }


class Conversation(BaseModel):
    """Conversation history."""

    messages: list[Message] = Field(default_factory=list)
    context: list[str] = Field(
        default_factory=list,
        description="Important context from previous messages"
    )
    max_history: int = Field(default=100, description="Maximum messages to keep")

    def add_message(self, message: Message) -> None:
        """Add message and maintain history limit."""
        self.messages.append(message)
        if len(self.messages) > self.max_history:
            self.messages.pop(0)
```

#### 6. Main Game State Model

**File**: `backend/src/agentic_rpg/models/game_state.py`

```python
"""Main game state model."""
from pydantic import BaseModel, Field
from datetime import datetime
from .character import Character
from .inventory import Inventory
from .world import WorldState
from .conversation import Conversation
from .versioning import SchemaVersion


class GameState(BaseModel):
    """Complete game state - versioned and validated."""

    schema_version: str = Field(
        default=SchemaVersion.CURRENT,
        description="Schema version for migrations"
    )
    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(..., description="Session creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    character: Character
    inventory: Inventory
    world: WorldState
    conversation: Conversation

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "schema_version": "1.0.0",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T12:00:00Z",
                "character": {
                    "id": "char_001",
                    "name": "Test Hero",
                    "profession": "Adventurer",
                    "stats": {
                        "health": 100,
                        "max_health": 100,
                        "energy": 50,
                        "max_energy": 50,
                        "money": 1000
                    },
                    "location": "start_location",
                    "status": []
                },
                "inventory": {"items": [], "capacity": 20, "max_weight": 100.0},
                "world": {
                    "current_location": {
                        "id": "start_location",
                        "name": "Starting Village",
                        "description": "A peaceful village",
                        "type": "settlement",
                        "connections": [],
                        "npcs": [],
                        "properties": {}
                    },
                    "available_locations": [],
                    "time_of_day": "day",
                    "weather": "clear",
                    "discovered_locations": ["start_location"]
                },
                "conversation": {"messages": [], "context": [], "max_history": 100}
            }]
        }
    }
```

#### 7. API Response Models

**File**: `backend/src/agentic_rpg/models/responses.py`

```python
"""API response models."""
from pydantic import BaseModel, Field
from typing import Dict, Any
from .game_state import GameState


class CreateGameResponse(BaseModel):
    """Response from game creation."""

    session_id: str = Field(..., description="New session ID")
    state: GameState = Field(..., description="Initial game state")


class GameResponse(BaseModel):
    """Response from game action."""

    response: str = Field(..., description="Narrative response")
    state_updates: Dict[str, Any] = Field(
        default_factory=dict,
        description="State changes"
    )
    tool_calls: list[str] = Field(
        default_factory=list,
        description="Tools that were executed"
    )
```

#### 8. Models Package Init

**File**: `backend/src/agentic_rpg/models/__init__.py`

```python
"""Data models package."""
from .game_state import GameState
from .character import Character, CharacterStats
from .inventory import Inventory, InventoryItem
from .world import WorldState, Location, NPC
from .conversation import Conversation, Message
from .responses import CreateGameResponse, GameResponse
from .versioning import SchemaVersion

__all__ = [
    "GameState",
    "Character",
    "CharacterStats",
    "Inventory",
    "InventoryItem",
    "WorldState",
    "Location",
    "NPC",
    "Conversation",
    "Message",
    "CreateGameResponse",
    "GameResponse",
    "SchemaVersion",
]
```

### Success Criteria:

#### Automated Verification:
- [ ] All model files import without errors: `python -c "from agentic_rpg.models import *"`
- [ ] Models validate example data: `poetry run pytest tests/unit/test_models/`
- [ ] Pydantic generates JSON schemas: Check `model_json_schema()` works
- [ ] Type checking passes: `poetry run poe typecheck`

#### Manual Verification:
- [ ] All models have proper docstrings
- [ ] Field descriptions are clear and accurate
- [ ] Example data in `json_schema_extra` is valid
- [ ] Models match PRD specifications

---

## Phase 3: Service Interfaces and Core Services

### Overview
Define service interfaces using Python Protocols and implement the core services (Event Bus, Tool Registry, State Manager). These establish the contracts for parallel development.

### Changes Required:

#### 1. Service Interfaces

**File**: `backend/src/agentic_rpg/services/interfaces.py`

```python
"""Service interface definitions using Protocol."""
from typing import Protocol
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.character import Character


class StateManager(Protocol):
    """Interface for game state persistence."""

    def create_session(self, character: Character) -> str:
        """Create new game session, return session ID."""
        ...

    def load_state(self, session_id: str) -> GameState:
        """Load complete game state."""
        ...

    def update_state(self, session_id: str, updates: dict) -> GameState:
        """Apply partial updates to state."""
        ...

    def delete_session(self, session_id: str) -> bool:
        """Delete game session."""
        ...
```

#### 2. Event Bus Implementation

**File**: `backend/src/agentic_rpg/services/event_bus.py`

```python
"""Event bus for component communication."""
from typing import Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Standard event types."""
    STATE_UPDATED = "state.updated"
    GAME_CREATED = "game.created"
    ITEM_ACQUIRED = "inventory.item_acquired"
    LOCATION_CHANGED = "world.location_changed"


@dataclass
class EventSchema:
    """Schema definition for event validation."""
    type: str
    required_fields: set[str]
    optional_fields: set[str] = field(default_factory=set)

    def validate(self, payload: dict) -> tuple[bool, str]:
        """Validate event payload against schema."""
        missing = self.required_fields - set(payload.keys())
        if missing:
            return False, f"Missing required fields: {missing}"

        extra = set(payload.keys()) - (self.required_fields | self.optional_fields)
        if extra:
            return False, f"Unexpected fields: {extra}"

        return True, ""


@dataclass
class GameEvent:
    """Game event with validated payload."""
    type: str
    payload: dict
    source: str  # Component that triggered event
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "payload": self.payload,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
        }


class EventBus:
    """Central event bus for component communication."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._schemas: dict[str, EventSchema] = {}
        self._history: list[GameEvent] = []
        self._max_history = 1000

    def register_schema(self, schema: EventSchema) -> None:
        """Register event schema for validation."""
        self._schemas[schema.type] = schema

    def publish(self, event: GameEvent) -> None:
        """Publish event to all subscribers."""
        # Validate if schema exists
        if event.type in self._schemas:
            valid, error = self._schemas[event.type].validate(event.payload)
            if not valid:
                raise ValueError(f"Invalid event payload: {error}")

        # Store in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Notify subscribers
        subscribers = self._subscribers.get(event.type, [])
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                # Log but don't fail
                print(f"Error in event subscriber: {e}")

    def subscribe(self, event_type: str, callback: Callable[[GameEvent], None]) -> None:
        """Subscribe to specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def get_history(
        self,
        event_type: str | None = None,
        session_id: str | None = None,
        limit: int = 100
    ) -> list[GameEvent]:
        """Get event history for debugging/replay."""
        events = self._history

        if event_type:
            events = [e for e in events if e.type == event_type]

        if session_id:
            events = [e for e in events if e.session_id == session_id]

        return events[-limit:]


# Global event bus instance
_event_bus = EventBus()

def get_event_bus() -> EventBus:
    """Get global event bus instance."""
    return _event_bus
```

#### 3. Tool Registry Implementation

**File**: `backend/src/agentic_rpg/agents/tools/base.py`

```python
"""Base tool interfaces."""
from typing import Protocol


class GameTool(Protocol):
    """Interface for all game tools callable by agents."""

    name: str
    description: str
    schema: dict  # JSON schema for parameters

    def execute(self, **kwargs) -> dict:
        """Execute the tool and return results."""
        ...

    def validate(self, **kwargs) -> bool:
        """Validate tool parameters before execution."""
        ...
```

**File**: `backend/src/agentic_rpg/agents/tools/registry.py`

```python
"""Tool registry for dynamic tool registration."""
from typing import Any
from .base import GameTool


class ToolRegistry:
    """Central registry for agent tools - prevents merge conflicts."""

    _tools: dict[str, GameTool] = {}
    _categories: dict[str, list[str]] = {}

    @classmethod
    def register(cls, tool: GameTool, category: str = "general") -> None:
        """Register a tool."""
        if tool.name in cls._tools:
            raise ValueError(f"Tool {tool.name} already registered")

        cls._tools[tool.name] = tool
        cls._categories.setdefault(category, []).append(tool.name)

    @classmethod
    def get_tool(cls, name: str) -> GameTool:
        """Get tool by name."""
        if name not in cls._tools:
            raise KeyError(f"Tool {name} not registered")
        return cls._tools[name]

    @classmethod
    def get_tools_by_category(cls, category: str) -> list[GameTool]:
        """Get all tools in a category."""
        tool_names = cls._categories.get(category, [])
        return [cls._tools[name] for name in tool_names]

    @classmethod
    def list_all(cls) -> list[str]:
        """List all registered tool names."""
        return list(cls._tools.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (for testing)."""
        cls._tools.clear()
        cls._categories.clear()
```

#### 4. Mock State Manager (for testing)

**File**: `backend/src/agentic_rpg/services/mock_state_manager.py`

```python
"""Mock state manager for testing."""
from datetime import datetime
import uuid
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.character import Character
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.models.world import WorldState, Location
from agentic_rpg.models.conversation import Conversation


class MockStateManager:
    """In-memory state manager for testing."""

    def __init__(self):
        self._sessions: dict[str, GameState] = {}

    def create_session(self, character: Character) -> str:
        """Create new game session."""
        session_id = str(uuid.uuid4())

        # Create initial location
        start_location = Location(
            id="start_location",
            name="Starting Village",
            description="A peaceful village where your journey begins",
            type="settlement",
            connections=[],
            npcs=[],
            properties={}
        )

        # Create initial game state
        state = GameState(
            session_id=session_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            character=character,
            inventory=Inventory(),
            world=WorldState(
                current_location=start_location,
                available_locations=[start_location],
                discovered_locations=[start_location.id]
            ),
            conversation=Conversation()
        )

        self._sessions[session_id] = state
        return session_id

    def load_state(self, session_id: str) -> GameState:
        """Load game state."""
        if session_id not in self._sessions:
            raise KeyError(f"Session {session_id} not found")
        return self._sessions[session_id]

    def update_state(self, session_id: str, updates: dict) -> GameState:
        """Apply updates to state."""
        state = self.load_state(session_id)

        # Simple deep update (extend for nested updates)
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)

        state.updated_at = datetime.utcnow()
        return state

    def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
```

#### 5. Configuration

**File**: `backend/src/agentic_rpg/config.py`

```python
"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Application
    app_name: str = "Agentic RPG"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]

    # State Storage
    state_storage_type: str = "json"
    state_storage_path: Path = Path("./gamestate")

    # Development Options
    use_mocks: bool = False

    def validate_config(self) -> None:
        """Validate configuration at startup."""
        if self.state_storage_type == "json":
            self.state_storage_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Settings | None = None

def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_config()
    return _settings
```

### Success Criteria:

#### Automated Verification:
- [ ] Event bus publishes and receives events: `poetry run pytest tests/unit/test_services/test_event_bus.py`
- [ ] Tool registry registers and retrieves tools: `poetry run pytest tests/unit/test_tools/test_registry.py`
- [ ] Mock state manager CRUD operations work: `poetry run pytest tests/unit/test_services/test_mock_state_manager.py`
- [ ] Configuration loads from environment: `poetry run pytest tests/unit/test_config.py`

#### Manual Verification:
- [ ] Service interfaces are properly defined with Protocols
- [ ] All services have comprehensive docstrings
- [ ] Code follows type hints strictly

---

## Phase 4: FastAPI Application

### Overview
Create the FastAPI application with health check endpoints and basic routing. Set up middleware, CORS, and OpenAPI documentation.

### Changes Required:

#### 1. Main FastAPI Application

**File**: `backend/src/agentic_rpg/api/main.py`

```python
"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agentic_rpg.config import get_settings
from agentic_rpg.api.routes import health

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Dynamic AI-driven RPG game with LangGraph agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print(f"🚀 Starting {settings.app_name}")
    print(f"📊 Environment: {settings.app_env}")
    print(f"🔧 Debug mode: {settings.debug}")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print(f"👋 Shutting down {settings.app_name}")
```

#### 2. Health Check Routes

**File**: `backend/src/agentic_rpg/api/routes/__init__.py`

```python
"""API routes package."""
```

**File**: `backend/src/agentic_rpg/api/routes/health.py`

```python
"""Health check endpoints."""
from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/health")


@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"ready": True}


@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}
```

#### 3. Run Script

**File**: `backend/scripts/run.py`

```python
"""Run the FastAPI application."""
import uvicorn
from agentic_rpg.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "agentic_rpg.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
```

Make executable:
```bash
chmod +x backend/scripts/run.py
```

### Success Criteria:

#### Automated Verification:
- [ ] FastAPI app starts: `poetry run python scripts/run.py` (then Ctrl+C)
- [ ] Health endpoint responds: `curl http://localhost:8000/api/health/`
- [ ] OpenAPI docs accessible: Check `http://localhost:8000/docs` in browser
- [ ] OpenAPI spec valid JSON: `curl http://localhost:8000/openapi.json`

#### Manual Verification:
- [ ] Server starts without errors
- [ ] CORS headers present in responses
- [ ] OpenAPI documentation is complete and accurate
- [ ] All endpoints are properly tagged

---

## Phase 5: Contract Tests Framework

### Overview
Set up the contract testing framework that validates all interfaces. This ensures teams can develop independently without breaking integrations.

### Changes Required:

#### 1. Test Configuration

**File**: `backend/tests/conftest.py`

```python
"""Shared fixtures and configuration."""
import pytest
from datetime import datetime
from agentic_rpg.models.character import Character, CharacterStats
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.inventory import Inventory
from agentic_rpg.models.world import WorldState, Location
from agentic_rpg.models.conversation import Conversation
from agentic_rpg.services.event_bus import EventBus
from agentic_rpg.services.mock_state_manager import MockStateManager


@pytest.fixture
def mock_character() -> Character:
    """Create mock character for testing."""
    return Character(
        id="test_char_001",
        name="Test Character",
        profession="Tester",
        stats=CharacterStats(
            health=100,
            max_health=100,
            energy=50,
            max_energy=50,
            money=1000
        ),
        location="test_location",
        status=[]
    )


@pytest.fixture
def mock_game_state(mock_character: Character) -> GameState:
    """Create complete mock game state."""
    return GameState(
        schema_version="1.0.0",
        session_id="test_session",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        character=mock_character,
        inventory=Inventory(),
        world=WorldState(
            current_location=Location(
                id="test_location",
                name="Test Location",
                description="A test location",
                type="test",
                connections=[],
                npcs=[],
                properties={}
            ),
            available_locations=[],
            discovered_locations=["test_location"]
        ),
        conversation=Conversation()
    )


@pytest.fixture
def event_bus() -> EventBus:
    """Create fresh event bus for each test."""
    return EventBus()


@pytest.fixture
def mock_state_manager() -> MockStateManager:
    """Create mock state manager."""
    return MockStateManager()
```

#### 2. State Manager Contract Tests

**File**: `backend/tests/contracts/test_state_manager_contract.py`

```python
"""Contract tests for StateManager interface."""
import pytest
from agentic_rpg.models.game_state import GameState
from agentic_rpg.services.mock_state_manager import MockStateManager


@pytest.mark.contract
class TestStateManagerContract:
    """Contract tests for StateManager interface.

    ALL implementations of StateManager must pass these tests.
    """

    @pytest.fixture
    def implementation(self):
        """Return the implementation to test."""
        return MockStateManager()

    def test_create_session_returns_valid_id(self, implementation, mock_character):
        """Contract: create_session must return a valid session ID."""
        session_id = implementation.create_session(mock_character)

        assert isinstance(session_id, str)
        assert len(session_id) > 0
        # UUID format
        assert len(session_id) == 36
        assert session_id.count('-') == 4

    def test_load_state_returns_complete_state(self, implementation, mock_character):
        """Contract: load_state must return a valid GameState."""
        session_id = implementation.create_session(mock_character)
        state = implementation.load_state(session_id)

        assert isinstance(state, GameState)
        assert state.session_id == session_id
        assert state.character is not None
        assert state.inventory is not None
        assert state.world is not None

    def test_load_nonexistent_session_raises_error(self, implementation):
        """Contract: loading non-existent session must raise KeyError."""
        with pytest.raises(KeyError):
            implementation.load_state("nonexistent_session")

    def test_delete_session_removes_state(self, implementation, mock_character):
        """Contract: delete_session must remove all state."""
        session_id = implementation.create_session(mock_character)

        success = implementation.delete_session(session_id)
        assert success is True

        with pytest.raises(KeyError):
            implementation.load_state(session_id)
```

#### 3. Model Validation Tests

**File**: `backend/tests/unit/test_models/test_character.py`

```python
"""Tests for character models."""
import pytest
from pydantic import ValidationError
from agentic_rpg.models.character import Character, CharacterStats


class TestCharacterStats:
    """Test CharacterStats model."""

    def test_valid_stats(self):
        """Test creating valid stats."""
        stats = CharacterStats(
            health=100,
            max_health=100,
            energy=50,
            max_energy=50,
            money=1000
        )
        assert stats.health == 100
        assert stats.max_health == 100

    def test_health_cannot_be_negative(self):
        """Test health validation."""
        with pytest.raises(ValidationError):
            CharacterStats(
                health=-10,
                max_health=100,
                energy=50,
                max_energy=50
            )

    def test_max_health_must_be_positive(self):
        """Test max_health validation."""
        with pytest.raises(ValidationError):
            CharacterStats(
                health=0,
                max_health=0,
                energy=50,
                max_energy=50
            )


class TestCharacter:
    """Test Character model."""

    def test_valid_character(self):
        """Test creating valid character."""
        character = Character(
            id="char_001",
            name="Test",
            profession="Tester",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50
            ),
            location="start"
        )
        assert character.name == "Test"
        assert character.profession == "Tester"

    def test_name_cannot_be_empty(self):
        """Test name validation."""
        with pytest.raises(ValidationError):
            Character(
                id="char_001",
                name="",
                profession="Tester",
                stats=CharacterStats(
                    health=100,
                    max_health=100,
                    energy=50,
                    max_energy=50
                ),
                location="start"
            )
```

### Success Criteria:

#### Automated Verification:
- [ ] All contract tests pass: `poetry run poe test-contracts`
- [ ] Model validation tests pass: `poetry run pytest tests/unit/test_models/`
- [ ] Test markers work: `pytest --markers` shows custom markers
- [ ] Coverage report generated: `poetry run poe test` shows coverage

#### Manual Verification:
- [ ] Contract tests are comprehensive
- [ ] All critical interfaces have contract tests
- [ ] Test fixtures are reusable

---

## Phase 6: Frontend Next.js Setup

### Overview
Initialize the Next.js 14+ project with TypeScript, Tailwind CSS, and basic structure. Set up the app router and create stub API client.

### Changes Required:

#### 1. Create Next.js Project

**Location**: `/home/mtomcal/code/agentic-rpg/frontend/`

**Actions**:
```bash
# Create Next.js project with TypeScript
npx create-next-app@latest frontend \
  --typescript \
  --tailwind \
  --app \
  --no-src-dir \
  --import-alias "@/*"

cd frontend
```

#### 2. Install Additional Dependencies

```bash
# State management
npm install zustand

# API client generation
npm install --save-dev openapi-typescript openapi-typescript-codegen

# Testing
npm install --save-dev @playwright/test
```

#### 3. Configuration Files

**File**: `frontend/tsconfig.json` (update generated file)

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowJs": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

**File**: `frontend/.env.example`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**File**: `frontend/.gitignore`

```
# Next.js
.next/
out/
build/
.vercel
.turbo

# Dependencies
node_modules/

# TypeScript
*.tsbuildinfo
next-env.d.ts

# Environment
.env
.env.local
.env.production.local

# Testing
/playwright-report/
/test-results/

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

#### 4. Basic Configuration

**File**: `frontend/lib/config.ts`

```typescript
const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    timeout: 30000,
    version: 'v1',
  },
  game: {
    maxMessageLength: 500,
    autosaveInterval: 60000,
    maxHistoryMessages: 100,
  },
  ui: {
    enableAnimations: true,
    theme: 'dark',
    debugMode: process.env.NODE_ENV === 'development',
  },
} as const;

export default config;
```

#### 5. Stub API Client

**File**: `frontend/lib/api/client.ts`

```typescript
import config from '../config';

export class GameAPIClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || config.api.baseUrl;
  }

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await fetch(`${this.baseUrl}/api/health/`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  }

  // More methods will be added in later phases
}

export const apiClient = new GameAPIClient();
```

#### 6. Basic Layout

**File**: `frontend/app/layout.tsx`

```typescript
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Agentic RPG',
  description: 'Dynamic AI-driven RPG game',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
```

**File**: `frontend/app/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api/client';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    apiClient.healthCheck()
      .then(data => setHealthStatus(data.status))
      .catch(() => setHealthStatus('error'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Agentic RPG</h1>
        <p className="text-xl mb-2">Backend Status: {healthStatus}</p>
        <p className="text-gray-600">Foundation setup complete</p>
      </div>
    </main>
  );
}
```

#### 7. Package.json Scripts

**File**: `frontend/package.json` (add to scripts section)

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "type-check": "tsc --noEmit",
    "test": "playwright test",
    "generate-types": "bash scripts/generate-types.sh"
  }
}
```

### Success Criteria:

#### Automated Verification:
- [ ] Next.js builds successfully: `npm run build`
- [ ] Type checking passes: `npm run type-check`
- [ ] Linting passes: `npm run lint`
- [ ] Dev server starts: `npm run dev` (check port 3000)

#### Manual Verification:
- [ ] Frontend loads in browser at http://localhost:3000
- [ ] Health check connects to backend and shows "healthy"
- [ ] No console errors in browser
- [ ] Tailwind CSS styles are working

---

## Phase 7: Type Generation Pipeline

### Overview
Create the automated type generation pipeline that keeps frontend and backend types synchronized. This is critical for preventing type drift.

### Changes Required:

#### 1. Backend Schema Generation Script

**File**: `backend/scripts/generate_schemas.py`

```python
"""Generate JSON schemas from Pydantic models."""
import json
from pathlib import Path
from agentic_rpg.models import (
    GameState,
    Character,
    CharacterStats,
    Inventory,
    InventoryItem,
    WorldState,
    Location,
    NPC,
    Conversation,
    Message,
    CreateGameResponse,
    GameResponse,
)


def main():
    """Generate schemas and save to shared-types directory."""
    schemas = {
        "GameState": GameState.model_json_schema(),
        "Character": Character.model_json_schema(),
        "CharacterStats": CharacterStats.model_json_schema(),
        "Inventory": Inventory.model_json_schema(),
        "InventoryItem": InventoryItem.model_json_schema(),
        "WorldState": WorldState.model_json_schema(),
        "Location": Location.model_json_schema(),
        "NPC": NPC.model_json_schema(),
        "Conversation": Conversation.model_json_schema(),
        "Message": Message.model_json_schema(),
        "CreateGameResponse": CreateGameResponse.model_json_schema(),
        "GameResponse": GameResponse.model_json_schema(),
    }

    # Ensure directory exists
    output_dir = Path("../shared-types")
    output_dir.mkdir(exist_ok=True)

    # Write schemas
    output_file = output_dir / "schemas.json"
    with open(output_file, "w") as f:
        json.dump(schemas, f, indent=2)

    print(f"✅ Generated schemas to {output_file}")


if __name__ == "__main__":
    main()
```

#### 2. Type Generation Script

**File**: `frontend/scripts/generate-types.sh`

```bash
#!/bin/bash
set -e

echo "🔄 Generating TypeScript types from backend..."

# Check if backend is running, if not start it temporarily
BACKEND_STARTED=false
if ! curl -s http://localhost:8000/api/health/ > /dev/null; then
    echo "📦 Starting backend temporarily..."
    cd ../backend
    poetry run python -m uvicorn agentic_rpg.api.main:app --port 8000 &
    BACKEND_PID=$!
    BACKEND_STARTED=true
    sleep 3
    cd ../frontend
fi

# Download OpenAPI spec
echo "📥 Downloading OpenAPI spec..."
curl -s http://localhost:8000/openapi.json > ../shared-types/openapi.json

# Generate TypeScript types
echo "🔨 Generating TypeScript types..."
npx openapi-typescript ../shared-types/openapi.json -o lib/types/api.ts

# Stop backend if we started it
if [ "$BACKEND_STARTED" = true ]; then
    echo "🛑 Stopping temporary backend..."
    kill $BACKEND_PID
fi

echo "✅ Type generation complete!"
```

Make executable:
```bash
chmod +x frontend/scripts/generate-types.sh
```

#### 3. Directory Setup

**Create shared-types directory**:
```bash
mkdir -p shared-types
touch shared-types/.gitkeep
```

**File**: `shared-types/README.md`

```markdown
# Shared Types

This directory contains generated type definitions shared between frontend and backend.

## Files

- `openapi.json` - Generated OpenAPI specification from FastAPI
- `schemas.json` - JSON schemas from Pydantic models

## Generation

Types are generated automatically:

```bash
# From backend directory
poetry run poe generate-schemas

# From frontend directory
npm run generate-types
```

## DO NOT EDIT

These files are auto-generated. Changes will be overwritten.
```

### Success Criteria:

#### Automated Verification:
- [ ] Schema generation works: `cd backend && poetry run poe generate-schemas`
- [ ] OpenAPI spec generates: Backend running, check `/openapi.json`
- [ ] TypeScript types generate: `cd frontend && npm run generate-types`
- [ ] Generated types have no errors: `cd frontend && npm run type-check`

#### Manual Verification:
- [ ] `shared-types/schemas.json` contains all models
- [ ] `shared-types/openapi.json` is valid JSON
- [ ] `frontend/lib/types/api.ts` exists and has types
- [ ] Types match backend models exactly

---

## Phase 8: CI/CD Pipeline

### Overview
Set up GitHub Actions for automated testing, type checking, and validation on every PR.

### Changes Required:

#### 1. GitHub Workflows Directory

```bash
mkdir -p .github/workflows
```

#### 2. Backend CI Workflow

**File**: `.github/workflows/backend-ci.yml`

```yaml
name: Backend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-ci.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'backend/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        working-directory: ./backend
        run: poetry install

      - name: Run linting
        working-directory: ./backend
        run: poetry run poe lint

      - name: Run type checking
        working-directory: ./backend
        run: poetry run poe typecheck

      - name: Run tests
        working-directory: ./backend
        run: poetry run poe test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
```

#### 3. Frontend CI Workflow

**File**: `.github/workflows/frontend-ci.yml`

```yaml
name: Frontend CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'frontend/**'
      - '.github/workflows/frontend-ci.yml'
  pull_request:
    branches: [main, develop]
    paths:
      - 'frontend/**'

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run linting
        working-directory: ./frontend
        run: npm run lint

      - name: Run type checking
        working-directory: ./frontend
        run: npm run type-check

      - name: Build
        working-directory: ./frontend
        run: npm run build
```

#### 4. Contract Tests Workflow

**File**: `.github/workflows/contract-tests.yml`

```yaml
name: Contract Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  contract-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Install dependencies
        working-directory: ./backend
        run: poetry install

      - name: Run contract tests
        working-directory: ./backend
        run: poetry run poe test-contracts
```

#### 5. CODEOWNERS File

**File**: `.github/CODEOWNERS`

```
# Module Ownership Map

# Core team owns models and services
/backend/src/agentic_rpg/models/              @team-core
/backend/src/agentic_rpg/services/state*      @team-core
/backend/src/agentic_rpg/services/event_bus*  @team-core

# Agent team owns agent logic
/backend/src/agentic_rpg/agents/              @team-agents

# Tools team owns tool implementations
/backend/src/agentic_rpg/agents/tools/        @team-tools

# API team owns API layer
/backend/src/agentic_rpg/api/                 @team-api

# Frontend team owns UI
/frontend/                                     @team-frontend

# Shared interfaces require multiple approvals
/backend/src/agentic_rpg/services/interfaces.py  @team-core @team-agents
/shared-types/                                    @team-core @team-frontend

# CI/CD requires tech lead approval
/.github/workflows/                            @tech-lead
```

### Success Criteria:

#### Automated Verification:
- [ ] GitHub Actions workflows are valid YAML
- [ ] Backend CI runs and passes
- [ ] Frontend CI runs and passes
- [ ] Contract tests CI runs and passes

#### Manual Verification:
- [ ] CODEOWNERS file syntax is correct
- [ ] Workflows trigger on correct paths
- [ ] All critical paths are covered by CI

---

## Phase 9: Documentation

### Overview
Create essential documentation for onboarding and development.

### Changes Required:

#### 1. Root README

**File**: `README.md`

```markdown
# Agentic RPG

Dynamic AI-driven RPG game with LangGraph agents.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Poetry
- npm

### Backend Setup

\`\`\`bash
cd backend
poetry install
cp .env.example .env
# Edit .env with your configuration
poetry run poe dev
\`\`\`

Backend runs at: http://localhost:8000
API Docs: http://localhost:8000/docs

### Frontend Setup

\`\`\`bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with backend URL
npm run dev
\`\`\`

Frontend runs at: http://localhost:3000

### Full Stack with Docker

\`\`\`bash
docker-compose up
\`\`\`

## Development

### Running Tests

\`\`\`bash
# Backend
cd backend
poetry run poe test              # All tests
poetry run poe test-unit         # Unit tests only
poetry run poe test-contracts    # Contract tests only

# Frontend
cd frontend
npm run type-check
npm run lint
npm run build
\`\`\`

### Type Generation

When backend models change:

\`\`\`bash
cd backend
poetry run poe generate-schemas

cd ../frontend
npm run generate-types
\`\`\`

## Project Structure

See [PRD.md](./PRD.md) for complete architecture documentation.

\`\`\`
├── backend/          # Python FastAPI backend
├── frontend/         # Next.js frontend
├── shared-types/     # Generated type definitions
└── docs/             # Documentation
\`\`\`

## Team Structure

- **@team-core**: Data models, state management, event bus
- **@team-api**: FastAPI routes, WebSocket, middleware
- **@team-agents**: LangGraph orchestration, agent logic
- **@team-tools**: Game mechanics, tool implementations
- **@team-frontend**: UI components, state management

## Documentation

- [Product Requirements](./PRD.md)
- [Architecture](./docs/ARCHITECTURE.md)
- [Contributing](./docs/CONTRIBUTING.md)
- [API Documentation](http://localhost:8000/docs) (when running)

## License

TBD
```

#### 2. Contributing Guide

**File**: `docs/CONTRIBUTING.md`

```markdown
# Contributing Guide

## Development Workflow

1. **Clone and setup**
   \`\`\`bash
   git clone <repo>
   cd agentic-rpg
   # Follow Quick Start in README.md
   \`\`\`

2. **Create feature branch**
   \`\`\`bash
   git checkout -b feature/team-feature-name
   \`\`\`

3. **Make changes**
   - Follow team ownership (see CODEOWNERS)
   - Write tests for new code
   - Update documentation if needed

4. **Run checks**
   \`\`\`bash
   # Backend
   cd backend
   poetry run poe check-all

   # Frontend
   cd frontend
   npm run lint
   npm run type-check
   npm run build
   \`\`\`

5. **Commit**
   \`\`\`bash
   git add .
   git commit -m "feat(team): description"
   \`\`\`

   Use conventional commits:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation
   - `test:` - Tests
   - `refactor:` - Code refactoring

6. **Push and create PR**
   \`\`\`bash
   git push origin feature/team-feature-name
   \`\`\`

## Code Standards

### Python (Backend)

- Use type hints everywhere
- Follow Ruff formatting
- Write docstrings for public functions
- Keep functions focused and small
- Use Pydantic for all data models

### TypeScript (Frontend)

- Enable strict mode
- Use TypeScript, not JavaScript
- Prefer functional components
- Use generated types from backend

## Testing

### Contract Tests

All interface implementations must pass contract tests:

\`\`\`python
@pytest.mark.contract
class TestMyServiceContract:
    def test_interface_requirement(self):
        # Test implementation meets interface
        pass
\`\`\`

### Unit Tests

Test isolated functionality:

\`\`\`python
def test_inventory_add_item():
    inventory = Inventory()
    item = InventoryItem(id="test", name="Test")
    success, msg = inventory.can_add(item)
    assert success is True
\`\`\`

## Integration Windows

- **10am UTC**: Morning integration window
- **3pm UTC**: Afternoon integration window

Merge completed features during these windows to minimize conflicts.

## Getting Help

- Check documentation first
- Ask in team channel
- Tag module owners for interface questions
- Create RFC for breaking changes
```

### Success Criteria:

#### Automated Verification:
- [ ] All markdown files are valid
- [ ] Links in docs are not broken
- [ ] Code blocks in docs have correct syntax

#### Manual Verification:
- [ ] README is clear and comprehensive
- [ ] Contributing guide covers all workflows
- [ ] Documentation matches actual project structure

---

## Phase 10: Docker Setup

### Overview
Create Docker configuration for easy local development environment setup.

### Changes Required:

#### 1. Backend Dockerfile

**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["poetry", "run", "python", "scripts/run.py"]
```

#### 2. Frontend Dockerfile

**File**: `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy dependency files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run application
CMD ["npm", "run", "dev"]
```

#### 3. Docker Compose

**File**: `docker-compose.yml` (in root)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=development
      - USE_MOCKS=false
      - STATE_STORAGE_TYPE=json
      - STATE_STORAGE_PATH=/app/gamestate
    volumes:
      - ./backend:/app
      - gamestate:/app/gamestate
    command: poetry run uvicorn agentic_rpg.api.main:app --reload --host 0.0.0.0

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_WS_URL=ws://backend:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: npm run dev

volumes:
  gamestate:
```

### Success Criteria:

#### Automated Verification:
- [ ] Docker Compose builds: `docker-compose build`
- [ ] Services start: `docker-compose up` (then Ctrl+C)
- [ ] Backend accessible: `curl http://localhost:8000/api/health/`
- [ ] Frontend accessible: Check http://localhost:3000

#### Manual Verification:
- [ ] Hot reload works in both services
- [ ] Volumes persist data correctly
- [ ] Services can communicate

---

## Testing Strategy

### Unit Tests

Focus on isolated component testing:
- Model validation
- Service logic
- Utility functions
- No external dependencies

### Contract Tests

Validate interface implementations:
- StateManager interface
- AgentService interface (placeholder for now)
- GameTool interface (placeholder for now)
- API response contracts

### Integration Tests

Test component interactions:
- API endpoints with state manager
- Event bus with subscribers
- Tool registry with tools

No end-to-end tests in Phase 0 (no real features yet).

## Migration Notes

N/A - This is initial setup, no existing data to migrate.

## Performance Considerations

- JSON state storage is temporary (Phase 0 only)
- Will switch to PostgreSQL in production
- Event bus is in-memory (consider Redis in production)
- No caching layer yet (add in later phases)

## References

- Original PRD: `PRD.md`
- Python type hints: https://docs.python.org/3/library/typing.html
- Pydantic docs: https://docs.pydantic.dev/
- FastAPI docs: https://fastapi.tiangolo.com/
- Next.js docs: https://nextjs.org/docs
- LangGraph docs: https://python.langchain.com/docs/langgraph
