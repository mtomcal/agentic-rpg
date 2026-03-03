"""Test fixtures for Phase 3 tool tests."""

import copy
from uuid import uuid4

import pytest

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.character import Character, StatusEffect, StatusEffectType
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
    BeatFlexibility,
    BeatStatus,
    StoryBeat,
    StoryOutline,
    StoryState,
)
from agentic_rpg.models.world import Location, World


# ---------------------------------------------------------------------------
# tool_game_state — a mutable copy of a fully populated GameState
# ---------------------------------------------------------------------------
@pytest.fixture
def tool_game_state() -> GameState:
    """A fully populated GameState for tool tests. Each test gets a fresh copy."""
    return GameState(
        session=Session(
            session_id=uuid4(),
            player_id=uuid4(),
            status=SessionStatus.active,
            schema_version=1,
        ),
        character=Character(
            name="Aldric",
            profession="Warrior",
            background="A veteran of the Northern Wars",
            stats={
                "health": 80.0,
                "max_health": 100.0,
                "energy": 60.0,
                "max_energy": 100.0,
                "money": 50.0,
            },
            status_effects=[
                StatusEffect(
                    name="Blessed",
                    effect_type=StatusEffectType.buff,
                    description="Divine protection",
                    duration=3,
                    magnitude=1.5,
                )
            ],
            level=2,
            experience=150,
            location_id="tavern",
        ),
        inventory=Inventory(
            items=[
                Item(
                    name="Iron Sword",
                    description="A sturdy iron blade",
                    item_type=ItemType.weapon,
                    quantity=1,
                    properties={"damage": 10},
                ),
                Item(
                    name="Health Potion",
                    description="Restores 25 health",
                    item_type=ItemType.consumable,
                    quantity=3,
                    properties={"heal_amount": 25},
                ),
                Item(
                    name="Rusty Key",
                    description="Opens something old",
                    item_type=ItemType.key,
                    quantity=1,
                ),
            ],
            capacity=20,
        ),
        world=World(
            locations={
                "tavern": Location(
                    id="tavern",
                    name="The Rusty Flagon",
                    description="A dimly lit tavern smelling of ale",
                    connections=["market", "alley"],
                    npcs_present=["bartender"],
                    visited=True,
                ),
                "market": Location(
                    id="market",
                    name="Market Square",
                    description="A bustling marketplace",
                    connections=["tavern", "gate"],
                    visited=True,
                ),
                "alley": Location(
                    id="alley",
                    name="Dark Alley",
                    description="A narrow, shadowy passage",
                    connections=["tavern"],
                    visited=False,
                ),
            },
            current_location_id="tavern",
            discovered_locations={"tavern", "market"},
            world_flags={"quest_started": True},
        ),
        story=StoryState(
            outline=StoryOutline(
                premise="A warrior seeks the lost crown of the Northern Kingdom",
                setting="Medieval fantasy, dark and gritty",
                beats=[
                    StoryBeat(
                        summary="Arrive at the tavern and learn of the missing crown",
                        location="tavern",
                        key_elements=["bartender", "rumor"],
                        player_objectives=["Talk to the bartender"],
                        flexibility=BeatFlexibility.fixed,
                        status=BeatStatus.resolved,
                    ),
                    StoryBeat(
                        summary="Explore the market for clues",
                        location="market",
                        key_elements=["merchant", "map"],
                        player_objectives=["Find the map seller"],
                        flexibility=BeatFlexibility.flexible,
                        status=BeatStatus.active,
                    ),
                    StoryBeat(
                        summary="Enter the dungeon",
                        location="dungeon",
                        key_elements=["guardian", "puzzle"],
                        player_objectives=["Solve the puzzle"],
                        flexibility=BeatFlexibility.flexible,
                        status=BeatStatus.pending,
                    ),
                ],
            ),
            active_beat_index=1,
            summary="Aldric arrived at the tavern and heard rumors of the lost crown.",
        ),
        conversation=Conversation(
            history=[
                Message(
                    role=MessageRole.system,
                    content="Welcome to the adventure!",
                ),
                Message(
                    role=MessageRole.player,
                    content="I look around the tavern.",
                ),
                Message(
                    role=MessageRole.agent,
                    content="The Rusty Flagon is dimly lit.",
                ),
            ],
            window_size=20,
            summary="",
        ),
    )


# ---------------------------------------------------------------------------
# tool_event_bus — fresh EventBus per test for capturing emitted events
# ---------------------------------------------------------------------------
@pytest.fixture
def tool_event_bus() -> EventBus:
    """Return a fresh EventBus for tool tests."""
    return EventBus()


# ---------------------------------------------------------------------------
# emitted_events — helper list that collects events published to the bus
# ---------------------------------------------------------------------------
@pytest.fixture
def emitted_events(tool_event_bus: EventBus) -> list:
    """Subscribe a catch-all listener and return the list of captured events.

    Tools emit events via the event bus. This fixture subscribes to all common
    event types and collects them for assertion.
    """
    captured: list = []

    async def _capture(event):
        captured.append(event)

    # Subscribe to all event types tools might emit
    event_types = [
        "character.stat_changed",
        "character.status_effect_added",
        "character.status_effect_removed",
        "character.money_changed",
        "inventory.item_added",
        "inventory.item_removed",
        "inventory.item_equipped",
        "inventory.item_unequipped",
        "inventory.item_used",
        "world.character_moved",
        "world.location_added",
        "world.flag_set",
        "story.beat_resolved",
        "story.beat_advanced",
        "story.beat_added",
        "story.outline_adapted",
        "story.summary_updated",
    ]
    for et in event_types:
        tool_event_bus.subscribe(et, _capture)

    return captured
