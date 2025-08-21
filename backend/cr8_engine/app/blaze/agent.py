"""
B.L.A.Z.E Agent - Main Pydantic AI Agent
Processes natural language requests and executes scene manipulations.
"""

import logging
import json
import os
from typing import Dict, Any, Optional
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from .context_manager import ContextManager
from .mcp_server import BlazeServer

logger = logging.getLogger(__name__)


class BlazeAgent:
    """Main B.L.A.Z.E agent for natural language scene control"""

    def __init__(self, session_manager, handlers, model_name: str = "anthropic/claude-sonnet-4"):
        """Initialize B.L.A.Z.E agent with OpenRouter"""
        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        self.session_manager = session_manager
        self.handlers = handlers
        self.context_manager = ContextManager()
        self.mcp_server = BlazeServer(session_manager, handlers)

        # Configure OpenRouter using OpenRouterProvider
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            self.logger.error(
                "OPENROUTER_API_KEY not found in environment variables")
            raise ValueError("OPENROUTER_API_KEY is required")

        # Create OpenAI model with OpenRouter provider
        model = OpenAIModel(
            model_name,
            provider=OpenRouterProvider(api_key=openrouter_api_key)
        )

        # Initialize Pydantic AI agent with OpenRouter model
        self.agent = Agent(
            model,
            system_prompt=self._get_system_prompt(),
            tools=self._create_scene_tools() + self._create_asset_tools()
        )

        self.logger.info(
            f"B.L.A.Z.E Agent initialized with OpenRouter model: {model_name}")

    def _get_system_prompt(self) -> str:
        """Get comprehensive system prompt for the agent"""
        return """
You are B.L.A.Z.E (Blender's Artistic Zen Engineer), an intelligent assistant that helps users control 3D scenes in Blender through natural language.

Your primary role is to:
1. Understand user requests for scene manipulation
2. Use available MCP tools to execute changes
3. Provide clear feedback about what was accomplished

AVAILABLE TOOLS:
Scene Control Tools:
- switch_camera(camera_name): Switch to a specific camera
- update_light_color(light_name, color): Change light color (use hex like #FF0000)
- update_light_strength(light_name, strength): Adjust light intensity (0-1000)
- update_light_properties(light_name, color, strength): Update both at once
- update_material_color(material_name, color): Change material color
- move_object(object_name, x, y, z): Move object to coordinates
- rotate_object(object_name, x, y, z): Rotate object by degrees
- scale_object(object_name, x, y, z): Scale object by factors

Asset Control Tools:
- add_asset(empty_name, filepath, asset_name): Add asset to position
- remove_assets(empty_name): Remove assets from position
- swap_assets(empty1_name, empty2_name): Swap assets between positions
- rotate_assets(empty_name, degrees): Rotate assets
- scale_assets(empty_name, scale_percent): Scale assets (100 = normal)
- reset_asset_rotation(empty_name): Reset asset rotation
- reset_asset_scale(empty_name): Reset asset scale
- get_asset_info(empty_name): Get asset information

GUIDELINES:
- Be conversational and helpful
- Always use the exact names provided in scene context
- For colors, use hex format (#FF0000 for red, #00FF00 for green, etc.)
- For light strength, use values between 100-1000 for typical lighting
- Confirm what you've done after executing commands
- If a request is unclear, ask for clarification
- If scene elements aren't available, explain what's currently in the scene

Remember: You have access to the current scene context, so you know what cameras, lights, materials, and objects are available.
"""

    async def process_message(self, username: str, message: str,
                              client_type: str = "browser") -> Dict[str, Any]:
        """Process a natural language message from user"""
        try:
            # Store current username for tool access
            self.current_username = username
            self.mcp_server.set_current_username(username)

            # Get current scene context
            scene_context = self.context_manager.get_scene_summary(username)
            self.logger.info(f"Scene context for {username}: {scene_context}")

            # Prepare context-aware prompt
            full_message = f"""
CURRENT SCENE CONTEXT: {scene_context}

USER REQUEST: {message}

Please analyze the request and use the appropriate tools to accomplish it. 
If the scene context shows no available elements, let the user know what's currently in the scene.
"""

            # Process with Pydantic AI agent
            result = await self.agent.run(full_message)

            # Return structured response
            return {
                "type": "agent_response",
                "status": "success",
                "message": result.output,
                "context": scene_context
            }

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                "type": "agent_response",
                "status": "error",
                "message": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e)
            }
        finally:
            # Clear username after processing
            self.current_username = None
            self.mcp_server.current_username = None

    def update_scene_context(self, username: str, template_controls: Dict[str, Any]) -> None:
        """Update scene context when template controls change"""
        self.context_manager.update_template_controls(
            username, template_controls)
        self.logger.info(f"Updated scene context for {username}")

    def update_asset_context(self, username: str, assets: list) -> None:
        """Update asset context when assets change"""
        self.context_manager.update_placed_assets(username, assets)
        self.logger.info(f"Updated asset context for {username}")

    def clear_user_context(self, username: str) -> None:
        """Clear context when user disconnects"""
        self.context_manager.clear_context(username)
        self.logger.info(f"Cleared context for {username}")

    async def handle_tool_call(self, tool_name: str, username: str, **kwargs) -> str:
        """Handle tool calls from the agent"""
        return await self.mcp_server.call_tool(tool_name, username, **kwargs)

    def get_available_tools(self) -> Dict[str, str]:
        """Get available tools for debugging"""
        return self.mcp_server.get_available_tools()

    def _create_scene_tools(self):
        """Create scene manipulation tools for Pydantic AI"""
        async def switch_camera(camera_name: str) -> str:
            """Switch to a specific camera in the scene"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.switch_camera(self.current_username, camera_name)

        async def update_light_color(light_name: str, color: str) -> str:
            """Update the color of a light (use hex colors like #FF0000 for red)"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.update_light_color(self.current_username, light_name, color)

        async def update_light_strength(light_name: str, strength: int) -> str:
            """Update the strength/intensity of a light (0-1000)"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.update_light_strength(self.current_username, light_name, strength)

        async def update_light_properties(light_name: str, color: str = None, strength: int = None) -> str:
            """Update both color and strength of a light at once"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.update_light_properties(self.current_username, light_name, color, strength)

        async def update_material_color(material_name: str, color: str) -> str:
            """Update the color of a material (use hex colors like #FF0000 for red)"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.update_material_color(self.current_username, material_name, color)

        async def move_object(object_name: str, x: float, y: float, z: float) -> str:
            """Move an object to specific coordinates"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.transform_object(self.current_username, object_name, location={"x": x, "y": y, "z": z})

        async def rotate_object(object_name: str, x: float, y: float, z: float) -> str:
            """Rotate an object by specified degrees on each axis"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.transform_object(self.current_username, object_name, rotation={"x": x, "y": y, "z": z})

        async def scale_object(object_name: str, x: float, y: float, z: float) -> str:
            """Scale an object by specified factors on each axis"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.scene_tools.transform_object(self.current_username, object_name, scale={"x": x, "y": y, "z": z})

        return [switch_camera, update_light_color, update_light_strength, update_light_properties, update_material_color, move_object, rotate_object, scale_object]

    def _create_asset_tools(self):
        """Create asset manipulation tools for Pydantic AI"""
        async def add_asset(empty_name: str, filepath: str, asset_name: str) -> str:
            """Add an asset to a specific empty position in the scene"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.append_asset(self.current_username, empty_name, filepath, asset_name)

        async def remove_assets(empty_name: str) -> str:
            """Remove all assets from a specific empty position"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.remove_assets(self.current_username, empty_name)

        async def swap_assets(empty1_name: str, empty2_name: str) -> str:
            """Swap assets between two empty positions"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.swap_assets(self.current_username, empty1_name, empty2_name)

        async def rotate_assets(empty_name: str, degrees: float) -> str:
            """Rotate assets in a specific empty by degrees"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.rotate_assets(self.current_username, empty_name, degrees)

        async def reset_asset_rotation(empty_name: str) -> str:
            """Reset rotation of assets in a specific empty"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.rotate_assets(self.current_username, empty_name, 0, reset=True)

        async def scale_assets(empty_name: str, scale_percent: float) -> str:
            """Scale assets in a specific empty by percentage (100 = normal size)"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.scale_assets(self.current_username, empty_name, scale_percent)

        async def reset_asset_scale(empty_name: str) -> str:
            """Reset scale of assets in a specific empty to normal size"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.scale_assets(self.current_username, empty_name, 100, reset=True)

        async def get_asset_info(empty_name: str) -> str:
            """Get information about assets in a specific empty"""
            if not hasattr(self, 'current_username') or not self.current_username:
                return "Error: No active user session"
            return await self.mcp_server.asset_tools.get_asset_info(self.current_username, empty_name)

        return [add_asset, remove_assets, swap_assets, rotate_assets, reset_asset_rotation, scale_assets, reset_asset_scale, get_asset_info]
