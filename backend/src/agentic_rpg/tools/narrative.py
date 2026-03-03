"""Narrative tools — inspect and modify story/outline state."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from agentic_rpg.events.bus import EventBus
from agentic_rpg.models.events import GameEvent
from agentic_rpg.models.game_state import GameState
from agentic_rpg.models.story import AdaptationRecord, BeatStatus, StoryBeat


# ---------------------------------------------------------------------------
# Input schemas
# ---------------------------------------------------------------------------
class ResolveBeatInput(BaseModel):
    """Input for resolve_beat."""

    outcome: str = Field(description="How the current beat was resolved")


class AdaptOutlineInput(BaseModel):
    """Input for adapt_outline."""

    reason: str = Field(description="Why the outline needs adaptation")
    changes: str = Field(description="What changed in the outline")


class AddBeatInput(BaseModel):
    """Input for add_beat."""

    summary: str = Field(description="What should happen at this beat")
    location: str = Field(default="any", description="Where this beat takes place")
    key_elements: list[str] = Field(default_factory=list, description="Key NPCs/items/events")
    player_objectives: list[str] = Field(default_factory=list, description="What the player can do")
    position: int | None = Field(default=None, description="Position to insert at (None = append)")


class UpdateStorySummaryInput(BaseModel):
    """Input for update_story_summary."""

    summary: str = Field(description="The updated running narrative summary")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _emit(event_bus: EventBus, game_state: GameState, event_type: str, payload: dict) -> None:
    """Publish an event synchronously via the event bus."""
    event = GameEvent(
        event_type=event_type,
        payload=payload,
        source="tool:narrative",
        session_id=game_state.session.session_id,
    )
    event_bus.publish_sync(event)


# ---------------------------------------------------------------------------
# GetStoryOutlineTool
# ---------------------------------------------------------------------------
class GetStoryOutlineTool(BaseTool):
    """Get the current story outline, beats, and summary."""

    name: str = "get_story_outline"
    description: str = "Get the current story outline including beats, summary, and adaptations."

    game_state: GameState
    event_bus: EventBus

    def _run(self, **kwargs: Any) -> dict:
        story = self.game_state.story
        if story.outline is None:
            return {"error": "No story outline exists"}

        return {
            "premise": story.outline.premise,
            "setting": story.outline.setting,
            "beats": [b.model_dump() for b in story.outline.beats],
            "active_beat_index": story.active_beat_index,
            "summary": story.summary,
            "adaptations": [a.model_dump() for a in story.adaptations],
        }


# ---------------------------------------------------------------------------
# ResolveBeatTool
# ---------------------------------------------------------------------------
class ResolveBeatTool(BaseTool):
    """Mark the current active beat as resolved."""

    name: str = "resolve_beat"
    description: str = "Mark the current active beat as resolved with an outcome."
    args_schema: type = ResolveBeatInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, outcome: str) -> dict:
        story = self.game_state.story
        if story.outline is None:
            return {"success": False, "error": "No story outline exists"}

        idx = story.active_beat_index
        if idx < 0 or idx >= len(story.outline.beats):
            return {"success": False, "error": f"Beat index {idx} out of range"}

        beat = story.outline.beats[idx]
        if beat.status != BeatStatus.active:
            return {"success": False, "error": f"Beat at index {idx} is not active (status: {beat.status})"}

        beat.status = BeatStatus.resolved

        _emit(self.event_bus, self.game_state, "story.beat_resolved", {
            "beat_index": idx,
            "beat_summary": beat.summary,
            "outcome": outcome,
        })

        return {"success": True, "beat_index": idx, "outcome": outcome}


# ---------------------------------------------------------------------------
# AdvanceBeatTool
# ---------------------------------------------------------------------------
class AdvanceBeatTool(BaseTool):
    """Move to the next story beat."""

    name: str = "advance_beat"
    description: str = "Advance to the next story beat."

    game_state: GameState
    event_bus: EventBus

    def _run(self, **kwargs: Any) -> dict:
        story = self.game_state.story
        if story.outline is None:
            return {"success": False, "error": "No story outline exists"}

        old_idx = story.active_beat_index
        new_idx = old_idx + 1

        if new_idx >= len(story.outline.beats):
            return {"success": False, "error": "No more beats to advance to"}

        story.active_beat_index = new_idx
        story.outline.beats[new_idx].status = BeatStatus.active

        _emit(self.event_bus, self.game_state, "story.beat_advanced", {
            "old_beat_index": old_idx,
            "new_beat_index": new_idx,
        })

        return {"success": True, "new_beat_index": new_idx}


# ---------------------------------------------------------------------------
# AdaptOutlineTool
# ---------------------------------------------------------------------------
class AdaptOutlineTool(BaseTool):
    """Record a story outline adaptation."""

    name: str = "adapt_outline"
    description: str = "Record an adaptation to the story outline with a reason and changes."
    args_schema: type = AdaptOutlineInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, reason: str, changes: str) -> dict:
        story = self.game_state.story
        if story.outline is None:
            return {"success": False, "error": "No story outline exists"}

        record = AdaptationRecord(reason=reason, changes=changes)
        story.adaptations.append(record)

        _emit(self.event_bus, self.game_state, "story.outline_adapted", {
            "reason": reason,
            "changes": changes,
        })

        return {"success": True, "reason": reason, "changes": changes}


# ---------------------------------------------------------------------------
# AddBeatTool
# ---------------------------------------------------------------------------
class AddBeatTool(BaseTool):
    """Insert a new story beat."""

    name: str = "add_beat"
    description: str = "Add a new story beat at a given position or at the end."
    args_schema: type = AddBeatInput

    game_state: GameState
    event_bus: EventBus

    def _run(
        self,
        summary: str,
        location: str = "any",
        key_elements: list[str] | None = None,
        player_objectives: list[str] | None = None,
        position: int | None = None,
    ) -> dict:
        story = self.game_state.story
        if story.outline is None:
            return {"success": False, "error": "No story outline exists"}

        if key_elements is None:
            key_elements = []
        if player_objectives is None:
            player_objectives = []

        new_beat = StoryBeat(
            summary=summary,
            location=location,
            key_elements=key_elements,
            player_objectives=player_objectives,
            status=BeatStatus.planned,
        )

        if position is None:
            position = len(story.outline.beats)
            story.outline.beats.append(new_beat)
        else:
            story.outline.beats.insert(position, new_beat)

        _emit(self.event_bus, self.game_state, "story.beat_added", {
            "summary": summary,
            "position": position,
        })

        return {"success": True, "position": position, "summary": summary}


# ---------------------------------------------------------------------------
# UpdateStorySummaryTool
# ---------------------------------------------------------------------------
class UpdateStorySummaryTool(BaseTool):
    """Update the running story summary."""

    name: str = "update_story_summary"
    description: str = "Update the condensed running narrative summary."
    args_schema: type = UpdateStorySummaryInput

    game_state: GameState
    event_bus: EventBus

    def _run(self, summary: str) -> dict:
        old_summary = self.game_state.story.summary
        self.game_state.story.summary = summary

        _emit(self.event_bus, self.game_state, "story.summary_updated", {
            "old_summary": old_summary,
            "new_summary": summary,
        })

        return {"success": True, "old_summary": old_summary, "new_summary": summary}
