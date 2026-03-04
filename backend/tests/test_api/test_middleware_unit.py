"""Unit tests for middleware — GameError and register_error_handlers."""

from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from agentic_rpg.api.middleware import GameError, game_error_handler, register_error_handlers


# ---------------------------------------------------------------------------
# GameError
# ---------------------------------------------------------------------------


class TestGameError:
    def test_code_attribute(self):
        err = GameError(code="session_not_found", message="Session not found")
        assert err.code == "session_not_found"

    def test_message_attribute(self):
        err = GameError(code="session_not_found", message="Session not found")
        assert err.message == "Session not found"

    def test_default_status_code_is_400(self):
        err = GameError(code="bad_request", message="Bad request")
        assert err.status_code == 400

    def test_custom_status_code(self):
        err = GameError(code="not_found", message="Not found", status_code=404)
        assert err.status_code == 404

    def test_is_exception(self):
        err = GameError(code="some_error", message="Some error")
        assert isinstance(err, Exception)

    def test_str_is_message(self):
        """GameError calls super().__init__(message) so str(err) == message."""
        err = GameError(code="some_error", message="Human readable message")
        assert str(err) == "Human readable message"

    def test_500_status_code(self):
        err = GameError(code="server_error", message="Internal error", status_code=500)
        assert err.status_code == 500
        assert err.code == "server_error"
        assert err.message == "Internal error"


# ---------------------------------------------------------------------------
# game_error_handler
# ---------------------------------------------------------------------------


class TestGameErrorHandler:
    async def test_returns_json_response(self):
        err = GameError(code="test_error", message="Test message", status_code=400)
        mock_request = MagicMock()

        response = await game_error_handler(mock_request, err)

        assert isinstance(response, JSONResponse)

    async def test_response_status_code_matches_error(self):
        err = GameError(code="not_found", message="Not here", status_code=404)
        mock_request = MagicMock()

        response = await game_error_handler(mock_request, err)

        assert response.status_code == 404

    async def test_response_body_contains_code_and_message(self):
        import json
        err = GameError(code="session_expired", message="Session has expired", status_code=410)
        mock_request = MagicMock()

        response = await game_error_handler(mock_request, err)

        body = json.loads(response.body)
        assert body["error"]["code"] == "session_expired"
        assert body["error"]["message"] == "Session has expired"

    async def test_response_400(self):
        import json
        err = GameError(code="invalid_action", message="Action not allowed")
        mock_request = MagicMock()

        response = await game_error_handler(mock_request, err)

        assert response.status_code == 400
        body = json.loads(response.body)
        assert body["error"]["code"] == "invalid_action"


# ---------------------------------------------------------------------------
# register_error_handlers — integration via mini FastAPI app
# ---------------------------------------------------------------------------


class TestRegisterErrorHandlers:
    async def test_register_adds_handler_for_game_error(self):
        """After register_error_handlers, GameError is caught and returns structured JSON."""
        mini_app = FastAPI()
        register_error_handlers(mini_app)

        @mini_app.get("/boom")
        async def boom():
            raise GameError(code="test_boom", message="Boom!", status_code=422)

        async with AsyncClient(
            transport=ASGITransport(app=mini_app),
            base_url="http://test",
        ) as ac:
            response = await ac.get("/boom")

        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "test_boom"
        assert data["error"]["message"] == "Boom!"

    async def test_register_handles_500_game_error(self):
        """GameError with status_code=500 is handled and returns 500."""
        mini_app = FastAPI()
        register_error_handlers(mini_app)

        @mini_app.get("/server-error")
        async def server_error():
            raise GameError(code="internal", message="Something broke", status_code=500)

        async with AsyncClient(
            transport=ASGITransport(app=mini_app),
            base_url="http://test",
        ) as ac:
            response = await ac.get("/server-error")

        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "internal"

    async def test_normal_routes_unaffected(self):
        """Routes that don't raise GameError still work normally."""
        mini_app = FastAPI()
        register_error_handlers(mini_app)

        @mini_app.get("/ok")
        async def ok():
            return {"status": "fine"}

        async with AsyncClient(
            transport=ASGITransport(app=mini_app),
            base_url="http://test",
        ) as ac:
            response = await ac.get("/ok")

        assert response.status_code == 200
        assert response.json() == {"status": "fine"}
