# Agentic RPG

A browser-based, single-player role-playing game where narrative, world state, and character interactions are dynamically generated and managed by LLM agents using LangGraph.

## Project Status

**Current Phase**: Phase 1 Complete - Foundation Setup
- Backend: FastAPI with state management and OpenAPI documentation
- Frontend: Next.js 16 with TypeScript, Tailwind CSS v4, and comprehensive testing

**Architecture**: Modular, interface-first design enabling parallel development across multiple teams

## Quick Start

### Prerequisites

- **Backend**: Python 3.11+, Poetry
- **Frontend**: Node.js 20+, npm
- **Optional**: Docker & Docker Compose

### Development Setup

#### Backend (FastAPI)

```bash
cd backend
poetry install
poetry run poe dev
# Backend runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

#### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
# Frontend runs at http://localhost:3000
```

#### Docker Compose (Full Stack)

```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## Project Structure

```
agentic-rpg/
├── backend/                    # FastAPI backend
│   ├── src/agentic_rpg/
│   │   ├── models/            # Pydantic data models
│   │   ├── services/          # Business logic
│   │   ├── agents/            # LangGraph agents and tools
│   │   └── api/               # FastAPI routes
│   ├── tests/                 # Backend tests
│   └── pyproject.toml
│
├── frontend/                   # Next.js frontend
│   ├── app/                   # Next.js App Router
│   ├── lib/                   # Utilities and API client
│   ├── scripts/               # Build and type generation scripts
│   └── package.json
│
├── PRD.md                     # Product Requirements Document
├── CLAUDE.md                  # AI Agent Development Instructions
└── README.md                  # This file
```

## Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **Pydantic** - Data validation and serialization
- **LangGraph** - Agent orchestration (planned)
- **Poetry** - Dependency management
- **pytest** - Testing framework

### Frontend
- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript 5** - Type safety
- **Tailwind CSS 4** - Utility-first CSS
- **Zustand** - State management
- **Vitest** - Unit testing
- **Playwright** - E2E testing

### Type Safety
- **OpenAPI** - API specification
- **openapi-typescript** - Type generation from OpenAPI specs
- Shared types between backend and frontend

## Documentation

- **[PRD.md](./PRD.md)** - Complete product requirements, architecture, and development roadmap
- **[CLAUDE.md](./CLAUDE.md)** - Development guidelines, TDD workflow, and readyq task management
- **[Frontend README](./frontend/README.md)** - Frontend-specific documentation, testing, and API integration

## Development Workflow

### Task Management

This project uses **readyq** for task tracking:

```bash
./readyq.py ready       # View actionable tasks
./readyq.py list        # View all tasks
./readyq.py show <id>   # View task details
./readyq.py web         # Launch web UI
```

### Test-Driven Development (TDD)

**Required workflow for all development:**

1. Write a failing test
2. Run test to confirm it fails
3. Implement minimal code to pass
4. Run test to confirm it passes
5. Refactor while keeping tests green
6. Log progress with `./readyq.py update <id> --log "message"`

### Type Generation

Keep frontend types in sync with backend:

```bash
# 1. Ensure backend is running
cd backend && poetry run poe dev

# 2. Generate frontend types
cd frontend && npm run generate-types
```

This generates TypeScript types from the backend's OpenAPI specification.

## Testing

### Backend Tests

```bash
cd backend
poetry run pytest                    # Run all tests
poetry run pytest --cov             # With coverage
poetry run pytest tests/unit/       # Unit tests only
```

### Frontend Tests

```bash
cd frontend
npm run test                        # Unit tests (Vitest)
npm run test:e2e                    # E2E tests (Playwright)
npm run lint                        # Linting
npm run type-check                  # TypeScript checks
```

## Code Quality

### Backend
```bash
cd backend
poetry run ruff check .             # Linting
poetry run ruff format .            # Formatting
poetry run mypy src/                # Type checking
```

### Frontend
```bash
cd frontend
npm run lint                        # ESLint
npm run type-check                  # TypeScript compiler
```

## Development Guidelines

### Interface Stability

- **Never change interfaces without explicit permission**
- Only non-breaking changes allowed (new optional params, new methods)
- Breaking changes require discussion and approval
- All interfaces validated by automated contract tests

### Git Workflow

- **Branch naming**: `feature/<task-description>`, `fix/<bug-description>`
- **Commits**: Descriptive messages following conventional commit style
- **Testing**: All tests must pass before merging
- **Code review**: Required for interface changes

### Team Ownership

```
Backend:
  /backend/src/agentic_rpg/models/     → @team-core
  /backend/src/agentic_rpg/services/   → @team-core
  /backend/src/agentic_rpg/agents/     → @team-agents
  /backend/src/agentic_rpg/api/        → @team-api

