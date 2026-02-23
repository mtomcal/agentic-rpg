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
- Schema validation happens at the application layer (JSON Schema), not the database

**Events as rows**: Each event is a row, not embedded in the session JSONB. This supports:
- Efficient time-range queries
- Type-based filtering
- Pagination
- Independent event storage growth

**No separate tables for character, inventory, etc.**: These are all part of the game state JSONB. If query patterns later require it, we can extract them into relational tables. Start simple.

## Migrations

Use `golang-migrate/migrate` for schema migrations:

```
backend/internal/db/migrations/
  000001_create_players.up.sql
  000001_create_players.down.sql
  000002_create_sessions.up.sql
  000002_create_sessions.down.sql
  000003_create_events.up.sql
  000003_create_events.down.sql
```

Migrations run on application startup (or as a separate migration step in CI/deployment).

## Connection Management

- Use `pgx` connection pool with sensible defaults (max 25 connections, 5 min idle timeout)
- One pool shared across the application
- Transactions for atomic state saves (update session + write events)

## Local Development

PostgreSQL runs in Docker Compose (see [Docker & Kubernetes](docker-kubernetes.md)). Connection string from environment variable.

## Future Considerations

- **Read replicas**: If load requires it, read game state from replicas
- **Partitioning**: Partition events table by time if it grows large
- **Full-text search**: PostgreSQL FTS for searching conversation history or event logs
- **Redis cache**: Cache active session state in Redis for fast reads (write-through to Postgres)
