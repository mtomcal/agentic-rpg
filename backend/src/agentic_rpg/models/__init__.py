"""Pydantic models for the Agentic RPG."""

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

__all__ = [
    # Character
    "Character",
    "StatusEffect",
    "StatusEffectType",
    # Inventory
    "Item",
    "ItemType",
    "Inventory",
    # World
    "Location",
    "World",
    # Story
    "StoryBeat",
    "StoryOutline",
    "StoryState",
    "AdaptationRecord",
    "BeatStatus",
    "BeatFlexibility",
    # Game State
    "GameState",
    "Session",
    "SessionStatus",
    "Message",
    "MessageRole",
    "Conversation",
    # Events
    "GameEvent",
    "EventPayload",
    "StatChangedPayload",
    "LocationChangedPayload",
    "ItemAcquiredPayload",
    "ItemRemovedPayload",
    "BeatResolvedPayload",
    # API
    "CharacterCreate",
    "SessionCreateRequest",
    "SessionCreateResponse",
    "SessionSummary",
    "SessionListResponse",
    "SessionDetailResponse",
    "DeleteResponse",
    "HealthResponse",
    "ErrorResponse",
    "PlayerActionRequest",
    "AgentResponseMessage",
    "StateUpdateMessage",
]
