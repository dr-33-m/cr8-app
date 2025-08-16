"""
FastMCP Server for B.L.A.Z.E Agent
Provides MCP tools for scene and asset manipulation.
"""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from .tools.scene_tools import SceneTools
from .tools.asset_tools import AssetTools

logger = logging.getLogger(__name__)


class BlazeServer:
    """FastMCP Server for B.L.A.Z.E scene manipulation tools"""

    def __init__(self, session_manager, handlers):
        """Initialize B.L.A.Z.E MCP server with tools"""
        self.session_manager = session_manager
        self.handlers = handlers
        self.server = FastMCP('B.L.A.Z.E Scene Controller')
        self.current_username = None  # Will be set by agent

        # Initialize tool classes
        self.scene_tools = SceneTools(session_manager, handlers)
        self.asset_tools = AssetTools(session_manager, handlers)

        # Register all tools
        self._register_scene_tools()
        self._register_asset_tools()

        self.logger = logging.getLogger(__name__)
        self.logger.info("B.L.A.Z.E MCP Server initialized")

    def set_current_username(self, username: str):
        """Set the current username for tool operations"""
        self.current_username = username

    def _register_scene_tools(self):
        """Register scene manipulation tools"""

        @self.server.tool()
        async def switch_camera(camera_name: str) -> str:
            """Switch to a specific camera in the scene"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.scene_tools.switch_camera(self.current_username, camera_name)

        @self.server.tool()
        async def update_light_color(light_name: str, color: str) -> str:
            """Update the color of a light (use hex colors like #FF0000 for red)"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.scene_tools.update_light_color(self.current_username, light_name, color)

        @self.server.tool()
        async def update_light_strength(light_name: str, strength: int) -> str:
            """Update the strength/intensity of a light (0-1000)"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.scene_tools.update_light_strength(self.current_username, light_name, strength)

        @self.server.tool()
        async def update_light_properties(light_name: str, color: str = None, strength: int = None) -> str:
            """Update both color and strength of a light at once"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.scene_tools.update_light_properties(self.current_username, light_name, color, strength)

        @self.server.tool()
        async def update_material_color(material_name: str, color: str) -> str:
            """Update the color of a material (use hex colors like #FF0000 for red)"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.scene_tools.update_material_color(self.current_username, material_name, color)

        @self.server.tool()
        async def move_object(object_name: str, x: float, y: float, z: float) -> str:
            """Move an object to specific coordinates"""
            if not self.current_username:
                return "Error: No active user session"
            location = {"x": x, "y": y, "z": z}
            return await self.scene_tools.transform_object(self.current_username, object_name, location=location)

        @self.server.tool()
        async def rotate_object(object_name: str, x: float, y: float, z: float) -> str:
            """Rotate an object by specified degrees on each axis"""
            if not self.current_username:
                return "Error: No active user session"
            rotation = {"x": x, "y": y, "z": z}
            return await self.scene_tools.transform_object(self.current_username, object_name, rotation=rotation)

        @self.server.tool()
        async def scale_object(object_name: str, x: float, y: float, z: float) -> str:
            """Scale an object by specified factors on each axis"""
            if not self.current_username:
                return "Error: No active user session"
            scale = {"x": x, "y": y, "z": z}
            return await self.scene_tools.transform_object(self.current_username, object_name, scale=scale)

    def _register_asset_tools(self):
        """Register asset manipulation tools"""

        @self.server.tool()
        async def add_asset(empty_name: str, filepath: str, asset_name: str) -> str:
            """Add an asset to a specific empty position in the scene"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.append_asset(self.current_username, empty_name, filepath, asset_name)

        @self.server.tool()
        async def remove_assets(empty_name: str) -> str:
            """Remove all assets from a specific empty position"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.remove_assets(self.current_username, empty_name)

        @self.server.tool()
        async def swap_assets(empty1_name: str, empty2_name: str) -> str:
            """Swap assets between two empty positions"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.swap_assets(self.current_username, empty1_name, empty2_name)

        @self.server.tool()
        async def rotate_assets(empty_name: str, degrees: float) -> str:
            """Rotate assets in a specific empty by degrees"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.rotate_assets(self.current_username, empty_name, degrees)

        @self.server.tool()
        async def reset_asset_rotation(empty_name: str) -> str:
            """Reset rotation of assets in a specific empty"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.rotate_assets(self.current_username, empty_name, 0, reset=True)

        @self.server.tool()
        async def scale_assets(empty_name: str, scale_percent: float) -> str:
            """Scale assets in a specific empty by percentage (100 = normal size)"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.scale_assets(self.current_username, empty_name, scale_percent)

        @self.server.tool()
        async def reset_asset_scale(empty_name: str) -> str:
            """Reset scale of assets in a specific empty to normal size"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.scale_assets(self.current_username, empty_name, 100, reset=True)

        @self.server.tool()
        async def get_asset_info(empty_name: str) -> str:
            """Get information about assets in a specific empty"""
            if not self.current_username:
                return "Error: No active user session"
            return await self.asset_tools.get_asset_info(self.current_username, empty_name)

    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools and their descriptions"""
        tools = {}
        for tool_name, tool_func in self.server._tools.items():
            # Get docstring as description
            tools[tool_name] = tool_func.__doc__ or "No description available"
        return tools
