"""
3D View Context Utilities
Utility functions for working with Blender's 3D viewport context
"""

import bpy
import logging
import mathutils

logger = logging.getLogger(__name__)


def ensure_view3d_context():
    """Ensure VIEW_3D context is available for viewport operations"""
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    return {'area': area, 'region': region}
    return None


def pan_view_manual(direction, amount=0.5):
    context = ensure_view3d_context()
    if not context:
        raise Exception("No VIEW_3D area found")
    
    area = context['area']
    space = area.spaces.active
    region_3d = space.region_3d
    
    # Viewport local coordinate system:
    # X-axis: left (-) / right (+) on screen
    # Y-axis: down (-) / up (+) on screen  
    # Z-axis: into screen (-) / out of screen (+)
    offset = mathutils.Vector((0, 0, 0))
    
    if direction == "PANLEFT":
        offset.x = -amount
    elif direction == "PANRIGHT":
        offset.x = amount
    elif direction == "PANUP":
        offset.y = amount
    elif direction == "PANDOWN":
        offset.y = -amount
    elif direction == "PANFORWARD":
        offset.z = -amount  # Into the screen (negative Z)
    elif direction == "PANBACK":
        offset.z = amount   # Out of the screen (positive Z)
    
    # Transform local offset to world space and apply
    offset_world = region_3d.view_rotation @ offset
    region_3d.view_location += offset_world
