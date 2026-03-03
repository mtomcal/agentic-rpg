"""Tests for all Pydantic models — Phase 1."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from agentic_rpg.models.character import Character, StatusEffect, StatusEffectType
from agentic_rpg.models.events import (
    BeatResolvedPayload,
    EventPayload,
    GameEvent,
    ItemAcquiredPayload,
    ItemRemovedPayload,
    LocationChangedPayload,
    StatChangedPayload,
)
from agentic_rpg.models.game_state import (
    Conversation,
    GameState,
    Message,
    MessageRole,
    Session,
    SessionStatus,
)
from agentic_rpg.models.inventory import Inventory, Item, ItemType
from agentic_rpg.models.story import (
    AdaptationRecord,
    BeatFlexibility,
    BeatStatus,
    StoryBeat,
    StoryOutline,
    StoryState,
)
from agentic_rpg.models.world import Location, World
from agentic_rpg.models.api import (
    AgentResponseMessage,
    CharacterCreate,
    DeleteResponse,
    ErrorResponse,
    HealthResponse,
    PlayerActionRequest,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
    SessionListResponse,
    SessionSummary,
    StateUpdateMessage,
)


# ──────────────────────────────────────────────
# StrEnum tests
# ──────────────────────────────────────────────


class TestStatusEffectType:
    def test_values(self):
        assert StatusEffectType.buff == "buff"
        assert StatusEffectType.debuff == "debuff"
        assert StatusEffectType.condition == "condition"

    def test_all_values_present(self):
        assert set(StatusEffectType) == {"buff", "debuff", "condition"}


class TestItemType:
    def test_values(self):
        assert ItemType.weapon == "weapon"
        assert ItemType.armor == "armor"
        assert ItemType.consumable == "consumable"
        assert ItemType.key == "key"
        assert ItemType.misc == "misc"

    def test_all_values_present(self):
        assert set(ItemType) == {"weapon", "armor", "consumable", "key", "misc"}


class TestSessionStatus:
    def test_values(self):
        assert SessionStatus.active == "active"
        assert SessionStatus.paused == "paused"
        assert SessionStatus.completed == "completed"
        assert SessionStatus.abandoned == "abandoned"

    def test_all_values_present(self):
        assert set(SessionStatus) == {"active", "paused", "completed", "abandoned"}


class TestMessageRole:
    def test_values(self):
        assert MessageRole.player == "player"
        assert MessageRole.agent == "agent"
        assert MessageRole.system == "system"

    def test_all_values_present(self):
        assert set(MessageRole) == {"player", "agent", "system"}


class TestBeatStatus:
    def test_values(self):
        assert BeatStatus.planned == "planned"
        assert BeatStatus.active == "active"
        assert BeatStatus.resolved == "resolved"
        assert BeatStatus.skipped == "skipped"
        assert BeatStatus.adapted == "adapted"

    def test_all_values_present(self):
        assert set(BeatStatus) == {"planned", "active", "resolved", "skipped", "adapted"}


class TestBeatFlexibility:
    def test_values(self):
        assert BeatFlexibility.fixed == "fixed"
        assert BeatFlexibility.flexible == "flexible"
        assert BeatFlexibility.optional == "optional"

    def test_all_values_present(self):
        assert set(BeatFlexibility) == {"fixed", "flexible", "optional"}


# ──────────────────────────────────────────────
# Character models
# ──────────────────────────────────────────────


class TestStatusEffect:
    def test_create_with_required_fields(self):
        effect = StatusEffect(name="Poison", effect_type=StatusEffectType.debuff)
        assert effect.name == "Poison"
        assert effect.effect_type == StatusEffectType.debuff
        assert effect.description == ""
        assert effect.duration is None
        assert effect.magnitude == 1.0

    def test_create_with_all_fields(self):
        effect = StatusEffect(
            name="Strength",
            effect_type=StatusEffectType.buff,
            description="Increases attack power",
            duration=5,
            magnitude=2.0,
        )
        assert effect.name == "Strength"
        assert effect.duration == 5
        assert effect.magnitude == 2.0

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            StatusEffect(effect_type=StatusEffectType.buff)
        assert "name" in str(exc_info.value)

    def test_serialization_roundtrip(self):
        effect = StatusEffect(name="Regen", effect_type=StatusEffectType.buff, magnitude=1.5)
        data = effect.model_dump()
        restored = StatusEffect(**data)
        assert restored.name == "Regen"
        assert restored.magnitude == 1.5
        assert restored.effect_type == StatusEffectType.buff


class TestCharacter:
    def test_defaults(self):
        char = Character(name="Aldric", profession="Warrior")
        assert char.name == "Aldric"
        assert char.profession == "Warrior"
        assert char.background == ""
        assert char.stats["health"] == 100.0
        assert char.stats["max_health"] == 100.0
        assert char.stats["energy"] == 100.0
        assert char.stats["max_energy"] == 100.0
        assert char.stats["money"] == 0.0
        assert char.status_effects == []
        assert char.level == 1
        assert char.experience == 0
        assert char.location_id == "start"
        assert isinstance(char.id, UUID)

    def test_custom_stats(self):
        char = Character(
            name="Mage",
            profession="Sorcerer",
            stats={"health": 60.0, "max_health": 60.0, "energy": 150.0, "max_energy": 150.0, "money": 50.0},
        )
        assert char.stats["health"] == 60.0
        assert char.stats["energy"] == 150.0

    def test_level_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            Character(name="Test", profession="Test", level=0)
        assert "level" in str(exc_info.value)

    def test_experience_must_be_nonneg(self):
        with pytest.raises(ValidationError) as exc_info:
            Character(name="Test", profession="Test", experience=-1)
        assert "experience" in str(exc_info.value)

    def test_with_status_effects(self):
        effect = StatusEffect(name="Shield", effect_type=StatusEffectType.buff)
        char = Character(name="Tank", profession="Knight", status_effects=[effect])
        assert len(char.status_effects) == 1
        assert char.status_effects[0].name == "Shield"

    def test_serialization_roundtrip(self):
        char = Character(name="Aldric", profession="Warrior", level=5)
        data = char.model_dump()
        restored = Character(**data)
        assert restored.name == "Aldric"
        assert restored.level == 5
        assert restored.id == char.id

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            Character(profession="Warrior")

    def test_missing_profession_raises(self):
        with pytest.raises(ValidationError):
            Character(name="Aldric")


# ──────────────────────────────────────────────
# Inventory models
# ──────────────────────────────────────────────


class TestItem:
    def test_create_item(self):
        item = Item(name="Iron Sword", item_type=ItemType.weapon)
        assert item.name == "Iron Sword"
        assert item.item_type == ItemType.weapon
        assert item.quantity == 1
        assert item.description == ""
        assert item.properties == {}
        assert isinstance(item.id, UUID)

    def test_item_with_properties(self):
        item = Item(
            name="Health Potion",
            item_type=ItemType.consumable,
            quantity=5,
            properties={"heal_amount": 50},
        )
        assert item.quantity == 5
        assert item.properties["heal_amount"] == 50

    def test_quantity_must_be_positive(self):
        with pytest.raises(ValidationError) as exc_info:
            Item(name="Bad", item_type=ItemType.misc, quantity=0)
        assert "quantity" in str(exc_info.value)

    def test_missing_item_type_raises(self):
        with pytest.raises(ValidationError):
            Item(name="Broken")

    def test_invalid_item_type_raises(self):
        with pytest.raises(ValidationError):
            Item(name="Test", item_type="invalid_type")

    def test_serialization_roundtrip(self):
        item = Item(name="Key", item_type=ItemType.key, quantity=1)
        data = item.model_dump()
        restored = Item(**data)
        assert restored.name == "Key"
        assert restored.item_type == ItemType.key


class TestInventory:
    def test_empty_defaults(self):
        inv = Inventory()
        assert inv.items == []
        assert inv.equipment == {}
        assert inv.capacity is None

    def test_with_items(self):
        item = Item(name="Shield", item_type=ItemType.armor)
        inv = Inventory(items=[item])
        assert len(inv.items) == 1
        assert inv.items[0].name == "Shield"

    def test_with_equipment(self):
        item_id = uuid4()
        inv = Inventory(equipment={"weapon": item_id, "armor": None})
        assert inv.equipment["weapon"] == item_id
        assert inv.equipment["armor"] is None

    def test_with_capacity(self):
        inv = Inventory(capacity=20)
        assert inv.capacity == 20

    def test_serialization_roundtrip(self):
        item = Item(name="Ring", item_type=ItemType.misc)
        inv = Inventory(items=[item], capacity=10)
        data = inv.model_dump()
        restored = Inventory(**data)
        assert len(restored.items) == 1
        assert restored.capacity == 10


# ──────────────────────────────────────────────
# World models
# ──────────────────────────────────────────────


class TestLocation:
    def test_create(self):
        loc = Location(id="tavern", name="The Rusty Nail")
        assert loc.id == "tavern"
        assert loc.name == "The Rusty Nail"
        assert loc.description == ""
        assert loc.connections == []
        assert loc.npcs_present == []
        assert loc.items_present == []
        assert loc.visited is False

    def test_full_fields(self):
        loc = Location(
            id="market",
            name="Market Square",
            description="A bustling marketplace",
            connections=["tavern", "gate"],
            npcs_present=["merchant"],
            items_present=["apple"],
            visited=True,
        )
        assert loc.connections == ["tavern", "gate"]
        assert loc.npcs_present == ["merchant"]
        assert loc.visited is True

    def test_missing_id_raises(self):
        with pytest.raises(ValidationError):
            Location(name="NoID")

    def test_serialization_roundtrip(self):
        loc = Location(id="forest", name="Dark Forest", visited=True)
        data = loc.model_dump()
        restored = Location(**data)
        assert restored.id == "forest"
        assert restored.visited is True


class TestWorld:
    def test_defaults(self):
        world = World()
        assert world.locations == {}
        assert world.current_location_id == "start"
        assert world.discovered_locations == set()
        assert world.world_flags == {}

    def test_with_locations(self):
        loc = Location(id="start", name="Village")
        world = World(
            locations={"start": loc},
            current_location_id="start",
            discovered_locations={"start"},
        )
        assert "start" in world.locations
        assert world.locations["start"].name == "Village"
        assert "start" in world.discovered_locations

    def test_serialization_roundtrip(self):
        loc = Location(id="start", name="Village")
        world = World(locations={"start": loc}, discovered_locations={"start"})
        data = world.model_dump()
        restored = World(**data)
        assert "start" in restored.locations
        assert "start" in restored.discovered_locations


# ──────────────────────────────────────────────
# Story models
# ──────────────────────────────────────────────


class TestStoryBeat:
    def test_defaults(self):
        beat = StoryBeat(summary="The hero arrives at the village")
        assert beat.summary == "The hero arrives at the village"
        assert beat.location == "any"
        assert beat.trigger_conditions == []
        assert beat.key_elements == []
        assert beat.player_objectives == []
        assert beat.possible_outcomes == []
        assert beat.flexibility == BeatFlexibility.flexible
        assert beat.status == BeatStatus.planned

    def test_full_beat(self):
        beat = StoryBeat(
            summary="Boss fight",
            location="dungeon",
            trigger_conditions=["has_key"],
            key_elements=["dragon"],
            player_objectives=["defeat dragon"],
            possible_outcomes=["victory", "defeat"],
            flexibility=BeatFlexibility.fixed,
            status=BeatStatus.active,
        )
        assert beat.location == "dungeon"
        assert beat.flexibility == BeatFlexibility.fixed
        assert beat.status == BeatStatus.active
        assert len(beat.possible_outcomes) == 2

    def test_missing_summary_raises(self):
        with pytest.raises(ValidationError):
            StoryBeat()


class TestAdaptationRecord:
    def test_create(self):
        rec = AdaptationRecord(reason="Player went off script", changes="Added new beat")
        assert rec.reason == "Player went off script"
        assert rec.changes == "Added new beat"
        assert isinstance(rec.timestamp, datetime)

    def test_missing_fields_raises(self):
        with pytest.raises(ValidationError):
            AdaptationRecord(reason="Only reason")


class TestStoryOutline:
    def test_create(self):
        outline = StoryOutline(premise="A hero's journey", setting="Medieval fantasy")
        assert outline.premise == "A hero's journey"
        assert outline.setting == "Medieval fantasy"
        assert outline.beats == []

    def test_with_beats(self):
        beat = StoryBeat(summary="Intro")
        outline = StoryOutline(premise="Test", setting="Test", beats=[beat])
        assert len(outline.beats) == 1
        assert outline.beats[0].summary == "Intro"


class TestStoryState:
    def test_defaults(self):
        state = StoryState()
        assert state.outline is None
        assert state.active_beat_index == 0
        assert state.summary == ""
        assert state.adaptations == []

    def test_with_outline(self):
        outline = StoryOutline(premise="Test", setting="Test")
        state = StoryState(outline=outline, active_beat_index=2)
        assert state.outline.premise == "Test"
        assert state.active_beat_index == 2

    def test_serialization_roundtrip(self):
        outline = StoryOutline(premise="Test", setting="Fantasy")
        state = StoryState(outline=outline, summary="So far so good")
        data = state.model_dump()
        restored = StoryState(**data)
        assert restored.outline.premise == "Test"
        assert restored.summary == "So far so good"


# ──────────────────────────────────────────────
# Game state models
# ──────────────────────────────────────────────


class TestSession:
    def test_defaults(self):
        session = Session()
        assert isinstance(session.session_id, UUID)
        assert isinstance(session.player_id, UUID)
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.schema_version == 1
        assert session.status == SessionStatus.active

    def test_custom_values(self):
        sid = uuid4()
        pid = uuid4()
        session = Session(
            session_id=sid,
            player_id=pid,
            schema_version=2,
            status=SessionStatus.paused,
        )
        assert session.session_id == sid
        assert session.player_id == pid
        assert session.schema_version == 2
        assert session.status == SessionStatus.paused


class TestMessage:
    def test_create(self):
        msg = Message(role=MessageRole.player, content="Hello world")
        assert msg.role == MessageRole.player
        assert msg.content == "Hello world"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_with_metadata(self):
        msg = Message(
            role=MessageRole.agent,
            content="Response",
            metadata={"tokens": 42},
        )
        assert msg.metadata["tokens"] == 42

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            Message(role="invalid", content="test")


class TestConversation:
    def test_defaults(self):
        conv = Conversation()
        assert conv.history == []
        assert conv.window_size == 20
        assert conv.summary == ""

    def test_with_messages(self):
        msg = Message(role=MessageRole.player, content="Hi")
        conv = Conversation(history=[msg], window_size=10)
        assert len(conv.history) == 1
        assert conv.window_size == 10


def _make_game_state(**overrides) -> GameState:
    """Helper to create a GameState with required Character fields."""
    defaults = {
        "character": Character(name="Aldric", profession="Warrior"),
    }
    defaults.update(overrides)
    return GameState(**defaults)


class TestGameState:
    def test_defaults(self):
        gs = _make_game_state()
        assert gs.session.status == SessionStatus.active
        assert gs.session.schema_version == 1
        assert gs.character.name == "Aldric"
        assert gs.character.profession == "Warrior"
        assert gs.inventory.items == []
        assert gs.world.current_location_id == "start"
        assert gs.story.outline is None
        assert gs.conversation.history == []
        assert gs.recent_events == []

    def test_requires_character_fields(self):
        """GameState() without character raises because Character needs name+profession."""
        with pytest.raises(ValidationError):
            GameState()

    def test_full_roundtrip(self):
        """Test serialization of a fully populated GameState."""
        char = Character(name="Aldric", profession="Warrior")
        item = Item(name="Sword", item_type=ItemType.weapon)
        inv = Inventory(items=[item])
        loc = Location(id="start", name="Village")
        world = World(locations={"start": loc}, current_location_id="start")
        gs = GameState(character=char, inventory=inv, world=world)

        data = gs.model_dump()
        restored = GameState(**data)
        assert restored.character.name == "Aldric"
        assert restored.inventory.items[0].name == "Sword"
        assert restored.world.locations["start"].name == "Village"

    def test_json_roundtrip(self):
        """Test JSON serialization preserves structure."""
        gs = _make_game_state()
        json_str = gs.model_dump_json()
        restored = GameState.model_validate_json(json_str)
        assert restored.session.schema_version == 1
        assert restored.session.status == SessionStatus.active


# ──────────────────────────────────────────────
# Event models
# ──────────────────────────────────────────────


class TestGameEvent:
    def test_create(self):
        sid = uuid4()
        event = GameEvent(
            event_type="character.stat_changed",
            source="character_tool",
            session_id=sid,
        )
        assert event.event_type == "character.stat_changed"
        assert event.source == "character_tool"
        assert event.session_id == sid
        assert event.payload == {}
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.timestamp, datetime)

    def test_frozen(self):
        sid = uuid4()
        event = GameEvent(
            event_type="test", source="test", session_id=sid
        )
        with pytest.raises(ValidationError):
            event.event_type = "changed"

    def test_with_payload(self):
        sid = uuid4()
        event = GameEvent(
            event_type="character.stat_changed",
            payload={"stat_name": "health", "old_value": 100, "new_value": 80},
            source="character_tool",
            session_id=sid,
        )
        assert event.payload["stat_name"] == "health"
        assert event.payload["new_value"] == 80

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            GameEvent(event_type="test")

    def test_serialization_roundtrip(self):
        sid = uuid4()
        event = GameEvent(
            event_type="test.event",
            source="test",
            session_id=sid,
            payload={"key": "value"},
        )
        data = event.model_dump()
        restored = GameEvent(**data)
        assert restored.event_type == "test.event"
        assert restored.payload["key"] == "value"
        assert restored.event_id == event.event_id


class TestEventPayload:
    def test_base_is_frozen(self):
        """EventPayload subclass instances cannot be mutated."""
        p = StatChangedPayload(stat_name="health", old_value=100.0, new_value=80.0)
        with pytest.raises(ValidationError):
            p.stat_name = "energy"

    def test_base_creates_empty_instance(self):
        payload = EventPayload()
        # EventPayload has no fields, so model_dump returns empty dict
        assert payload.model_dump() == {}


class TestStatChangedPayload:
    def test_create(self):
        p = StatChangedPayload(stat_name="health", old_value=100.0, new_value=80.0)
        assert p.stat_name == "health"
        assert p.old_value == 100.0
        assert p.new_value == 80.0
        assert p.reason == ""

    def test_with_reason(self):
        p = StatChangedPayload(
            stat_name="energy", old_value=50.0, new_value=30.0, reason="Used spell"
        )
        assert p.reason == "Used spell"

    def test_frozen(self):
        p = StatChangedPayload(stat_name="health", old_value=100.0, new_value=80.0)
        with pytest.raises(ValidationError):
            p.stat_name = "energy"

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            StatChangedPayload(stat_name="health")


class TestLocationChangedPayload:
    def test_create(self):
        p = LocationChangedPayload(old_location_id="tavern", new_location_id="market")
        assert p.old_location_id == "tavern"
        assert p.new_location_id == "market"
        assert p.location_name == ""

    def test_with_name(self):
        p = LocationChangedPayload(
            old_location_id="a", new_location_id="b", location_name="Market Square"
        )
        assert p.location_name == "Market Square"


class TestItemAcquiredPayload:
    def test_create(self):
        p = ItemAcquiredPayload(item_id="sword-1", item_name="Iron Sword")
        assert p.item_id == "sword-1"
        assert p.item_name == "Iron Sword"
        assert p.quantity == 1

    def test_quantity(self):
        p = ItemAcquiredPayload(item_id="potion-1", item_name="Potion", quantity=5)
        assert p.quantity == 5

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValidationError):
            ItemAcquiredPayload(item_id="x", item_name="X", quantity=0)


class TestItemRemovedPayload:
    def test_create(self):
        p = ItemRemovedPayload(item_id="key-1", item_name="Rusty Key")
        assert p.item_id == "key-1"
        assert p.item_name == "Rusty Key"
        assert p.quantity == 1

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValidationError):
            ItemRemovedPayload(item_id="x", item_name="X", quantity=0)


class TestBeatResolvedPayload:
    def test_create(self):
        p = BeatResolvedPayload(beat_index=0, beat_summary="Hero arrived")
        assert p.beat_index == 0
        assert p.beat_summary == "Hero arrived"
        assert p.outcome == ""

    def test_with_outcome(self):
        p = BeatResolvedPayload(
            beat_index=1, beat_summary="Boss fight", outcome="Victory"
        )
        assert p.outcome == "Victory"

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            BeatResolvedPayload(beat_index=0)


# ──────────────────────────────────────────────
# API models
# ──────────────────────────────────────────────


class TestCharacterCreate:
    def test_create(self):
        cc = CharacterCreate(name="Aldric", profession="Warrior")
        assert cc.name == "Aldric"
        assert cc.profession == "Warrior"
        assert cc.background == ""

    def test_with_background(self):
        cc = CharacterCreate(name="Mage", profession="Sorcerer", background="A lost mage")
        assert cc.background == "A lost mage"

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError):
            CharacterCreate(profession="Warrior")

    def test_missing_profession_raises(self):
        with pytest.raises(ValidationError):
            CharacterCreate(name="Hero")


class TestSessionCreateRequest:
    def test_create(self):
        req = SessionCreateRequest(
            genre="fantasy",
            character=CharacterCreate(name="Hero", profession="Knight"),
        )
        assert req.genre == "fantasy"
        assert req.character.name == "Hero"

    def test_missing_genre_raises(self):
        with pytest.raises(ValidationError):
            SessionCreateRequest(
                character=CharacterCreate(name="Hero", profession="Knight")
            )

    def test_missing_character_raises(self):
        with pytest.raises(ValidationError):
            SessionCreateRequest(genre="fantasy")


class TestSessionCreateResponse:
    def test_create(self):
        sid = uuid4()
        gs = _make_game_state()
        resp = SessionCreateResponse(session_id=sid, game_state=gs)
        assert resp.session_id == sid
        assert resp.game_state.character.name == "Aldric"


class TestSessionSummary:
    def test_create(self):
        sid = uuid4()
        s = SessionSummary(
            session_id=sid,
            character_name="Aldric",
            genre="fantasy",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        assert s.session_id == sid
        assert s.character_name == "Aldric"
        assert s.status == "active"


class TestSessionListResponse:
    def test_empty(self):
        resp = SessionListResponse(sessions=[])
        assert resp.sessions == []

    def test_with_sessions(self):
        summary = SessionSummary(
            session_id=uuid4(),
            character_name="Test",
            status="active",
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )
        resp = SessionListResponse(sessions=[summary])
        assert len(resp.sessions) == 1
        assert resp.sessions[0].character_name == "Test"


class TestSessionDetailResponse:
    def test_create(self):
        resp = SessionDetailResponse(game_state=_make_game_state())
        assert resp.game_state.character.name == "Aldric"


class TestDeleteResponse:
    def test_success(self):
        resp = DeleteResponse(success=True)
        assert resp.success is True

    def test_failure(self):
        resp = DeleteResponse(success=False)
        assert resp.success is False


class TestHealthResponse:
    def test_defaults(self):
        resp = HealthResponse(status="ok")
        assert resp.status == "ok"
        assert resp.version == "0.1.0"

    def test_custom_version(self):
        resp = HealthResponse(status="ok", version="1.0.0")
        assert resp.version == "1.0.0"


class TestErrorResponse:
    def test_create(self):
        resp = ErrorResponse(error="Not found")
        assert resp.error == "Not found"
        assert resp.detail is None

    def test_with_detail(self):
        resp = ErrorResponse(error="Bad request", detail="Missing field")
        assert resp.detail == "Missing field"


class TestPlayerActionRequest:
    def test_create(self):
        sid = uuid4()
        req = PlayerActionRequest(action="go north", session_id=sid)
        assert req.action == "go north"
        assert req.session_id == sid

    def test_missing_action_raises(self):
        with pytest.raises(ValidationError):
            PlayerActionRequest(session_id=uuid4())

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            PlayerActionRequest(action="go north")


class TestAgentResponseMessage:
    def test_create(self):
        sid = uuid4()
        msg = AgentResponseMessage(content="You walk north.", session_id=sid)
        assert msg.content == "You walk north."
        assert msg.session_id == sid
        assert msg.events == []

    def test_with_events(self):
        sid = uuid4()
        msg = AgentResponseMessage(
            content="Test",
            session_id=sid,
            events=[{"type": "test"}],
        )
        assert len(msg.events) == 1

    def test_missing_content_raises(self):
        with pytest.raises(ValidationError):
            AgentResponseMessage(session_id=uuid4())

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            AgentResponseMessage(content="Hello")


class TestStateUpdateMessage:
    def test_create(self):
        sid = uuid4()
        gs = _make_game_state()
        msg = StateUpdateMessage(session_id=sid, game_state=gs)
        assert msg.session_id == sid
        assert msg.game_state.character.name == "Aldric"
