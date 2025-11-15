# Product Requirements Document: Agentic RPG

## 1. Overview

### 1.1. Project Vision
A browser-based, single-player role-playing game where narrative, world state, and character interactions are dynamically generated and managed by LLM agents using LangGraph. The system features a modular architecture with clear interfaces enabling parallel development across multiple teams.

### 1.2. Project Goals
- **Primary Goal:** Build a production-ready agentic RPG with persistent state and dynamic narrative generation
- **Architecture Goal:** Create a highly modular system with well-defined interfaces for independent component development
- **Scalability Goal:** Design for future expansion with additional agents, game systems, and features
- **Coordination Goal:** Enable 6+ developers to work in parallel with minimal merge conflicts

### 1.3. Target Audience
- **End Users:** Players seeking dynamic, AI-driven narrative experiences
- **Development Team:** Multiple developers working in parallel on different components

## 2. Core Principles

### 2.1. Architectural Principles
- **Interface-First Design:** All components communicate through well-defined API contracts validated by automated tests
- **Plugin Architecture:** Components register capabilities dynamically to prevent merge conflicts
- **Agent Autonomy:** LLM agents use tools to perceive and modify game state independently
- **State Determinism:** Core game state managed through deterministic functions with clear ownership
- **Component Isolation:** Each module can be developed, tested, and deployed independently
- **Event-Driven Updates:** Components communicate via event bus for loose coupling
- **Feature Flag Driven:** Incomplete features ship safely behind feature flags

### 2.2. Technical Principles
- **API-First:** Backend exposes RESTful/WebSocket APIs consumed by frontend
- **Type Safety Everywhere:** Strong typing across the stack with generated types from single source of truth
- **State as Source of Truth:** Single source of truth for game state with versioned schemas and migrations
- **Graph-Based Agent Orchestration:** LangGraph manages complex agent workflows and decision trees
- **Contract Testing:** Interface boundaries validated by executable tests
- **Observability First:** All critical paths instrumented for debugging and monitoring

## 3. Parallel Development Strategy

### 3.1. Team Structure (10 developers)

```yaml
teams:
  team_core:
    size: 2
    focus: [state_management, data_models, event_bus, configuration]
    critical_path: true
    
  team_agents:
    size: 3
    focus: [langgraph_orchestration, agent_logic, prompts]
    complexity: high
    
  team_tools:
    size: 2
    focus: [game_mechanics, tool_implementation, validation]
    
  team_api:
    size: 1
    focus: [fastapi, websockets, authentication, routing]
    
  team_frontend:
    size: 2
    focus: [ui_components, state_management, api_integration]

integration:
  leads: one_per_team
  sync_frequency: daily_15min_standup
  integration_windows: [10am, 3pm]  # UTC - merge windows twice daily
```

### 3.2. Module Ownership Map

```yaml
# .github/CODEOWNERS
/src/agentic_rpg/models/*              @team-core
/src/agentic_rpg/services/state*       @team-core
/src/agentic_rpg/services/event_bus*   @team-core

/src/agentic_rpg/agents/*              @team-agents
/src/agentic_rpg/agents/graph.py       @team-agents @team-core

/src/agentic_rpg/agents/tools/*        @team-tools
/src/agentic_rpg/agents/tools/base.py  @team-tools @team-agents

/src/agentic_rpg/api/*                 @team-api
/src/agentic_rpg/api/routes/*          @team-api

/frontend/src/components/*             @team-frontend
/frontend/src/lib/api/*                @team-frontend @team-api
/frontend/src/lib/types/*              @team-frontend @team-core

# Shared interfaces require multiple approvals
/src/agentic_rpg/interfaces.py         @team-core @team-agents @team-tools
/shared-types/*                        @team-core @team-frontend
```

### 3.3. Git Workflow

