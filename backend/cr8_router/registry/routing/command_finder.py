"""
Command discovery and lookup functionality
"""

import logging

logger = logging.getLogger(__name__)


class CommandFinder:
    """Finds and discovers available commands in the addon registry"""

    def __init__(self, registry):
        """
        Initialize command finder

        Args:
            registry: AIAddonRegistry instance
        """
        self.registry = registry

    def find_command_target(self, command: str, preferred_addon_id: str = None):
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
        """
        Get all available commands grouped by addon

        Returns:
            Dictionary mapping addon_id to command information
        """
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
        """
        Check if a command exists in the system

        Args:
            command: Command name to check
            addon_id: Optional specific addon to check

        Returns:
            True if command exists, False otherwise
        """
        target_addon, tool_spec = self.find_command_target(command, addon_id)
        return target_addon is not None and tool_spec is not None

    def get_command_info(self, command: str, addon_id: str = None) -> dict:
        """
        Get detailed information about a command

        Args:
            command: Command name
            addon_id: Optional specific addon

        Returns:
            Command information or empty dict if not found
        """
        target_addon, tool_spec = self.find_command_target(command, addon_id)
        if not target_addon or not tool_spec:
            return {}

        return {
            'addon_id': target_addon,
            'command': command,
            'description': tool_spec.get('description', ''),
            'usage': tool_spec.get('usage', ''),
            'parameters': tool_spec.get('parameters', []),
            'examples': tool_spec.get('examples', [])
        }
