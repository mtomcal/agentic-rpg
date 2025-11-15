"""Tests for character models."""
import pytest
from pydantic import ValidationError

from agentic_rpg.models.character import Character, CharacterStats


class TestCharacterStats:
    """Test CharacterStats model."""

    def test_valid_character_stats(self):
        """Test creating valid character stats."""
        stats = CharacterStats(
            health=100,
            max_health=100,
            energy=50,
            max_energy=50,
            money=1000
        )
        assert stats.health == 100
        assert stats.max_health == 100
        assert stats.energy == 50
        assert stats.max_energy == 50
        assert stats.money == 1000

    def test_character_stats_default_money(self):
        """Test default money value."""
        stats = CharacterStats(
            health=100,
            max_health=100,
            energy=50,
            max_energy=50
        )
        assert stats.money == 0

    def test_character_stats_health_must_be_non_negative(self):
        """Test that health cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterStats(
                health=-1,
                max_health=100,
                energy=50,
                max_energy=50
            )
        assert "health" in str(exc_info.value)

    def test_character_stats_max_health_must_be_positive(self):
        """Test that max_health must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterStats(
                health=0,
                max_health=0,
                energy=50,
                max_energy=50
            )
        assert "max_health" in str(exc_info.value)

    def test_character_stats_energy_must_be_non_negative(self):
        """Test that energy cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterStats(
                health=100,
                max_health=100,
                energy=-5,
                max_energy=50
            )
        assert "energy" in str(exc_info.value)

    def test_character_stats_money_cannot_be_negative(self):
        """Test that money cannot be negative."""
        with pytest.raises(ValidationError) as exc_info:
            CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50,
                money=-100
            )
        assert "money" in str(exc_info.value)

    def test_character_stats_json_schema_extra(self):
        """Test that JSON schema examples are defined."""
        schema = CharacterStats.model_json_schema()
        assert "examples" in schema
        assert len(schema["examples"]) > 0


class TestCharacter:
    """Test Character model."""

    def test_valid_character(self):
        """Test creating valid character."""
        char = Character(
            id="char_123",
            name="Jax",
            profession="Space Pirate",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50,
                money=1000
            ),
            location="cantina_001",
            status=["well_rested"]
        )
        assert char.id == "char_123"
        assert char.name == "Jax"
        assert char.profession == "Space Pirate"
        assert char.stats.health == 100
        assert char.location == "cantina_001"
        assert char.status == ["well_rested"]

    def test_character_default_status(self):
        """Test default status is empty list."""
        char = Character(
            id="char_123",
            name="Jax",
            profession="Space Pirate",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50
            ),
            location="cantina_001"
        )
        assert char.status == []

    def test_character_name_min_length(self):
        """Test that name must be at least 1 character."""
        with pytest.raises(ValidationError) as exc_info:
            Character(
                id="char_123",
                name="",
                profession="Space Pirate",
                stats=CharacterStats(
                    health=100,
                    max_health=100,
                    energy=50,
                    max_energy=50
                ),
                location="cantina_001"
            )
        assert "name" in str(exc_info.value)

    def test_character_name_max_length(self):
        """Test that name cannot exceed 50 characters."""
        with pytest.raises(ValidationError) as exc_info:
            Character(
                id="char_123",
                name="a" * 51,
                profession="Space Pirate",
                stats=CharacterStats(
                    health=100,
                    max_health=100,
                    energy=50,
                    max_energy=50
                ),
                location="cantina_001"
            )
        assert "name" in str(exc_info.value)

    def test_character_json_schema_extra(self):
        """Test that JSON schema examples are defined."""
        schema = Character.model_json_schema()
        assert "examples" in schema
        assert len(schema["examples"]) > 0

    def test_character_serialization(self):
        """Test character can be serialized to JSON."""
        char = Character(
            id="char_123",
            name="Jax",
            profession="Space Pirate",
            stats=CharacterStats(
                health=100,
                max_health=100,
                energy=50,
                max_energy=50,
                money=1000
            ),
            location="cantina_001",
            status=["well_rested"]
        )
        json_data = char.model_dump()
        assert json_data["id"] == "char_123"
        assert json_data["name"] == "Jax"
        assert json_data["stats"]["health"] == 100

    def test_character_deserialization(self):
        """Test character can be deserialized from JSON."""
        data = {
            "id": "char_123",
            "name": "Jax",
            "profession": "Space Pirate",
            "stats": {
                "health": 100,
                "max_health": 100,
                "energy": 50,
                "max_energy": 50,
                "money": 1000
            },
            "location": "cantina_001",
            "status": ["well_rested"]
        }
        char = Character(**data)
        assert char.id == "char_123"
        assert char.name == "Jax"
        assert char.stats.health == 100
