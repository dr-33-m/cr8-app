"""
Conversation Store - Per-user Pydantic AI message history.

B.L.A.Z.E used to call agent.run() with no message_history, so every message was
a fresh conversation and follow-ups like "now move it to the left" had nothing to
refer back to. This keeps the last few turns per user so that works.

The agent itself is a process-wide singleton (see namespaces/browser/singleton.py),
so history has to be keyed by username — the only session identity this codebase has.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# How many user turns to remember. Each turn is a user prompt plus every model
# response and tool exchange it triggered, which for a tool-heavy request can be
# a dozen messages — so this is deliberately modest.
DEFAULT_MAX_TURNS = 8


def _is_turn_start(message: Any) -> bool:
    """True if this message opens a new user turn (carries a user prompt)."""
    for part in getattr(message, 'parts', []) or []:
        if getattr(part, 'part_kind', None) == 'user-prompt':
            return True
    return False


def trim_to_recent_turns(messages: List[Any], max_turns: int = DEFAULT_MAX_TURNS) -> List[Any]:
    """
    Drop the oldest turns, cutting only on turn boundaries.

    Trimming to a flat message count is not safe here: it can strip a tool call
    while leaving its tool return behind, which providers reject. Cutting at
    user-prompt boundaries always leaves a well-formed conversation.
    """
    turn_starts = [i for i, m in enumerate(messages) if _is_turn_start(m)]
    if len(turn_starts) <= max_turns:
        return messages
    return messages[turn_starts[-max_turns]:]


class ConversationStore:
    """In-memory conversation history, keyed by username."""

    def __init__(self, max_turns: int = DEFAULT_MAX_TURNS):
        self.max_turns = max_turns
        self._histories: Dict[str, List[Any]] = {}
        self.logger = logging.getLogger(__name__)

    def get(self, username: str) -> List[Any]:
        """History to feed into the next run. Empty list for an unknown user."""
        return self._histories.get(username, [])

    def replace(self, username: str, messages: List[Any]) -> None:
        """
        Set a user's history to the full message list of a completed run.

        Takes the whole list (result.all_messages()) rather than appending
        new_messages(), so a run that was itself given history doesn't end up
        storing it twice.
        """
        if not messages:
            return
        trimmed = trim_to_recent_turns(list(messages), self.max_turns)
        self._histories[username] = trimmed
        self.logger.debug(
            f"Stored {len(trimmed)} messages for {username} "
            f"(trimmed from {len(messages)})"
        )

    def clear(self, username: str) -> None:
        """Forget a user's conversation."""
        if self._histories.pop(username, None) is not None:
            self.logger.info(f"Cleared conversation history for {username}")
