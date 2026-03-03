"""Tests for the story engine — outline generation, beat lifecycle, adaptation."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from agentic_rpg.models.story import (
    AdaptationRecord,
    BeatFlexibility,
    BeatStatus,
    StoryBeat,
    StoryOutline,
    StoryState,
)


def _make_outline(num_beats: int = 5) -> StoryOutline:
    """Helper: create a StoryOutline with N planned beats."""
    beats = [
        StoryBeat(
            summary=f"Beat {i + 1} summary",
            location=f"location_{i + 1}",
            trigger_conditions=[f"trigger_{i + 1}"],
            key_elements=[f"npc_{i + 1}"],
            player_objectives=[f"objective_{i + 1}"],
            possible_outcomes=[f"outcome_a_{i + 1}", f"outcome_b_{i + 1}"],
            flexibility=BeatFlexibility.flexible,
            status=BeatStatus.planned,
        )
        for i in range(num_beats)
    ]
    return StoryOutline(
        premise="A hero sets out on a quest to save the realm.",
        setting="Medieval fantasy kingdom under siege",
        beats=beats,
    )


def _make_story_state(num_beats: int = 5) -> StoryState:
    """Helper: create a StoryState with an active first beat."""
    outline = _make_outline(num_beats)
    outline.beats[0].status = BeatStatus.active
    return StoryState(
        outline=outline,
        active_beat_index=0,
        summary="",
        adaptations=[],
    )


def _mock_llm_for_generation() -> MagicMock:
    """Create a mock LLM that returns a StoryOutline from structured output."""
    outline = _make_outline(6)
    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=outline)

    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=structured_llm)
    return llm


# ---- Generation tests ----


async def test_generate_outline():
    """generate_outline calls LLM with structured output and returns StoryOutline."""
    from agentic_rpg.agent.story_engine import generate_outline

    llm = _mock_llm_for_generation()
    result = await generate_outline(llm, "dark fantasy", "Aldric the fallen knight")

    assert isinstance(result, StoryOutline)
    assert result.premise == "A hero sets out on a quest to save the realm."
    assert result.setting == "Medieval fantasy kingdom under siege"
    assert len(result.beats) == 6
    llm.with_structured_output.assert_called_once_with(StoryOutline)


async def test_outline_has_minimum_beats():
    """Generated outline has at least 5 beats (enforced by prompt, verified here)."""
    from agentic_rpg.agent.story_engine import generate_outline

    llm = _mock_llm_for_generation()
    result = await generate_outline(llm, "sci-fi", "Captain Zara")

    assert len(result.beats) >= 5


async def test_outline_beats_start_as_planned():
    """All beats in the generated outline start with status 'planned'."""
    from agentic_rpg.agent.story_engine import generate_outline

    llm = _mock_llm_for_generation()
    result = await generate_outline(llm, "horror", "Dr. Morrow")

    for beat in result.beats:
        assert beat.status == BeatStatus.planned


# ---- First beat activation ----


async def test_first_beat_activated():
    """activate_first_beat sets the first beat's status to 'active'."""
    from agentic_rpg.agent.story_engine import activate_first_beat

    outline = _make_outline(5)
    assert outline.beats[0].status == BeatStatus.planned

    activated = activate_first_beat(outline)
    assert activated.beats[0].status == BeatStatus.active
    # Other beats remain planned
    for beat in activated.beats[1:]:
        assert beat.status == BeatStatus.planned


# ---- Beat resolution ----


async def test_resolve_beat():
    """resolve_beat marks the active beat as 'resolved' and records the outcome."""
    from agentic_rpg.agent.story_engine import resolve_beat

    state = _make_story_state(5)
    assert state.outline.beats[0].status == BeatStatus.active

    result = resolve_beat(state, outcome="The hero defeated the guardian")

    assert result.outline.beats[0].status == BeatStatus.resolved
    assert "defeated the guardian" in result.outline.beats[0].possible_outcomes[-1]


async def test_resolve_beat_updates_summary():
    """After resolving a beat, the story summary is updated."""
    from agentic_rpg.agent.story_engine import resolve_beat

    state = _make_story_state(5)
    assert state.summary == ""

    result = resolve_beat(state, outcome="The hero found the ancient sword")

    assert "ancient sword" in result.summary


# ---- Skip beat ----


async def test_skip_beat():
    """skip_beat marks the active beat as 'skipped'."""
    from agentic_rpg.agent.story_engine import skip_beat

    state = _make_story_state(5)
    assert state.outline.beats[0].status == BeatStatus.active

    result = skip_beat(state)

    assert result.outline.beats[0].status == BeatStatus.skipped


# ---- Advance beat ----


async def test_advance_beat():
    """advance_beat increments active_beat_index and sets next beat to 'active'."""
    from agentic_rpg.agent.story_engine import advance_beat

    state = _make_story_state(5)
    # Resolve the first beat so we can advance
    state.outline.beats[0].status = BeatStatus.resolved

    result = advance_beat(state)

    assert result.active_beat_index == 1
    assert result.outline.beats[1].status == BeatStatus.active
    # Previous beat is still resolved
    assert result.outline.beats[0].status == BeatStatus.resolved