```markdown
## Branch Strategy
- `main`: Production-ready code (protected)
- `develop`: Integration branch (protected)
- `feature/{team}-{feature}`: Team feature branches
- `hotfix/*`: Emergency fixes

## Branch Protection Rules

### main
- Requires 2 approvals
- All CI checks must pass
- No direct pushes
- Squash merge only

### develop
- Requires 1 approval from module owner
- Integration tests must pass
- Contract tests must pass
- No force pushes

## Integration Strategy

### Daily Workflow
1. **Morning (10am UTC)**: First integration window
   - Teams merge completed features to develop
   - Integration tests run automatically
   - Breaking changes announced in #integration

2. **Throughout day**: 
   - Merge develop into feature branches (not rebase)
   - Continue feature work
   - Monitor integration test results

3. **Afternoon (3pm UTC)**: Second integration window
   - Teams merge day's work to develop
   - Full test suite runs overnight

### Conflict Resolution
- Module owners have final authority on their code
- Cross-module conflicts discussed in #integration channel
- Breaking changes require RFC (see section 18)

## Commit Standards
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`
- Include issue number: `feat(api): add websocket support #123`
- Keep commits atomic and buildable
```

## 4. System Architecture

### 4.1. High-Level Architecture

```
┌─────────────────────────────────────┐
│         Next.js Frontend            │
│  (TypeScript - Generated Types)     │
└────────────┬────────────────────────┘
             │ HTTP/WebSocket
             │ OpenAPI Contract
┌────────────▼────────────────────────┐
│         FastAPI API Layer           │
│    (Python - Source of Truth)       │
└────────────┬────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
┌─────▼──────┐  ┌──▼─────────┐
│   Agent    │  │   State    │
│  Engine    │  │   Store    │
│ (LangGraph)│  │  (JSON/PG) │
└─────┬──────┘  └──┬─────────┘
      │            │
      └─────┬──────┘
            │
      ┌─────▼──────┐
      │  Event Bus │
      │ (Pub/Sub)  │
      └────────────┘
```

### 4.2. Component Breakdown

#### 4.2.1. Frontend (Next.js)
- **Path:** `frontend/`
- **Owner:** @team-frontend
- **Responsibilities:**
  - Render chat interface and game UI
  - Manage local UI state (Zustand)
  - Communicate with backend via generated API client
  - Handle real-time updates via WebSocket
  - Consume generated TypeScript types from OpenAPI spec
- **Key Features:**
  - Server-side rendering for initial load
  - Real-time message streaming
  - Character sheet display
  - Inventory management UI
  - Optimistic updates with rollback

#### 4.2.2. API Layer (FastAPI)
- **Path:** `src/agentic_rpg/api/`
- **Owner:** @team-api
- **Responsibilities:**
  - Expose versioned REST endpoints
  - Manage WebSocket connections for real-time updates
  - Handle authentication and session management
  - Validate requests/responses with Pydantic
  - Route commands to appropriate services
  - Generate OpenAPI spec for type generation
- **Versioning Strategy:**
  ```python
  # Support multiple API versions
  app.include_router(v1_router, prefix="/api/v1")
  app.include_router(v2_router, prefix="/api/v2")
  app.include_router(v1_router, prefix="/api")  # default to stable
  ```

#### 4.2.3. Agent Engine (LangGraph)
- **Path:** `src/agentic_rpg/agents/`
- **Owner:** @team-agents
- **Responsibilities:**
  - Orchestrate LLM agents and decision trees
  - Execute tool calls to modify game state
  - Generate narrative responses
  - Handle multi-step reasoning and planning
  - Manage agent memory and context
- **Agent Types:**
  - **Game Master Agent:** Main narrative and world management
  - **Combat Agent:** Handle combat encounters and tactics
  - **NPC Agent:** Generate and manage NPC interactions
  - **World Agent:** Maintain world state and consistency

#### 4.2.4. Tool System
- **Path:** `src/agentic_rpg/agents/tools/`
- **Owner:** @team-tools
- **Responsibilities:**
  - Implement game mechanics as callable tools
  - Validate tool parameters
  - Execute deterministic state changes
  - Register tools dynamically in registry
  - Document tool usage for agents

#### 4.2.5. State Store
- **Path:** `src/agentic_rpg/services/state_manager.py`
- **Owner:** @team-core
- **Responsibilities:**
  - Store and retrieve game state
  - Enforce state schema validation
  - Provide transactional updates
  - Support state versioning and migrations
  - Handle concurrent access safely
- **Storage:**
  - Development: JSON files
  - Production: PostgreSQL + Redis cache

#### 4.2.6. Event Bus
- **Path:** `src/agentic_rpg/services/event_bus.py`
- **Owner:** @team-core
- **Responsibilities:**
  - Publish/subscribe event system
  - Validate event schemas
  - Route events to subscribers
  - Support event replay for debugging
  - Enable loose coupling between components

## 5. Core Architectural Patterns

### 5.1. Tool Registry Pattern

**Purpose:** Enable dynamic tool registration to prevent merge conflicts

```python
# src/agentic_rpg/agents/tools/registry.py
from typing import Protocol, Callable
from dataclasses import dataclass

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

class ToolRegistry:
    """Central registry for agent tools - prevents merge conflicts."""
    
    _tools: dict[str, GameTool] = {}
    _categories: dict[str, list[str]] = {}
    
    @classmethod
    def register(cls, tool: GameTool, category: str = "general") -> None:
        """Register a tool - can be called from anywhere.
        
        Teams register their tools independently:
        - Team Tools: game mechanics
        - Team Agents: agent-specific utilities
        - Team Combat: combat tools
        """
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

# Usage - each team registers their tools independently
# src/agentic_rpg/agents/tools/character.py
from .registry import ToolRegistry, GameTool

@dataclass
class UpdateHealthTool:
    name: str = "update_health"
    description: str = "Update character health"
    schema: dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {
            "amount": {"type": "integer"},
            "reason": {"type": "string"}
        },
        "required": ["amount"]
    })
    
    def execute(self, amount: int, reason: str = "") -> dict:
        # Implementation
        return {"success": True, "new_health": 90}
    
    def validate(self, amount: int, **kwargs) -> bool:
        return -100 <= amount <= 100

# Register at module initialization
ToolRegistry.register(UpdateHealthTool(), category="character")

# src/agentic_rpg/agents/tools/combat.py
ToolRegistry.register(DealDamageTool(), category="combat")
ToolRegistry.register(ApplyStatusEffectTool(), category="combat")

# Agents can discover and use tools dynamically
combat_tools = ToolRegistry.get_tools_by_category("combat")
```

### 5.2. Event Bus Pattern

**Purpose:** Enable loose coupling and independent component development

```python
# src/agentic_rpg/services/event_bus.py
from typing import Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class EventType(str, Enum):
    """Standard event types - teams can add more."""
    STATE_UPDATED = "state.updated"
    COMBAT_STARTED = "combat.started"
    COMBAT_ENDED = "combat.ended"
    ITEM_ACQUIRED = "inventory.item_acquired"
    LOCATION_CHANGED = "world.location_changed"
    NPC_SPAWNED = "npc.spawned"
    ACHIEVEMENT_EARNED = "achievement.earned"

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
        """Publish event to all subscribers.
        
        Validates event against schema if registered.
        Stores in history for debugging/replay.
        """
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
                # Log but don't fail - one bad subscriber shouldn't break others
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

# Usage across teams

# Team Core registers schemas
event_bus = EventBus()
event_bus.register_schema(EventSchema(
    type=EventType.STATE_UPDATED,
    required_fields={"path", "value"},
    optional_fields={"old_value"}
))

# Team Tools publishes events
event_bus.publish(GameEvent(
    type=EventType.ITEM_ACQUIRED,
    payload={"item_id": "sword_001", "quantity": 1},
    source="inventory_tool",
    session_id="session_123"
))

# Team Frontend subscribes to events
def on_state_update(event: GameEvent):
    # Update UI
    pass

event_bus.subscribe(EventType.STATE_UPDATED, on_state_update)

# Team Agents subscribes to trigger narratives
def on_location_change(event: GameEvent):
    # Generate location description
    pass

event_bus.subscribe(EventType.LOCATION_CHANGED, on_location_change)
```

### 5.3. Feature Flags Pattern

**Purpose:** Ship incomplete features safely and enable independent deployment

```python
# src/agentic_rpg/config.py
from pydantic_settings import BaseSettings
from enum import Enum

class FeatureFlag(str, Enum):
    """Feature flags for progressive feature rollout."""
    
    # Combat system
    COMBAT_SYSTEM = "combat_system"
    ADVANCED_TACTICS = "combat_advanced_tactics"
    
    # NPC system
    NPC_PERSONALITIES = "npc_personalities"
    NPC_MEMORY = "npc_memory"
    NPC_RELATIONSHIPS = "npc_relationships"
    
    # World features
    WORLD_PERSISTENCE = "world_persistence"
    DYNAMIC_EVENTS = "world_dynamic_events"
    WEATHER_SYSTEM = "world_weather"
    
    # Agent features
    MULTI_AGENT_COORDINATION = "agent_coordination"
    AGENT_PLANNING = "agent_planning"
    
    # API features
    WEBSOCKET_UPDATES = "websocket_updates"
    API_V2 = "api_v2"
    
    # Frontend features
    ADVANCED_UI = "frontend_advanced_ui"
    VOICE_INPUT = "frontend_voice"

class FeatureFlags(BaseSettings):
    """Feature flag configuration from environment."""
    
    # Combat
    combat_system: bool = False
    combat_advanced_tactics: bool = False
    
    # NPC
    npc_personalities: bool = False
    npc_memory: bool = False
    npc_relationships: bool = False
    
    # World
    world_persistence: bool = True
    world_dynamic_events: bool = False
    world_weather: bool = False
    
    # Agents
    agent_coordination: bool = False
    agent_planning: bool = False
    
    # API
    websocket_updates: bool = False
    api_v2: bool = False
    
    # Frontend
    frontend_advanced_ui: bool = False
    frontend_voice: bool = False
    
    class Config:
        env_prefix = "FEATURE_"
        env_file = ".env"
    
    def is_enabled(self, flag: FeatureFlag) -> bool:
        """Check if a feature flag is enabled."""
        return getattr(self, flag.value, False)

# Global instance
feature_flags = FeatureFlags()

# Usage in code
if feature_flags.is_enabled(FeatureFlag.COMBAT_SYSTEM):
    # Use new combat system
    result = advanced_combat_handler.process(action)
else:
    # Use basic combat
    result = basic_combat_handler.process(action)

# Conditional route registration
if feature_flags.is_enabled(FeatureFlag.API_V2):
    app.include_router(v2_router, prefix="/api/v2")

# Agent tool registration based on flags
if feature_flags.is_enabled(FeatureFlag.COMBAT_ADVANCED_TACTICS):
    ToolRegistry.register(AdvancedTacticsTool(), category="combat")
```

### 5.4. Dependency Injection Pattern

**Purpose:** Enable testing with mocks and flexible service swapping

```python
# src/agentic_rpg/services/interfaces.py
from typing import Protocol
from models.game_state import GameState, Character

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

class AgentService(Protocol):
    """Interface for agent execution."""
    
    def process_message(
        self, 
        session_id: str, 
        message: str,
        context: GameState
    ) -> "AgentResponse":
        """Process user message through agent."""
        ...

# src/agentic_rpg/services/factory.py
from config import Settings
from .json_state_manager import JSONStateManager
from .postgres_state_manager import PostgresStateManager
from .mock_state_manager import MockStateManager

class ServiceFactory:
    """Factory for creating service instances."""
    
    @staticmethod
    def create_state_manager(settings: Settings) -> StateManager:
        """Create appropriate state manager based on config."""
        if settings.use_mocks:
            return MockStateManager()
        elif settings.state_storage_type == "json":
            return JSONStateManager(settings.state_storage_path)
        elif settings.state_storage_type == "postgres":
            return PostgresStateManager(settings.database_url)
        else:
            raise ValueError(f"Unknown storage type: {settings.state_storage_type}")

# src/agentic_rpg/api/dependencies.py
from fastapi import Depends
from config import get_settings, Settings
from services.factory import ServiceFactory
from services.interfaces import StateManager, AgentService

def get_state_manager(settings: Settings = Depends(get_settings)) -> StateManager:
    """FastAPI dependency for state manager."""
    return ServiceFactory.create_state_manager(settings)

def get_agent_service(settings: Settings = Depends(get_settings)) -> AgentService:
    """FastAPI dependency for agent service."""
    return ServiceFactory.create_agent_service(settings)

# Usage in routes
@router.post("/game/message")
async def send_message(
    request: MessageRequest,
    state_manager: StateManager = Depends(get_state_manager),
    agent_service: AgentService = Depends(get_agent_service)
):
    state = state_manager.load_state(request.session_id)
    response = agent_service.process_message(
        request.session_id,
        request.message,
        state
    )
    return response
```

## 6. Type Safety and Contract Generation

### 6.1. Single Source of Truth Strategy

**Approach:** Python Pydantic models → OpenAPI spec → TypeScript types

```python
# src/agentic_rpg/models/game_state.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional

class Character(BaseModel):
    """Character model - source of truth for all layers."""
    
    id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., min_length=1, max_length=50)
    profession: str = Field(..., description="Character's profession")
    stats: "CharacterStats"
    location: str = Field(..., description="Current location ID")
    status: List[str] = Field(default_factory=list)
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "id": "char_123",
                "name": "Jax",
                "profession": "Space Pirate",
                "stats": {
                    "health": 100,
                    "maxHealth": 100,
                    "energy": 50,
                    "maxEnergy": 50,
                    "money": 1000
                },
                "location": "cantina_001",
                "status": ["well_rested"]
            }]
        }
    }

class CharacterStats(BaseModel):
    health: int = Field(..., ge=0, description="Current health points")
    max_health: int = Field(..., ge=1)
    energy: int = Field(..., ge=0)
    max_energy: int = Field(..., ge=1)
    money: int = Field(default=0, ge=0)

class GameState(BaseModel):
    """Complete game state - versioned and validated."""
    
    schema_version: str = Field(default="1.0.0", alias="version")
    session_id: str
    created_at: datetime
    updated_at: datetime
    character: Character
    inventory: "Inventory"
    world: "WorldState"
    conversation: "Conversation"

# Export JSON Schema for frontend
def generate_schemas():
    """Generate JSON schemas for frontend type generation."""
    schemas = {
        "GameState": GameState.model_json_schema(),
        "Character": Character.model_json_schema(),
        "Inventory": Inventory.model_json_schema(),
        # ... more models
    }
    
    with open("shared-types/schemas.json", "w") as f:
        json.dump(schemas, f, indent=2)
```

### 6.2. Type Generation Workflow

```bash
# scripts/generate-types.sh
#!/bin/bash

# Step 1: Start FastAPI app to generate OpenAPI spec
poetry run python -m agentic_rpg.api.main &
API_PID=$!
sleep 2

# Step 2: Download OpenAPI spec
curl http://localhost:8000/openapi.json > shared-types/openapi.json

# Step 3: Generate TypeScript types
cd frontend
npx openapi-typescript ../shared-types/openapi.json -o src/lib/types/api.ts

# Step 4: Generate client SDK
npx openapi-typescript-codegen \
  --input ../shared-types/openapi.json \
  --output src/lib/api/generated \
  --client fetch

# Step 5: Stop API
kill $API_PID

echo "✅ Types generated successfully"
```

```typescript
// frontend/src/lib/types/api.ts (auto-generated)
export interface Character {
  id: string;
  name: string;
  profession: string;
  stats: CharacterStats;
  location: string;
  status: string[];
}

export interface GameState {
  version: string;
  sessionId: string;
  createdAt: string;
  updatedAt: string;
  character: Character;
  inventory: Inventory;
  world: WorldState;
  conversation: Conversation;
}

// frontend/src/lib/api/client.ts (manually maintained)
import type { GameState, Character } from './types/api';
import { GameAPIClient as GeneratedClient } from './generated';

export class GameAPIClient extends GeneratedClient {
  // Add custom methods or overrides here
  async getGameStateWithCache(sessionId: string): Promise<GameState> {
    // Custom caching logic
  }
}
```

## 7. Data Models

### 7.1. Versioned State Schema

```python
# src/agentic_rpg/models/versioning.py
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
        # Build migration path
        path = cls._build_migration_path(from_version, to_version)
        
        # Apply migrations in sequence
        for (from_v, to_v) in path:
            if (from_v, to_v) in cls._migrations:
                state = cls._migrations[(from_v, to_v)](state)
                state["schema_version"] = to_v
        
        return state
    
    @classmethod
    def _build_migration_path(
        cls, 
        from_version: str, 
        to_version: str
    ) -> list[tuple[str, str]]:
        """Build shortest migration path between versions."""
        # Simple linear path for now
        versions = ["1.0.0", "1.1.0", "1.2.0"]  # Extend as needed
        
        if from_version not in versions or to_version not in versions:
            raise ValueError(f"Unknown version: {from_version} or {to_version}")
        
        from_idx = versions.index(from_version)
        to_idx = versions.index(to_version)
        
        if from_idx >= to_idx:
            return []
        
        path = []
        for i in range(from_idx, to_idx):
            path.append((versions[i], versions[i + 1]))
        
        return path

# Define migrations
@SchemaVersion.register_migration("1.0.0", "1.1.0")
def add_character_backstory(state: dict) -> dict:
    """Add backstory field to character."""
    if "character" in state and "backstory" not in state["character"]:
        state["character"]["backstory"] = ""
    return state

@SchemaVersion.register_migration("1.1.0", "1.2.0")
def add_reputation_system(state: dict) -> dict:
    """Add reputation tracking to world state."""
    if "world" in state and "reputation" not in state["world"]:
        state["world"]["reputation"] = {
            "factions": {},
            "characters": {}
        }
    return state

# Usage in state loading
class VersionedGameState(BaseModel):
    """Game state with automatic migration support."""
    
    schema_version: str = Field(default=SchemaVersion.CURRENT)
    # ... other fields
    
    @classmethod
    def from_any_version(cls, data: dict) -> "VersionedGameState":
        """Load state from any version, migrating if needed."""
        version = data.get("schema_version", "1.0.0")
        
        if version != SchemaVersion.CURRENT:
            data = SchemaVersion.migrate(
                data,
                from_version=version,
                to_version=SchemaVersion.CURRENT
            )
        
        return cls(**data)
```

### 7.2. Core Models

```python
# src/agentic_rpg/models/__init__.py
from .game_state import (
    GameState,
    Character,
    CharacterStats,
    Inventory,
    InventoryItem,
    WorldState,
    Location,
    Conversation,
    Message
)
from .events import GameEvent, EventType
from .responses import (
    GameResponse,
    AgentResponse,
    ToolResult
)

__all__ = [
    "GameState",
    "Character",
    "CharacterStats",
    "Inventory",
    "InventoryItem",
    "WorldState",
    "Location",
    "Conversation",
    "Message",
    "GameEvent",
    "EventType",
    "GameResponse",
    "AgentResponse",
    "ToolResult",
]

# src/agentic_rpg/models/inventory.py
from pydantic import BaseModel, Field
from typing import Dict, Any

class InventoryItem(BaseModel):
    id: str = Field(..., description="Unique item identifier")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    quantity: int = Field(default=1, ge=1)
    weight: float = Field(default=1.0, ge=0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    
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
    items: list[InventoryItem] = Field(default_factory=list)
    capacity: int = Field(default=20, ge=1)
    max_weight: float = Field(default=100.0, ge=0)
    
    @property
    def current_weight(self) -> float:
        return sum(item.weight * item.quantity for item in self.items)
    
    @property
    def is_full(self) -> bool:
        return len(self.items) >= self.capacity
    
    def can_add(self, item: InventoryItem) -> tuple[bool, str]:
        """Check if item can be added to inventory."""
        if self.is_full:
            return False, "Inventory is full"
        
        new_weight = self.current_weight + (item.weight * item.quantity)
        if new_weight > self.max_weight:
            return False, f"Too heavy (would be {new_weight}/{self.max_weight})"
        
        return True, ""

# src/agentic_rpg/models/world.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NPC(BaseModel):
    id: str
    name: str
    description: str
    personality: str = Field(default="neutral")
    dialogue_state: Dict[str, Any] = Field(default_factory=dict)

class Location(BaseModel):
    id: str = Field(..., description="Unique location identifier")
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    type: str = Field(..., description="Location type: city, wilderness, dungeon, etc.")
    connections: List[str] = Field(default_factory=list, description="Connected location IDs")
    npcs: List[NPC] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)

class GameEvent(BaseModel):
    id: str
    type: str
    description: str
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool = True
    effects: Dict[str, Any] = Field(default_factory=dict)

class WorldState(BaseModel):
    current_location: Location
    available_locations: List[Location] = Field(default_factory=list)
    time_of_day: str = Field(default="day")
    weather: str = Field(default="clear")
    active_events: List[GameEvent] = Field(default_factory=list)
    discovered_locations: List[str] = Field(default_factory=list)

# src/agentic_rpg/models/conversation.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Dict, Any, Optional

class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
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
    messages: List[Message] = Field(default_factory=list)
    context: List[str] = Field(
        default_factory=list,
        description="Important context from previous messages"
    )
    max_history: int = Field(default=100)
    
    def add_message(self, message: Message) -> None:
        """Add message and maintain history limit."""
        self.messages.append(message)
        if len(self.messages) > self.max_history:
            self.messages.pop(0)
```

## 8. API Specifications

### 8.1. REST API Endpoints

```python
# src/agentic_rpg/api/routes/game.py
from fastapi import APIRouter, Depends, HTTPException, status
from models.game_state import GameState, Character
from models.responses import GameResponse, CreateGameResponse
from api.dependencies import get_state_manager, get_agent_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/game", tags=["game"])

class CreateGameRequest(BaseModel):
    character_name: str = Field(..., min_length=1, max_length=50)
    profession: str = Field(..., min_length=1, max_length=50)

class MessageRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1, max_length=500)

@router.post("/new", response_model=CreateGameResponse)
async def create_game(
    request: CreateGameRequest,
    state_manager: StateManager = Depends(get_state_manager),
    event_bus: EventBus = Depends(get_event_bus)
) -> CreateGameResponse:
    """Create a new game session.
    
    Creates a new character and initializes game state.
    Returns session ID for future requests.
    """
    character = Character(
        id=f"char_{uuid.uuid4().hex[:8]}",
        name=request.character_name,
        profession=request.profession,
        stats=CharacterStats(
            health=100,
            max_health=100,
            energy=50,
            max_energy=50,
            money=1000
        ),
        location="starting_location",
        status=[]
    )
    
    session_id = state_manager.create_session(character)
    state = state_manager.load_state(session_id)
    
    # Publish event
    event_bus.publish(GameEvent(
        type=EventType.GAME_CREATED,
        payload={"session_id": session_id},
        source="api.game.create"
    ))
    
    return CreateGameResponse(
        session_id=session_id,
        state=state
    )

@router.get("/state/{session_id}", response_model=GameState)
async def get_game_state(
    session_id: str,
    state_manager: StateManager = Depends(get_state_manager)
) -> GameState:
    """Get current game state.
    
    Returns complete game state including character, inventory,
    world state, and conversation history.
    """
    try:
        return state_manager.load_state(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

@router.post("/message", response_model=GameResponse)
async def send_message(
    request: MessageRequest,
    state_manager: StateManager = Depends(get_state_manager),
    agent_service: AgentService = Depends(get_agent_service)
) -> GameResponse:
    """Send a message to the game.
    
    Processes user input through the agent system and returns
    narrative response with any state updates.
    """
    # Load current state
    state = state_manager.load_state(request.session_id)
    
    # Process through agent
    response = await agent_service.process_message(
        request.session_id,
        request.message,
        state
    )
    
    return GameResponse(
        response=response.narrative,
        state_updates=response.state_updates,
        tool_calls=response.tool_calls
    )

@router.get("/history/{session_id}")
async def get_conversation_history(
    session_id: str,
    limit: int = 50,
    state_manager: StateManager = Depends(get_state_manager)
):
    """Get conversation history for a session."""
    state = state_manager.load_state(session_id)
    messages = state.conversation.messages[-limit:]
    return {"messages": messages}

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_game(
    session_id: str,
    state_manager: StateManager = Depends(get_state_manager)
):
    """Delete a game session."""
    success = state_manager.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )

# src/agentic_rpg/api/routes/character.py
router = APIRouter(prefix="/api/v1/character", tags=["character"])

@router.patch("/{session_id}", response_model=Character)
async def update_character(
    session_id: str,
    updates: Dict[str, Any],
    state_manager: StateManager = Depends(get_state_manager)
):
    """Update character properties."""
    # Implementation
    pass

@router.get("/stats/{session_id}")
async def get_character_stats(session_id: str):
    """Get character stats."""
    # Implementation
    pass

# src/agentic_rpg/api/routes/inventory.py
router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

@router.post("/add")
async def add_item(
    session_id: str,
    item: InventoryItem,
    state_manager: StateManager = Depends(get_state_manager)
):
    """Add item to inventory."""
    # Implementation
    pass

@router.delete("/remove/{session_id}/{item_id}")
async def remove_item(session_id: str, item_id: str, quantity: int = 1):
    """Remove item from inventory."""
    # Implementation
    pass

# src/agentic_rpg/api/routes/world.py
router = APIRouter(prefix="/api/v1/world", tags=["world"])

@router.get("/location/{session_id}", response_model=Location)
async def get_current_location(session_id: str):
    """Get current location details."""
    # Implementation
    pass

@router.post("/travel")
async def travel_to_location(
    session_id: str,
    destination_id: str
):
    """Travel to a new location."""
    # Implementation
    pass
```

### 8.2. WebSocket Events

```python
# src/agentic_rpg/api/websocket.py
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json

class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send message to all connections for a session."""
        if session_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected clients
            for connection in disconnected:
                self.disconnect(connection, session_id)

manager = ConnectionManager()

@router.websocket("/ws/game/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    event_bus: EventBus = Depends(get_event_bus)
):
    """WebSocket endpoint for real-time game updates."""
    await manager.connect(websocket, session_id)
    
    # Subscribe to events for this session
    def on_event(event: GameEvent):
        if event.session_id == session_id:
            asyncio.create_task(manager.send_to_session(
                session_id,
                {
                    "type": "event",
                    "payload": event.to_dict()
                }
            ))
    
    # Subscribe to relevant events
    event_bus.subscribe(EventType.STATE_UPDATED, on_event)
    event_bus.subscribe(EventType.ITEM_ACQUIRED, on_event)
    event_bus.subscribe(EventType.LOCATION_CHANGED, on_event)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Handle client messages
            if data["type"] == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
        # Unsubscribe from events
        event_bus.unsubscribe(EventType.STATE_UPDATED, on_event)
        event_bus.unsubscribe(EventType.ITEM_ACQUIRED, on_event)
        event_bus.unsubscribe(EventType.LOCATION_CHANGED, on_event)
```

### 8.3. Health and Monitoring Endpoints

```python
# src/agentic_rpg/api/routes/health.py
from fastapi import APIRouter, Depends
from datetime import datetime

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/integrations")
async def check_integrations(
    state_manager: StateManager = Depends(get_state_manager),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Check health of all integration points."""
    results = {
        "state_manager": "unknown",
        "agent_engine": "unknown",
        "event_bus": "unknown",
        "websocket": "unknown"
    }
    
    # Check state manager
    try:
        # Try a simple operation
        test_session = "health_check_test"
        results["state_manager"] = "healthy"
    except Exception as e:
        results["state_manager"] = f"unhealthy: {str(e)}"
    
    # Check agent engine
    try:
        # Verify agent is responsive
        results["agent_engine"] = "healthy"
    except Exception as e:
        results["agent_engine"] = f"unhealthy: {str(e)}"
    
    # Check event bus
    try:
        event_bus = get_event_bus()
        results["event_bus"] = "healthy"
    except Exception as e:
        results["event_bus"] = f"unhealthy: {str(e)}"
    
    # Check WebSocket manager
    try:
        results["websocket"] = "healthy"
    except Exception as e:
        results["websocket"] = f"unhealthy: {str(e)}"
    
    # Overall status
    all_healthy = all(v == "healthy" for v in results.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": results,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe."""
    # Check if app is ready to receive traffic
    return {"ready": True}

@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe."""
    # Check if app is alive
    return {"alive": True}
```

## 9. Contract Testing Strategy

### 9.1. Contract Test Framework

```python
# tests/contracts/base.py
import pytest
from abc import ABC, abstractmethod
from typing import Protocol

class ContractTest(ABC):
    """Base class for contract tests.
    
    Contract tests validate that implementations meet interface requirements.
    They ensure teams can work independently without breaking integrations.
    """
    
    @abstractmethod
    def get_implementation(self):
        """Return the implementation to test."""
        pass
    
    @pytest.fixture
    def implementation(self):
        """Fixture providing implementation."""
        return self.get_implementation()

# tests/contracts/test_state_manager_contract.py
@pytest.mark.contract
class TestStateManagerContract(ContractTest):
    """Contract tests for StateManager interface.
    
    ALL implementations of StateManager must pass these tests.
    Teams can develop different implementations (JSON, Postgres, Mock)
    independently as long as they satisfy this contract.
    """
    
    def get_implementation(self):
        # Default to JSON implementation for contract tests
        from services.json_state_manager import JSONStateManager
        return JSONStateManager(path=tmpdir)
    
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
    
    def test_update_state_persists_changes(self, implementation, mock_character):
        """Contract: update_state must persist changes."""
        session_id = implementation.create_session(mock_character)
        
        updates = {
            "character": {
                "stats": {
                    "health": 50
                }
            }
        }
        
        updated_state = implementation.update_state(session_id, updates)
        assert updated_state.character.stats.health == 50
        
        # Verify persistence
        loaded_state = implementation.load_state(session_id)
        assert loaded_state.character.stats.health == 50
    
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

# tests/contracts/test_agent_service_contract.py
@pytest.mark.contract
class TestAgentServiceContract(ContractTest):
    """Contract tests for AgentService interface."""
    
    def get_implementation(self):
        from agents.service import LangGraphAgentService
        return LangGraphAgentService()
    
    def test_process_message_returns_response(
        self,
        implementation,
        mock_game_state
    ):
        """Contract: process_message must return AgentResponse."""
        response = implementation.process_message(
            session_id="test_session",
            message="Hello",
            context=mock_game_state
        )
        
        assert isinstance(response, AgentResponse)
        assert isinstance(response.narrative, str)
        assert len(response.narrative) > 0
        assert isinstance(response.tool_calls, list)

# tests/contracts/test_game_tool_contract.py
@pytest.mark.contract  
class TestGameToolContract(ContractTest):
    """Contract tests for GameTool interface."""
    
    def test_tool_has_required_attributes(self, implementation):
        """Contract: tools must have name, description, schema."""
        assert hasattr(implementation, 'name')
        assert hasattr(implementation, 'description')
        assert hasattr(implementation, 'schema')
        assert isinstance(implementation.name, str)
        assert isinstance(implementation.description, str)
        assert isinstance(implementation.schema, dict)
    
    def test_execute_returns_dict(self, implementation):
        """Contract: execute must return dict."""
        # This test needs to be customized per tool
        # but validates the return type contract
        result = implementation.execute()
        assert isinstance(result, dict)
```

### 9.2. API Contract Tests

```python
# tests/contracts/test_api_contracts.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

@pytest.mark.contract
class TestGameAPIContract:
    """Contract tests ensuring API meets frontend expectations."""
    
    def test_create_game_response_structure(self):
        """Contract: POST /api/v1/game/new returns expected structure."""
        response = client.post(
            "/api/v1/game/new",
            json={
                "character_name": "Test Character",
                "profession": "Tester"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "session_id" in data
        assert "state" in data
        assert isinstance(data["session_id"], str)
        assert isinstance(data["state"], dict)
        
        # Verify state structure
        state = data["state"]
        required_fields = ["version", "sessionId", "character", "inventory", "world"]
        for field in required_fields:
            assert field in state, f"Missing required field: {field}"
    
    def test_get_state_response_structure(self):
        """Contract: GET /api/v1/game/state/{id} returns GameState."""
        # Create a game first
        create_response = client.post(
            "/api/v1/game/new",
            json={"character_name": "Test", "profession": "Tester"}
        )
        session_id = create_response.json()["session_id"]
        
        # Get state
        response = client.get(f"/api/v1/game/state/{session_id}")
        
        assert response.status_code == 200
        state = response.json()
        
        # Frontend expects these exact fields
        assert "version" in state
        assert "sessionId" in state
        assert "character" in state
        assert "inventory" in state
        assert "world" in state
        assert "conversation" in state
    
    def test_send_message_response_structure(self):
        """Contract: POST /api/v1/game/message returns GameResponse."""
        # Create game
        create_response = client.post(
            "/api/v1/game/new",
            json={"character_name": "Test", "profession": "Tester"}
        )
        session_id = create_response.json()["session_id"]
        
        # Send message
        response = client.post(
            "/api/v1/game/message",
            json={
                "session_id": session_id,
                "message": "I explore the area"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Frontend expects these fields
        assert "response" in data
        assert "stateUpdates" in data
        assert isinstance(data["response"], str)
        assert isinstance(data["stateUpdates"], dict)

@pytest.mark.contract
class TestOpenAPIContract:
    """Ensure OpenAPI spec doesn't break frontend types."""
    
    def test_openapi_spec_valid(self):
        """Contract: OpenAPI spec must be valid JSON."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        spec = response.json()
        assert "openapi" in spec
        assert "paths" in spec
        assert "components" in spec
    
    def test_game_state_schema_present(self):
        """Contract: GameState schema must be in OpenAPI spec."""
        response = client.get("/openapi.json")
        spec = response.json()
        
        schemas = spec["components"]["schemas"]
        assert "GameState" in schemas
        
        game_state = schemas["GameState"]
        required_fields = ["version", "sessionId", "character", "inventory", "world"]
        
        properties = game_state["properties"]
        for field in required_fields:
            assert field in properties
```

## 10. Testing Strategy

### 10.1. Test Organization

```python
# tests/conftest.py
"""Shared fixtures and configuration."""

import pytest
import tempfile
from pathlib import Path
from models.game_state import Character, CharacterStats, GameState, Inventory, WorldState, Location, Conversation
from services.event_bus import EventBus

@pytest.fixture
def temp_dir() -> Path:
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

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
def mock_game_state(mock_character) -> GameState:
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
                type="test"
            ),
            available_locations=[],
            time_of_day="day",
            weather="clear",
            active_events=[]
        ),
        conversation=Conversation()
    )

@pytest.fixture
def event_bus() -> EventBus:
    """Create fresh event bus for each test."""
    return EventBus()

@pytest.fixture
def mock_config(monkeypatch):
    """Mock configuration for tests."""
    from agentic_rpg import config as config_module
    
    monkeypatch.setattr(config_module.Settings, "use_mocks", True)
    monkeypatch.setattr(config_module.Settings, "state_storage_type", "json")
    monkeypatch.setattr(config_module.Settings, "log_level", "DEBUG")

# Markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "contract: Contract tests for interface validation"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests requiring multiple components"
    )
    config.addinivalue_line(
        "markers", "slow: Slow-running tests (LLM calls, etc.)"
    )
    config.addinivalue_line(
        "markers", "requires_llm: Tests that require LLM API access"
    )
```

### 10.2. Test Structure

```
tests/
├── unit/                           # Fast, isolated tests
│   ├── test_models/
│   │   ├── test_character.py
│   │   ├── test_inventory.py
│   │   └── test_versioning.py
│   ├── test_tools/
│   │   ├── test_character_tools.py
│   │   ├── test_inventory_tools.py
│   │   └── test_registry.py
│   ├── test_services/
│   │   ├── test_state_manager.py
│   │   └── test_event_bus.py
│   └── test_utils/
├── integration/                    # Multi-component tests
│   ├── test_api/
│   │   ├── test_game_endpoints.py
│   │   ├── test_websocket.py
│   │   └── test_health.py
│   ├── test_agents/
│   │   ├── test_agent_tool_execution.py
│   │   └── test_agent_workflows.py
│   └── test_state/
│       └── test_state_persistence.py
├── contracts/                      # Interface validation tests
│   ├── test_state_manager_contract.py
│   ├── test_agent_service_contract.py
│   ├── test_game_tool_contract.py
│   └── test_api_contracts.py
├── e2e/                           # End-to-end user flows
│   └── test_gameplay/
│       ├── test_character_creation.py
│       ├── test_combat_flow.py
│       └── test_exploration.py
└── conftest.py
```

### 10.3. Test Commands (Poe Tasks)

```toml
# pyproject.toml
[tool.poe.tasks]
# Testing
test = {cmd = "pytest tests/ -v --cov=src/agentic_rpg --cov-report=term-missing", help = "Run all tests with coverage"}
test-unit = {cmd = "pytest tests/unit/ -v", help = "Run unit tests only"}
test-integration = {cmd = "pytest tests/integration/ -v", help = "Run integration tests"}
test-contracts = {cmd = "pytest tests/contracts/ -v -m contract", help = "Run contract tests"}
test-e2e = {cmd = "pytest tests/e2e/ -v", help = "Run end-to-end tests"}
test-fast = {cmd = "pytest tests/ -v -m 'not slow'", help = "Run fast tests only"}
test-watch = {cmd = "pytest tests/ -v --lf --ff", help = "Run only failed tests (last-failed, failed-first)"}

# Code quality
lint = {cmd = "ruff check src tests", help = "Run linter"}
format = {cmd = "ruff format src tests", help = "Format code"}
format-check = {cmd = "ruff format --check src tests", help = "Check formatting"}
typecheck = {cmd = "mypy src", help = "Run type checking"}

# Combined checks
check-all = ["format-check", "lint", "typecheck", "test-contracts", "test-unit"]
check-integrations = ["test-contracts", "test-integration", "health-check"]

# Generate types
generate-types = {shell = "bash scripts/generate-types.sh", help = "Generate TypeScript types from OpenAPI"}
generate-schemas = {cmd = "python scripts/generate_schemas.py", help = "Generate JSON schemas"}

# Development
dev = {cmd = "uvicorn agentic_rpg.api.main:app --reload", help = "Start dev server"}
health-check = {cmd = "python scripts/health_check.py", help = "Check integration health"}
```

## 11. Configuration Management

### 11.1. Backend Configuration

```python
# src/agentic_rpg/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List
import os

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
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # LLM Configuration
    llm_provider: str = "anthropic"
    llm_model: str = "claude-3-5-sonnet-20241022"
    llm_api_key: str = ""
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000
    llm_timeout: int = 30
    
    # State Storage
    state_storage_type: str = "json"  # json | postgres | redis
    state_storage_path: Path = Path("./gamestate")
    database_url: str = ""  # For postgres
    redis_url: str = ""  # For redis
    
    # Session Configuration
    session_timeout: int = 3600  # seconds
    max_message_history: int = 100
    max_sessions_per_user: int = 10
    
    # Feature Flags (from FeatureFlags class)
    feature_combat_system: bool = False
    feature_npc_personalities: bool = False
    feature_world_persistence: bool = True
    feature_websocket_updates: bool = False
    feature_api_v2: bool = False
    
    # Development Options
    use_mocks: bool = False
    enable_debug_endpoints: bool = False
    
    # Observability
    enable_tracing: bool = True
    enable_metrics: bool = True
    trace_agent_reasoning: bool = True
    metrics_port: int = 9090
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    def validate_config(self) -> None:
        """Validate configuration at startup."""
        # Create storage paths
        if self.state_storage_type == "json":
            self.state_storage_path.mkdir(parents=True, exist_ok=True)
        
        # Validate LLM config
        if not self.use_mocks and not self.llm_api_key:
            raise ValueError("LLM_API_KEY must be set when not using mocks")
        
        # Validate database config
        if self.state_storage_type == "postgres" and not self.database_url:
            raise ValueError("DATABASE_URL required for postgres storage")

# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.validate_config()
    return _settings
```

### 11.2. Environment Configuration

```bash
# .env.example
# Copy to .env and fill in values

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
# DATABASE_URL=postgresql://user:password@localhost:5432/agentic_rpg
# REDIS_URL=redis://localhost:6379/0

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

### 11.3. Frontend Configuration

```typescript
// frontend/src/lib/config.ts
const config = {
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
    timeout: 30000,
    version: 'v1',
  },
  game: {
    maxMessageLength: 500,
    autosaveInterval: 60000, // 1 minute
    maxHistoryMessages: 100,
  },
  ui: {
    enableAnimations: true,
    theme: 'dark',
    debugMode: process.env.NODE_ENV === 'development',
  },
  features: {
    enableVoiceInput: false,
    enableAdvancedUI: false,
  },
} as const;

export default config;

// frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 12. Module Structure

### 12.1. Backend Structure

```
backend/
├── src/
│   └── agentic_rpg/
│       ├── __init__.py
│       │
│       ├── api/                    # @team-api
│       │   ├── __init__.py
│       │   ├── main.py            # FastAPI app entry point
│       │   ├── dependencies.py    # Shared dependencies
│       │   ├── websocket.py       # WebSocket manager
│       │   ├── middleware.py      # Custom middleware
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── game.py        # Game endpoints
│       │       ├── character.py   # Character endpoints
│       │       ├── inventory.py   # Inventory endpoints
│       │       ├── world.py       # World endpoints
│       │       └── health.py      # Health/monitoring
│       │
│       ├── agents/                 # @team-agents
│       │   ├── __init__.py
│       │   ├── graph.py           # LangGraph definitions
│       │   ├── service.py         # AgentService implementation
│       │   ├── game_master.py     # GM agent logic
│       │   ├── combat.py          # Combat agent
│       │   ├── npc.py             # NPC agent
│       │   ├── prompts/           # Agent prompts
│       │   │   ├── game_master.txt
│       │   │   ├── combat.txt
│       │   │   └── npc.txt
│       │   └── tools/             # @team-tools
│       │       ├── __init__.py
│       │       ├── base.py        # Tool interfaces
│       │       ├── registry.py    # Tool registry
│       │       ├── character.py   # Character tools
│       │       ├── inventory.py   # Inventory tools
│       │       ├── world.py       # World tools
│       │       └── combat.py      # Combat tools
│       │
│       ├── models/                 # @team-core
│       │   ├── __init__.py
│       │   ├── game_state.py      # Core state models
│       │   ├── character.py       # Character models
│       │   ├── inventory.py       # Inventory models
│       │   ├── world.py           # World models
│       │   ├── conversation.py    # Conversation models
│       │   ├── events.py          # Event models
│       │   ├── responses.py       # API response models
│       │   └── versioning.py      # Schema versioning
│       │
│       ├── services/               # @team-core
│       │   ├── __init__.py
│       │   ├── interfaces.py      # Service interfaces
│       │   ├── factory.py         # Service factory
│       │   ├── state_manager.py   # State management
│       │   ├── json_state_manager.py
│       │   ├── postgres_state_manager.py
│       │   ├── mock_state_manager.py
│       │   ├── session_manager.py # Session management
│       │   ├── event_bus.py       # Event system
│       │   └── cache.py           # Caching layer
│       │
│       ├── config.py               # Configuration
│       │
│       └── utils/
│           ├── __init__.py
│           ├── validators.py      # Validation utilities
│           ├── serializers.py     # Serialization
│           └── logging.py         # Logging setup
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models/
│   │   ├── test_tools/
│   │   ├── test_services/
│   │   └── test_utils/
│   ├── integration/
│   │   ├── test_api/
│   │   ├── test_agents/
│   │   └── test_state/
│   ├── contracts/
│   │   ├── test_state_manager_contract.py
│   │   ├── test_agent_service_contract.py
│   │   └── test_api_contracts.py
│   └── e2e/
│       └── test_gameplay/
│
├── scripts/
│   ├── generate_types.sh          # Type generation
│   ├── generate_schemas.py        # Schema export
│   ├── health_check.py            # Health check script
│   └── seed_data.py               # Test data generation
│
├── gamestate/                      # State storage (gitignored)
│   └── sessions/
│
├── shared-types/                   # Shared type definitions
│   ├── openapi.json               # Generated OpenAPI spec
│   └── schemas.json               # JSON schemas
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md                     # Auto-generated
│   ├── AGENTS.md
│   └── ADR/                       # Architectural Decision Records
│       ├── 001-use-langgraph.md
│       ├── 002-tool-registry-pattern.md
│       └── 003-event-bus-design.md
│
├── .github/
│   ├── CODEOWNERS
│   └── workflows/
│       ├── test.yml
│       ├── integration.yml
│       └── deploy.yml
│
├── pyproject.toml
├── poetry.lock
├── .env.example
├── .gitignore
├── README.md
└── Dockerfile
```

### 12.2. Frontend Structure

```
frontend/
├── src/
│   ├── app/                        # Next.js app router
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Landing page
│   │   ├── game/
│   │   │   └── [sessionId]/
│   │   │       ├── layout.tsx
│   │   │       └── page.tsx       # Main game page
│   │   └── api/                   # API routes (if needed)
│   │
│   ├── components/                 # @team-frontend
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── MessageBubble.tsx
│   │   ├── character/
│   │   │   ├── CharacterSheet.tsx
│   │   │   ├── StatsDisplay.tsx
│   │   │   ├── StatusEffects.tsx
│   │   │   └── CharacterCreation.tsx
│   │   ├── inventory/
│   │   │   ├── InventoryGrid.tsx
│   │   │   ├── ItemCard.tsx
│   │   │   └── ItemTooltip.tsx
│   │   ├── world/
│   │   │   ├── LocationDisplay.tsx
│   │   │   ├── WorldMap.tsx
│   │   │   └── TravelMenu.tsx
│   │   ├── ui/                    # Reusable UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Loading.tsx
│   │   └── layout/
│   │       ├── GameLayout.tsx
│   │       └── Sidebar.tsx
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts          # Main API client
│   │   │   ├── game.ts            # Game API methods
│   │   │   ├── character.ts       # Character API methods
│   │   │   ├── inventory.ts       # Inventory API methods
│   │   │   ├── websocket.ts       # WebSocket client
│   │   │   ├── stubs.ts           # Stub data for development
│   │   │   └── generated/         # Generated from OpenAPI
│   │   │       └── ...
│   │   ├── types/
│   │   │   ├── api.ts             # Generated from OpenAPI
│   │   │   ├── game.ts            # Additional game types
│   │   │   └── ui.ts              # UI-specific types
│   │   ├── hooks/
│   │   │   ├── useGameState.ts
│   │   │   ├── useWebSocket.ts
│   │   │   ├── useInventory.ts
│   │   │   ├── useCharacter.ts
│   │   │   └── useLocalStorage.ts
│   │   ├── utils/
│   │   │   ├── formatting.ts
│   │   │   └── validation.ts
│   │   └── config.ts              # Frontend configuration
│   │
│   ├── stores/                     # State management
│   │   ├── gameStore.ts           # Game state (Zustand)
│   │   ├── uiStore.ts             # UI state
│   │   └── cacheStore.ts          # API cache
│   │
│   └── styles/
│       ├── globals.css
│       └── themes/
│
├── public/
│   ├── images/
│   └── fonts/
│
├── tests/
│   ├── unit/
│   │   └── components/
│   ├── integration/
│   │   └── api/
│   └── e2e/
│       └── playwright/
│
├── scripts/
│   └── generate-stubs.ts          # Generate stub data
│
├── .env.local
├── .env.example
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
├── .eslintrc.json
└── README.md
```

## 13. Development Phases

### Phase 0: Foundation Setup (Week 1)

**Goal:** Establish development infrastructure and contracts

**@team-core:**
- [x] Initialize Python project with Poetry
- [x] Set up project structure
- [x] Define core data models (Pydantic)
- [x] Implement schema versioning system
- [x] Create Tool Registry
- [x] Create Event Bus
- [x] Define service interfaces

**@team-api:**
- [x] Initialize FastAPI application
- [x] Set up CORS and middleware
- [x] Create health check endpoints
- [x] Set up OpenAPI documentation
- [x] Implement dependency injection

**@team-frontend:**
- [x] Initialize Next.js project
- [x] Set up TypeScript configuration
- [x] Set up Tailwind CSS
- [x] Create basic layout components
- [x] Set up API client stubs

**Integration:**
- [x] Set up Git repository and CODEOWNERS
- [x] Create shared-types directory
- [x] Set up CI/CD pipelines
- [x] Define contract test framework
- [x] Create type generation scripts

**Success Criteria:**
- All teams can run their projects locally
- Contract tests framework is in place
- Type generation works end-to-end
- CI pipeline runs successfully

### Phase 1: Core Vertical Slice (Week 2)

**Goal:** Implement character creation flow end-to-end

**@team-core:**
- [ ] Implement JSON state manager
- [ ] Implement session manager
- [ ] Create character creation logic
- [ ] Write unit tests for state management

**@team-api:**
- [ ] Implement POST /api/v1/game/new
- [ ] Implement GET /api/v1/game/state/{id}
- [ ] Write contract tests for endpoints
- [ ] Generate OpenAPI spec

**@team-agents:**
- [ ] Set up LangGraph basic workflow
- [ ] Implement character creation agent
- [ ] Write agent contract tests
- [ ] Create basic prompts

**@team-frontend:**
- [ ] Create character creation UI
- [ ] Implement API client
- [ ] Set up state management (Zustand)
- [ ] Connect to real API

**Integration:**
- [ ] Run contract tests across all modules
- [ ] Test character creation flow end-to-end
- [ ] Verify type generation
- [ ] Document any issues in ADRs

**Success Criteria:**
- Users can create a character
- State persists across page refresh
- All contract tests pass
- Types are synchronized

### Phase 2: Conversation System (Weeks 3-4)

**Goal:** Enable basic chat and narrative generation

**@team-agents:**
- [ ] Implement Game Master agent
- [ ] Create narrative generation prompts
- [ ] Implement message processing workflow
- [ ] Add conversation history management

**@team-tools:**
- [ ] Implement basic character tools
- [ ] Implement basic world tools
- [ ] Register tools in registry
- [ ] Write tool contract tests

**@team-api:**
- [ ] Implement POST /api/v1/game/message
- [ ] Implement GET /api/v1/game/history
- [ ] Add request validation
- [ ] Write integration tests

**@team-frontend:**
- [ ] Create chat interface
- [ ] Implement message input/display
- [ ] Add loading states
- [ ] Implement optimistic updates

**@team-core:**
- [ ] Implement conversation persistence
- [ ] Add event publishing for messages
- [ ] Create message validation

**Integration:**
- [ ] Test conversation flow end-to-end
- [ ] Verify tool execution
- [ ] Test event propagation
- [ ] Performance testing

**Success Criteria:**
- Users can have conversations
- Agent responds coherently
- Tools execute correctly
- Events propagate to frontend

### Phase 3: Game Systems (Weeks 5-6)

**Goal:** Implement inventory, locations, and basic world

**@team-tools:**
- [ ] Implement inventory tools
- [ ] Implement location/travel tools
- [ ] Implement item tools
- [ ] Write comprehensive tool tests

**@team-agents:**
- [ ] Add inventory management to GM agent
- [ ] Add location awareness
- [ ] Create location description generation
- [ ] Implement travel logic

**@team-api:**
- [ ] Implement inventory endpoints
- [ ] Implement world endpoints
- [ ] Add location management
- [ ] Write integration tests

**@team-frontend:**
- [ ] Create inventory UI
- [ ] Create location display
- [ ] Create travel menu
- [ ] Add item interactions

**@team-core:**
- [ ] Extend state models for locations
- [ ] Add inventory validation
- [ ] Implement location graph

**Integration:**
- [ ] Test inventory operations
- [ ] Test location changes
- [ ] Test item acquisition
- [ ] E2E gameplay tests

**Success Criteria:**
- Users can manage inventory
- Users can travel between locations
- Items can be acquired/used
- World state persists correctly

### Phase 4: Real-Time Features (Week 7)

**Goal:** Add WebSocket support and real-time updates

**@team-api:**
- [ ] Implement WebSocket endpoint
- [ ] Create connection manager
- [ ] Add event streaming
- [ ] Handle reconnection

**@team-core:**
- [ ] Integrate event bus with WebSocket
- [ ] Add event filtering by session
- [ ] Implement event history

**@team-frontend:**
- [ ] Implement WebSocket client
- [ ] Add real-time state updates
- [ ] Handle connection state
- [ ] Add reconnection logic

**@team-agents:**
- [ ] Publish events for agent actions
- [ ] Add streaming responses (optional)

**Integration:**
- [ ] Test real-time updates
- [ ] Test multiple clients
- [ ] Test connection recovery
- [ ] Performance testing

**Success Criteria:**
- State updates appear in real-time
- Multiple tabs stay synchronized
- Reconnection works correctly
- No message loss

### Phase 5: Advanced Agents (Weeks 8-9)

**Goal:** Implement specialized agents and coordination

**@team-agents:**
- [ ] Implement combat agent
- [ ] Implement NPC agent
- [ ] Implement world consistency agent
- [ ] Add multi-agent coordination

**@team-tools:**
- [ ] Implement combat tools
- [ ] Implement NPC tools
- [ ] Add advanced mechanics

**@team-frontend:**
- [ ] Create combat UI
- [ ] Create NPC dialogue UI
- [ ] Add advanced visualizations

**@team-api:**
- [ ] Add combat endpoints (if needed)
- [ ] Add NPC management endpoints

**Integration:**
- [ ] Test agent coordination
- [ ] Test combat encounters
- [ ] Test NPC interactions
- [ ] Performance optimization

**Success Criteria:**
- Combat system works
- NPCs have personalities
- Agents coordinate smoothly
- World remains consistent

### Phase 6: Polish & Production (Weeks 10-12)

**Goal:** Production readiness and deployment

**All Teams:**
- [ ] Comprehensive error handling
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Complete documentation
- [ ] Increase test coverage to 80%+

**@team-api:**
- [ ] Add rate limiting
- [ ] Add authentication (if needed)
- [ ] Optimize database queries
- [ ] Add monitoring

**@team-frontend:**
- [ ] Add error boundaries
- [ ] Optimize bundle size
- [ ] Add loading skeletons
- [ ] Accessibility improvements

**@team-core:**
- [ ] Add database migrations (if using Postgres)
- [ ] Add backup/restore
- [ ] Optimize state serialization

**Integration:**
- [ ] Load testing
- [ ] Security audit
- [ ] E2E test suite completion
- [ ] Deployment to staging
- [ ] Deployment to production

**Success Criteria:**
- 95%+ uptime in testing
- <2s p95 response times
- No critical security issues
- 80%+ test coverage
- Deployment automated

## 14. Observability and Monitoring

### 14.1. Logging Configuration

```python
# src/agentic_rpg/utils/logging.py
import logging
import sys
from config import get_settings

def setup_logging():
    """Configure application logging."""
    settings = get_settings()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))
    root_logger.addHandler(console_handler)
    
    # Set library loggers to WARNING
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    return root_logger

# Usage in agent for debugging
logger = logging.getLogger(__name__)

if settings.trace_agent_reasoning:
    logger.debug(f"Agent decision: {decision}")
    logger.debug(f"Available tools: {tools}")
    logger.debug(f"Selected tool: {selected_tool}")
```

### 14.2. Metrics Collection

```python
# src/agentic_rpg/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge
from functools import wraps
from time import time

# Define metrics
agent_calls = Counter(
    'agent_calls_total',
    'Total agent calls',
    ['agent_type', 'status']
)

tool_execution_time = Histogram(
    'tool_execution_seconds',
    'Tool execution time',
    ['tool_name']
)

active_sessions = Gauge(
    'active_sessions',
    'Number of active game sessions'
)

api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method']
)

# Decorators for automatic instrumentation
def track_tool_execution(func):
    """Decorator to track tool execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        tool_name = func.__name__
        start = time()
        try:
            result = func(*args, **kwargs)
            tool_execution_time.labels(tool_name=tool_name).observe(time() - start)
            return result
        except Exception as e:
            tool_execution_time.labels(tool_name=f"{tool_name}_error").observe(time() - start)
            raise
    return wrapper

# Usage
@track_tool_execution
def execute_combat_tool(**kwargs):
    # Tool implementation
    pass
```

## 15. Architectural Decision Records (ADR)

### 15.1. ADR Template

```markdown
# ADR-XXX: [Title]

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue that we're seeing that is motivating this decision or change?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?

## Alternatives Considered
What other options were evaluated?

## Related Decisions
- ADR-XXX
- ADR-YYY
```

### 15.2. Example ADRs

```markdown
# ADR-001: Use LangGraph for Agent Orchestration

## Status
Accepted

## Context
We need a framework to orchestrate multiple LLM agents with complex workflows
including loops, conditionals, and tool execution. Options evaluated:
- LangChain LCEL only
- Custom state machine
- LangGraph
- CrewAI

## Decision
Use LangGraph for agent orchestration because:
- Built specifically for stateful, multi-agent workflows
- Strong typing with Pydantic
- Graph visualization for debugging
- Active development and community support

## Consequences
**Positive:**
- Clear visual representation of agent flows
- Built-in state management
- Easy to add new agents and workflows

**Negative:**
- Learning curve for developers new to LangGraph
- Dependency on Anthropic's ecosystem
- May be overkill for simple linear flows

## Alternatives Considered
- **LangChain LCEL**: Too linear for our multi-agent needs
- **Custom state machine**: Too much reinvention, hard to debug
- **CrewAI**: Less flexible for game-specific workflows
```

```markdown
# ADR-002: Tool Registry Pattern

## Status
Accepted

## Context
Multiple teams developing tools simultaneously. Need to prevent merge conflicts
in tool registration and enable dynamic discovery.

## Decision
Implement a Tool Registry pattern where:
- Tools self-register via decorator or explicit call
- Registry provides dynamic tool discovery
- No central registration file needed

## Consequences
**Positive:**
- No merge conflicts on tool registration
- Easy to add/remove tools
- Supports feature flags for tools
- Clear ownership per tool

**Negative:**
- Tools must be imported to register
- Less explicit than central registry

## Implementation
```python
# Each team registers independently
ToolRegistry.register(MyTool(), category="combat")
```
```

## 16. Documentation Requirements

### 16.1. Required Documentation

```markdown
docs/
├── ARCHITECTURE.md           # System architecture overview
├── API.md                    # Auto-generated API docs
├── AGENTS.md                 # Agent behavior and prompts
├── TOOLS.md                  # Tool development guide
├── DEPLOYMENT.md             # Deployment procedures
├── TROUBLESHOOTING.md        # Common issues and solutions
├── CONTRIBUTING.md           # How to contribute
└── ADR/                      # Architectural decisions
    ├── 001-use-langgraph.md
    ├── 002-tool-registry.md
    └── 003-event-bus.md
```

### 16.2. Code Documentation Standards

```python
# All public functions require docstrings
def create_character(name: str, profession: str) -> Character:
    """Create a new character.
    
    Creates a character with default stats based on profession.
    The character starts at the default starting location with
    1000 money and full health.
    
    Args:
        name: Character name (1-50 characters)
        profession: Character profession (e.g., "Space Pirate")
    
    Returns:
        Newly created Character object
    
    Raises:
        ValueError: If name is empty or too long
        ValueError: If profession is invalid
    
    Example:
        >>> char = create_character("Jax", "Space Pirate")
        >>> char.stats.money
        1000
    """
    pass

# Type hints required
def process_tool_call(
    tool_name: str,
    parameters: dict[str, Any]
) -> ToolResult:
    """Process a tool call."""
    pass
```

## 17. Security Considerations

### 17.1. API Security

```python
# src/agentic_rpg/api/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier
        client = request.client.host
        
        # Check rate limit
        now = time.time()
        if client in self.requests:
            requests = [r for r in self.requests[client] if now - r < self.period]
            if len(requests) >= self.calls:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            requests.append(now)
            self.requests[client] = requests
        else:
            self.requests[client] = [now]
        
        response = await call_next(request)
        return response

# Add to app
app.add_middleware(RateLimitMiddleware, calls=100, period=60)
```

### 17.2. Input Validation

```python
# All Pydantic models have validation
class MessageRequest(BaseModel):
    session_id: str = Field(..., min_length=36, max_length=36)
    message: str = Field(..., min_length=1, max_length=500)
    
    @validator('session_id')
    def validate_session_id(cls, v):
        # Validate UUID format
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Invalid session ID format')
        return v
    
    @validator('message')
    def validate_message(cls, v):
        # Sanitize input
        if any(char in v for char in ['<', '>', '{', '}']):
            raise ValueError('Invalid characters in message')
        return v.strip()
```

### 17.3. Environment Security

```bash
# .env (never commit)
LLM_API_KEY=sk-ant-...
DATABASE_PASSWORD=...

# .gitignore
.env
.env.local
.env.*.local
gamestate/sessions/
*.key
*.pem
```

## 18. RFC Process for Breaking Changes

### 18.1. When to Create an RFC

Create an RFC for:
- Changes to shared interfaces (Protocol definitions)
- Changes to data models affecting multiple teams
- Changes to API contracts
- New architectural patterns
- Major refactoring

### 18.2. RFC Template

```markdown
# RFC-XXX: [Title]

**Author:** @username  
**Date:** YYYY-MM-DD  
**Status:** [Draft | Review | Accepted | Rejected]

## Summary
One paragraph explanation of the change.

## Motivation
Why are we doing this? What use cases does it support? What problems does it solve?

## Proposed Solution
Detailed explanation of the proposed change.

```python
# Code examples
```

## Impact Analysis
### Affected Teams
- @team-core
- @team-api

### Breaking Changes
List all breaking changes and migration path.

### Migration Plan
Step-by-step guide for teams to adapt.

## Alternatives Considered
What other approaches were evaluated?

## Open Questions
Unresolved issues that need discussion.

## Timeline
- Week 1: Review and feedback
- Week 2: Implementation
- Week 3: Migration

## Sign-off
Required approvals from affected teams:
- [ ] @team-core-lead
- [ ] @team-api-lead
```

## 19. Success Metrics

### 19.1. Technical Metrics

```yaml
performance:
  api_response_time_p95: "<2s"
  api_response_time_p99: "<5s"
  websocket_latency: "<200ms"
  state_persistence_reliability: "100%"
  
quality:
  test_coverage: ">80%"
  contract_test_pass_rate: "100%"
  integration_test_pass_rate: ">95%"
  build_success_rate: ">95%"
  
reliability:
  uptime: ">99%"
  error_rate: "<1%"
  tool_success_rate: ">95%"
  agent_coherence_score: ">4/5"
  
development:
  merge_conflict_rate: "<10%"
  time_to_integrate: "<1 day"
  pr_review_time: "<4 hours"
  deployment_frequency: "multiple/week"
```

### 19.2. Team Metrics

```yaml
collaboration:
  cross_team_blockers: "<5/week"
  integration_issues: "<3/week"
  contract_test_failures: "<2/week"
  
velocity:
  story_completion_rate: ">90%"
  sprint_predictability: ">80%"
  feature_flag_adoption: ">75%"
```

## 20. Deployment

### 20.1. Development Environment

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=development
      - USE_MOCKS=false
    volumes:
      - ./backend:/app
      - ./gamestate:/app/gamestate
    command: poetry run uvicorn agentic_rpg.api.main:app --reload --host 0.0.0.0
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev
  
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=agentic_rpg
      - POSTGRES_USER=dev
      - POSTGRES_PASSWORD=devpassword
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### 20.2. Production Considerations

```markdown
## Production Architecture

```
                    ┌─────────────┐
                    │   Nginx     │
                    │   (SSL)     │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │  Next.js    │          │   FastAPI   │
       │  (Frontend) │          │  (Backend)  │
       └─────────────┘          └──────┬──────┘
                                       │
                            ┌──────────┴──────────┐
                            │                     │
                     ┌──────▼──────┐      ┌──────▼──────┐
                     │  PostgreSQL │      │    Redis    │
                     │   (State)   │      │   (Cache)   │
                     └─────────────┘      └─────────────┘
```

### Requirements
- PostgreSQL for state persistence
- Redis for session cache
- SSL certificates
- Rate limiting at nginx level
- Monitoring (Prometheus/Grafana)
```

---

## Appendix A: Technology Stack Summary

### Backend
- **Python 3.11+**
- **FastAPI 0.104+**: REST API framework
- **LangGraph 0.2+**: Agent orchestration
- **LangChain 0.1+**: LLM framework
- **Pydantic 2.5+**: Data validation
- **Anthropic SDK**: Claude API client
- **uvicorn**: ASGI server
- **websockets**: Real-time communication
- **Poetry**: Dependency management
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **ruff**: Linting and formatting
- **mypy**: Type checking

### Frontend
- **Next.js 14+**: React framework (App Router)
- **React 18+**: UI library
- **TypeScript 5+**: Type safety
- **Tailwind CSS 3+**: Styling
- **Zustand**: State management
- **SWR**: Data fetching and caching
- **openapi-typescript**: Type generation
- **Playwright**: E2E testing
- **ESLint/Prettier**: Code quality

### DevOps
- **Docker**: Containerization
- **GitHub Actions**: CI/CD
- **Prometheus**: Metrics
- **Nginx**: Reverse proxy
- **PostgreSQL**: Production database (optional)
- **Redis**: Caching layer (optional)

## Appendix B: Quick Start Guide

### Backend Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd backend

# 2. Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 3. Install dependencies
poetry install

# 4. Configure environment
cp .env.example .env
# Edit .env with your LLM API key

# 5. Run tests
poetry run poe test

# 6. Start server
poetry run poe dev
```

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure environment
cp .env.example .env.local
# Edit with backend URL

# 3. Generate types from backend
npm run generate-types

# 4. Start dev server
npm run dev
```

### Full Stack with Docker

```bash
# Start everything
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

**Document Version:** 2.0  
**Last Updated:** 2025-01-06  
**Status:** Ready for Implementation
