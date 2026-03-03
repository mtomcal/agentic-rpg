# Implementation Plan — Ralph A Backend

## Context Table

| # | Feature/Change | Key Files | Affected Items |
|---|---------------|-----------|----------------|
| 1 | Full plan lives in `docs/plans/ralph-a-backend.md` | docs/plans/ralph-a-backend.md | All items |
| 2 | Pydantic model specs | docs/specs/schema-registry.md, docs/tech/pydantic-models.md | Phase 1 models |
| 3 | Project structure spec | docs/tech/python-backend.md | Phase 1 scaffold |
| 4 | Docker/Postgres spec | docs/tech/docker-kubernetes.md, docs/tech/postgres.md | Phase 1 docker |
| 5 | Game state spec | docs/specs/game-state.md | Phase 2 |
| 6 | Event system spec | docs/specs/event-system.md | Phase 2 |
| 7 | Tool registry spec | docs/specs/tool-registry.md | Phase 3 |
| 8 | Agent system spec | docs/specs/agent-system.md | Phase 4 |
| 9 | LangChain integration | docs/tech/langchain-integration.md | Phase 4 |
| 10 | Story engine spec | docs/specs/story-engine.md | Phase 5 |
| 11 | API layer spec | docs/specs/api-layer.md | Phase 6 |
| 12 | WebSocket spec | docs/tech/websockets.md | Phase 6 |
| 13 | Sandbox runs on `sandbox-net` docker network | docker-compose.yml, Dockerfile.sandbox | DB tests need `postgres` hostname |

## Task Order

### High Priority — Phase 1: Scaffold + Docker + Models

- [x] 1. Create `backend/pyproject.toml` with uv, all dependencies, pytest config, coverage config
- [x] 2. Create full directory structure (all `__init__.py`, empty modules per plan)
- [x] 3. Write `backend/src/agentic_rpg/config.py` (Pydantic Settings)
- [x] 4. Write `backend/src/agentic_rpg/db.py` (asyncpg pool create/close)
- [x] 5. Write `backend/src/agentic_rpg/main.py` (FastAPI app, lifespan, health endpoint, CORS)
- [x] 6. Write `docker-compose.yml` (postgres service, backend service, network, volume)
- [x] 7. Write `backend/Dockerfile` (Python 3.12 slim, uv, uvicorn CMD)
- [x] 8. Write all Pydantic models: character, inventory, world, story, game_state, events, api
- [x] 9. Set up Alembic: alembic.ini, env.py, initial migration (game_sessions + game_events tables)
- [x] 10. Write Phase 1 tests: test_schemas.py (all model tests) + test_health.py
- [x] 11. Run `uv sync` and `uv run pytest` — all Phase 1 tests green

### High Priority — Phase 2: State Manager + Event Bus

- [x] 12. Write test fixtures in conftest.py (db_pool, clean_db, sample_game_state, event_bus)
- [x] 13. Write state manager tests (test_manager.py) — RED
- [x] 14. Implement StateManager (state/manager.py) — GREEN
- [x] 15. Write event bus tests (test_bus.py) — RED
- [x] 16. Implement EventBus (events/bus.py) + EventPayloadRegistry (events/schemas.py) — GREEN
- [x] 17. Write event persistence tests (test_persistence.py) — RED
- [ ] 18. Implement event persistence (events/persistence.py) — GREEN
- [ ] 19. Run full test suite — all Phase 1+2 tests green

### Medium Priority — Phase 3: Tool Registry + All Tools

- [ ] 20. Write tool test fixtures (tool_game_state, tool_event_bus, tool_registry)
- [ ] 21. Write registry tests + implement ToolRegistry (tools/registry.py)
- [ ] 22. Write character tool tests — RED, then implement (tools/character.py) — GREEN
- [ ] 23. Write inventory tool tests — RED, then implement (tools/inventory.py) — GREEN
- [ ] 24. Write world tool tests — RED, then implement (tools/world.py) — GREEN
- [ ] 25. Write narrative tool tests — RED, then implement (tools/narrative.py) — GREEN
- [ ] 26. Run full test suite — all Phase 1+2+3 tests green

### Medium Priority — Phase 4: Agent Graph + LLM Integration

- [ ] 27. Write LLM client tests + implement (llm/client.py)
- [ ] 28. Write context assembly tests — RED, then implement (agent/context.py, agent/prompt.py) — GREEN
- [ ] 29. Write agent graph tests — RED, then implement (agent/graph.py) — GREEN
- [ ] 30. Run full test suite — all Phase 1-4 tests green

### Medium Priority — Phase 5: Story Engine

- [ ] 31. Write story engine tests — RED
- [ ] 32. Implement story engine (agent/story_engine.py) — GREEN
- [ ] 33. Run full test suite — all Phase 1-5 tests green

### Lower Priority — Phase 6: FastAPI Wiring (HTTP + WebSocket)

- [ ] 34. Write API test fixtures (app_client, ws_client, seeded_session)
- [ ] 35. Write session endpoint tests — RED, then implement (api/handlers.py, api/routes.py) — GREEN
- [ ] 36. Write game state endpoint tests — RED, then implement — GREEN
- [ ] 37. Write WebSocket tests — RED, then implement (api/websocket.py) — GREEN
- [ ] 38. Wire everything in main.py (lifespan, routes, middleware, dependencies)
- [ ] 39. Run full test suite — all tests green, docker compose up works
- [ ] 40. Final coverage check: `uv run pytest --cov=agentic_rpg --cov-branch --cov-report=term-missing` meets 85%

## Discoveries

Add rows here when you find things the plan missed or got wrong:

| # | Discovery | Impact |
|---|-----------|--------|
| 1 | Sandbox has no outbound network — `uv sync` and `pip install` fail. pyproject.toml is correct but deps can't be installed in sandbox. Need network or pre-built venv. | All items needing `uv run pytest` |
| 2 | pytest-asyncio needs `asyncio_default_test_loop_scope = "session"` to match session-scoped pool fixture, otherwise asyncpg gets "another operation is in progress" errors | All DB tests |
| 3 | Session model `datetime.utcnow()` produces naive datetimes; manager and DB produce aware datetimes. Fixed by using `datetime.now(UTC)` everywhere. | State manager, any datetime comparisons |

## Per-Item Process

1. Read the item description and find the relevant spec in `docs/specs/` or `docs/tech/`
2. If it's a test item (RED), write the failing tests first
3. If it's an implementation item (GREEN), write the minimum code to pass tests
4. Run `cd backend && uv run pytest` to verify
5. Check off the item in this file
6. If you discover something the plan missed, add it to Discoveries
7. Commit with: `git commit --author="mtomcal <mtomcal@users.noreply.github.com>"`

## Rules

1. Read spec files before implementing — they are authoritative
2. One checklist item per iteration — do it well, commit, stop
3. Tests must have specific assertions, never bare truthy checks
4. Coverage target: 85% lines, branches, functions
5. Preserve existing code — edit surgically, don't rewrite whole files
6. If a test is failing and you can't fix it quickly, `@pytest.mark.skip` it and move on
7. The docker-compose postgres is on the `sandbox-net` network — use `postgres` as hostname
8. Always run `uv run pytest` before committing to make sure nothing is broken
9. Use `asyncio_mode = "auto"` in pytest config — no manual event loop management
10. Follow the Pydantic model conventions in `docs/specs/schema-registry.md`