# ---- Adaptation ----


async def test_adapt_outline():
    """adapt_outline replaces unresolved beats with LLM-generated ones and logs adaptation."""
    from agentic_rpg.agent.story_engine import adapt_outline

    state = _make_story_state(5)
    # Resolve beat 0, make beat 1 active
    state.outline.beats[0].status = BeatStatus.resolved
    state.outline.beats[1].status = BeatStatus.active
    state.active_beat_index = 1

    # Mock LLM returns new outline with fresh beats
    new_beats = [
        StoryBeat(
            summary=f"Adapted beat {i}",
            location=f"new_loc_{i}",
            flexibility=BeatFlexibility.flexible,
        )
        for i in range(4)
    ]
    new_outline = StoryOutline(
        premise=state.outline.premise,
        setting=state.outline.setting,
        beats=new_beats,
    )
    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=new_outline)
    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=structured_llm)

    result = await adapt_outline(
        llm, state, reason="Player went off-script", changes="Headed to the mountains"
    )

    # Resolved beat 0 is preserved
    assert result.outline.beats[0].status == BeatStatus.resolved
    assert result.outline.beats[0].summary == "Beat 1 summary"
    # Remaining beats replaced with adapted ones
    assert result.outline.beats[1].summary == "Adapted beat 0"
    # Adaptation logged
    assert len(result.adaptations) == 1
    assert result.adaptations[0].reason == "Player went off-script"
    assert result.adaptations[0].changes == "Headed to the mountains"


async def test_adaptation_preserves_resolved_beats():
    """Adaptation never changes resolved beats."""
    from agentic_rpg.agent.story_engine import adapt_outline

    state = _make_story_state(5)
    # Resolve first two beats
    state.outline.beats[0].status = BeatStatus.resolved
    state.outline.beats[1].status = BeatStatus.resolved
    state.outline.beats[2].status = BeatStatus.active
    state.active_beat_index = 2

    new_outline = StoryOutline(
        premise=state.outline.premise,
        setting=state.outline.setting,
        beats=[
            StoryBeat(summary="New beat A", location="new_a"),
            StoryBeat(summary="New beat B", location="new_b"),
        ],
    )
    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=new_outline)
    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=structured_llm)

    result = await adapt_outline(llm, state, reason="test", changes="test")

    # First two beats preserved exactly
    assert result.outline.beats[0].summary == "Beat 1 summary"
    assert result.outline.beats[0].status == BeatStatus.resolved
    assert result.outline.beats[1].summary == "Beat 2 summary"
    assert result.outline.beats[1].status == BeatStatus.resolved
    # Adapted beats follow
    assert result.outline.beats[2].summary == "New beat A"


async def test_adaptation_history_recorded():
    """Each adaptation adds an AdaptationRecord to the history."""
    from agentic_rpg.agent.story_engine import adapt_outline

    state = _make_story_state(5)
    state.outline.beats[0].status = BeatStatus.resolved
    state.outline.beats[1].status = BeatStatus.active
    state.active_beat_index = 1

    new_outline = StoryOutline(
        premise=state.outline.premise,
        setting=state.outline.setting,
        beats=[StoryBeat(summary="Replacement", location="any")],
    )
    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=new_outline)
    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=structured_llm)

    result = await adapt_outline(
        llm, state, reason="Divergence", changes="Player fled"
    )

    assert len(result.adaptations) == 1
    record = result.adaptations[0]
    assert isinstance(record, AdaptationRecord)
    assert record.reason == "Divergence"
    assert record.changes == "Player fled"
    assert record.timestamp is not None


# ---- Advance beat — edge cases ----


async def test_advance_beat_past_last_beat():
    """advance_beat at the final beat increments index but does not error or modify beats."""
    from agentic_rpg.agent.story_engine import advance_beat

    state = _make_story_state(3)
    # Set up: beats 0..1 resolved, beat 2 is active, index=2
    state.outline.beats[0].status = BeatStatus.resolved
    state.outline.beats[1].status = BeatStatus.resolved
    state.outline.beats[2].status = BeatStatus.active
    state.active_beat_index = 2

    # Advancing past the last beat should not raise
    result = advance_beat(state)

    # Index moves beyond the list
    assert result.active_beat_index == 3
    # No beat was changed — all three retain their prior statuses
    assert result.outline.beats[0].status == BeatStatus.resolved
    assert result.outline.beats[1].status == BeatStatus.resolved
    assert result.outline.beats[2].status == BeatStatus.active


# ---- Resolve beat — summary accumulation ----


async def test_resolve_beat_appends_to_existing_summary():
    """resolve_beat appends the outcome to a non-empty summary with a space separator."""
    from agentic_rpg.agent.story_engine import resolve_beat

    state = _make_story_state(5)
    state.summary = "The hero entered the dungeon."
    state.outline.beats[0].status = BeatStatus.active

    result = resolve_beat(state, outcome="The hero slew the dragon.")

    # Both parts should appear in the summary
    assert "The hero entered the dungeon." in result.summary
    assert "The hero slew the dragon." in result.summary
    # Joined by a space
    assert result.summary == "The hero entered the dungeon. The hero slew the dragon."


