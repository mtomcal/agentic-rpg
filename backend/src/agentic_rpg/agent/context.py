"""Context assembly for the agent graph."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agentic_rpg.agent.prompt import build_system_prompt
from agentic_rpg.models.game_state import GameState, MessageRole


def assemble_context(game_state: GameState, player_input: str) -> dict:
    """Assemble the full message list and context for the LLM.

    Builds a list of LangChain messages from:
    - A system prompt (derived from game state)
    - Conversation history (windowed)
    - The current player input

    Args:
        game_state: Current game state.
        player_input: The player's current action text.

    Returns:
        Dict with keys: messages, game_state (dict), system_prompt (str).
    """
    system_prompt = build_system_prompt(game_state)

    messages: list[SystemMessage | HumanMessage | AIMessage] = []

    # 1. System message with full game context
    messages.append(SystemMessage(content=system_prompt))

    # 2. Conversation history (windowed, most recent N messages)
    history = game_state.conversation.history
    window = game_state.conversation.window_size
    windowed = history[-window:] if len(history) > window else history

    for msg in windowed:
        if msg.role == MessageRole.player:
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == MessageRole.agent:
            messages.append(AIMessage(content=msg.content))
        # System messages from history are folded into the system prompt,
        # not added as separate SystemMessages.

    # 3. Player's current input
    messages.append(HumanMessage(content=player_input))

    return {
        "messages": messages,
        "game_state": game_state.model_dump(),
        "system_prompt": system_prompt,
    }
