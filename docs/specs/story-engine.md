# Story Engine Specification

## Overview

The story engine manages narrative coherence across a player's entire session. It generates a loose story outline before play begins, tracks the player's progress through it, and adapts the outline when the player makes unexpected choices. The goal is to provide a "north star" narrative that gives the story direction without railroading the player.

## Core Concepts

### Story Outline

A story outline is a structured plan for the narrative arc. It consists of:

- **Premise**: A 2-3 sentence summary of the overall story (e.g., "A disgraced knight seeks redemption by recovering a stolen relic from the Shadowlands")
- **Setting**: The world, tone, genre, and key locations
- **Beats**: An ordered sequence of 5-10 narrative beats that form the story arc
- **Current beat**: Which beat the player is currently in or approaching
- **Adaptation history**: A log of how the outline has changed due to player choices

### Story Beats

A beat is a planned narrative moment. Each beat has:

- **Summary**: What should happen at this point in the story (1-2 sentences)
- **Location**: Where this beat takes place (or "any" if location-independent)
- **Trigger conditions**: What causes this beat to activate (player arrives at a location, completes an objective, enough time passes, etc.)
- **Key elements**: NPCs, items, or events that should be present
- **Player objectives**: What the player can/should do during this beat
- **Possible outcomes**: 2-3 ways this beat might resolve, affecting the subsequent outline
- **Flexibility rating**: How much this beat can change (fixed, flexible, optional)

Beats are not rigid scripts. They're guide points. The agent uses them to keep the story moving in a coherent direction while still responding naturally to what the player does.

### Beat Lifecycle

```
planned → active → resolved
                 → skipped (player bypassed it)
                 → adapted (player changed it significantly)
```

## Outline Generation

When a new game session starts:

1. The player selects or describes a genre/setting
2. The player creates a character (name, profession, background)
3. The agent generates a story outline based on the setting + character:
   - Creates a premise that fits the character's background
   - Generates 5-10 beats forming a narrative arc (setup → rising action → climax → resolution)
   - Assigns locations and trigger conditions to each beat
4. The outline is stored as part of the game state
5. The first beat becomes active and the game begins

The outline generation is itself an LLM call with a specific prompt and output schema. The agent does not use tools during outline generation — it produces the outline as structured output.

## Outline Adaptation

The outline adapts when the player diverges from expectations. Adaptation triggers:

- **Player skips a beat**: They leave a location or ignore an objective. Mark the beat as skipped, and regenerate downstream beats to account for the gap.
- **Player takes an unexpected action**: Something significant that the outline didn't predict. Log the divergence, then regenerate the remaining beats to incorporate the new direction.
- **Beat resolves differently than expected**: The outcome changes the story trajectory. Update subsequent beats accordingly.
- **Player explicitly changes direction**: "I don't want to go to the castle, I want to sail west." Regenerate the outline with the new direction.

### Adaptation Process

1. Identify what changed (which beat, what the player did)
2. Assess the impact on remaining beats (minor tweak vs. major rewrite)
3. Call the LLM with the current outline, the change, and a request to adapt
4. Replace the remaining unresolved beats with the new plan
5. Log the adaptation in the adaptation history
6. Continue play with the updated outline

### Adaptation Constraints

- Never retroactively change resolved beats (what happened, happened)
- The premise can evolve but shouldn't completely change unless the player explicitly drives it
- Maintain at least 3 future beats at all times — if beats are running out, generate more
- Adaptation frequency: don't re-plan on every minor action. Only adapt when something structurally changes the narrative.

## Story State

The story engine maintains:

- **Current outline**: The full outline with beat statuses
- **Active beat**: The beat currently in play
- **Adaptation history**: A log of every adaptation with before/after and the reason
- **Story summary**: A running summary of what has happened so far (used for context assembly)

The story summary is updated after each beat resolves. It's a condensed narrative of the player's journey so far, used to keep the agent grounded in what has already happened.

## Integration with the Agent

The agent receives the story outline as part of its context (see [Agent System](agent-system.md)). Specifically:

- The **premise** and **active beat** are always in context
- The **next 2-3 upcoming beats** are included as summaries so the agent can foreshadow
- The **story summary** (resolved beats) is included to maintain continuity
- The agent does **not** reveal upcoming beats to the player directly

The agent has narrative tools to:
- Mark a beat as resolved (with the outcome)
- Request an outline adaptation
- Advance to the next beat
- Add an unplanned beat (player-driven side quest)

## Future Extensions

- **Branching arcs**: Multiple parallel story threads the player can pursue
- **Recurring themes**: The engine tracks themes (betrayal, redemption, discovery) and weaves them through beats
- **NPC arcs**: NPCs have their own mini story arcs that intersect with the main story
- **World events**: Background events that happen regardless of player action, creating a living world
