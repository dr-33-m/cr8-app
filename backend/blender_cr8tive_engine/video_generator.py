import bpy
import os
from datetime import datetime
import pprint


class GenerateVideo:
    def __init__(self, image_sequence_directory, output_file, resolution=(1280, 720), fps=30):
        self.image_folder_path = image_sequence_directory
        self.output_file = output_file
        self.resolution = resolution
        self.fps = fps

    @staticmethod
    def clean_sequencer(sequence_editor):
        """
        Clean the sequence editor by removing all strips.

        :param sequence_editor: Blender sequence editor context
        """
        for strip in sequence_editor.sequences:
            sequence_editor.sequences.remove(strip)

    @staticmethod
    def ensure_sequence_editor():
        """
        Ensure the Sequence Editor is available and active.

        :return: Sequence editor context or None
        """
        # First, try to find an existing Sequence Editor
        for area in bpy.context.screen.areas:
            if area.type == 'SEQUENCE_EDITOR':
                return area

        # If no Sequence Editor exists, try to create one
        try:
            # Change area type to Sequence Editor
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.type = 'SEQUENCE_EDITOR'
                    return area
        except Exception as e:
            print(f"Could not create Sequence Editor: {e}")
            return None

    @staticmethod
    def get_image_files(image_folder_path, image_extension=".png"):
        """
        Get sorted list of image files in the specified directory.

        :param image_folder_path: Directory containing image sequence
        :param image_extension: File extension to filter
        :return: Sorted list of image filenames
        """
        try:
            image_files = [
                f for f in os.listdir(image_folder_path)
                if f.endswith(image_extension)
            ]
            image_files.sort()
            pprint.pprint(image_files)
            return image_files
        except Exception as e:
            print(f"Error reading image files: {e}")
            return []

    @staticmethod
    def get_image_dimensions(image_path):
        """
        Get dimensions of the first image in the sequence.

        :param image_path: Full path to the image
        :return: Tuple of (width, height)
        """
        try:
            image = bpy.data.images.load(image_path)
            width, height = image.size
            bpy.data.images.remove(image)
            return width, height
        except Exception as e:
            print(f"Error getting image dimensions: {e}")
            return None

    def set_up_output_params(self):
        """
        Configure render and output settings for video generation.
        """
        try:
            # Get image files and verify sequence
            image_files = self.get_image_files(self.image_folder_path)
            if not image_files:
                raise ValueError(
                    "No image files found in the specified directory")

            # Set up scene parameters
            scene = bpy.context.scene
            scene.frame_end = len(image_files)

            # Get first image dimensions
            first_image_path = os.path.join(
                self.image_folder_path, image_files[0])
            width, height = self.get_image_dimensions(first_image_path)

            # Set render resolution
            scene.render.resolution_x = width or self.resolution[0]
            scene.render.resolution_y = height or self.resolution[1]

            # Configure video export settings
            scene.render.fps = self.fps
            scene.render.image_settings.file_format = "FFMPEG"
            scene.render.ffmpeg.format = "MPEG4"
            scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"

            # Generate unique output filename
            now = datetime.now()
            time = now.strftime("%H-%M-%S")
            filepath = os.path.join(
                self.image_folder_path,
                f"{self.output_file}_{time}.mp4"
            )
            scene.render.filepath = filepath

        except Exception as e:
            print(f"Error setting up output parameters: {e}")
            raise

    def gen_video_from_images(self):
        """
        Generate video from image sequence using Blender's Video Sequencer.
        """
        try:
            # Ensure output parameters are set
            self.set_up_output_params()

            # Find or create Sequence Editor
            sequence_editor_area = self.ensure_sequence_editor()
            if not sequence_editor_area:
                raise RuntimeError("Could not find or create Sequence Editor")

            # Get image files
            image_files = self.get_image_files(self.image_folder_path)
            file_info = [{"name": image_name} for image_name in image_files]

            # Override context and add image strips
            with bpy.context.temp_override(area=sequence_editor_area):
                # Clean existing sequences
                self.clean_sequencer(bpy.context.scene.sequence_editor)

                # Add image strip
                bpy.ops.sequencer.image_strip_add(
                    directory=self.image_folder_path + os.sep,
                    files=file_info,
                    frame_start=1
                )

            # Render animation
            bpy.ops.render.render(animation=True)

        except Exception as e:
            print(f"Error generating video: {e}")
            raise