# ---- activate_first_beat — empty outline ----


def test_activate_first_beat_empty_outline():
    """activate_first_beat on an outline with no beats returns the outline unchanged."""
    from agentic_rpg.agent.story_engine import activate_first_beat

    outline = StoryOutline(
        premise="A quiet tale",
        setting="Modern city",
        beats=[],
    )

    result = activate_first_beat(outline)

    assert result.beats == []


# ---- generate_outline — beat status normalisation ----


async def test_generate_outline_normalises_beat_statuses():
    """generate_outline forces all returned beats to 'planned' even if LLM returns other statuses."""
    from agentic_rpg.agent.story_engine import generate_outline

    # Build an outline where the LLM has returned beats with non-planned statuses
    beats_with_wrong_statuses = [
        StoryBeat(
            summary="Beat A",
            location="loc_a",
            status=BeatStatus.active,
        ),
        StoryBeat(
            summary="Beat B",
            location="loc_b",
            status=BeatStatus.resolved,
        ),
        StoryBeat(
            summary="Beat C",
            location="loc_c",
            status=BeatStatus.skipped,
        ),
    ]
    bad_outline = StoryOutline(
        premise="Test premise",
        setting="Test setting",
        beats=beats_with_wrong_statuses,
    )

    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=bad_outline)
    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=structured_llm)

    result = await generate_outline(llm, "test setting", "test character")

    # All beats must be reset to planned regardless of what the LLM returned
    for beat in result.beats:
        assert beat.status == BeatStatus.planned


# ---- adapt_outline — prompt invoked with correct context ----


async def test_adapt_outline_passes_summary_to_llm():
    """adapt_outline passes the current story summary to the adaptation prompt."""
    from agentic_rpg.agent.story_engine import adapt_outline

    state = _make_story_state(3)
    state.outline.beats[0].status = BeatStatus.resolved
    state.outline.beats[1].status = BeatStatus.active
    state.active_beat_index = 1
    state.summary = "The hero crossed the mountains."

    new_outline = StoryOutline(
        premise=state.outline.premise,
        setting=state.outline.setting,
        beats=[StoryBeat(summary="Replacement beat", location="valley")],
    )
    structured_llm = AsyncMock()
    structured_llm.ainvoke = AsyncMock(return_value=new_outline)
    llm = MagicMock()
    llm.with_structured_output = MagicMock(return_value=structured_llm)

    result = await adapt_outline(
        llm, state, reason="Player detoured", changes="Took mountain pass"
    )

    # The replacement beat is present in the final outline after the resolved beat
    assert result.outline.beats[1].summary == "Replacement beat"
    # Adaptation was logged with exact reason and changes
    assert len(result.adaptations) == 1
    assert result.adaptations[0].reason == "Player detoured"
    assert result.adaptations[0].changes == "Took mountain pass"


# ---- Multiple adaptations ----


async def test_multiple_adaptations_accumulate():
    """Each call to adapt_outline adds another AdaptationRecord."""
    from agentic_rpg.agent.story_engine import adapt_outline

    state = _make_story_state(5)
    state.outline.beats[0].status = BeatStatus.resolved
    state.outline.beats[1].status = BeatStatus.active
    state.active_beat_index = 1

    def _mock_llm_with_outline(outline: StoryOutline) -> MagicMock:
        structured_llm = AsyncMock()
        structured_llm.ainvoke = AsyncMock(return_value=outline)
        llm = MagicMock()
        llm.with_structured_output = MagicMock(return_value=structured_llm)
        return llm

    replacement_1 = StoryOutline(
        premise=state.outline.premise,
        setting=state.outline.setting,
        beats=[StoryBeat(summary="After first adapt", location="forest")],
    )
    state = await adapt_outline(
        _mock_llm_with_outline(replacement_1),
        state,
        reason="First divergence",
        changes="Went to forest",
    )

    assert len(state.adaptations) == 1
    assert state.adaptations[0].reason == "First divergence"

    replacement_2 = StoryOutline(
        premise=state.outline.premise,
        setting=state.outline.setting,
        beats=[StoryBeat(summary="After second adapt", location="cave")],
    )
    state = await adapt_outline(
        _mock_llm_with_outline(replacement_2),
        state,
        reason="Second divergence",
        changes="Went to cave",
    )

    assert len(state.adaptations) == 2
    assert state.adaptations[1].reason == "Second divergence"
    assert state.adaptations[1].changes == "Went to cave"


# ---- Initial story state creation ----


async def test_generate_initial_story_state():
    """create_initial_story_state builds a StoryState from an outline."""
    from agentic_rpg.agent.story_engine import create_initial_story_state

    outline = _make_outline(5)
    outline.beats[0].status = BeatStatus.active  # assume activation happened

    state = create_initial_story_state(outline)

    assert isinstance(state, StoryState)
    assert state.outline is outline
    assert state.active_beat_index == 0
    assert state.summary == ""
    assert state.adaptations == []
