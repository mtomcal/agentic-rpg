# Technology Choice: Python Backend

## Decision

Use Python 3.12+ with FastAPI and uvicorn for the backend server. Use `uv` for dependency management.

## Rationale

- **FastAPI**: Modern async web framework with automatic OpenAPI docs, Pydantic integration, dependency injection, and native WebSocket support. The most productive Python web framework for API-first applications.
- **LangChain ecosystem**: Python is the primary language for LangChain, LangGraph, and LangSmith. Building in Python gives us first-class access to the entire ecosystem with no wrapper libraries or version lag.
- **async/await**: Python's `asyncio` provides clean concurrency for handling WebSocket connections, LLM API calls, and database queries without threads.
- **Learning goal**: Gain deep experience with FastAPI, LangChain/LangGraph, and modern async Python patterns by building a real project.
- **Pydantic v2**: Native integration with FastAPI for request/response validation, and serves as the single source of truth for all data models across the stack.

## What We're Using

### Core Framework

- **FastAPI** — async web framework (HTTP + WebSocket)
- **uvicorn** — ASGI server
- **Pydantic v2** — data validation and serialization (see [Pydantic Models](pydantic-models.md))
- **uv** — fast Python package manager and project tool

### LLM / Agent Layer

- **LangChain** — LLM abstraction, tool binding, prompt templates
- **LangGraph** — agent workflow as a state graph
- **LangSmith** — tracing, debugging, and observability (see [LangChain Integration](langchain-integration.md))

### Database

- **asyncpg** — high-performance async PostgreSQL driver
- **Alembic** — database schema migrations
- **SQLAlchemy** (Core only, optional) — query builder for complex queries

### Testing

- **pytest** — test framework
- **pytest-asyncio** — async test support
- **httpx** — async HTTP test client (FastAPI's `TestClient` uses it under the hood)

### Utilities

- **structlog** — structured logging
- **pydantic-settings** — configuration management from environment variables

### What We're NOT Using

- **Django / Flask** — FastAPI is a better fit for async APIs with Pydantic
- **ORMs** (SQLAlchemy ORM, Django ORM) — we write SQL directly for learning and control. SQLAlchemy Core is acceptable as a query builder.
- **Celery / task queues** — asyncio is sufficient for our concurrency needs
- **Socket.IO** — native FastAPI/Starlette WebSocket support is simpler

## Project Structure

```
backend/
  src/
    agentic_rpg/
      __init__.py
      main.py                 # FastAPI app factory, lifespan events, mount routes
      config.py               # Pydantic Settings for app configuration
      db.py                   # asyncpg pool setup, connection helpers
      api/
        __init__.py
        routes.py             # APIRouter definitions, mount all route groups
        handlers.py           # HTTP endpoint handlers (sessions, players, state)
        websocket.py          # WebSocket hub and connection handling
        middleware.py         # CORS, logging, error handling middleware
        dependencies.py       # FastAPI Depends providers (db pool, services)
      agent/
        __init__.py
        graph.py              # LangGraph StateGraph definition (agent loop)
        context.py            # Context window assembly for LLM calls
        prompt.py             # System prompt construction
      tools/
        __init__.py
        registry.py           # Tool registry (collects all tools for LangChain binding)
        character.py          # Character tools (@tool decorated)
        inventory.py          # Inventory tools
        world.py              # World/location tools
        narrative.py          # Narrative/story tools
      state/
        __init__.py
        manager.py            # State management (load, save, update game state)
        migrations.py         # Game state schema migrations (not DB migrations)
      events/
        __init__.py
        bus.py                # Async event bus (publish/subscribe)
        schemas.py            # Event type definitions and validation
      models/
        __init__.py
        game_state.py         # GameState, Character, Location Pydantic models
        character.py          # Character-specific models
        inventory.py          # Inventory models
        world.py              # World/location models
        story.py              # Story outline, narrative models
        events.py             # Event payload models
        api.py                # API request/response models
      llm/
        __init__.py
        client.py             # LangChain ChatModel setup (ChatAnthropic, ChatOpenAI)
        types.py              # LLM-related type definitions
  tests/
    __init__.py
    conftest.py               # Shared fixtures (test db, test client, mock LLM)
    test_api/                 # API endpoint tests
    test_agent/               # Agent graph tests
    test_tools/               # Tool unit tests
    test_state/               # State management tests
    test_events/              # Event bus tests
  alembic/
    env.py                    # Alembic environment config
    versions/                 # Migration files
  alembic.ini
  pyproject.toml              # Project metadata, dependencies, tool config
```

## Key Patterns

### Dependency Injection

FastAPI's `Depends` system replaces manual constructor wiring. Dependencies are declared as function parameters and resolved automatically.

```python
# dependencies.py
from asyncpg import Pool
from fastapi import Depends, Request

async def get_db_pool(request: Request) -> Pool:
    return request.app.state.db_pool

async def get_state_manager(pool: Pool = Depends(get_db_pool)) -> StateManager:
    return StateManager(pool)

async def get_agent(
    state_manager: StateManager = Depends(get_state_manager),
) -> AgentGraph:
    return AgentGraph(state_manager=state_manager)
```

```python
# handlers.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    state_manager: StateManager = Depends(get_state_manager),
) -> SessionResponse:
    session = await state_manager.create_session(request)
    return SessionResponse.from_session(session)
```

### Application Lifespan

Use FastAPI's lifespan context manager for startup/shutdown:

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create connection pool, initialize services
    app.state.db_pool = await asyncpg.create_pool(settings.database_url)
    yield
    # Shutdown: close pool, drain connections
    await app.state.db_pool.close()

app = FastAPI(title="Agentic RPG", lifespan=lifespan)
```

### Error Handling

Use FastAPI exception handlers and custom exception classes:

```python
# exceptions.py
class GameError(Exception):
    """Base exception for game logic errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

class SessionNotFoundError(GameError):
    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", status_code=404)

# middleware.py
@app.exception_handler(GameError)
async def game_error_handler(request: Request, exc: GameError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )
```

### Async Database Access

Use asyncpg directly for database queries:

```python
# db.py
async def fetch_session(pool: Pool, session_id: str) -> dict | None:
    return await pool.fetchrow(
        "SELECT * FROM sessions WHERE id = $1",
        session_id,
    )

async def save_game_state(pool: Pool, session_id: str, state: GameState) -> None:
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE sessions SET game_state = $1, updated_at = now() WHERE id = $2",
                state.model_dump_json(),
                session_id,
            )
```

### Configuration

Use pydantic-settings for type-safe configuration from environment variables:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    anthropic_api_key: str
    log_level: str = "info"
    host: str = "0.0.0.0"
    port: int = 8080
    model_name: str = "claude-sonnet-4-20250514"

    model_config = {"env_prefix": ""}

settings = Settings()
```

### Testing

Use pytest with async support and FastAPI's test client:

```python
# conftest.py
import pytest
from httpx import ASGITransport, AsyncClient
from agentic_rpg.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

# test_api/test_sessions.py
@pytest.mark.asyncio
async def test_create_session(client: AsyncClient):
    response = await client.post("/api/v1/sessions", json={
        "genre": "fantasy",
        "character_name": "Aldric",
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
```

## Build and Run

```bash
# Install dependencies
uv sync

# Development (with auto-reload)
uv run uvicorn agentic_rpg.main:app --reload --host 0.0.0.0 --port 8080

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=agentic_rpg

# Run a specific test file
uv run pytest tests/test_api/test_sessions.py

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "add sessions table"

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
uv run ruff format src/

# Docker
docker build -t agentic-rpg-server ./backend
```
