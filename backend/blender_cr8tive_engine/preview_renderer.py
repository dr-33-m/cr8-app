import tempfile
from pathlib import Path
import bpy
import mathutils
import os


class PreviewRenderer:
    def __init__(self):
        self.preview_dir = Path(
            "/home/thamsanqa/Cr8-xyz Creative Studio/Test Renders") / "box_preview"
        self.preview_dir.mkdir(exist_ok=True, parents=True)

    def setup_preview_render(self, params=None):
        """Setup the preview render with given parameters"""
        render = bpy.context.scene.render

        # Cycles Configuration
        # render.engine = 'CYCLES'  # Using Cycles renderer for high-quality preview
        # render.image_settings.file_format = 'PNG'
        # cycles_settings = bpy.context.scene.cycles
        # cycles_settings.samples = params.get('samples', 16)
        # cycles_settings.use_denoising = True
        # cycles_settings.device = 'GPU'

        # Eevee Configuration
        render.engine = 'BLENDER_EEVEE_NEXT'
        render.image_settings.file_format = 'PNG'
        eevee_settings = bpy.context.scene.eevee
        eevee_settings.taa_render_samples = params.get('samples', 16)
        eevee_settings.use_taa_reprojection = True
        eevee_settings.use_fast_gi = True

        # Common settings
        render.resolution_x = params.get('resolution_x', 480)
        render.resolution_y = params.get('resolution_y', 270)
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
