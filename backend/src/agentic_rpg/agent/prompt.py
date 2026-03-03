"""System prompt builder for the agent."""

from __future__ import annotations

from agentic_rpg.models.game_state import GameState


def build_system_prompt(game_state: GameState) -> str:
    """Build the system prompt string from the current game state.

    Assembles character info, location, inventory, story context, recent events,
    and behavioral rules into a single system prompt for the LLM.
    """
    sections: list[str] = []

    # --- Role ---
    sections.append(
        "You are a Game Master for a fantasy RPG. "
        "Narrate the world, respond to the player's actions, and use tools to modify game state. "
        "Respect the player's agency — never act for the player or kill them without warning."
    )

    # --- Story context ---
    story = game_state.story
    if story.outline is not None:
        outline = story.outline
        sections.append(
            f"\n## Story\n"
            f"Premise: {outline.premise}\n"
            f"Setting: {outline.setting}"
        )
        # Active beat
        if outline.beats and 0 <= story.active_beat_index < len(outline.beats):
            beat = outline.beats[story.active_beat_index]
            sections.append(
                f"\n## Active Story Beat\n"
                f"Summary: {beat.summary}\n"
                f"Location: {beat.location}\n"
                f"Key elements: {', '.join(beat.key_elements)}\n"
                f"Player objectives: {', '.join(beat.player_objectives)}\n"
                f"Flexibility: {beat.flexibility.value}"
            )

    # --- Conversation summary ---
    if game_state.conversation.summary:
        sections.append(
            f"\n## Previous Conversation Summary\n"
            f"{game_state.conversation.summary}"
        )

    # --- Character ---
    char = game_state.character
    stats_str = ", ".join(f"{k}: {v}" for k, v in char.stats.items()) if char.stats else "none"
    effects_str = ", ".join(e.name for e in char.status_effects) if char.status_effects else "none"
    sections.append(
        f"\n## Character\n"
        f"Name: {char.name}\n"
        f"Profession: {char.profession}\n"
        f"Level: {char.level}\n"
        f"Stats: {stats_str}\n"
        f"Status effects: {effects_str}"
    )

    # --- Current location ---
    world = game_state.world
    loc = world.locations.get(world.current_location_id)
    if loc is not None:
        connections = ", ".join(loc.connections) if loc.connections else "none"
        npcs = ", ".join(loc.npcs_present) if loc.npcs_present else "none"
        items = ", ".join(loc.items_present) if loc.items_present else "none"
        sections.append(
            f"\n## Current Location\n"
            f"Name: {loc.name}\n"
            f"Description: {loc.description}\n"
            f"Connections: {connections}\n"
            f"NPCs present: {npcs}\n"
            f"Items present: {items}"
        )

    # --- Inventory ---
    inv = game_state.inventory
    if inv.items:
        item_lines = [f"- {it.name} (x{it.quantity}, {it.item_type.value})" for it in inv.items]
        sections.append(f"\n## Inventory\n" + "\n".join(item_lines))
    else:
        sections.append("\n## Inventory\nEmpty")

    # --- Recent events ---
    if game_state.recent_events:
        event_lines: list[str] = []
        for ev in game_state.recent_events:
            payload = ev.get("payload", {})
            reason = payload.get("reason", "")
            stat = payload.get("stat_name", "")
            etype = ev.get("event_type", "unknown")
            desc = f"{etype}"
            if stat:
                desc += f" ({stat}: {payload.get('old_value', '?')} → {payload.get('new_value', '?')})"
            if reason:
                desc += f" — {reason}"
            event_lines.append(f"- {desc}")
        sections.append(f"\n## Recent Events\n" + "\n".join(event_lines))

    return "\n".join(sections)
