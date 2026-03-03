# Agentic RPG — Documentation Index

A browser-based, genre-agnostic RPG powered by LangChain/LangGraph agents with tool use.

**Start here**: [Product Requirements Document](prd.md)

**Build order**: [Roadmap](roadmap.md)

---

## System Specifications

Specs that define how each system works, written for the Python/FastAPI/LangChain stack.

| Spec | Description |
|------|-------------|
| [Agent System](specs/agent-system.md) | LangGraph agent loop: context assembly, LLM tool use, decision making |
| [Story Engine](specs/story-engine.md) | Story outline generation, beat lifecycle, narrative adaptation |
| [Game State](specs/game-state.md) | Pydantic state models, persistence interface, sessions, schema versioning |
| [Event System](specs/event-system.md) | Async event bus, event types, Pydantic validation, event persistence |
| [Tool Registry](specs/tool-registry.md) | LangChain tool registration, discovery, execution pipeline |
| [API Layer](specs/api-layer.md) | FastAPI HTTP endpoints, WebSocket protocol, authentication, error handling |
| [Frontend](specs/frontend.md) | Screens, state management, player input, real-time updates |
| [Schema Registry](specs/schema-registry.md) | Pydantic models as source of truth, schema organization, TypeScript generation |

## Technology Choices

Implementation-specific decisions: what we're using and why.

| Doc | Description |
|-----|-------------|
| [Python Backend](tech/python-backend.md) | FastAPI + uvicorn, project structure, dependencies, patterns |
| [Next.js Frontend](tech/nextjs-frontend.md) | Next.js + TypeScript + Tailwind + Zustand |
| [PostgreSQL](tech/postgres.md) | Schema design, JSONB state storage, event table, Alembic migrations |
| [LangChain Integration](tech/langchain-integration.md) | LangChain/LangGraph agents, LangSmith tracing, streaming, cost management |
| [Docker & Kubernetes](tech/docker-kubernetes.md) | Docker Compose for dev, K8s design for production |
| [WebSockets](tech/websockets.md) | Protocol design, connection lifecycle, FastAPI WebSocket handling |
| [Pydantic Models](tech/pydantic-models.md) | Pydantic v2 models → TypeScript types generation pipeline |

## Implementation Plans

Generated per-phase as work begins. Each plan is tied to a specific roadmap phase and/or spec change.

| Plan | Status |
|------|--------|
| *(none yet)* | |

Plans live in [`docs/plans/`](plans/).

---

## How to Use These Docs

### Starting a new feature or phase

1. Read the relevant **system spec(s)** to understand what needs to be built
2. Read the relevant **tech doc(s)** to understand implementation specifics
3. Check the **roadmap** for build order and dependencies
4. Generate an **implementation plan** in `docs/plans/`
5. Build from the plan

### Updating a spec

1. Edit the spec in `docs/specs/`
2. Review the diff to understand what changed
3. Generate an implementation plan for the delta
4. Build from the plan

### Adding a new system

1. Write a spec in `docs/specs/`
2. If it introduces new technology, write a tech doc in `docs/tech/`
3. Update the roadmap with the new phase or insert it into an existing phase
4. Update this README with the new doc links
