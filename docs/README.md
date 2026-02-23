# Agentic RPG — Documentation Index

A browser-based, genre-agnostic RPG powered by LLM agents with direct API tool use.

**Start here**: [Product Requirements Document](prd.md)

**Build order**: [Roadmap](roadmap.md)

---

## System Specifications

Stack-agnostic specs that define how each system works. These could be implemented in any language or framework.

| Spec | Description |
|------|-------------|
| [Agent System](specs/agent-system.md) | The agent loop: context assembly, LLM tool use, decision making |
| [Story Engine](specs/story-engine.md) | Story outline generation, beat lifecycle, narrative adaptation |
| [Game State](specs/game-state.md) | State structure, persistence interface, sessions, schema versioning |
| [Event System](specs/event-system.md) | Event bus, event types, JSON schema validation, event persistence |
| [Tool Registry](specs/tool-registry.md) | Tool registration, discovery, execution pipeline |
| [API Layer](specs/api-layer.md) | HTTP endpoints, WebSocket protocol, authentication, error handling |
| [Frontend](specs/frontend.md) | Screens, state management, player input, real-time updates |
| [Schema Registry](specs/schema-registry.md) | JSON Schema as source of truth, schema organization, code generation contract |

## Technology Choices

Implementation-specific decisions: what we're using and why.

| Doc | Description |
|-----|-------------|
| [Go Backend](tech/go-backend.md) | Go stdlib approach, project structure, dependencies, patterns |
| [Next.js Frontend](tech/nextjs-frontend.md) | Next.js + TypeScript + Tailwind + Zustand |
| [PostgreSQL](tech/postgres.md) | Schema design, JSONB state storage, event table, migrations |
| [LLM Integration](tech/llm-integration.md) | Direct API calls, provider abstraction, streaming, cost management |
| [Docker & Kubernetes](tech/docker-kubernetes.md) | Docker Compose for dev, K8s design for production |
| [WebSockets](tech/websockets.md) | Protocol design, connection lifecycle, hub architecture |
| [Schema Codegen](tech/schema-codegen.md) | JSON Schema → Go structs + TypeScript types pipeline |

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

1. Write a stack-agnostic spec in `docs/specs/`
2. If it introduces new technology, write a tech doc in `docs/tech/`
3. Update the roadmap with the new phase or insert it into an existing phase
4. Update this README with the new doc links
