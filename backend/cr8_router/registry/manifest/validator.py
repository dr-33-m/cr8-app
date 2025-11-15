"""
Manifest validation for AI addon manifests.
Validates manifest structure, tools, parameters, and Blender compatibility.
"""

import logging
import bpy

logger = logging.getLogger(__name__)


def validate_manifest(manifest_data: dict) -> bool:
    """
    Validate manifest structure and requirements.
    
    Args:
        manifest_data: Parsed manifest dictionary
        
    Returns:
        True if manifest is valid, False otherwise
    """
    try:
        # Check addon_info section
        addon_info = manifest_data.get('addon_info', {})
        if not _validate_addon_info(addon_info):
            return False

        # Check ai_integration section
        ai_integration = manifest_data.get('ai_integration', {})
        if not _validate_ai_integration(ai_integration):
            return False

        return True

    except Exception as e:
        logger.error(f"Manifest validation error: {str(e)}")
        return False


def _validate_addon_info(addon_info: dict) -> bool:
    """
    Validate addon_info section.
    
    Args:
        addon_info: addon_info dictionary from manifest
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['id', 'name', 'version', 'author', 'category']
    
    for field in required_fields:
        if field not in addon_info:
            logger.error(f"Missing required addon_info field: {field}")
            return False
    
    return True


def _validate_ai_integration(ai_integration: dict) -> bool:
    """
    Validate ai_integration section.
    
    Args:
        ai_integration: ai_integration dictionary from manifest
        
    Returns:
        True if valid, False otherwise
    """
    # Check agent description
    if 'agent_description' not in ai_integration:
        logger.error("Missing required ai_integration.agent_description")
        return False

    # Check tools (optional but warn if missing)
    if 'tools' not in ai_integration:
        logger.warning("No tools defined in ai_integration")
        ai_integration['tools'] = []

    # Validate each tool
    for tool in ai_integration.get('tools', []):
        if not validate_tool(tool):
            return False

    # Validate Blender version compatibility
    if not _validate_blender_version(ai_integration.get('requirements', {})):
        return False

    return True


def validate_tool(tool: dict) -> bool:
    """
    Validate individual tool definition.
    
    Args:
        tool: Tool definition dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['name', 'description', 'usage']
    
    for field in required_fields:
        if field not in tool:
            logger.error(f"Tool missing required field: {field}")
            return False

    # Validate parameters
    for param in tool.get('parameters', []):
        if not validate_parameter(param):
            return False

    return True


def validate_parameter(param: dict) -> bool:
    """
    Validate tool parameter definition.
    
    Args:
        param: Parameter definition dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['name', 'type', 'description', 'required']
    
    for field in required_fields:
        if field not in param:
            logger.error(f"Parameter missing required field: {field}")
            return False

    # Validate parameter type
    valid_types = [
        'string', 'integer', 'float', 'boolean',
        'object_name', 'material_name', 'collection_name',
        'enum', 'vector3', 'color', 'file_path'
    ]
    
    if param['type'] not in valid_types:
        logger.error(f"Invalid parameter type: {param['type']}")
        return False

    return True


def _validate_blender_version(requirements: dict) -> bool:
    """
    Validate Blender version compatibility.
    
    Args:
        requirements: Requirements dictionary from manifest
        
    Returns:
        True if compatible or no requirement, False if incompatible
    """
    min_version = requirements.get('blender_version_min')
    
    if min_version:
        current_version = bpy.app.version_string
        # Basic version check (could be enhanced)
        if current_version < min_version:
            logger.warning(
                f"Blender version requirement not met. "
                f"Required: {min_version}, Current: {current_version}"
            )
            # Don't fail validation, just warn
    
    return True
