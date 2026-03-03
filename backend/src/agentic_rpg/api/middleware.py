"""Custom error handling middleware and exception classes."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class GameError(Exception):
    """Application-level error with structured error response.

    Attributes:
        code: Machine-readable error code (e.g. "session_not_found").
        message: Human-readable error message.
        status_code: HTTP status code to return (default 400).
    """

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def game_error_handler(request: Request, exc: GameError) -> JSONResponse:
    """Handle GameError exceptions and return structured JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the app."""
    app.add_exception_handler(GameError, game_error_handler)
