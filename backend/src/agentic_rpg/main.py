"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic_rpg.api.middleware import register_error_handlers
from agentic_rpg.api.routes import register_routes
from agentic_rpg.db import close_pool, create_pool
from agentic_rpg.events.bus import EventBus
from agentic_rpg.events.persistence import EventPersistence


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    app.state.db_pool = await create_pool()
    app.state.event_bus = EventBus()
    app.state.event_persistence = EventPersistence(app.state.db_pool)
    yield
    await close_pool(app.state.db_pool)


app = FastAPI(title="Agentic RPG", version="0.1.0", lifespan=lifespan)
register_routes(app)
register_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
