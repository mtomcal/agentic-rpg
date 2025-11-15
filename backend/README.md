# Agentic RPG Backend

A modular, agent-driven RPG backend built with Python, FastAPI, and LangGraph.

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)

### Installation

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=agentic_rpg

# Run specific test file
poetry run pytest tests/unit/test_models/test_character.py -v

# Run with type checking
poetry run mypy backend/src

# Run with linting
poetry run ruff check backend/src
```

## Project Structure

```
backend/
├── src/agentic_rpg/
│   ├── agents/           # LangGraph agents and tool implementations
│   │   └── tools/        # Game tool registry and tool definitions
│   │       ├── base.py   # GameTool Protocol
│   │       └── registry.py  # ToolRegistry class
│   ├── models/           # Pydantic data models (source of truth for types)
│   │   ├── character.py  # Character, Stats, Attributes
│   │   ├── conversation.py  # Message, ConversationHistory
│   │   ├── game_state.py    # GameState (root model)
│   │   ├── inventory.py     # Item, Inventory
│   │   ├── responses.py     # API response models
│   │   ├── versioning.py    # Schema versioning system
│   │   └── world.py         # Location, WorldState
│   ├── services/         # Core services
│   │   ├── event_bus.py       # Event pub/sub system
│   │   ├── interfaces.py      # Service Protocol definitions
│   │   └── mock_state_manager.py  # In-memory state for testing
│   ├── api/              # FastAPI routes (future)
│   └── config.py         # Application configuration
└── tests/
    └── unit/             # Unit tests (mirrors src structure)
```

## Architecture

### Core Components

#### 1. Data Models (`models/`)

All data models are defined using Pydantic v2 with strict type checking. These models serve as the **single source of truth** for the entire system, including TypeScript frontend types.

**Key Models:**
- `GameState`: Root state container for entire game session
- `Character`: Player character with stats, attributes, and profession
- `WorldState`: Game world with locations and NPCs
- `Inventory`: Item management system
- `ConversationHistory`: Message history with metadata

**Features:**
- JSON schema generation for validation
- Automatic versioning with migrations
- Comprehensive field validation
- Rich documentation via docstrings

Example:
```python
from agentic_rpg.models.game_state import GameState

# Create new game state
state = GameState.create_initial_state(session_id="session_123")

# Access nested data
character = state.character
location = state.world.current_location
```

#### 2. Event Bus (`services/event_bus.py`)

Pub/sub system for loose coupling between components. Uses deque for O(1) event history management.

**Event Types (Phase 0):**
- `STATE_UPDATED`: Game state changed
- `GAME_CREATED`: New game session created
- `ITEM_ACQUIRED`: Item added to inventory
- `LOCATION_CHANGED`: Player moved to new location

**Features:**
- Schema validation for event payloads
- Event history for debugging/replay
- Exception isolation (one bad subscriber doesn't break others)
- Proper logging with `logger.exception()`

Example:
```python
from agentic_rpg.services.event_bus import get_event_bus, GameEvent, EventType

bus = get_event_bus()

# Subscribe to events
def on_location_change(event: GameEvent):
    print(f"Player moved to {event.payload['location_id']}")

bus.subscribe(EventType.LOCATION_CHANGED, on_location_change)

# Publish events
bus.publish(GameEvent(
    type=EventType.LOCATION_CHANGED,
    payload={"location_id": "forest_001"},
    source="movement_tool",
    session_id="session_123"
))
```

#### 3. Tool Registry (`agents/tools/`)

Dynamic registration system for agent tools. Prevents merge conflicts by allowing teams to register tools independently.

**Features:**
- Protocol-based interface (`GameTool`)
- Category-based organization
- Thread-safe registration
- Type-checked tool discovery

Example:
```python
from agentic_rpg.agents.tools.registry import ToolRegistry, GameTool
from dataclasses import dataclass

@dataclass
class MyGameTool:
    name: str = "my_tool"
    description: str = "Does something useful"

    def execute(self, **kwargs) -> dict[str, object]:
        return {"success": True}

# Register tool
ToolRegistry.register(MyGameTool(), category="exploration")

# Discover tools
tool = ToolRegistry.get_tool("my_tool")
exploration_tools = ToolRegistry.get_tools_by_category("exploration")
```

#### 4. Configuration (`config.py`)

Environment-based configuration using pydantic-settings.

**Phase 0 Settings:**
- Application metadata (name, env, debug mode)
- API server configuration (host, port)
- CORS origins
- State storage (type, path)
- Development options (use_mocks)

Example:
```python
from agentic_rpg.config import get_settings

settings = get_settings()
print(f"Running in {settings.app_env} mode")
print(f"API will listen on {settings.api_host}:{settings.api_port}")
```

#### 5. State Management (`services/`)

**StateManager Protocol** defines the interface for state persistence.

**Phase 0 Implementation: MockStateManager**
- In-memory storage for testing
- CRUD operations (create, load, update, delete)
- Thread-safe with dictionary-based storage
- Auto-initializes game state with starting location

**Future:** Production StateManager with PostgreSQL/Redis will implement the same Protocol.

Example:
```python
from agentic_rpg.services.mock_state_manager import MockStateManager

manager = MockStateManager()

# Create session
state = manager.create_session("session_123")

# Update state
state.character.stats.health = 90
manager.update_session("session_123", state)

