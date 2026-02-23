# Technology Choice: Go Backend

## Decision

Use Go (standard library + minimal dependencies) for the backend server.

## Rationale

- **Performance**: Go's compiled binaries and goroutine model handle concurrent WebSocket connections and HTTP requests efficiently without tuning
- **Simplicity**: The standard library provides HTTP server, JSON handling, and testing out of the box. Minimal framework needed.
- **Deployment**: Single static binary. No runtime dependencies. Simple Docker images. Ideal for Kubernetes.
- **Learning goal**: Gain deeper Go experience with a real project
- **Concurrency model**: Goroutines and channels map naturally to handling multiple game sessions simultaneously

## What We're Using

### Standard Library

- `net/http` — HTTP server and routing
- `encoding/json` — JSON serialization
- `database/sql` — Database interface
- `context` — Request context and cancellation
- `testing` — Test framework
- `log/slog` — Structured logging (Go 1.21+)

### Minimal External Dependencies

- **Router**: `chi` or `gorilla/mux` — lightweight HTTP router with middleware support. The stdlib `http.ServeMux` (Go 1.22+ with pattern matching) is also an option if we want zero dependencies.
- **WebSocket**: `gorilla/websocket` or `nhooyr.io/websocket` — WebSocket upgrade and message handling
- **PostgreSQL driver**: `pgx` — high-performance Postgres driver for Go
- **Migration tool**: `golang-migrate/migrate` — database schema migrations
- **JSON Schema validation**: `santhosh-tekuri/jsonschema` — runtime JSON Schema validation for events and API requests
- **JSON Schema codegen**: `atombender/go-jsonschema` or similar — generate Go structs from JSON Schema files

### What We're NOT Using

- **Web frameworks** (Gin, Echo, Fiber) — too much magic, stdlib is sufficient
- **ORMs** (GORM, Ent) — we want to write SQL directly for learning and control
- **LLM frameworks** (LangChainGo) — direct API calls for transparency and learning
- **DI frameworks** — manual dependency injection via constructors

## Project Structure

```
backend/
  cmd/
    server/
      main.go             # Entry point, wire up dependencies, start server
  internal/
    api/
      routes.go           # HTTP route definitions
      handlers.go         # HTTP handlers
      websocket.go        # WebSocket hub and connection handling
      middleware.go        # Auth, logging, CORS middleware
    agent/
      agent.go            # Agent loop (context assembly → LLM call → tool execution)
      context.go          # Context window assembly
      prompt.go           # System prompt construction
    tools/
      registry.go         # Tool registry
      character.go        # Character tools
      inventory.go        # Inventory tools
      world.go            # World tools
      narrative.go        # Narrative/story tools
    state/
      manager.go          # State management (load, save, update)
      migrations.go       # State schema migrations
    events/
      bus.go              # Event bus (pub/sub)
      schemas.go          # Event schema registry and validation
    models/
      ...                 # Hand-written models (if any beyond generated)
    llm/
      client.go           # LLM API client (Anthropic/OpenAI)
      types.go            # Request/response types for LLM APIs
    config/
      config.go           # Application configuration
    db/
      postgres.go         # Database connection and queries
      migrations/         # SQL migration files
  generated/
    ...                   # Generated Go structs from JSON Schema
  go.mod
  go.sum
```

## Key Patterns

### Dependency Injection

Manual constructor injection. No framework.

```go
// main.go
db := postgres.Connect(cfg.DatabaseURL)
eventBus := events.NewBus()
stateManager := state.NewManager(db, eventBus)
toolRegistry := tools.NewRegistry(stateManager, eventBus)
agent := agent.New(llmClient, toolRegistry, stateManager)
server := api.NewServer(agent, stateManager, cfg)
server.ListenAndServe(":8080")
```

### Error Handling

Go-standard error returns. No panics for expected errors. Wrap errors with context using `fmt.Errorf("loading state: %w", err)`.

### Testing

- Unit tests next to source files (`foo_test.go`)
- Integration tests in `internal/integration/`
- Table-driven tests for tools and handlers
- Mock interfaces for database, LLM client, event bus

## Build and Run

```bash
# Development
go run ./cmd/server

# Build
go build -o bin/server ./cmd/server

# Test
go test ./...

# Docker
docker build -t agentic-rpg-server .
```
