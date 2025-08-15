import os
import bpy


def get_template_path():
    """Returns the path where templates will be stored"""
    # Use version-specific path to ensure templates are found
    return os.path.join(
        bpy.utils.resource_path('USER'),
        "scripts",
        "presets",
        "camera_templates"
    )


def ensure_template_directory():
    """Creates the template directory if it doesn't exist"""
    template_path = get_template_path()
    if not os.path.exists(template_path):
        os.makedirs(template_path)
    return template_path
