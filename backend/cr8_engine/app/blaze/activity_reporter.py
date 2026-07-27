"""
Activity Reporter - Streams B.L.A.Z.E's progress to the browser mid-run.

An agent run can take a long time and, until now, said nothing until it was
finished. This turns Pydantic AI's stream events into AGENT_PROCESSING messages
so the UI can show which tool is running instead of a silent wait.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Activity lines are for glancing at, and tool payloads can be enormous (the
# addon registry dump alone is ~100KB). Never let one through untrimmed.
MAX_DETAIL_CHARS = 200

# Tool names are mechanical; these read better in a chat feed.
FRIENDLY_TOOL_NAMES = {
    'process_inbox_assets': 'Downloading assets',
    'list_scene_objects': 'Checking the scene',
    'clear_inbox_tool': 'Clearing the inbox',
    'execute_python': 'Running Python in Blender',
    'search_polyhaven_assets': 'Searching Polyhaven',
    'download_polyhaven_asset': 'Downloading from Polyhaven',
    'find_and_add_polyhaven_asset': 'Finding and adding an asset',
}


def _friendly(tool_name: Optional[str]) -> str:
    """
    Turn a tool name into something worth reading in the chat feed.

    tool_name is genuinely optional: RetryPromptPart.tool_name is None when the
    retry is not tied to a specific tool (an output-validation retry, say).
    """
    if not tool_name:
        return 'A step'
    if tool_name in FRIENDLY_TOOL_NAMES:
        return FRIENDLY_TOOL_NAMES[tool_name]
    return tool_name.replace('_', ' ').capitalize()


def _truncate(text: str) -> str:
    text = str(text)
    return text if len(text) <= MAX_DETAIL_CHARS else text[:MAX_DETAIL_CHARS] + '…'


class ActivityReporter:
    """Bridges Pydantic AI stream events to AGENT_PROCESSING socket messages."""

    def __init__(self, browser_namespace, username: str, message_id: Optional[str] = None):
        self.browser_namespace = browser_namespace
        self.username = username
        self.message_id = message_id
        self.logger = logging.getLogger(__name__)
        # Tools whose completion we've already announced, so a retry or a
        # duplicate event doesn't post the same line twice.
        self._announced_text = False

    async def _emit(self, phase: str, message: str, **data: Any) -> None:
        """Best-effort push. Never raises into the agent run."""
        try:
            await self.browser_namespace.send_agent_processing(
                username=self.username,
                phase=phase,
                message=_truncate(message),
                data={k: _truncate(v) for k, v in data.items() if v is not None} or None,
                message_id=self.message_id,
            )
        except Exception as e:
            self.logger.debug(f"Activity emit failed ({phase}): {e}")

    async def started(self) -> None:
        """Announce the turn before the first model call goes out."""
        await self._emit('started', 'Thinking…')

    def handler(self):
        """
        Build the callable Pydantic AI expects for `event_stream_handler`.

        Signature is (RunContext, AsyncIterable[AgentStreamEvent]) -> Awaitable[None]
        (pydantic_ai.agent.abstract.EventStreamHandler).
        """
        async def event_stream_handler(ctx, stream):
            # The stream MUST be drained to completion. pydantic-ai's
            # CallToolsNode sets `self._next_node` at the very end of the
            # generator body, after the last event is yielded, and then asserts
            # on it: "the stream should set `self._next_node` before it ends"
            # (_agent_graph.py:550). Breaking out of this loop early — including
            # by letting an exception escape — kills the whole agent run.
            #
            # So the guard goes *inside* the loop: one bad event is skipped, the
            # iteration continues, and reporting can never break execution.
            async for event in stream:
                try:
                    await self._handle_event(event)
                except Exception as e:
                    self.logger.warning(
                        f"Skipped an activity event ({getattr(event, 'event_kind', '?')}): {e}"
                    )

        return event_stream_handler

    async def _handle_event(self, event: Any) -> None:
        kind = getattr(event, 'event_kind', None)

        if kind == 'function_tool_call':
            tool_name = getattr(event.part, 'tool_name', 'a tool')
            await self._emit('tool_call', f"{_friendly(tool_name)}…", tool=tool_name)

        elif kind == 'function_tool_result':
            tool_name = getattr(event.result, 'tool_name', 'a tool')
            # RetryPromptPart means the tool call failed and the model is being
            # asked to try again — worth showing, it explains a long wait.
            failed = getattr(event.result, 'part_kind', '') == 'retry-prompt'
            if failed:
                await self._emit('tool_retry', f"{_friendly(tool_name)} failed, retrying…",
                                 tool=tool_name)
            else:
                await self._emit('tool_result', f"{_friendly(tool_name)} — done", tool=tool_name)

        elif kind == 'part_start':
            # The model has started composing prose rather than calling a tool,
            # which in practice means the answer is on its way. Once per run.
            part_kind = getattr(getattr(event, 'part', None), 'part_kind', '')
            if part_kind == 'text' and not self._announced_text:
                self._announced_text = True
                await self._emit('responding', 'Writing a response…')
