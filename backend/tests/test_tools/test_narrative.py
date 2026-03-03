"""Tests for narrative tools — get_story_outline, resolve_beat, adapt_outline,
advance_beat, add_beat, update_story_summary."""

import asyncio

import pytest

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.story import (
    BeatFlexibility,
    BeatStatus,
    StoryBeat,
    StoryOutline,
    StoryState,
)
from agentic_rpg.tools.narrative import (
    AddBeatTool,
    AdaptOutlineTool,
    AdvanceBeatTool,
    GetStoryOutlineTool,
    ResolveBeatTool,
    UpdateStorySummaryTool,
)


# ---------------------------------------------------------------------------
# Helper to build tool with injected deps
# ---------------------------------------------------------------------------
def _make(cls, game_state: GameState, event_bus: EventBus):
    return cls(game_state=game_state, event_bus=event_bus)


# ===========================================================================
# GetStoryOutlineTool
# ===========================================================================
class TestGetStoryOutlineTool:
    def test_returns_outline_premise(self, tool_game_state, tool_event_bus):
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["premise"] == "A warrior seeks the lost crown of the Northern Kingdom"

    def test_returns_outline_setting(self, tool_game_state, tool_event_bus):
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["setting"] == "Medieval fantasy, dark and gritty"

    def test_returns_beats(self, tool_game_state, tool_event_bus):
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert len(result["beats"]) == 3
        assert result["beats"][0]["summary"] == "Arrive at the tavern and learn of the missing crown"
        assert result["beats"][0]["status"] == "resolved"
        assert result["beats"][1]["status"] == "active"
        assert result["beats"][2]["status"] == "planned"

    def test_returns_active_beat_index(self, tool_game_state, tool_event_bus):
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["active_beat_index"] == 1

    def test_returns_summary(self, tool_game_state, tool_event_bus):
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["summary"] == "Aldric arrived at the tavern and heard rumors of the lost crown."

    def test_returns_adaptations(self, tool_game_state, tool_event_bus):
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["adaptations"] == []

    def test_returns_error_when_no_outline(self, tool_game_state, tool_event_bus):
        tool_game_state.story.outline = None
        tool = _make(GetStoryOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["error"] == "No story outline exists"


# ===========================================================================
# ResolveBeatTool
# ===========================================================================
class TestResolveBeatTool:
    def test_resolves_active_beat(self, tool_game_state, tool_event_bus):
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"outcome": "Found the map seller and bought the map"})
        assert result["success"] is True
        assert result["beat_index"] == 1
        beat = tool_game_state.story.outline.beats[1]
        assert beat.status == BeatStatus.resolved

    def test_resolve_stores_outcome_in_result(self, tool_game_state, tool_event_bus):
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"outcome": "Defeated the guardian"})
        assert result["outcome"] == "Defeated the guardian"

    def test_resolve_fails_when_no_outline(self, tool_game_state, tool_event_bus):
        tool_game_state.story.outline = None
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"outcome": "something"})
        assert result["success"] is False
        assert result["error"] == "No story outline exists"

    def test_resolve_fails_when_index_out_of_range(self, tool_game_state, tool_event_bus):
        tool_game_state.story.active_beat_index = 99
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"outcome": "something"})
        assert result["success"] is False
        assert "out of range" in result["error"]

    def test_resolve_fails_when_beat_not_active(self, tool_game_state, tool_event_bus):
        # Beat at index 1 is active; set it to resolved first
        tool_game_state.story.outline.beats[1].status = BeatStatus.resolved
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"outcome": "something"})
        assert result["success"] is False
        assert "not active" in result["error"]

    async def test_emits_beat_resolved_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        tool.invoke({"outcome": "Found the map"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "story.beat_resolved"
        assert evt.payload["beat_index"] == 1
        assert evt.payload["beat_summary"] == "Explore the market for clues"
        assert evt.payload["outcome"] == "Found the map"
        assert evt.source == "tool:narrative"

    async def test_no_event_on_failed_resolve(self, tool_game_state, tool_event_bus, emitted_events):
        tool_game_state.story.outline = None
        tool = _make(ResolveBeatTool, tool_game_state, tool_event_bus)
        tool.invoke({"outcome": "something"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 0


# ===========================================================================
# AdvanceBeatTool
# ===========================================================================
class TestAdvanceBeatTool:
    def test_advances_to_next_beat(self, tool_game_state, tool_event_bus):
        tool = _make(AdvanceBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["success"] is True
        assert result["new_beat_index"] == 2
        assert tool_game_state.story.active_beat_index == 2
        assert tool_game_state.story.outline.beats[2].status == BeatStatus.active

    def test_advance_fails_when_no_outline(self, tool_game_state, tool_event_bus):
        tool_game_state.story.outline = None
        tool = _make(AdvanceBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["success"] is False
        assert result["error"] == "No story outline exists"

    def test_advance_fails_when_no_more_beats(self, tool_game_state, tool_event_bus):
        tool_game_state.story.active_beat_index = 2  # last beat index
        tool = _make(AdvanceBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({})
        assert result["success"] is False
        assert "no more beats" in result["error"].lower()

    async def test_emits_beat_advanced_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(AdvanceBeatTool, tool_game_state, tool_event_bus)
        tool.invoke({})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "story.beat_advanced"
        assert evt.payload["old_beat_index"] == 1
        assert evt.payload["new_beat_index"] == 2
        assert evt.source == "tool:narrative"

    async def test_no_event_on_failed_advance(self, tool_game_state, tool_event_bus, emitted_events):
        tool_game_state.story.outline = None
        tool = _make(AdvanceBeatTool, tool_game_state, tool_event_bus)
        tool.invoke({})
        await asyncio.sleep(0)
        assert len(emitted_events) == 0


# ===========================================================================
# AdaptOutlineTool
# ===========================================================================
class TestAdaptOutlineTool:
    def test_adapt_records_adaptation(self, tool_game_state, tool_event_bus):
        tool = _make(AdaptOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "reason": "Player took unexpected path",
            "changes": "Added a cave exploration beat",
        })
        assert result["success"] is True
        assert result["reason"] == "Player took unexpected path"
        assert result["changes"] == "Added a cave exploration beat"
        assert len(tool_game_state.story.adaptations) == 1
        record = tool_game_state.story.adaptations[0]
        assert record.reason == "Player took unexpected path"
        assert record.changes == "Added a cave exploration beat"

    def test_adapt_fails_when_no_outline(self, tool_game_state, tool_event_bus):
        tool_game_state.story.outline = None
        tool = _make(AdaptOutlineTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"reason": "test", "changes": "test"})
        assert result["success"] is False
        assert result["error"] == "No story outline exists"

    async def test_emits_outline_adapted_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(AdaptOutlineTool, tool_game_state, tool_event_bus)
        tool.invoke({
            "reason": "Player went off script",
            "changes": "Revised remaining beats",
        })
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "story.outline_adapted"
        assert evt.payload["reason"] == "Player went off script"
        assert evt.payload["changes"] == "Revised remaining beats"
        assert evt.source == "tool:narrative"

    async def test_no_event_on_failed_adapt(self, tool_game_state, tool_event_bus, emitted_events):
        tool_game_state.story.outline = None
        tool = _make(AdaptOutlineTool, tool_game_state, tool_event_bus)
        tool.invoke({"reason": "test", "changes": "test"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 0


# ===========================================================================
# AddBeatTool
# ===========================================================================
class TestAddBeatTool:
    def test_add_beat_appends_by_default(self, tool_game_state, tool_event_bus):
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "summary": "Discover the hidden cave",
            "location": "cave",
            "key_elements": ["crystal", "bat"],
            "player_objectives": ["Explore the cave"],
        })
        assert result["success"] is True
        assert result["position"] == 3  # appended at end
        assert len(tool_game_state.story.outline.beats) == 4
        new_beat = tool_game_state.story.outline.beats[3]
        assert new_beat.summary == "Discover the hidden cave"
        assert new_beat.location == "cave"
        assert new_beat.status == BeatStatus.planned

    def test_add_beat_at_specific_position(self, tool_game_state, tool_event_bus):
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "summary": "Side quest: help the farmer",
            "location": "farm",
            "position": 2,
        })
        assert result["success"] is True
        assert result["position"] == 2
        assert len(tool_game_state.story.outline.beats) == 4
        inserted = tool_game_state.story.outline.beats[2]
        assert inserted.summary == "Side quest: help the farmer"
        # Original beat at index 2 should now be at index 3
        assert tool_game_state.story.outline.beats[3].summary == "Enter the dungeon"

    def test_add_beat_fails_when_no_outline(self, tool_game_state, tool_event_bus):
        tool_game_state.story.outline = None
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({
            "summary": "Something",
            "location": "somewhere",
        })
        assert result["success"] is False
        assert result["error"] == "No story outline exists"

    def test_add_beat_with_defaults(self, tool_game_state, tool_event_bus):
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"summary": "A simple beat"})
        assert result["success"] is True
        new_beat = tool_game_state.story.outline.beats[-1]
        assert new_beat.location == "any"
        assert new_beat.key_elements == []
        assert new_beat.player_objectives == []
        assert new_beat.flexibility == BeatFlexibility.flexible

    def test_add_beat_with_explicit_none_lists(self, tool_game_state, tool_event_bus):
        """Covers branches where key_elements/player_objectives are explicitly None."""
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        result = tool._run(
            summary="Null lists beat",
            location="void",
            key_elements=None,
            player_objectives=None,
            position=None,
        )
        assert result["success"] is True
        new_beat = tool_game_state.story.outline.beats[-1]
        assert new_beat.key_elements == []
        assert new_beat.player_objectives == []

    async def test_emits_beat_added_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        tool.invoke({
            "summary": "New beat",
            "location": "forest",
        })
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "story.beat_added"
        assert evt.payload["summary"] == "New beat"
        assert evt.payload["position"] == 3
        assert evt.source == "tool:narrative"

    async def test_no_event_on_failed_add(self, tool_game_state, tool_event_bus, emitted_events):
        tool_game_state.story.outline = None
        tool = _make(AddBeatTool, tool_game_state, tool_event_bus)
        tool.invoke({"summary": "Something"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 0


# ===========================================================================
# UpdateStorySummaryTool
# ===========================================================================
class TestUpdateStorySummaryTool:
    def test_updates_summary(self, tool_game_state, tool_event_bus):
        tool = _make(UpdateStorySummaryTool, tool_game_state, tool_event_bus)
        new_summary = "Aldric found the map and headed to the dungeon."
        result = tool.invoke({"summary": new_summary})
        assert result["success"] is True
        assert tool_game_state.story.summary == new_summary

    def test_returns_old_and_new_summary(self, tool_game_state, tool_event_bus):
        tool = _make(UpdateStorySummaryTool, tool_game_state, tool_event_bus)
        result = tool.invoke({"summary": "New summary"})
        assert result["old_summary"] == "Aldric arrived at the tavern and heard rumors of the lost crown."
        assert result["new_summary"] == "New summary"

    async def test_emits_summary_updated_event(self, tool_game_state, tool_event_bus, emitted_events):
        tool = _make(UpdateStorySummaryTool, tool_game_state, tool_event_bus)
        tool.invoke({"summary": "Updated narrative summary"})
        await asyncio.sleep(0)
        assert len(emitted_events) == 1
        evt = emitted_events[0]
        assert evt.event_type == "story.summary_updated"
        assert evt.payload["new_summary"] == "Updated narrative summary"
        assert evt.source == "tool:narrative"
