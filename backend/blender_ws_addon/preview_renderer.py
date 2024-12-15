import tempfile
from pathlib import Path
import bpy
import mathutils
import os


class PreviewRenderer:
    def __init__(self):
        self.preview_dir = Path(
            "/media/970_evo/SC Studio/cr8-xyz/Test Renders") / "box_preview"
        self.preview_dir.mkdir(exist_ok=True, parents=True)

    def setup_preview_render(self, params=None):
        """Setup the preview render with given parameters"""
        render = bpy.context.scene.render
        render.engine = 'CYCLES'  # Using Cycles renderer for high-quality preview
        render.image_settings.file_format = 'PNG'

        # Set resolution with default fallbacks
        render.resolution_x = params.get('resolution_x', 480)
        render.resolution_y = params.get('resolution_y', 270)

        # Setup Cycles settings for speed vs quality
        bpy.context.scene.cycles.samples = params.get('samples', 16)
        bpy.context.scene.cycles.use_denoising = True
        bpy.context.scene.cycles.device = 'GPU'

        # Ensure filepath is set for preview frames
        render.filepath = str(self.preview_dir / "frame_")

    def render_preview_frame(self, frame):
        """Render a specific frame and save it to the preview directory"""
        try:
            bpy.context.scene.frame_set(frame)
            # Ensure filepath is unique for each frame
            bpy.context.scene.render.filepath = f"{str(self.preview_dir)}/frame_{frame:04d}.png"

            bpy.ops.render.render(write_still=True)

        except Exception as e:
            print(f"Error rendering frame {frame}: {e}")
            import traceback
            traceback.print_exc()

    def cleanup(self):
        """Remove all preview frame files"""
        try:
            for file in self.preview_dir.glob("frame_*.png"):
                file.unlink()
        except Exception as e:
            print(f"Error removing file: {e}")
            import traceback
            traceback.print_exc()


def get_preview_renderer():
    """Create and return a preview renderer instance"""
    return PreviewRenderer()
