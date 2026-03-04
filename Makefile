.PHONY: help install dev dev-backend dev-frontend test test-unit test-frontend test-db test-all test-coverage lint build clean db-up db-down check-zombies kill-dev

# Default target - show help
help:
	@echo "Agentic RPG - Build Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies for both backend and frontend"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start all services via docker compose (live reload)"
	@echo "  make dev-backend      Start backend + Postgres only"
	@echo "  make dev-frontend     Start frontend only"
	@echo "  make db-up            Start Postgres via docker compose"
	@echo "  make db-down          Stop Postgres"
	@echo "  make check-zombies    Check for orphaned dev processes"
	@echo "  make kill-dev         Kill any orphaned dev processes"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run unit tests (backend + frontend, no DB required)"
	@echo "  make test-unit        Run backend unit tests only (no DB required)"
	@echo "  make test-frontend    Run frontend tests only"
	@echo "  make test-db          Start Postgres, run DB-dependent backend tests, stop Postgres"
	@echo "  make test-all         Run everything: unit tests, DB tests, frontend tests"
	@echo "  make test-coverage    Run all tests with coverage reports"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters for both backend and frontend"
	@echo ""
	@echo "Build:"
	@echo "  make build            Build both backend and frontend for production"
	@echo "  make clean            Remove build artifacts"

# Install dependencies
install:
	@echo "Installing backend dependencies..."
	cd backend && uv sync
	@echo ""
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo ""
	@echo "All dependencies installed"

# Database
db-up:
	@echo "Starting Postgres..."
	docker compose up -d postgres
	@echo "Waiting for Postgres to be healthy..."
	@until docker compose exec postgres pg_isready -U postgres > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Postgres is ready"

db-down:
	@echo "Stopping Postgres..."
	docker compose down postgres

# Development — all via docker compose with live reload
dev:
	@echo "Starting all services (Ctrl+C to stop)..."
	@echo "Postgres: localhost:5432"
	@echo "Backend:  http://localhost:8080 (live reload)"
	@echo "Frontend: http://localhost:3000 (hot reload)"
	@echo ""
	docker compose up --build

dev-backend:
	docker compose up --build backend postgres

dev-frontend:
	docker compose up --build frontend

# Testing - backend unit tests (no DB required)
test-unit:
	@echo "Running backend unit tests (no DB)..."
	cd backend && uv run pytest \
		tests/test_models/ \
		tests/test_tools/ \
		tests/test_agent/ \
		tests/test_llm/ \
		tests/test_events/test_bus.py \
		tests/test_events/test_schemas.py \
		tests/test_api/test_health.py \
		tests/test_api/test_websocket.py \
		--tb=short -q

# Testing - frontend
test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test

# Testing - unit tests (backend + frontend, no DB)
test: test-unit test-frontend
	@echo ""
	@echo "All unit tests passed"

# Testing - DB-dependent backend tests (spins up Postgres)
test-db:
	@echo "Starting Postgres for DB tests..."
	docker compose up -d postgres
	@until docker compose exec postgres pg_isready -U postgres > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "Running migrations..."
	cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_rpg uv run alembic upgrade head
	@echo "Running DB-dependent tests..."
	cd backend && DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agentic_rpg uv run pytest \
		tests/test_state/ \
		tests/test_events/test_persistence.py \
		tests/test_api/test_sessions.py \
		tests/test_api/test_game_state.py \
		tests/test_api/test_fixtures_smoke.py \
		tests/test_api/test_wiring.py \
		--tb=short -q; \
	TEST_EXIT=$$?; \
	echo "Stopping Postgres..."; \
	docker compose down; \
	exit $$TEST_EXIT

# Testing - everything
test-all: test-unit test-frontend test-db
	@echo ""
	@echo "All tests passed (unit + frontend + DB)"

# Testing - with coverage
test-coverage:
	@echo "Running backend tests with coverage (unit only, no DB)..."
	cd backend && uv run pytest \
		tests/test_models/ \
		tests/test_tools/ \
		tests/test_agent/ \
		tests/test_llm/ \
		tests/test_events/test_bus.py \
		tests/test_events/test_schemas.py \
		tests/test_api/test_health.py \
		tests/test_api/test_websocket.py \
		--cov=agentic_rpg --cov-branch --cov-report=term-missing
	@echo ""
	@echo "Running frontend tests with coverage..."
	cd frontend && npm run test -- --coverage
	@echo ""
	@echo "Coverage reports complete"

# Linting
lint:
	@echo "Running backend linters..."
	cd backend && uv run ruff check src/
	cd backend && uv run ruff format --check src/
	@echo ""
	@echo "Running frontend build check..."
	cd frontend && npm run build
	@echo ""
	@echo "All checks passed"

# Build
build:
	@echo "Building frontend..."
	cd frontend && npm run build
	@echo ""
	@echo "Building backend Docker image..."
	docker compose build backend
	@echo ""
	@echo "Build complete"

# Clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf frontend/.next
	rm -rf frontend/node_modules/.cache
	rm -rf backend/.pytest_cache
	rm -rf backend/htmlcov
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"

# Check for zombie processes
check-zombies:
	@echo "Checking for orphaned dev processes..."
	@lsof -ti:8080 > /dev/null 2>&1 && echo "Warning: Port 8080 is in use" || echo "Port 8080 is free"
	@lsof -ti:3000 > /dev/null 2>&1 && echo "Warning: Port 3000 is in use" || echo "Port 3000 is free"
	@lsof -ti:5432 > /dev/null 2>&1 && echo "Warning: Port 5432 is in use" || echo "Port 5432 is free"

# Kill orphaned dev processes
kill-dev:
	@echo "Killing orphaned dev processes..."
	@lsof -ti:8080 | xargs kill -9 2>/dev/null || echo "Port 8080 was already free"
	@lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "Port 3000 was already free"
	docker compose down 2>/dev/null || true
	@echo "Cleanup complete"
