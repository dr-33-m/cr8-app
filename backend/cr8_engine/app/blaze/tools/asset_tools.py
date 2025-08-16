"""
Asset manipulation tools for B.L.A.Z.E Agent
Provides MCP tools for asset operations like append, remove, swap, rotate, and scale.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class AssetTools:
    """Asset manipulation tools that wrap existing handlers"""

    def __init__(self, session_manager, handlers):
        """Initialize with session manager and handler references"""
        self.session_manager = session_manager
        self.asset_handler = handlers.get('asset')
        self.logger = logging.getLogger(__name__)

    async def append_asset(self, username: str, empty_name: str, filepath: str,
                           asset_name: str, mode: str = "LINK",
                           scale_factor: float = 1.0, center_origin: bool = True) -> str:
        """Append an asset to a specific empty in the scene"""
        try:
            if not self.asset_handler:
                return "Asset handler not available"

            await self.asset_handler.handle_append_asset(
                username=username,
                data={
                    "command": "append_asset",
                    "empty_name": empty_name,
                    "filepath": filepath,
                    "asset_name": asset_name,
                    "mode": mode,
                    "scale_factor": scale_factor,
                    "center_origin": center_origin
                },
                client_type="agent"
            )

            return f"Added asset '{asset_name}' to {empty_name}"

        except Exception as e:
            self.logger.error(f"Error appending asset: {str(e)}")
            return f"Error adding asset: {str(e)}"

    async def remove_assets(self, username: str, empty_name: str) -> str:
        """Remove all assets from a specific empty"""
        try:
            if not self.asset_handler:
                return "Asset handler not available"

            await self.asset_handler.handle_remove_assets(
                username=username,
                data={
                    "command": "remove_assets",
                    "empty_name": empty_name
                },
                client_type="agent"
            )

            return f"Removed all assets from {empty_name}"

        except Exception as e:
            self.logger.error(f"Error removing assets: {str(e)}")
            return f"Error removing assets: {str(e)}"

    async def swap_assets(self, username: str, empty1_name: str, empty2_name: str) -> str:
        """Swap assets between two empties"""
        try:
            if not self.asset_handler:
                return "Asset handler not available"

            await self.asset_handler.handle_swap_assets(
                username=username,
                data={
                    "command": "swap_assets",
                    "empty1_name": empty1_name,
                    "empty2_name": empty2_name
                },
                client_type="agent"
            )

            return f"Swapped assets between {empty1_name} and {empty2_name}"

        except Exception as e:
            self.logger.error(f"Error swapping assets: {str(e)}")
            return f"Error swapping assets: {str(e)}"

    async def rotate_assets(self, username: str, empty_name: str,
                            degrees: float, reset: bool = False) -> str:
        """Rotate assets in a specific empty"""
        try:
            if not self.asset_handler:
                return "Asset handler not available"

            await self.asset_handler.handle_rotate_assets(
                username=username,
                data={
                    "command": "rotate_assets",
                    "empty_name": empty_name,
                    "degrees": degrees,
                    "reset": reset
                },
                client_type="agent"
            )

            if reset:
                return f"Reset rotation for assets in {empty_name}"
            else:
                return f"Rotated assets in {empty_name} by {degrees} degrees"

        except Exception as e:
            self.logger.error(f"Error rotating assets: {str(e)}")
            return f"Error rotating assets: {str(e)}"

    async def scale_assets(self, username: str, empty_name: str,
                           scale_percent: float, reset: bool = False) -> str:
        """Scale assets in a specific empty"""
        try:
            if not self.asset_handler:
                return "Asset handler not available"

            await self.asset_handler.handle_scale_assets(
                username=username,
                data={
                    "command": "scale_assets",
                    "empty_name": empty_name,
                    "scale_percent": scale_percent,
                    "reset": reset
                },
                client_type="agent"
            )

            if reset:
                return f"Reset scale for assets in {empty_name}"
            else:
                return f"Scaled assets in {empty_name} to {scale_percent}%"

        except Exception as e:
            self.logger.error(f"Error scaling assets: {str(e)}")
            return f"Error scaling assets: {str(e)}"

    async def get_asset_info(self, username: str, empty_name: str) -> str:
        """Get information about assets in a specific empty"""
        try:
            if not self.asset_handler:
                return "Asset handler not available"

            await self.asset_handler.handle_get_asset_info(
                username=username,
                data={
                    "command": "get_asset_info",
                    "empty_name": empty_name
                },
                client_type="agent"
            )

            return f"Retrieved asset information for {empty_name}"

        except Exception as e:
            self.logger.error(f"Error getting asset info: {str(e)}")
            return f"Error getting asset information: {str(e)}"
