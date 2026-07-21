"""
Python code execution for B.L.A.Z.E.

Adapted from `_execute_code` in the Blender MCP add-on's
`mcp_to_blender_server.py` (SPDX-FileCopyrightText: 2026 Blender Authors,
GPL-3.0-or-later).

The code contract is upstream's, because it is a good one and the model already
knows it:

- Assign the answer to a module-level `result` dict.
- `print()` output comes back alongside it.
- Define a `check_is_finished` callable to defer the response (see below).

The response *envelope* is cr8's, not upstream's. MCP replies
`{"status": "ok", "result": ...}`; the cr8 router checks for
`status == "success"` and B.L.A.Z.E reads `payload.data.message`, so we emit
`{"status": "success", "message": ..., "data": ...}` instead.
"""

import json
import logging
import traceback

from .capture_output import CaptureOutput
from .weak_sandbox import WeakSandboxForLLM

logger = logging.getLogger(__name__)

_RESULT_NOT_DICT_MESSAGE = (
    "The `result` variable must be a dict, not {:s}. "
    "Wrap your return value: `result = {{\"key\": value}}`"
)


class DeferredResult:
    """
    Returned instead of a dict when tool-code starts background work.

    Duck-typed against `cr8_router.registry.routing.deferred`: the router only
    looks for a callable `check_is_finished` attribute, so this addon does not
    need to import from the router extension.
    """

    __slots__ = ("check_is_finished", "stdout", "stderr")

    def __init__(self, check_is_finished, stdout: str = "", stderr: str = ""):
        self.check_is_finished = check_is_finished
        self.stdout = stdout
        self.stderr = stderr


def _with_captured(response: dict, captured: CaptureOutput) -> dict:
    """Attach captured output to a response, omitting empty streams."""
    if captured.stdout:
        response["stdout"] = captured.stdout
    if captured.stderr:
        response["stderr"] = captured.stderr
    return response


def execute_code(code: str) -> dict:
    """
    Execute `code` in a fresh namespace and return a cr8 command response.

    Returns a `DeferredResult` instead of a dict when the code defines
    `check_is_finished`.
    """
    namespace: dict = {"result": {}}

    with CaptureOutput() as captured, WeakSandboxForLLM():
        try:
            exec(code, namespace)
        except Exception:
            # The traceback is the payload here — it is what lets B.L.A.Z.E fix
            # its own code on the retry rather than repeating the same mistake.
            logger.info("execute_python raised; returning traceback to the agent")
            return _with_captured({
                "status": "error",
                "message": traceback.format_exc(),
                "error_code": "CODE_EXECUTION_FAILED",
            }, captured)

    # Background job in progress — the response is sent when it finishes.
    check_fn = namespace.get("check_is_finished")
    if callable(check_fn):
        logger.info("execute_python deferred: code defined check_is_finished")
        return DeferredResult(check_fn, captured.stdout, captured.stderr)

    result = namespace["result"]
    if not isinstance(result, dict):
        return _with_captured({
            "status": "error",
            "message": _RESULT_NOT_DICT_MESSAGE.format(type(result).__name__),
            "error_code": "INVALID_RESULT",
        }, captured)

    # Guard against code storing live Blender data, e.g.
    # `result = {"obj": bpy.context.active_object}`. Rather than erroring, fall
    # back to repr so the agent sees something useful and can move on — it is
    # not worth a round trip to correct a cosmetic mistake.
    try:
        result = json.loads(json.dumps(result, default=repr))
    except (TypeError, ValueError) as e:
        return _with_captured({
            "status": "error",
            "message": f"The `result` value could not be serialized: {e}",
            "error_code": "UNSERIALIZABLE_RESULT",
        }, captured)

    return _with_captured({
        "status": "success",
        "message": "Code executed successfully",
        "data": result,
    }, captured)
