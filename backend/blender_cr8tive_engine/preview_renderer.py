import tempfile
from pathlib import Path
import bpy
import mathutils
import os


class PreviewRenderer:
    def __init__(self, username):
        self.preview_dir = Path(
            f"/mnt/shared_storage/Cr8tive_Engine/Sessions/{username}/preview")
        self.preview_dir.mkdir(exist_ok=True, parents=True)

    def setup_preview_render(self, params=None):
        """Setup the preview render with OpenGL viewport settings"""
        # Get the current window and screen
        window = bpy.context.window_manager.windows[0]
        screen = window.screen

        # Get 3D viewport
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                # Disable all overlays
                overlay = area.spaces[0].overlay
                overlay.show_overlays = False

                # Set render engine to EEVEE
                bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'

                # Switch to rendered viewport shading
                space = area.spaces[0]
                space.shading.type = 'RENDERED'
                break

        # Set up common render settings
        render = bpy.context.scene.render
        render.resolution_x = params.get('resolution_x', 480)
        render.resolution_y = params.get('resolution_y', 270)
        render.filepath = str(self.preview_dir / "frame_")
        render.image_settings.file_format = 'PNG'

    def cleanup(self):
        """Remove all preview frame files"""
        try:
            for file in self.preview_dir.glob("frame_*.png"):
                file.unlink()
        except Exception as e:
            print(f"Error removing file: {e}")
            import traceback
            traceback.print_exc()


def get_preview_renderer(username):
    """Create and return a preview renderer instance with the given username"""
    return PreviewRenderer(username)
