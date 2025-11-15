"""
Texture utility functions for Polyhaven assets.

Handles applying downloaded textures to Blender objects.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def apply_texture_to_object(object_name: str, texture_asset_id: str) -> Dict[str, Any]:
    """Apply a Polyhaven texture to a specific object - using proven blender-mcp code"""
    try:
        import bpy
        
        # Get the object
        obj = bpy.data.objects.get(object_name)
        if not obj:
            return {"error": f"Object not found: {object_name}"}
        
        # Make sure object can accept materials
        if not hasattr(obj, 'data') or not hasattr(obj.data, 'materials'):
            return {"error": f"Object {object_name} cannot accept materials"}
        
        # Find all images related to this texture
        texture_images = {}
        for img in bpy.data.images:
            if img.name.startswith(texture_asset_id + "_"):
                map_type = img.name.split('_')[-1].split('.')[0]
                img.reload()
                
                # Set proper color space
                if map_type.lower() in ['color', 'diffuse', 'albedo']:
                    try:
                        img.colorspace_settings.name = 'sRGB'
                    except:
                        pass
                else:
                    try:
                        img.colorspace_settings.name = 'Non-Color'
                    except:
                        pass
                
                if not img.packed_file:
                    img.pack()
                
                texture_images[map_type] = img
        
        if not texture_images:
            return {"error": f"No texture images found for: {texture_asset_id}. Please download the texture first."}
        
        # Create new material
        new_mat_name = f"{texture_asset_id}_material_{object_name}"
        existing_mat = bpy.data.materials.get(new_mat_name)
        if existing_mat:
            bpy.data.materials.remove(existing_mat)
        
        new_mat = bpy.data.materials.new(name=new_mat_name)
        new_mat.use_nodes = True
        
        # Set up material nodes using proven blender-mcp patterns
        nodes = new_mat.node_tree.nodes
        links = new_mat.node_tree.links
        nodes.clear()
        
        # Create output and principled BSDF
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (600, 0)
        
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled.location = (300, 0)
        links.new(principled.outputs[0], output.inputs[0])
        
        # Add texture coordinate and mapping
        tex_coord = nodes.new(type='ShaderNodeTexCoord')
        tex_coord.location = (-800, 0)
        
        mapping = nodes.new(type='ShaderNodeMapping')
        mapping.location = (-600, 0)
        mapping.vector_type = 'TEXTURE'
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        
        # Connect texture maps
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
        
        # Clear existing materials and apply new one
        while len(obj.data.materials) > 0:
            obj.data.materials.pop(index=0)
        
        obj.data.materials.append(new_mat)
        
        # Make object active and update
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.context.view_layer.update()
        
        return {
            "success": True,
            "message": f"Applied texture {texture_asset_id} to {object_name}",
            "material": new_mat.name,
            "maps": list(texture_images.keys())
        }
        
    except ImportError:
        return {"error": "Blender API not available"}
    except Exception as e:
        return {"error": f"Failed to apply texture: {str(e)}"}
