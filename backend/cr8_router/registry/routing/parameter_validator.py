"""
Parameter validation orchestrator for command parameters
"""

import logging
from .type_validators import get_validator

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
        """
        Validate and convert a single parameter value

        Args:
            value: Parameter value to validate
            param_spec: Parameter specification

        Returns:
            Validated and converted value

        Raises:
            ValueError: If validation fails
        """
        param_type = param_spec['type']
        param_name = param_spec['name']

        # Handle None values
        if value is None:
            if param_spec.get('required', False):
                raise ValueError(
                    f"Required parameter {param_name} cannot be None")
            return value

        # Get validator for parameter type
        validator_class = get_validator(param_type)
        if not validator_class:
            logger.warning(f"Unknown parameter type: {param_type}, passing through")
            return value

        # Validate using type-specific validator
        return validator_class.validate(value, param_spec)
