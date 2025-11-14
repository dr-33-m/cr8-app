"""
AI Command Router - Routes commands to appropriate addon handlers
"""

import logging
from .addon_registry import AIAddonRegistry, AddonManifest

logger = logging.getLogger(__name__)


class ParameterValidator:
    """Validates command parameters against manifest specifications"""

    @staticmethod
    def validate_parameters(params: dict, tool_spec: dict) -> dict:
        """
        Validate and convert parameters according to tool specification

        Args:
            params: Raw parameters from command
            tool_spec: Tool specification from manifest

        Returns:
            Validated and converted parameters

        Raises:
            ValueError: If validation fails
        """
        validated_params = {}
        tool_params = tool_spec.get('parameters', [])

        # Create parameter lookup by name
        param_specs = {param['name']: param for param in tool_params}

        # Check required parameters
        for param_spec in tool_params:
            param_name = param_spec['name']
            is_required = param_spec.get('required', False)

            if is_required and param_name not in params:
                raise ValueError(f"Missing required parameter: {param_name}")

        # Validate and convert each parameter
        for param_name, param_value in params.items():
            if param_name not in param_specs:
                logger.warning(f"Unknown parameter: {param_name}")
                continue

            param_spec = param_specs[param_name]
            try:
                validated_value = ParameterValidator._validate_parameter_value(
                    param_value, param_spec
                )
                validated_params[param_name] = validated_value
            except Exception as e:
                raise ValueError(
                    f"Parameter '{param_name}' validation failed: {str(e)}")

        # Add default values for missing optional parameters
        for param_spec in tool_params:
            param_name = param_spec['name']
            if param_name not in validated_params and 'default' in param_spec:
                validated_params[param_name] = param_spec['default']

        return validated_params

    @staticmethod
    def _validate_parameter_value(value, param_spec):
        """Validate and convert a single parameter value"""
        param_type = param_spec['type']
        param_name = param_spec['name']

        # Handle None values
        if value is None:
            if param_spec.get('required', False):
                raise ValueError(
                    f"Required parameter {param_name} cannot be None")
            return value

        # Type conversion and validation
        if param_type == 'string':
            return str(value)

        elif param_type == 'integer':
            try:
                int_value = int(value)
                # Check range constraints
                if 'min' in param_spec and int_value < param_spec['min']:
                    raise ValueError(
                        f"Value {int_value} below minimum {param_spec['min']}")
                if 'max' in param_spec and int_value > param_spec['max']:
                    raise ValueError(
                        f"Value {int_value} above maximum {param_spec['max']}")
                return int_value
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{value}' to integer")

        elif param_type == 'float':
            try:
                float_value = float(value)
                # Check range constraints
                if 'min' in param_spec and float_value < param_spec['min']:
                    raise ValueError(
                        f"Value {float_value} below minimum {param_spec['min']}")
                if 'max' in param_spec and float_value > param_spec['max']:
                    raise ValueError(
                        f"Value {float_value} above maximum {param_spec['max']}")
                return float_value
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert '{value}' to float")

        elif param_type == 'boolean':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'yes', 'on'):
                    return True
                elif value.lower() in ('false', '0', 'no', 'off'):
                    return False
            raise ValueError(f"Cannot convert '{value}' to boolean")

        elif param_type == 'enum':
            options = param_spec.get('options', [])
            if value not in options:
                raise ValueError(
                    f"Value '{value}' not in allowed options: {options}")
            return value

        elif param_type == 'vector3':
            if isinstance(value, (list, tuple)) and len(value) == 3:
                try:
                    return [float(v) for v in value]
                except (ValueError, TypeError):
                    raise ValueError("Vector3 values must be numeric")
            raise ValueError(
                "Vector3 must be a list/tuple of 3 numeric values")

        elif param_type == 'color':
            # Validate hex color format
            if isinstance(value, str) and value.startswith('#') and len(value) == 7:
                try:
                    int(value[1:], 16)  # Validate hex digits
                    return value
                except ValueError:
                    raise ValueError("Invalid hex color format")
            raise ValueError("Color must be in hex format (#RRGGBB)")

        elif param_type in ['object_name', 'material_name', 'collection_name', 'file_path']:
            return str(value)

        else:
            logger.warning(f"Unknown parameter type: {param_type}")
            return value


class AICommandRouter:
    """Routes commands to appropriate addon handlers"""

    def __init__(self, registry: AIAddonRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)

    def route_command(self, command: str, params: dict, addon_id: str = None) -> dict:
        """
        Route command to appropriate addon handler

        Args:
            command: Command name to execute
            params: Command parameters
            addon_id: Optional specific addon to target

        Returns:
            Command execution result
        """
        try:
            # Find the target addon and tool
            target_addon, tool_spec = self._find_command_target(
                command, addon_id)

            if not target_addon or not tool_spec:
                return {
                    "status": "error",
                    "message": f"Command '{command}' not found",
                    "error_code": "COMMAND_NOT_FOUND"
                }

            # Execute the command
            return self.execute_command(target_addon, command, params, tool_spec)

        except Exception as e:
            self.logger.error(f"Error routing command '{command}': {str(e)}")
            return {
                "status": "error",
                "message": f"Command routing failed: {str(e)}",
                "error_code": "ROUTING_FAILED"
            }

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
            self.logger.info(
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

            self.logger.info(
                f"Command '{command}' completed with status: {result['status']}")
            return result

        except Exception as e:
            self.logger.error(
                f"Error executing command '{command}' on addon '{addon_id}': {str(e)}")
            return {
                "status": "error",
                "message": f"Command execution failed: {str(e)}",
                "error_code": "EXECUTION_FAILED"
            }

    def _find_command_target(self, command: str, preferred_addon_id: str = None):
        """
        Find which addon provides the specified command

        Args:
            command: Command name to find
            preferred_addon_id: Optional preferred addon to check first

        Returns:
            Tuple of (addon_id, tool_spec) or (None, None) if not found
        """
        # If specific addon is requested, check it first
        if preferred_addon_id:
            manifest = self.registry.get_addon_manifest(preferred_addon_id)
            if manifest:
                tool_spec = manifest.get_tool_by_name(command)
                if tool_spec:
                    return preferred_addon_id, tool_spec

        # Search all registered addons
        for addon_id, manifest in self.registry.get_registered_addons().items():
            if preferred_addon_id and addon_id == preferred_addon_id:
                continue  # Already checked above

            tool_spec = manifest.get_tool_by_name(command)
            if tool_spec:
                return addon_id, tool_spec

        return None, None

    def get_available_commands(self) -> dict:
        """Get all available commands grouped by addon"""
        commands_by_addon = {}

        for addon_id, manifest in self.registry.get_registered_addons().items():
            addon_name = manifest.addon_info.get('name', addon_id)
            commands = []

            for tool in manifest.get_tools():
                commands.append({
                    'name': tool['name'],
                    'description': tool['description'],
                    'usage': tool['usage'],
                    'parameters': tool.get('parameters', []),
                    'examples': tool.get('examples', [])
                })

            if commands:
                commands_by_addon[addon_id] = {
                    'addon_name': addon_name,
                    'commands': commands
                }

        return commands_by_addon

    def validate_command_exists(self, command: str, addon_id: str = None) -> bool:
        """Check if a command exists in the system"""
        target_addon, tool_spec = self._find_command_target(command, addon_id)
        return target_addon is not None and tool_spec is not None