Frontend:
  /frontend/app/                       → @team-frontend
  /frontend/lib/                       → @team-frontend

Shared:
  /frontend/lib/api/generated/         → Generated (don't edit)
  CLAUDE.md, PRD.md                    → All teams
```

## API Integration

The frontend communicates with the backend through a type-safe API client:

```typescript
// Frontend (TypeScript)
import { apiClient } from '@/lib/api/client';

const health = await apiClient.healthCheck();
// Types are automatically generated from backend OpenAPI spec
```

Backend endpoints are documented at `http://localhost:8000/docs` when running.

## Environment Configuration

### Backend (.env)

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# LLM Configuration (future)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Frontend (.env.local)

```env
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Roadmap

### Completed
- ✅ Phase 1: Foundation Setup
  - Backend API structure
  - Frontend Next.js setup
  - Type generation pipeline
  - Testing infrastructure

### In Progress
- Phase 2: Core Game Loop
  - Character creation
  - State management
  - Agent integration

### Upcoming
- Phase 3: Game Systems (inventory, location, travel)
- Phase 4: Event & Messaging (WebSocket, real-time updates)
- Phase 5: Advanced Features (combat, NPCs, complex agents)
- Phase 6: Polish & Production (deployment, monitoring, optimization)

See [PRD.md](./PRD.md) for detailed phase breakdown and task assignments.

## Troubleshooting

### Type Generation Fails

**Issue**: Frontend type generation cannot connect to backend

**Solution**:
```bash
# Ensure backend is running
cd backend && poetry run poe dev

# Verify health endpoint
curl http://localhost:8000/api/health/

# Then generate types
cd frontend && npm run generate-types
```

### Port Conflicts

**Issue**: Port 3000 or 8000 already in use

**Solution**:
```bash
# Find and kill process on port
lsof -ti:3000 | xargs kill -9   # Frontend
lsof -ti:8000 | xargs kill -9   # Backend
```

### Test Failures

**Issue**: Tests failing after changes

**Solution**:
1. Ensure you followed TDD (test first, then implementation)
2. Check if interface contracts were violated
3. Verify dependencies are installed (`poetry install` / `npm install`)
4. Clear caches and rebuild:
   ```bash
   # Backend
   cd backend && rm -rf .pytest_cache && poetry install

   # Frontend
   cd frontend && rm -rf .next node_modules && npm install
   ```

## Contributing

1. Check `./readyq.py ready` for available tasks
2. Follow TDD workflow (test first, always)
3. Maintain interface stability (no breaking changes)
4. Update documentation with changes
5. Ensure all tests pass before committing
6. Log progress with readyq session logs

For detailed contribution guidelines, see [CLAUDE.md](./CLAUDE.md).

## Resources

- **Product Spec**: [PRD.md](./PRD.md) - Complete requirements and architecture
- **Development Guide**: [CLAUDE.md](./CLAUDE.md) - TDD, readyq, and guidelines
- **Frontend Docs**: [frontend/README.md](./frontend/README.md) - Frontend-specific details
- **API Docs**: http://localhost:8000/docs (when backend running)

## License

[To be determined]

## Contact

For questions or issues, refer to the PRD.md for team ownership and contact information.
