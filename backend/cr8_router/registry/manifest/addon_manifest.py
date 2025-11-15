"""
AddonManifest - Data container for parsed addon manifests.
Represents a validated addon manifest with access to tools and metadata.
"""

import logging
from pathlib import Path
from . import validator

logger = logging.getLogger(__name__)


class AddonManifest:
    """Represents a parsed and validated addon manifest"""

    def __init__(self, addon_id: str, manifest_data: dict, addon_path: Path):
        """
        Initialize an addon manifest.
        
        Args:
            addon_id: Unique identifier for the addon
            manifest_data: Parsed manifest dictionary
            addon_path: Path to the addon directory
        """
        self.addon_id = addon_id
        self.manifest_data = manifest_data
        self.addon_path = addon_path

        # Parse core info
        self.addon_info = manifest_data.get('addon_info', {})
        self.ai_integration = manifest_data.get('ai_integration', {})

        # Validation
        self.is_valid = validator.validate_manifest(manifest_data)

    def get_tools(self) -> list:
        """
        Get list of tools provided by this addon.
        
        Returns:
            List of tool definitions
        """
        return self.ai_integration.get('tools', [])

    def get_tool_by_name(self, tool_name: str):
        """
        Get specific tool by name.
        
        Args:
            tool_name: Name of the tool to retrieve
            
        Returns:
            Tool definition if found, None otherwise
        """
        for tool in self.get_tools():
            if tool['name'] == tool_name:
                return tool
        return None
