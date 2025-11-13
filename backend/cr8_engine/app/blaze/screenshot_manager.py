"""
Screenshot Manager - Manages screenshot data lifecycle for image analysis
"""

import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ScreenshotManager:
    """Manages screenshot data storage and retrieval per user"""

    def __init__(self):
        """Initialize screenshot storage"""
        self.screenshot_data = {}  # username -> screenshot_data

    def store_screenshot(self, response_data: Dict[str, Any], username: str) -> None:
        """Store screenshot data for image analysis"""
        try:
            if not username:
                logger.warning("No username provided to store screenshot data")
                return

            import base64

            image_data_b64 = response_data.get('image_data')
            media_type = response_data.get('media_type', 'image/png')
            width = response_data.get('width', 'unknown')
            height = response_data.get('height', 'unknown')

            if image_data_b64:
                # Convert base64 to binary data for BinaryContent
                image_bytes = base64.b64decode(image_data_b64)

                # Store screenshot data for this user
                self.screenshot_data[username] = {
                    'image_bytes': image_bytes,
                    'media_type': media_type,
                    'width': width,
                    'height': height,
                    'timestamp': time.time()
                }

                logger.debug(f"Stored screenshot data for {username}: {width}x{height}")
            else:
                logger.warning("No image data in response_data")

        except Exception as e:
            logger.error(f"Error storing screenshot data: {str(e)}")

    def get_and_clear_screenshot(self, username: str) -> Optional[Dict[str, Any]]:
        """Get screenshot data for user and clear it from storage"""
        try:
            screenshot_data = self.screenshot_data.pop(username, None)
            if screenshot_data:
                logger.debug(f"Retrieved screenshot data for {username}")
            return screenshot_data
        except Exception as e:
            logger.error(f"Error retrieving screenshot data: {str(e)}")
            return None
