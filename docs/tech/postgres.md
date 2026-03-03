# Technology Choice: PostgreSQL

## Decision

Use PostgreSQL for all persistent data storage.

## Rationale

- **Learning goal**: Gain more experience with PostgreSQL in a real project
- **Production-grade**: Handles concurrent access, transactions, and complex queries
- **JSON support**: `jsonb` columns store game state as structured JSON with indexing — good fit for flexible, schema-evolving game state
- **Event storage**: PostgreSQL handles the event log well with time-based queries and indexing
- **Kubernetes-ready**: Well-supported in K8s (StatefulSets, operators like CloudNativePG)

## Schema Design

### Tables

**players**
```sql
CREATE TABLE players (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**sessions**
```sql
CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id       UUID NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'abandoned')),
    genre           TEXT NOT NULL,
    schema_version  TEXT NOT NULL,
    game_state      JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_sessions_player ON sessions(player_id);
CREATE INDEX idx_sessions_status ON sessions(status);
```

**events**
```sql
CREATE TABLE events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    type        TEXT NOT NULL,
    payload     JSONB NOT NULL,
    source      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_created ON events(created_at);
CREATE INDEX idx_events_session_type ON events(session_id, type);
```

### Design Decisions

**Game state as JSONB**: The full game state is stored as a single JSONB document in the `sessions` table. This is intentional:
- The state structure evolves as the game develops
- State is always loaded and saved as a unit (no partial reads needed from the DB)
- JSONB allows indexing specific paths if needed later
- Schema validation happens at the application layer (Pydantic models), not the database

**Events as rows**: Each event is a row, not embedded in the session JSONB. This supports:
- Efficient time-range queries
- Type-based filtering
- Pagination
- Independent event storage growth

**No separate tables for character, inventory, etc.**: These are all part of the game state JSONB. If query patterns later require it, we can extract them into relational tables. Start simple.

## Migrations

Use **Alembic** for schema migrations:

```
backend/alembic/
  alembic.ini
  env.py
  versions/
    0001_create_players.py
    0002_create_sessions.py
    0003_create_events.py
```

Migration commands:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current migration status
alembic current
```

Migrations run on application startup (or as a separate migration step in CI/deployment). Alembic's `env.py` is configured with the async engine for asyncpg compatibility.

## Connection Management

- Use **asyncpg** with an async connection pool via SQLAlchemy's `create_async_engine` or a raw `asyncpg.Pool`
- Pool settings: max 25 connections, 5 min idle timeout
- One pool shared across the application, created at FastAPI startup and closed at shutdown
- Transactions for atomic state saves (update session + write events)

```python
import asyncpg

async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=25,
        max_inactive_connection_lifetime=300,
    )
```

FastAPI lifespan manages the pool:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db_pool = await create_pool()
    yield
    await app.state.db_pool.close()
```

## Local Development

PostgreSQL runs in Docker Compose (see [Docker & Kubernetes](docker-kubernetes.md)). Connection string from environment variable (`DATABASE_URL`).

## Future Considerations

- **Read replicas**: If load requires it, read game state from replicas
- **Partitioning**: Partition events table by time if it grows large
- **Full-text search**: PostgreSQL FTS for searching conversation history or event logs
- **Redis cache**: Cache active session state in Redis for fast reads (write-through to Postgres)
