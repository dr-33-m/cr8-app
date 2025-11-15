"""
Command execution and result handling
"""

import logging
from .parameter_validator import ParameterValidator

logger = logging.getLogger(__name__)


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

            # Ensure result follows standard format
            if not isinstance(result, dict):
                result = {
                    "status": "success",
                    "message": str(result),
                    "data": result
                }

            # Ensure required fields
            if 'status' not in result:
                result['status'] = 'success'
            if 'message' not in result:
                result['message'] = f"Command '{command}' executed successfully"

            logger.info(
                f"Command '{command}' completed with status: {result['status']}")
            return result

        except Exception as e:
            logger.error(
                f"Error executing command '{command}' on addon '{addon_id}': {str(e)}")
            return {
                "status": "error",
                "message": f"Command execution failed: {str(e)}",
                "error_code": "EXECUTION_FAILED"
            }
