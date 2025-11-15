"""
AI Command Router - Routes commands to appropriate addon handlers

This module provides the main command routing orchestrator that composes
specialized routing components for parameter validation, command discovery,
and command execution.
"""

import logging
from .addon_registry import AIAddonRegistry
from .routing import ParameterValidator, CommandFinder, CommandExecutor

logger = logging.getLogger(__name__)


class AICommandRouter:
    """Routes commands to appropriate addon handlers
    
    Thin orchestrator that composes specialized routing components:
    - CommandFinder: Discovers and locates commands
    - CommandExecutor: Executes commands on handlers
    - ParameterValidator: Validates command parameters
    """

    def __init__(self, registry: AIAddonRegistry):
        self.registry = registry
        self.logger = logging.getLogger(__name__)
        self.finder = CommandFinder(registry)
        self.executor = CommandExecutor(registry)

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
            # Delegate to CommandFinder to locate the command
            target_addon, tool_spec = self.finder.find_command_target(
                command, addon_id)

            if not target_addon or not tool_spec:
                return {
                    "status": "error",
                    "message": f"Command '{command}' not found",
                    "error_code": "COMMAND_NOT_FOUND"
                }

            # Delegate to CommandExecutor to execute the command
            return self.executor.execute_command(target_addon, command, params, tool_spec)

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

        Delegates to CommandExecutor for actual execution.

        Args:
            addon_id: Target addon ID
            command: Command name
            params: Command parameters
            tool_spec: Optional tool specification for validation

        Returns:
            Command execution result
        """
        return self.executor.execute_command(addon_id, command, params, tool_spec)

    def _find_command_target(self, command: str, preferred_addon_id: str = None):
        """
        Find which addon provides the specified command

        Delegates to CommandFinder for actual lookup.

        Args:
            command: Command name to find
            preferred_addon_id: Optional preferred addon to check first

        Returns:
            Tuple of (addon_id, tool_spec) or (None, None) if not found
        """
        return self.finder.find_command_target(command, preferred_addon_id)

    def get_available_commands(self) -> dict:
        """Get all available commands grouped by addon
        
        Delegates to CommandFinder for discovery.
        """
        return self.finder.get_available_commands()

    def validate_command_exists(self, command: str, addon_id: str = None) -> bool:
        """Check if a command exists in the system
        
        Delegates to CommandFinder for validation.
        """
        return self.finder.validate_command_exists(command, addon_id)
