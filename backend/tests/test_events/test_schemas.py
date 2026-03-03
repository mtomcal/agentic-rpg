"""Tests for EventPayloadRegistry — registration, lookup, validation."""

import pytest
from pydantic import ValidationError

from agentic_rpg.events.schemas import EventPayloadRegistry
from agentic_rpg.models.events import (
    EventPayload,
    LocationChangedPayload,
    StatChangedPayload,
)


class TestRegisterAndLookup:
    """EventPayloadRegistry.register and payload_for."""

    def test_register_then_lookup_returns_model(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        assert registry.payload_for("character.stat_changed") is StatChangedPayload

    def test_lookup_unregistered_returns_none(self):
        registry = EventPayloadRegistry()
        assert registry.payload_for("unknown.type") is None

    def test_register_overwrites_previous(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        registry.register("character.stat_changed", LocationChangedPayload)
        assert registry.payload_for("character.stat_changed") is LocationChangedPayload

    def test_register_multiple_types(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        registry.register("world.location_changed", LocationChangedPayload)
        assert registry.payload_for("character.stat_changed") is StatChangedPayload
        assert registry.payload_for("world.location_changed") is LocationChangedPayload


class TestValidatePayload:
    """EventPayloadRegistry.validate_payload."""

    def test_validate_valid_payload(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        result = registry.validate_payload(
            "character.stat_changed",
            {"stat_name": "health", "old_value": 100, "new_value": 80},
        )
        assert isinstance(result, StatChangedPayload)
        assert result.stat_name == "health"
        assert result.old_value == 100.0
        assert result.new_value == 80.0

    def test_validate_unregistered_type_raises_key_error(self):
        registry = EventPayloadRegistry()
        with pytest.raises(KeyError, match="No payload model registered"):
            registry.validate_payload("unknown.type", {"foo": "bar"})

    def test_validate_invalid_payload_raises_validation_error(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        with pytest.raises(ValidationError):
            registry.validate_payload("character.stat_changed", {"bad": "data"})


class TestRegisteredTypes:
    """EventPayloadRegistry.registered_types and is_registered."""

    def test_empty_registry_returns_empty_list(self):
        registry = EventPayloadRegistry()
        assert registry.registered_types() == []

    def test_registered_types_returns_all(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        registry.register("world.location_changed", LocationChangedPayload)
        types = registry.registered_types()
        assert set(types) == {"character.stat_changed", "world.location_changed"}

    def test_is_registered_true(self):
        registry = EventPayloadRegistry()
        registry.register("character.stat_changed", StatChangedPayload)
        assert registry.is_registered("character.stat_changed") is True

    def test_is_registered_false(self):
        registry = EventPayloadRegistry()
        assert registry.is_registered("unknown.type") is False
