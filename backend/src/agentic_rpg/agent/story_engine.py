"""Story engine — outline generation, beat lifecycle, and adaptation."""

from langchain_core.prompts import ChatPromptTemplate

from agentic_rpg.models.story import (
    AdaptationRecord,
    BeatStatus,
    StoryOutline,
    StoryState,
)

GENERATE_OUTLINE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a narrative designer for a single-player RPG. "
            "Create a story outline with 5-10 narrative beats forming a "
            "complete arc (setup → rising action → climax → resolution). "
            "Each beat should have a clear summary, location, trigger conditions, "
            "key elements, player objectives, possible outcomes, and flexibility rating.",
        ),
        (
            "human",
            "Create a story outline for the following:\n"
            "Setting: {setting}\n"
            "Character: {character_summary}",
        ),
    ]
)

ADAPT_OUTLINE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a narrative designer adapting an RPG story outline. "
            "The player has diverged from the plan. Generate replacement beats "
            "that account for the changes while maintaining narrative coherence. "
            "All beats should have status 'planned'.",
        ),
        (
            "human",
            "Current premise: {premise}\n"
            "Setting: {setting}\n"
            "Story so far: {summary}\n"
            "Reason for adaptation: {reason}\n"
            "What changed: {changes}\n\n"
            "Generate new beats to continue the story.",
        ),
    ]
)


async def generate_outline(
    llm, setting: str, character_summary: str
) -> StoryOutline:
    """Generate a story outline using LLM structured output."""
    structured_llm = llm.with_structured_output(StoryOutline)
    messages = await GENERATE_OUTLINE_PROMPT.ainvoke(
        {"setting": setting, "character_summary": character_summary}
    )
    outline: StoryOutline = await structured_llm.ainvoke(messages)
    # Ensure all beats start as planned
    for beat in outline.beats:
        beat.status = BeatStatus.planned
    return outline


def activate_first_beat(outline: StoryOutline) -> StoryOutline:
    """Set the first beat's status to 'active'."""
    if outline.beats:
        outline.beats[0].status = BeatStatus.active
    return outline


def create_initial_story_state(outline: StoryOutline) -> StoryState:
    """Create a StoryState from a generated outline."""
    return StoryState(
        outline=outline,
        active_beat_index=0,
        summary="",
        adaptations=[],
    )


def resolve_beat(story_state: StoryState, outcome: str) -> StoryState:
    """Resolve the active beat with the given outcome."""
    idx = story_state.active_beat_index
    beat = story_state.outline.beats[idx]
    beat.status = BeatStatus.resolved
    beat.possible_outcomes.append(outcome)
    # Update the running summary
    if story_state.summary:
        story_state.summary += f" {outcome}"
    else:
        story_state.summary = outcome
    return story_state


def skip_beat(story_state: StoryState) -> StoryState:
    """Skip the active beat."""
    idx = story_state.active_beat_index
    story_state.outline.beats[idx].status = BeatStatus.skipped
    return story_state


def advance_beat(story_state: StoryState) -> StoryState:
    """Advance to the next beat."""
    story_state.active_beat_index += 1
    idx = story_state.active_beat_index
    if idx < len(story_state.outline.beats):
        story_state.outline.beats[idx].status = BeatStatus.active
    return story_state


async def adapt_outline(
    llm, story_state: StoryState, reason: str, changes: str
) -> StoryState:
    """Adapt the outline by replacing unresolved beats with LLM-generated ones."""
    outline = story_state.outline

    # Collect resolved beats to preserve
    resolved_beats = [
        beat for beat in outline.beats if beat.status == BeatStatus.resolved
    ]

    # Call LLM for new beats
    structured_llm = llm.with_structured_output(StoryOutline)
    messages = await ADAPT_OUTLINE_PROMPT.ainvoke(
        {
            "premise": outline.premise,
            "setting": outline.setting,
            "summary": story_state.summary,
            "reason": reason,
            "changes": changes,
        }
    )
    new_outline: StoryOutline = await structured_llm.ainvoke(messages)

    # Merge: preserved resolved beats + new beats
    story_state.outline.beats = resolved_beats + new_outline.beats

    # Log the adaptation
    story_state.adaptations.append(
        AdaptationRecord(reason=reason, changes=changes)
    )

    return story_state
