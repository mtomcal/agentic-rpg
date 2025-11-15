"""Tests for schema versioning and migrations."""
import pytest
from agentic_rpg.models.versioning import SchemaVersion


class TestSchemaVersion:
    """Test schema version management."""

    def test_current_version_defined(self):
        """Test that current version is defined."""
        assert SchemaVersion.CURRENT is not None
        assert isinstance(SchemaVersion.CURRENT, str)
        assert SchemaVersion.CURRENT == "1.0.0"

    def test_minimum_compatible_version_defined(self):
        """Test that minimum compatible version is defined."""
        assert SchemaVersion.MINIMUM_COMPATIBLE is not None
        assert isinstance(SchemaVersion.MINIMUM_COMPATIBLE, str)
        assert SchemaVersion.MINIMUM_COMPATIBLE == "1.0.0"

    def test_migrate_same_version(self):
        """Test migration with same version returns unchanged state."""
        state = {"data": "test", "schema_version": "1.0.0"}
        result = SchemaVersion.migrate(state, "1.0.0", "1.0.0")
        assert result == state

    def test_migrate_updates_schema_version(self):
        """Test migration updates schema_version field."""
        state = {"data": "test", "schema_version": "0.9.0"}
        result = SchemaVersion.migrate(state, "0.9.0", "1.0.0")
        assert result["schema_version"] == "1.0.0"
        assert result["data"] == "test"

    def test_migration_registry_exists(self):
        """Test that migration registry exists."""
        assert hasattr(SchemaVersion, "_migrations")
        assert isinstance(SchemaVersion._migrations, dict)

    def test_register_migration_decorator(self):
        """Test migration registration decorator."""
        # Clear any existing test migrations
        test_key = ("1.0.0", "1.1.0")
        if test_key in SchemaVersion._migrations:
            del SchemaVersion._migrations[test_key]

        @SchemaVersion.register_migration("1.0.0", "1.1.0")
        def test_migration(state: dict) -> dict:
            state["migrated"] = True
            return state

        # Verify migration was registered
        assert test_key in SchemaVersion._migrations
        assert SchemaVersion._migrations[test_key] == test_migration

        # Clean up
        del SchemaVersion._migrations[test_key]
