"""
Deferred command results for long-running Blender operations.

Adapted from the Blender MCP add-on's `deferred_tool.py`
(SPDX-FileCopyrightText: 2026 Blender Authors, GPL-3.0-or-later).

Commands normally run to completion inside the main-thread command drainer and
reply immediately. That does not work for anything slow — a render, a bake, a
modal operator invoked with INVOKE_DEFAULT — because the drainer is the only
thing servicing incoming commands, and blocking it also stalls the WebRTC
viewport stream.

A handler can instead return a *deferred result*: any object exposing a callable
`check_is_finished` attribute. The command's `message_id` is parked here and the
checker is polled on a Blender timer until it returns a dict, at which point the
response is sent with the original message_id and route. The engine side needs no
changes — `CommandExecutor._send_command_and_wait_response` already awaits its
Future without a timeout.

Deferred results are duck-typed rather than isinstance-checked so that addons
shipped as separate extensions (cr8_script, cr8_sets, ...) can define their own
carrier class without importing from cr8_router. The contract is:

    result.check_is_finished()  -> None while pending, dict when done
    result.stdout / result.stderr  (optional str, merged into the response)

Checkers must be cheap — they run on the main thread — and must return promptly
once the work is done so the user is not left waiting.
"""

import logging
import time
import traceback

import bpy

logger = logging.getLogger(__name__)

# Wall-time allowed for a deferred operation before we give up and report an
# error. The underlying Blender job keeps running; only the reply is abandoned.
# One hour is long for an interactive session, but renders are renders.
DEFERRED_TIMEOUT = 60.0 * 60.0

# Seconds between checker polls. Matches the command drainer's active rate so a
# finished job is reported promptly without adding meaningful idle load.
_POLL_INTERVAL = 0.1


class DeferredResult:
    """
    Carrier a handler returns to defer its response.

    In-tree convenience class. Addons packaged separately may define their own
    equivalent — only the duck-typed `check_is_finished` attribute matters.
    """

    __slots__ = ("check_is_finished", "stdout", "stderr")

    def __init__(self, check_is_finished, stdout: str = "", stderr: str = ""):
        self.check_is_finished = check_is_finished
        self.stdout = stdout
        self.stderr = stderr


class _PendingCommand:
    """A command awaiting completion of its background work."""

    __slots__ = ("result", "command", "message_id", "route", "deadline")

    def __init__(self, result, command: str, message_id: str, route: str):
        self.result = result
        self.command = command
        self.message_id = message_id
        self.route = route
        self.deadline = time.monotonic() + DEFERRED_TIMEOUT


_pending: list = []


def is_deferred(result) -> bool:
    """Return True if a handler's return value defers its response."""
    return callable(getattr(result, "check_is_finished", None))


def _send(pending: _PendingCommand, success: bool, data: dict) -> None:
    """Send the final response for a pending command and retire it."""
    # Imported lazily — this module is loaded during registry construction,
    # before the ws package has finished wiring itself up.
    from ...ws.utils.response_manager import ResponseManager

    for stream in ("stdout", "stderr"):
        captured = getattr(pending.result, stream, "")
        if captured:
            data.setdefault(stream, captured)

    try:
        ResponseManager.get_instance().send_response(
            f"{pending.command}_result",
            success,
            data,
            pending.message_id,
            route=pending.route,
        )
    except Exception as e:
        logger.error(f"Failed to send deferred response for {pending.command}: {e}")

    try:
        _pending.remove(pending)
    except ValueError:
        pass


def _poll():
    """
    Blender timer callback: check every pending command for completion.

    Returns the next interval, or None once nothing is pending (which
    unregisters the timer until the next deferred command arrives).
    """
    for pending in _pending[:]:
        if time.monotonic() > pending.deadline:
            logger.warning(
                f"Deferred command '{pending.command}' timed out after "
                f"{DEFERRED_TIMEOUT:.0f}s"
            )
            _send(pending, False, {
                "status": "error",
                "message": (
                    f"Operation timed out after {DEFERRED_TIMEOUT:.0f} seconds. "
                    "The Blender job may still be running."
                ),
                "error_code": "DEFERRED_TIMEOUT",
            })
            continue

        try:
            result = pending.result.check_is_finished()
        except Exception:
            logger.error(f"Deferred checker for '{pending.command}' raised")
            _send(pending, False, {
                "status": "error",
                "message": traceback.format_exc(),
                "error_code": "DEFERRED_CHECK_FAILED",
            })
            continue

        if result is None:
            # Still working.
            continue

        if not isinstance(result, dict):
            _send(pending, False, {
                "status": "error",
                "message": (
                    "check_is_finished must return None or a dict, not "
                    f"{type(result).__name__}"
                ),
                "error_code": "INVALID_DEFERRED_RESULT",
            })
            continue

        result.setdefault("status", "success")
        result.setdefault("message", f"Command '{pending.command}' completed")
        logger.info(f"Deferred command '{pending.command}' finished")
        _send(pending, result.get("status") == "success", result)

    if not _pending:
        return None
    return _POLL_INTERVAL


def register(result, command: str, message_id: str, route: str = "direct") -> None:
    """
    Park a command's response until its background work reports completion.

    Args:
        result: The deferred carrier returned by the handler
        command: Command name, used to build the response event name
        message_id: Original message ID the engine is awaiting
        route: Route to preserve on the eventual response
    """
    _pending.append(_PendingCommand(result, command, message_id, route))
    logger.info(
        f"Deferred command '{command}' (message_id={message_id}); "
        f"{len(_pending)} pending"
    )

    if not bpy.app.timers.is_registered(_poll):
        bpy.app.timers.register(_poll, first_interval=_POLL_INTERVAL)


def close_all() -> None:
    """
    Drop all pending deferred commands without responding.

    Called on disconnect: the engine-side Futures die with the session, and
    letting stale work resolve into a fresh session would emit responses for
    message IDs nobody is waiting on.
    """
    if _pending:
        logger.info(f"Dropping {len(_pending)} pending deferred command(s)")
    _pending.clear()

    if bpy.app.timers.is_registered(_poll):
        try:
            bpy.app.timers.unregister(_poll)
        except Exception as e:
            logger.warning(f"Could not unregister deferred poll timer: {e}")