# Load state
loaded = manager.load_session("session_123")
```

## Development Workflow

### Test-Driven Development (TDD)

**CRITICAL:** Always write tests first. This is non-negotiable.

1. **Write failing test** describing expected behavior
2. **Run test** to confirm it fails (red)
3. **Write minimal code** to pass the test
4. **Run test** to confirm it passes (green)
5. **Refactor** while keeping tests green
6. **Repeat**

Example workflow:
```bash
# 1. Create test file
vim tests/unit/test_services/test_my_service.py

# 2. Run test (should fail)
poetry run pytest tests/unit/test_services/test_my_service.py -v

# 3. Implement the code
vim src/agentic_rpg/services/my_service.py

# 4. Run test again (should pass)
poetry run pytest tests/unit/test_services/test_my_service.py -v

# 5. Run full test suite
poetry run pytest

# 6. Check types and linting
poetry run mypy backend/src
poetry run ruff check backend/src
```

### Code Quality Standards

All code must pass:
- **pytest**: All tests passing (currently 159 tests)
- **mypy**: Zero type errors (strict mode)
- **ruff**: Zero linting errors (auto-fix with `ruff check --fix`)

```bash
# Run all quality checks
poetry run pytest
poetry run mypy backend/src
poetry run ruff check backend/src
```

### Adding New Models

1. Create model in `src/agentic_rpg/models/`
2. Write comprehensive tests in `tests/unit/test_models/`
3. Update `models/__init__.py` exports
4. Generate JSON schemas if needed
5. Document in docstrings

### Adding New Services

1. Define Protocol in `services/interfaces.py` if needed
2. Write tests first in `tests/unit/test_services/`
3. Implement service following TDD
4. Add singleton pattern if appropriate
5. Update this README

### Adding New Tools

1. Define tool class implementing `GameTool` Protocol
2. Write tests in `tests/unit/test_tools/`
3. Register tool in `ToolRegistry`
4. Document tool usage in docstring

## Testing

### Test Organization

Tests mirror the source structure:
```
tests/unit/
├── test_models/      # Data model tests
├── test_services/    # Service tests
└── test_tools/       # Tool tests
```

### Test Coverage

Current coverage: **95%+**

Key tested areas:
- All Pydantic models and validation
- Event bus pub/sub mechanics
- Tool registry registration and retrieval
- Mock state manager CRUD
- Configuration loading and validation
- Schema versioning system

### Running Specific Tests

```bash
# Test a specific module
poetry run pytest tests/unit/test_services/test_event_bus.py -v

# Test with pattern matching
poetry run pytest -k "test_event" -v

# Test with coverage report
poetry run pytest --cov=agentic_rpg --cov-report=html
```

## Configuration

### Environment Variables

Create `.env` file in backend directory:

```bash
# Application
APP_NAME="Agentic RPG"
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# State Storage
STATE_STORAGE_TYPE=json
STATE_STORAGE_PATH=./gamestate

# Development
USE_MOCKS=false
```

## Current Status

### Phase 3: Complete ✅

**Implemented:**
- ✅ Event Bus with 4 core event types
- ✅ Tool Registry with GameTool Protocol
- ✅ Mock State Manager for testing
- ✅ Configuration Service (minimal Phase 0)
- ✅ StateManager Protocol interface
- ✅ 73 tests passing (Event Bus: 22, Tool Registry: 16, Mock State Manager: 17, Config: 18)
- ✅ All mypy type errors fixed (0 errors)
- ✅ All ruff linting errors fixed (0 errors)
- ✅ Proper logging throughout
- ✅ Efficient data structures (deque for event history)

**Code Quality:**
- 159 total tests passing
- 0 mypy errors
- 0 ruff errors
- Modern Python 3.11+ type hints
- Comprehensive docstrings
- TDD workflow followed throughout

### Next Steps

**Phase 1: Core Vertical Slice**
- Implement JSON state manager (production-ready)
- Implement session manager
- Create character creation logic
- Add first LangGraph agents
- Build FastAPI endpoints
- Integrate frontend

## Contributing

### Interface Stability Rules

**CRITICAL:** Do not change public interfaces without permission.

**Breaking changes require approval:**
- Function signature changes (parameters, return types)
- Removing/renaming public methods
- Changing data model fields
- Modifying Protocol definitions
- Altering API endpoints

**Non-breaking changes (allowed):**
- Adding optional parameters with defaults
- Adding new methods
- Adding new fields with defaults
- Improving documentation
- Refactoring internals

### Git Workflow

1. Create feature branch: `feature/team-{feature-name}`
2. Follow TDD: tests first, then implementation
3. Run quality checks before committing
4. Create PR with clear description
5. Request review from module owner

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the poetry shell
poetry shell

# Or prefix commands with poetry run
poetry run pytest
```

**Type errors:**
```bash
# Run mypy to see all type issues
poetry run mypy backend/src

# Common fix: add type hints to function signatures
```

**Test failures:**
```bash
# Run with verbose output
poetry run pytest -vv

# Run single test for debugging
poetry run pytest tests/unit/test_models/test_character.py::test_character_creation -v
```

## Resources

- [PRD](../PRD.md) - Full product requirements document
- [CLAUDE.md](../CLAUDE.md) - AI agent development instructions
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## License

[Add license information]
