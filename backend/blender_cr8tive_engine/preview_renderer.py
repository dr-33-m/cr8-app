import bpy
import os
from pathlib import Path
import numpy as np
import logging
from typing import Optional


class PreviewRenderer:
    def __init__(self, username: str, webrtc_track=None):
        self.username = username
        self.webrtc_track = webrtc_track
        self.base_dir = Path("/mnt/shared_storage/Cr8tive_Engine/Sessions")
        self.preview_dir = self.base_dir / username / "preview"
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def cleanup(self):
        """Clean up existing preview frames"""
        try:
            for file in self.preview_dir.glob("frame_*.png"):
                file.unlink()
        except Exception as e:
            self.logger.error(f"Error cleaning up preview frames: {e}")

    def setup_preview_render(self, params=None):
        """Set up render settings for preview"""
        try:
            # Set render settings
            render = bpy.context.scene.render
            render.resolution_x = 1280
            render.resolution_y = 720
            render.image_settings.file_format = 'PNG'
            render.image_settings.color_mode = 'RGBA'

            # Set up frame handler for WebRTC streaming
            if self.webrtc_track:
                bpy.app.handlers.render_post.clear()
                bpy.app.handlers.render_post.append(
                    self._handle_render_complete)

            # Apply any additional render settings from params
            if params:
                self._apply_render_params(params)

        except Exception as e:
            self.logger.error(f"Error setting up preview render: {e}")
            raise

    def _apply_render_params(self, params):
        """Apply render parameters"""
        try:
            scene = bpy.context.scene
            if 'start_frame' in params:
                scene.frame_start = params['start_frame']
            if 'end_frame' in params:
                scene.frame_end = params['end_frame']
            if 'fps' in params:
                scene.render.fps = params['fps']
        except Exception as e:
            self.logger.error(f"Error applying render params: {e}")
            raise

    def _handle_render_complete(self, scene):
        """Handle render completion - called after each frame is rendered"""
        try:
            if not self.webrtc_track:
                return

            # Get the render result
            render_result = bpy.data.images['Render Result']
            if not render_result:
                self.logger.error("No render result available")
                return

            # Convert render result to numpy array
            width = render_result.size[0]
            height = render_result.size[1]
            pixels = np.array(render_result.pixels[:])
            pixels = (pixels * 255).astype(np.uint8)
            pixels = pixels.reshape(height, width, 4)  # RGBA format

            # Send frame to WebRTC track
            self.webrtc_track.add_frame(pixels.tobytes())

        except Exception as e:
            self.logger.error(f"Error handling render complete: {e}")

    def save_frame(self, frame_number: int):
        """Save frame to disk (used as fallback when WebRTC is not available)"""
        try:
            frame_path = self.preview_dir / f"frame_{frame_number:04d}.png"
            bpy.context.scene.render.filepath = str(frame_path)
            bpy.ops.render.render(write_still=True)
            return frame_path
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            raise

    def render_frame(self, frame_number: int):
        """Render a single frame"""
        try:
            bpy.context.scene.frame_set(frame_number)

            if self.webrtc_track:
                # For WebRTC, render directly to memory
                bpy.ops.render.render()
            else:
                # Fallback to disk-based rendering
                self.save_frame(frame_number)

        except Exception as e:
            self.logger.error(f"Error rendering frame {frame_number}: {e}")
            raise

    def render_animation(self, start_frame: Optional[int] = None, end_frame: Optional[int] = None):
        """Render animation frames"""
        try:
            scene = bpy.context.scene
            start = start_frame if start_frame is not None else scene.frame_start
            end = end_frame if end_frame is not None else scene.frame_end

            for frame in range(start, end + 1):
                self.render_frame(frame)

        except Exception as e:
            self.logger.error(f"Error rendering animation: {e}")
            raise
