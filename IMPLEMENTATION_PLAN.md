# Implementation Plan — Ralph B Frontend

## Context Table

| # | Feature/Change | Key Files | Affected Items |
|---|---------------|-----------|----------------|
| 1 | No frontend/ directory exists yet | frontend/ | All items — must scaffold first |
| 2 | No docker-compose.yml exists | docker-compose.yml | Docker Setup items |
| 3 | Backend spec defines API contracts | docs/specs/api-layer.md, docs/specs/schema-registry.md | Types, API client, WebSocket |
| 4 | Tailwind CSS only, no component libs | frontend/ | All components |
| 5 | 85% coverage required on all metrics | jest/vitest config | All test files |

## Task Order

### High Priority (Foundation)

| # | Item | What to Check |
|---|------|---------------|
| 1 | Project Setup — scaffold Next.js App Router with TS + Tailwind | `npm run dev` starts, `npm run build` succeeds |
| 2 | TypeScript Types — `types/game.ts` | All interfaces match spec in docs/specs/schema-registry.md |
| 3 | TypeScript Types — `types/api.ts` | All WS message types and API types defined |
| 4 | API Client — `lib/api.ts` | Functions for all endpoints, error handling |
| 5 | WebSocket Client — `lib/websocket.ts` | Connect, disconnect, send, handlers, auto-reconnect |
| 6 | State Management — `lib/store.ts` | All actions defined, correct state shape |

### Medium Priority (UI)

| # | Item | What to Check |
|---|------|---------------|
| 7 | Layout & Styling — `app/layout.tsx` + dark theme | Dark bg, monospace font, responsive base |
| 8 | ChatPanel Component | Messages render, input works, streaming indicator, auto-scroll |
| 9 | CharacterPanel Component | Stats display, health/energy bars, status effects |
| 10 | InventoryPanel Component | Item list, equipment section, type color coding |
| 11 | LocationPanel Component | Location name/desc, connections, NPCs, items |
| 12 | StoryPanel Component | Premise, current beat, progress, beat list |
| 13 | Sidebar Component | Tab bar, panel switching, scrollable content |

### Medium Priority (Pages)

| # | Item | What to Check |
|---|------|---------------|
| 14 | Home Page — `app/page.tsx` | Session list, new game button, empty/loading/error states, delete |
| 15 | New Game Page — `app/new/page.tsx` | Form, validation, submit, redirect, error display |
| 16 | Play Page — `app/play/[sessionId]/page.tsx` | WS connect/disconnect, message routing, sidebar + chat layout |

### Medium Priority (Integration)

| # | Item | What to Check |
|---|------|---------------|
| 17 | WebSocket ↔ Store Integration | All message types wired, state updates flow correctly |

### Lower Priority (Docker)

| # | Item | What to Check |
|---|------|---------------|
| 18 | Docker Setup — Dockerfile + .dockerignore | `docker compose build frontend` succeeds |
| 19 | Docker Compose — frontend service | `docker compose up frontend` serves on 3000 |

### Wrap-up

| # | Item | What to Check |
|---|------|---------------|
| 20 | Final build + coverage check | `npm run build` clean, `npm test -- --coverage` meets 85% |

## Progress Checklist

- [x] 1. Project Setup — scaffold Next.js with TS + Tailwind
- [x] 2. TypeScript Types — types/game.ts
- [x] 3. TypeScript Types — types/api.ts
- [x] 4. API Client — lib/api.ts
- [x] 5. WebSocket Client — lib/websocket.ts
- [x] 6. State Management — lib/store.ts
- [ ] 7. Layout & Styling — app/layout.tsx + dark theme
- [ ] 8. ChatPanel Component
- [ ] 9. CharacterPanel Component
- [ ] 10. InventoryPanel Component
- [ ] 11. LocationPanel Component
- [ ] 12. StoryPanel Component
- [ ] 13. Sidebar Component
- [ ] 14. Home Page — app/page.tsx
- [ ] 15. New Game Page — app/new/page.tsx
- [ ] 16. Play Page — app/play/[sessionId]/page.tsx
- [ ] 17. WebSocket ↔ Store Integration
- [ ] 18. Docker Setup — Dockerfile + .dockerignore
- [ ] 19. Docker Compose — frontend service
- [ ] 20. Final build + coverage check

## Discoveries

- Fixed jest.config.js typo: `setupFilesAfterSetup` → `setupFilesAfterEnv` (correct Jest option name)

_Add rows to the Context Table when you find things the plan missed._

## Per-Item Process

1. Read the item description in this file and cross-reference docs/plans/ralph-b-frontend.md for details
2. Read any relevant spec files (docs/specs/schema-registry.md, docs/specs/api-layer.md, docs/specs/frontend.md)
3. Write failing tests first (RED) — specific assertions, not truthy checks
4. Write the minimum code to make tests pass (GREEN)
5. Run `npm test -- --coverage` and verify 85% on all metrics
6. Use the test-quality-verifier agent to audit test quality
7. Fix any issues found by the verifier
8. Check off the item in this file's Progress Checklist
9. Check off corresponding items in docs/plans/ralph-b-frontend.md
10. Commit with a descriptive message

## Rules

1. Read files before editing them — never blindly overwrite
2. One checklist item per iteration — finish it, commit, stop
3. Tests first — write the test, see it fail, then implement
4. Assertions must be specific — no bare truthy checks (see CLAUDE.md testing standards)
5. 85% coverage minimum on lines, branches, functions, statements
6. Tailwind utility classes only — no custom CSS files, no component libraries
7. TypeScript types must match backend Pydantic models from docs/specs/schema-registry.md
8. Keep components simple — no fancy animations or over-engineering
9. Use `any` sparingly — prefer proper types but don't block on it
10. If stuck for more than a few minutes on something, skip it and note it in Discoveries
