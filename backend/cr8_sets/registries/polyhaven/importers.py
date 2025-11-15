"""
Blender import functions for Polyhaven assets.

Handles importing HDRIs, textures, and models into Blender scenes.
"""

import os
import shutil
import logging
from typing import Dict, Any, Optional, Tuple
from contextlib import suppress

logger = logging.getLogger(__name__)


def import_hdri_to_scene(file_path: str, asset_name: str, file_format: str) -> Dict[str, Any]:
    """Import HDRI to Blender scene using proven blender-mcp code"""
    try:
        import bpy
        
        # Create a new world if none exists
        if not bpy.data.worlds:
            bpy.data.worlds.new("World")
        
        world = bpy.data.worlds[0]
        world.use_nodes = True
        node_tree = world.node_tree
        
        # Clear existing nodes
        for node in node_tree.nodes:
            node_tree.nodes.remove(node)
        
        # Create nodes
        tex_coord = node_tree.nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)
        
        mapping = node_tree.nodes.new(type='ShaderNodeMapping')
        mapping.location = (-600, 0)
        
        # Load the image from the temporary file
        env_tex = node_tree.nodes.new(type='ShaderNodeTexEnvironment')
        env_tex.location = (-400, 0)
        env_tex.image = bpy.data.images.load(file_path)
        
        # Set proper color space
        if file_format.lower() == 'exr':
            try:
                env_tex.image.colorspace_settings.name = 'Linear'
            except:
                env_tex.image.colorspace_settings.name = 'Non-Color'
        else:  # hdr
            for color_space in ['Linear', 'Linear Rec.709', 'Non-Color']:
                try:
                    env_tex.image.colorspace_settings.name = color_space
                    break
                except:
                    continue
        
        background = node_tree.nodes.new(type='ShaderNodeBackground')
        background.location = (-200, 0)
        
        output = node_tree.nodes.new(type='ShaderNodeOutputWorld')
        output.location = (0, 0)
        
        # Connect nodes
        node_tree.links.new(tex_coord.outputs['Generated'], mapping.inputs['Vector'])
        node_tree.links.new(mapping.outputs['Vector'], env_tex.inputs['Vector'])
        node_tree.links.new(env_tex.outputs['Color'], background.inputs['Color'])
        node_tree.links.new(background.outputs['Background'], output.inputs['Surface'])
        
        # Set as active world
        bpy.context.scene.world = world
        
        return {
            "success": True,
            "message": f"HDRI {asset_name} imported successfully",
            "image_name": env_tex.image.name
        }
        
    except ImportError:
        return {
            "success": False,
            "message": "Blender API not available - file downloaded but not imported"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to import HDRI: {str(e)}"
        }


def import_texture_to_scene(asset_id: str, asset_name: str, downloaded_maps: Dict[str, str]) -> Dict[str, Any]:
    """Import texture maps as PBR material using proven blender-mcp code"""
    try:
        import bpy
        
        # Load images into Blender
        texture_images = {}
        for map_type, file_path in downloaded_maps.items():
            image = bpy.data.images.load(file_path)
            image.name = f"{asset_id}_{map_type}"
            image.pack()  # Pack into blend file
            
            # Set proper color space
            if map_type.lower() in ['color', 'diffuse', 'albedo']:
                try:
                    image.colorspace_settings.name = 'sRGB'
                except:
                    pass
            else:
                try:
                    image.colorspace_settings.name = 'Non-Color'
                except:
                    pass
            
            texture_images[map_type] = image
        
        # Create PBR material
        mat = bpy.data.materials.new(name=f"{asset_id}_material")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default nodes
        for node in nodes:
            nodes.remove(node)
        
        # Create output and principled BSDF
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = (0, 0)
        links.new(principled.outputs[0], output.inputs[0])
        
        # Add texture coordinate and mapping
        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)
        
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = (-600, 0)
        mapping.vector_type = 'TEXTURE'
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        
        # Connect texture maps using proven blender-mcp patterns
        x_pos = -400
        y_pos = 300
        
        for map_type, image in texture_images.items():
            tex_node = nodes.new(type='ShaderNodeTexImage')
            tex_node.location = (x_pos, y_pos)
            tex_node.image = image
            
            links.new(mapping.outputs['Vector'], tex_node.inputs['Vector'])
            
            # Connect to appropriate Principled BSDF input
            if map_type.lower() in ['color', 'diffuse', 'albedo']:
                links.new(tex_node.outputs['Color'], principled.inputs['Base Color'])
            elif map_type.lower() in ['roughness', 'rough']:
                links.new(tex_node.outputs['Color'], principled.inputs['Roughness'])
            elif map_type.lower() in ['metallic', 'metalness', 'metal']:
                links.new(tex_node.outputs['Color'], principled.inputs['Metallic'])
            elif map_type.lower() in ['normal', 'nor', 'dx', 'gl']:
                normal_map = nodes.new(type='ShaderNodeNormalMap')
                normal_map.location = (x_pos + 200, y_pos)
                links.new(tex_node.outputs['Color'], normal_map.inputs['Color'])
                links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
            elif map_type.lower() in ['displacement', 'disp', 'height']:
                disp_node = nodes.new(type='ShaderNodeDisplacement')
                disp_node.location = (x_pos + 200, y_pos - 200)
                disp_node.inputs['Scale'].default_value = 0.1
                links.new(tex_node.outputs['Color'], disp_node.inputs['Height'])
                links.new(disp_node.outputs['Displacement'], output.inputs['Displacement'])
            
            y_pos -= 250
        
        return {
            "success": True,
            "message": f"Texture {asset_name} imported as material",
            "material": mat.name,
            "maps": list(texture_images.keys())
        }
        
    except ImportError:
        return {
            "success": False,
            "message": "Blender API not available - texture downloaded but not imported"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to import texture: {str(e)}"
        }


def import_model_to_scene(file_path: str, asset_name: str, file_format: str,
                         location: Optional[Tuple[float, float, float]]) -> Dict[str, Any]:
    """Import model to Blender scene using proven blender-mcp code"""
    try:
        import bpy
        
        # Store existing objects to identify imported ones
        existing_objects = set(bpy.data.objects)
        
        # Import based on file format
        if file_format == "gltf" or file_format == "glb":
            bpy.ops.import_scene.gltf(filepath=file_path)
        elif file_format == "fbx":
            bpy.ops.import_scene.fbx(filepath=file_path)
        elif file_format == "obj":
            bpy.ops.import_scene.obj(filepath=file_path)
        elif file_format == "blend":
            with bpy.data.libraries.load(file_path, link=False) as (data_from, data_to):
                data_to.objects = data_from.objects
            
            # Link objects to scene
            for obj in data_to.objects:
                if obj is not None:
                    bpy.context.collection.objects.link(obj)
        else:
            return {
                "success": False,
                "message": f"Unsupported model format: {file_format}"
            }
        
        # Get imported objects
        imported_objects = list(set(bpy.data.objects) - existing_objects)
        
        # Position objects if location specified
        if location and imported_objects:
            for obj in imported_objects:
                obj.location = location
        
        return {
            "success": True,
            "message": f"Model {asset_name} imported successfully",
            "imported_objects": [obj.name for obj in imported_objects]
        }
        
    except ImportError:
        return {
            "success": False,
            "message": "Blender API not available - model downloaded but not imported"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to import model: {str(e)}"
        }
