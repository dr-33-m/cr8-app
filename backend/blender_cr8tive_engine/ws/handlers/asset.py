"""
Asset command handlers for WebSocket communication.
"""

import logging
import bpy
from ...assets.asset_placer import AssetPlacer
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class AssetHandlers:
    """Handlers for asset-related WebSocket commands."""

    # Create a single shared instance of AssetPlacer
    asset_placer = AssetPlacer()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_append_asset(data):
        """Handle appending an asset to an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling append asset request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')
            filepath = data.get('filepath')
            asset_name = data.get('asset_name')
            mode = data.get('mode', 'PLACE')
            scale_factor = data.get('scale_factor', 1.0)
            center_origin = data.get('center_origin', False)

            # Call the asset placer to append the asset
            result = AssetHandlers.asset_placer.append_asset(
                empty_name,
                filepath,
                asset_name,
                mode=mode,
                scale_factor=scale_factor,
                center_origin=center_origin
            )

            logger.info(f"Asset append result: {result}")

            # Send response with the result
            AssetHandlers.response_manager.send_response('append_asset_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during asset append: {e}")
            import traceback
            traceback.print_exc()
            AssetHandlers.response_manager.send_response('append_asset_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_remove_assets(data):
        """Handle removing assets from an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling remove assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')

            # Call the asset placer to remove the assets
            result = AssetHandlers.asset_placer.remove_assets(empty_name)

            logger.info(f"Asset removal result: {result}")

            # Send response with the result
            AssetHandlers.response_manager.send_response('remove_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during asset removal: {e}")
            import traceback
            traceback.print_exc()
            AssetHandlers.response_manager.send_response('remove_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_swap_assets(data):
        """Handle swapping assets between two empties"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling swap assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty1_name = data.get('empty1_name')
            empty2_name = data.get('empty2_name')

            # Call the asset placer to swap the assets
            result = AssetHandlers.asset_placer.swap_assets(
                empty1_name, empty2_name)

            logger.info(f"Asset swap result: {result}")

            # Send response with the result
            AssetHandlers.response_manager.send_response('swap_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during asset swap: {e}")
            import traceback
            traceback.print_exc()
            AssetHandlers.response_manager.send_response('swap_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_rotate_assets(data):
        """Handle rotating assets on an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling rotate assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')
            degrees = data.get('degrees')
            reset = data.get('reset', False)

            # Call the asset placer to rotate the assets
            result = AssetHandlers.asset_placer.rotate_assets(
                empty_name, degrees, reset)

            logger.info(f"Asset rotation result: {result}")

            # Send response with the result
            AssetHandlers.response_manager.send_response('rotate_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during asset rotation: {e}")
            import traceback
            traceback.print_exc()
            AssetHandlers.response_manager.send_response('rotate_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_scale_assets(data):
        """Handle scaling assets on an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling scale assets request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')
            scale_percent = data.get('scale_percent')
            reset = data.get('reset', False)

            # Call the asset placer to scale the assets
            result = AssetHandlers.asset_placer.scale_assets(
                empty_name, scale_percent, reset)

            logger.info(f"Asset scaling result: {result}")

            # Send response with the result
            AssetHandlers.response_manager.send_response('scale_assets_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during asset scaling: {e}")
            import traceback
            traceback.print_exc()
            AssetHandlers.response_manager.send_response('scale_assets_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_get_asset_info(data):
        """Handle getting information about assets on an empty"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling get asset info request with message_id: {message_id}")

            # Extract parameters from the request
            empty_name = data.get('empty_name')

            # Call the asset placer to get the asset info
            result = AssetHandlers.asset_placer.get_asset_info(empty_name)

            logger.info(f"Asset info result: {result}")

            # Send response with the result
            AssetHandlers.response_manager.send_response('asset_info_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error during get asset info: {e}")
            import traceback
            traceback.print_exc()
            AssetHandlers.response_manager.send_response('asset_info_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })
