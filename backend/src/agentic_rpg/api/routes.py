"""Route registration for the FastAPI application."""

from fastapi import FastAPI

from agentic_rpg.api.handlers import router as session_router


def register_routes(app: FastAPI) -> None:
    """Register all API routers on the FastAPI application."""
    app.include_router(session_router)
