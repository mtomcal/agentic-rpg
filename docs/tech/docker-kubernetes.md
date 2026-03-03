# Technology Choice: Docker & Kubernetes

## Decision

Use Docker Compose for local development. Design for Kubernetes deployment in production.

## Rationale

- **Learning goal**: Gain hands-on Kubernetes experience with a real application
- **Docker Compose**: Simple multi-container development environment (Python/FastAPI server + Postgres + frontend)
- **Kubernetes-ready**: Design choices (environment config, health checks, stateless server, external database) make the FastAPI server K8s-compatible from day one
- **Progressive deployment**: Start with Docker Compose → deploy to a single-node K8s cluster → scale as needed

## Docker Compose (Development)

```yaml
# docker-compose.yml
services:
  server:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://rpg:rpg@postgres:5432/agentic_rpg
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=debug
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=rpg
      - POSTGRES_PASSWORD=rpg
      - POSTGRES_DB=agentic_rpg
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rpg"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### Development Workflow

```bash
# Start everything
docker compose up -d

# Start with rebuild
docker compose up -d --build

# View logs
docker compose logs -f server

# Run backend tests
docker compose exec server uv run pytest

# Run migrations
docker compose exec server uv run alembic upgrade head

# Stop everything
docker compose down

# Stop and wipe data
docker compose down -v
```

## Dockerfiles

### Backend

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

## Kubernetes (Production)

### Design Principles for K8s

The application is designed to be K8s-friendly:

- **Stateless server**: All state is in PostgreSQL. Any server instance can handle any request.
- **Environment-based config**: All configuration via environment variables (12-factor app)
- **Health endpoints**: `/api/health` for liveness and readiness probes
- **Graceful shutdown**: Handle SIGTERM, drain WebSocket connections, finish in-flight requests (uvicorn handles SIGTERM natively)
- **Lightweight container**: Python slim image with only production dependencies

### Python-Specific K8s Considerations

- **Workers**: Use `gunicorn` with `uvicorn` workers in production for multi-process handling: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
- **Resource limits**: Python processes use more memory than compiled languages. Set memory limits accordingly (256–512 MB per pod as a starting point).
- **Startup time**: Python app startup is slower than compiled binaries. Set appropriate `initialDelaySeconds` on readiness probes.
- **WebSocket affinity**: WebSocket connections are long-lived. Use session affinity (sticky sessions) on the Ingress to keep a client connected to the same pod.

### K8s Resources (Future)

When deploying to Kubernetes:

- **Deployment**: FastAPI server (2+ replicas for availability)
- **Service**: ClusterIP service for the FastAPI server
- **Ingress**: Route external traffic to the service (with TLS)
- **StatefulSet or Operator**: PostgreSQL (CloudNativePG operator recommended)
- **ConfigMap**: Non-secret configuration
- **Secret**: API keys, database credentials
- **HPA**: Horizontal Pod Autoscaler based on CPU/connections

### K8s Learning Path

1. **Start local**: Docker Compose for development
2. **Single-node K8s**: Deploy to minikube or kind for learning
3. **Managed K8s**: Deploy to a cloud provider (GKE, EKS, or DigitalOcean K8s) for production
4. **Helm charts**: Package the deployment as a Helm chart for repeatability

This progression is not needed immediately. The application runs fine in Docker Compose. Kubernetes is a future deployment target.

## Future Extensions

- **CI/CD pipeline**: Build images and deploy to K8s on merge to main
- **Monitoring**: Prometheus + Grafana for metrics
- **Log aggregation**: Loki or ELK for centralized logging
- **Database backups**: Automated Postgres backups with retention
