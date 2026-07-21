"""
Command execution and result handling
"""

import json
import logging
import traceback

from .parameter_validator import ParameterValidator
from .deferred import is_deferred

logger = logging.getLogger(__name__)


def _json_safe(result: dict) -> dict:
    """
    Coerce a handler result into something Socket.IO can serialize.

    Handlers occasionally return live Blender data (a bpy.types.Object, a
    Vector, a set) either directly or nested inside `data`. Those raise at
    `sio.emit` time, far from the handler that caused it, and the command
    appears to hang because the engine's Future never resolves. Round-tripping
    through json with a repr fallback turns that class of bug into a readable
    string in the response.

    Applied at the router boundary so every addon gets the protection.
    """
    try:
        return json.loads(json.dumps(result, default=repr))
    except (TypeError, ValueError) as e:
        logger.error(f"Handler result could not be serialized: {e}")
        return {
            "status": "error",
            "message": f"Handler returned a result that cannot be serialized: {e}",
            "error_code": "UNSERIALIZABLE_RESULT",
        }


class CommandExecutor:
    """Executes commands on addon handlers"""

    def __init__(self, registry):
        """
        Initialize command executor

        Args:
            registry: AIAddonRegistry instance
        """
        self.registry = registry

    def execute_command(self, addon_id: str, command: str, params: dict, tool_spec: dict = None) -> dict:
        """
        Execute command on specific addon

        Args:
            addon_id: Target addon ID
            command: Command name
            params: Command parameters
            tool_spec: Optional tool specification for validation

        Returns:
            Command execution result
        """
        try:
            # Get addon handlers
            handlers = self.registry.get_addon_handlers(addon_id)
            if not handlers:
                return {
                    "status": "error",
                    "message": f"No handlers found for addon '{addon_id}'",
                    "error_code": "NO_HANDLERS"
                }

            # Find command handler
            if command not in handlers:
                available_commands = list(handlers.keys())
                return {
                    "status": "error",
                    "message": f"Command '{command}' not found in addon '{addon_id}'. Available: {available_commands}",
                    "error_code": "COMMAND_NOT_FOUND"
                }

            handler = handlers[command]

            # Validate parameters if tool spec is provided
            validated_params = params
            if tool_spec:
                try:
                    validated_params = ParameterValidator.validate_parameters(
                        params, tool_spec)
                except ValueError as e:
                    return {
                        "status": "error",
                        "message": f"Parameter validation failed: {str(e)}",
                        "error_code": "INVALID_PARAMETERS"
                    }

            # Execute the handler
            logger.info(
                f"Executing command '{command}' on addon '{addon_id}' with params: {validated_params}")

            result = handler(**validated_params)

            # A handler that started background work (render, bake, modal op)
            # returns a deferred carrier instead of a result. Pass it through
            # untouched — the caller parks the message_id and replies later.
            if is_deferred(result):
                logger.info(f"Command '{command}' deferred its response")
                return result

            # Ensure result follows standard format
            if not isinstance(result, dict):
                result = {
                    "status": "success",
                    "message": f"Command '{command}' executed successfully",
                    "data": result
                }

            # Ensure required fields
            if 'status' not in result:
                result['status'] = 'success'
            if 'message' not in result:
                result['message'] = f"Command '{command}' executed successfully"

            logger.info(
                f"Command '{command}' completed with status: {result['status']}")
            return _json_safe(result)

        except Exception as e:
            # Full traceback, not just str(e): this reaches B.L.A.Z.E as a
            # ModelRetry, and a stack trace is what lets it correct itself
            # instead of retrying the same broken call.
            logger.error(
                f"Error executing command '{command}' on addon '{addon_id}': {str(e)}")
            return {
                "status": "error",
                "message": f"Command execution failed: {str(e)}",
                "traceback": traceback.format_exc(),
                "error_code": "EXECUTION_FAILED"
            }
