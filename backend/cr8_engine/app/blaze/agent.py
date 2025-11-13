"""
B.L.A.Z.E Agent - Main Pydantic AI Agent Orchestrator
Processes natural language requests and executes scene manipulations.
"""

import logging
import os
from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import FunctionToolset
from .providers import create_provider_from_env
from .screenshot_manager import ScreenshotManager
from .command_executor import CommandExecutor
from .toolset_builder import ToolsetBuilder
from .message_processor import MessageProcessor
from .local_tools import clear_inbox

logger = logging.getLogger(__name__)


class BlazeAgent:
    """Main B.L.A.Z.E agent for natural language scene control"""

    def __init__(self, browser_namespace, blender_namespace):
        """Initialize B.L.A.Z.E agent with Socket.IO namespaces"""
        self.logger = logging.getLogger(__name__)

        self.browser_namespace = browser_namespace
        self.blender_namespace = blender_namespace

        # Current username and route for tool execution context
        self.current_username = None
        self.current_route = 'agent'  # Default route for agent-initiated commands

        # Initialize specialized modules
        self.screenshot_manager = ScreenshotManager()
        self.command_executor = CommandExecutor(self, self.screenshot_manager)
        self.toolset_builder = ToolsetBuilder(self)
        self.message_processor = MessageProcessor(self)

        # Create AI model using the new provider system
        try:
            self.model = create_provider_from_env()
        except Exception as e:
            self.logger.error(f"Failed to create AI provider: {e}")
            raise

        # Initialize Pydantic AI agent with dynamic toolsets
        self.agent = Agent(
            self.model,
            deps_type=Dict[str, Any],
            system_prompt="""You are B.L.A.Z.E (Blender's Artistic Zen Engineer), an intelligent assistant that helps users control 3D scenes in Blender through natural language.

## Important Workflow for Inbox Assets

When users request to download assets from their inbox:
1. Use process_inbox_assets() to download and import the assets into the scene
2. After successful download, call list_scene_objects() to verify the assets are now in the scene
3. Once verified, ALWAYS call clear_inbox() to remove the processed items from the inbox
4. Provide a summary to the user confirming what was added and that the inbox has been cleared

This workflow ensures the inbox stays clean and users know exactly what was added to their scene."""
        )

        # Register local tools (system operation tools)
        @self.agent.tool
        async def clear_inbox_tool(ctx: RunContext[Dict[str, Any]]) -> str:
            """Clear the user's inbox after successful asset processing"""
            return await clear_inbox(ctx)

        # Register dynamic toolset using decorator
        @self.agent.toolset
        def dynamic_addon_toolset(ctx: RunContext[Dict[str, Any]]) -> Optional[FunctionToolset]:
            """Build toolset dynamically from registry data in context"""
            registry_data = ctx.deps.get('addon_registry') if ctx.deps else None
            if not registry_data:
                self.logger.debug("No registry data in context")
                return None

            return self.toolset_builder.build_toolset_from_registry(registry_data)

        # Get provider info for logging
        provider_type = os.getenv("AI_PROVIDER", "openrouter")
        model_name = os.getenv("AI_MODEL_NAME")
        self.logger.info(
            f"B.L.A.Z.E Agent initialized with {provider_type} provider and model: {model_name}")

    async def execute_addon_command_direct(self, addon_id: str, command: str, params: Dict[str, Any]):
        """Execute command on addon via WebSocket with response waiting and error handling"""
        return await self.command_executor.execute_addon_command(addon_id, command, params)

    def handle_command_response(self, message_id: str, response_data: Dict[str, Any]):
        """Handle incoming command responses from WebSocket"""
        self.command_executor.handle_command_response(message_id, response_data)

    async def process_message(
        self,
        username: str,
        message: str,
        client_type: str = "browser",
        context: Optional[Dict[str, Any]] = None,
        deps: Optional[Dict[str, Any]] = None,
        route: str = 'agent'
    ) -> Dict[str, Any]:
        """Process a natural language message from user"""
        return await self.message_processor.process_message(
            username, message, client_type, context, deps, route
        )

    def clear_user_context(self, username: str) -> None:
        """Clear context when user disconnects"""
        self.logger.info(f"Cleared context for {username}")
