"""
Command handlers for the Blaze Script addon.
"""

import logging
import os

from ..executor import execute_code

logger = logging.getLogger(__name__)

# Kill switch. Checked here rather than at AI_COMMAND_HANDLERS registration
# because the router builds B.L.A.Z.E's tool list from addon_ai.json on disk,
# independently of which handlers exist — withholding the handler would leave a
# phantom tool failing with an opaque NO_HANDLERS. Refusing here gives the agent
# a message it can actually act on.
_ENABLE_ENV_VAR = "CR8_ALLOW_CODE_EXEC"

_DISABLED_MESSAGE = (
    "Python execution is disabled on this instance "
    f"({_ENABLE_ENV_VAR}=0). Use the dedicated scene tools instead."
)


def _is_enabled() -> bool:
    """Return whether code execution is permitted. Defaults to on."""
    return os.environ.get(_ENABLE_ENV_VAR, "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def handle_execute_python(code: str) -> dict:
    """
    Execute Python code inside Blender on behalf of B.L.A.Z.E.

    Args:
        code: Python source. Assigns its answer to a `result` dict, or defines
              `check_is_finished` to defer the response for long-running work.

    Returns:
        A command response dict, or a DeferredResult the router will poll.
    """
    if not _is_enabled():
        logger.warning("execute_python called while disabled by %s", _ENABLE_ENV_VAR)
        return {
            "status": "error",
            "message": _DISABLED_MESSAGE,
            "error_code": "CODE_EXECUTION_DISABLED",
        }

    if not isinstance(code, str) or not code.strip():
        return {
            "status": "error",
            "message": "No code provided. Pass Python source in the `code` parameter.",
            "error_code": "INVALID_PARAMETERS",
        }

    logger.info("Executing agent-authored Python (%d chars)", len(code))
    return execute_code(code)
