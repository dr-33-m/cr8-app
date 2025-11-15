"""
Type-specific parameter validators for command parameters
"""

import logging

logger = logging.getLogger(__name__)


class StringValidator:
    """Validates string parameters"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert value to string"""
        return str(value)


class IntegerValidator:
    """Validates integer parameters with optional range constraints"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert value to integer"""
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


class FloatValidator:
    """Validates float parameters with optional range constraints"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert value to float"""
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


class BooleanValidator:
    """Validates boolean parameters"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert value to boolean"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ('true', '1', 'yes', 'on'):
                return True
            elif value.lower() in ('false', '0', 'no', 'off'):
                return False
        raise ValueError(f"Cannot convert '{value}' to boolean")


class EnumValidator:
    """Validates enum parameters against allowed options"""

    @staticmethod
    def validate(value, param_spec):
        """Validate value is in allowed options"""
        options = param_spec.get('options', [])
        if value not in options:
            raise ValueError(
                f"Value '{value}' not in allowed options: {options}")
        return value


class Vector3Validator:
    """Validates 3D vector parameters"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert value to vector3 (list of 3 floats)"""
        if isinstance(value, (list, tuple)) and len(value) == 3:
            try:
                return [float(v) for v in value]
            except (ValueError, TypeError):
                raise ValueError("Vector3 values must be numeric")
        raise ValueError(
            "Vector3 must be a list/tuple of 3 numeric values")


class ColorValidator:
    """Validates color parameters in hex format"""

    @staticmethod
    def validate(value, param_spec):
        """Validate color in hex format (#RRGGBB)"""
        if isinstance(value, str) and value.startswith('#') and len(value) == 7:
            try:
                int(value[1:], 16)  # Validate hex digits
                return value
            except ValueError:
                raise ValueError("Invalid hex color format")
        raise ValueError("Color must be in hex format (#RRGGBB)")


class NameValidator:
    """Validates name parameters (object_name, material_name, collection_name)"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert name to string"""
        return str(value)


class FilePathValidator:
    """Validates file path parameters"""

    @staticmethod
    def validate(value, param_spec):
        """Validate and convert file path to string"""
        return str(value)


# Validator registry mapping parameter types to validators
VALIDATOR_REGISTRY = {
    'string': StringValidator,
    'integer': IntegerValidator,
    'float': FloatValidator,
    'boolean': BooleanValidator,
    'enum': EnumValidator,
    'vector3': Vector3Validator,
    'color': ColorValidator,
    'object_name': NameValidator,
    'material_name': NameValidator,
    'collection_name': NameValidator,
    'file_path': FilePathValidator,
}


def get_validator(param_type: str):
    """
    Get validator for parameter type

    Args:
        param_type: Parameter type name

    Returns:
        Validator class or None if not found
    """
    validator = VALIDATOR_REGISTRY.get(param_type)
    if not validator:
        logger.warning(f"Unknown parameter type: {param_type}")
    return validator
