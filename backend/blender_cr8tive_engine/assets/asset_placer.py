import bpy
import os
import math
from mathutils import Vector, Euler
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_child_assets(empty):
    """Get all direct children of an empty"""
    return [obj for obj in bpy.data.objects if obj.parent == empty]


class AssetPlacer:
    """
    Class for handling asset placement operations in Blender.
    This is a port of the assetPlacer addon functionality to be used with WebSockets.
    """

    def append_asset(self, empty_name, filepath, asset_name, mode='PLACE', scale_factor=1.0, center_origin=False):
        """
        Append an asset from an external file and place it as a child of the specified empty.

        Args:
            empty_name (str): Name of the empty object to parent the asset to
            filepath (str): Path to the .blend file containing the asset
            asset_name (str): Name of the asset to append
            mode (str): 'PLACE' to add a new asset, 'REPLACE' to replace existing assets
            scale_factor (float): Scale factor to apply to the asset
            center_origin (bool): Whether to center the origin of the asset to its geometry

        Returns:
            dict: Result of the operation with success status and message
        """
        try:
            # Validate inputs
            if not filepath or not os.path.exists(filepath):
                return {
                    'success': False,
                    'message': f"Invalid file path: {filepath}"
                }

            if not asset_name:
                return {
                    'success': False,
                    'message': "Asset name cannot be empty"
                }

            # Get the empty object
            empty = bpy.data.objects.get(empty_name)
            if not empty or empty.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty_name}"
                }

            # Check if empty already has children and remove them if replace mode is active
            if mode == 'REPLACE':
                children = get_child_assets(empty)
                if children:
                    for child in children:
                        # Unparent and delete
                        child.parent = None
                        bpy.data.objects.remove(child, do_unlink=True)
                    logging.info(f"Removed existing assets from {empty.name}")

            # Deselect all objects
            bpy.ops.object.select_all(action='DESELECT')

            # Append the asset from external file
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                # Check if the asset exists in the file
                if asset_name not in data_from.objects:
                    return {
                        'success': False,
                        'message': f"Asset '{asset_name}' not found in file"
                    }

                # Load the asset
                data_to.objects = [asset_name]

            # Get the newly appended object
            if not data_to.objects:
                return {
                    'success': False,
                    'message': "Failed to append asset"
                }

            new_obj = data_to.objects[0]

            # Store original scale
            original_scale = new_obj.scale.copy()

            # Link the object to the current collection if it's not already linked
            if new_obj.name not in bpy.context.collection.objects:
                bpy.context.collection.objects.link(new_obj)

            # If origin centering is enabled, center the origin
            if center_origin:
                # Select the object
                new_obj.select_set(True)
                bpy.context.view_layer.objects.active = new_obj
                # Center origin to geometry
                bpy.ops.object.origin_set(
                    type='ORIGIN_GEOMETRY', center='BOUNDS')
                # Deselect
                new_obj.select_set(False)

            # Select objects in the correct order for parenting
            bpy.ops.object.select_all(action='DESELECT')
            new_obj.select_set(True)  # Select the child first
            empty.select_set(True)    # Select the parent last
            bpy.context.view_layer.objects.active = empty  # Make empty the active object

            # Parent without inverse (places object at empty's location)
            bpy.ops.object.parent_no_inverse_set(keep_transform=False)

            # Reset scale to original
            new_obj.scale = original_scale

            # Apply any scale adjustment
            if scale_factor != 1.0:
                new_obj.scale *= scale_factor

            # Store the original scale as a custom property for later reference
            new_obj["original_scale"] = [original_scale[0],
                                         original_scale[1], original_scale[2]]

            # Select the new object
            new_obj.select_set(True)
            bpy.context.view_layer.objects.active = new_obj

            return {
                'success': True,
                'message': f"Successfully placed '{asset_name}' as child of '{empty.name}'",
                'object_name': new_obj.name
            }

        except Exception as e:
            logging.error(f"Failed to place asset: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Failed to place asset: {str(e)}"
            }

    def remove_assets(self, empty_name):
        """
        Remove all assets from the specified empty.

        Args:
            empty_name (str): Name of the empty object to remove assets from

        Returns:
            dict: Result of the operation with success status and message
        """
        try:
            # Get the empty object
            empty = bpy.data.objects.get(empty_name)
            if not empty or empty.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty_name}"
                }

            children = get_child_assets(empty)
            if not children:
                return {
                    'success': False,
                    'message': f"No assets found on {empty.name}"
                }

            # Remove all child assets
            removed_count = 0
            for child in children:
                child.parent = None
                bpy.data.objects.remove(child, do_unlink=True)
                removed_count += 1

            return {
                'success': True,
                'message': f"Removed {removed_count} assets from {empty.name}"
            }

        except Exception as e:
            logging.error(f"Failed to remove assets: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Failed to remove assets: {str(e)}"
            }

    def swap_assets(self, empty1_name, empty2_name):
        """
        Swap assets between two empties.

        Args:
            empty1_name (str): Name of the first empty object
            empty2_name (str): Name of the second empty object

        Returns:
            dict: Result of the operation with success status and message
        """
        try:
            # Get the empty objects
            empty1 = bpy.data.objects.get(empty1_name)
            empty2 = bpy.data.objects.get(empty2_name)

            if not empty1 or empty1.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty1_name}"
                }

            if not empty2 or empty2.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty2_name}"
                }

            # Get their children
            children1 = get_child_assets(empty1)
            children2 = get_child_assets(empty2)

            if not children1:
                return {
                    'success': False,
                    'message': f"No assets found on {empty1.name}"
                }

            if not children2:
                return {
                    'success': False,
                    'message': f"No assets found on {empty2.name}"
                }

            # Store objects for later use
            objects_to_reparent = []

            # Unparent all children first to avoid conflicts
            for child in children1:
                # Store original scale
                original_scale = child.scale.copy()
                # Unparent
                child.parent = None
                # Add to list for reparenting
                objects_to_reparent.append((child, empty2, original_scale))

            for child in children2:
                # Store original scale
                original_scale = child.scale.copy()
                # Unparent
                child.parent = None
                # Add to list for reparenting
                objects_to_reparent.append((child, empty1, original_scale))

            # Now reparent all objects using parent_no_inverse_set
            for obj, target_empty, original_scale in objects_to_reparent:
                # Select objects in the correct order
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                target_empty.select_set(True)
                bpy.context.view_layer.objects.active = target_empty

                # Parent without inverse
                bpy.ops.object.parent_no_inverse_set(keep_transform=False)

                # Restore original scale
                obj.scale = original_scale

            return {
                'success': True,
                'message': f"Swapped assets between {empty1.name} and {empty2.name}"
            }

        except Exception as e:
            logging.error(f"Failed to swap assets: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Failed to swap assets: {str(e)}"
            }

    def rotate_assets(self, empty_name, degrees=None, reset=False):
        """
        Rotate assets attached to the specified empty.

        Args:
            empty_name (str): Name of the empty object
            degrees (float, optional): Rotation angle in degrees. If None, no rotation is applied.
            reset (bool, optional): Whether to reset rotation to default

        Returns:
            dict: Result of the operation with success status and message
        """
        try:
            # Get the empty object
            empty = bpy.data.objects.get(empty_name)
            if not empty or empty.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty_name}"
                }

            children = get_child_assets(empty)
            if not children:
                return {
                    'success': False,
                    'message': f"No assets found on {empty.name}"
                }

            # Apply rotation to all children
            for child in children:
                # Convert rotation to Euler to ensure we can modify Z
                if child.rotation_mode != 'XYZ':
                    child.rotation_mode = 'XYZ'

                if reset:
                    # Reset rotation
                    child.rotation_euler = Euler((0, 0, 0), 'XYZ')
                elif degrees is not None:
                    # Set absolute rotation
                    child.rotation_euler.z = math.radians(degrees)

            return {
                'success': True,
                'message': f"{'Reset' if reset else 'Applied'} rotation to assets on {empty.name}"
            }

        except Exception as e:
            logging.error(f"Failed to rotate assets: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Failed to rotate assets: {str(e)}"
            }

    def scale_assets(self, empty_name, scale_percent=None, reset=False):
        """
        Scale assets attached to the specified empty.

        Args:
            empty_name (str): Name of the empty object
            scale_percent (float, optional): Scale percentage (100% = original size)
            reset (bool, optional): Whether to reset scale to original

        Returns:
            dict: Result of the operation with success status and message
        """
        try:
            # Get the empty object
            empty = bpy.data.objects.get(empty_name)
            if not empty or empty.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty_name}"
                }

            children = get_child_assets(empty)
            if not children:
                return {
                    'success': False,
                    'message': f"No assets found on {empty.name}"
                }

            # Apply scale to all children
            for child in children:
                if reset or scale_percent is not None:
                    if "original_scale" in child:
                        orig_scale = child["original_scale"]
                        if reset:
                            child.scale = (
                                orig_scale[0], orig_scale[1], orig_scale[2])
                        else:
                            scale_factor = scale_percent / 100.0
                            child.scale = (
                                orig_scale[0] * scale_factor,
                                orig_scale[1] * scale_factor,
                                orig_scale[2] * scale_factor
                            )
                    else:
                        # If original scale not stored, use uniform scale
                        if reset:
                            child.scale = (1.0, 1.0, 1.0)
                        else:
                            scale_factor = scale_percent / 100.0
                            child.scale = (
                                scale_factor, scale_factor, scale_factor)

            return {
                'success': True,
                'message': f"{'Reset' if reset else 'Applied'} scale to assets on {empty.name}"
            }

        except Exception as e:
            logging.error(f"Failed to scale assets: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Failed to scale assets: {str(e)}"
            }

    def get_asset_info(self, empty_name):
        """
        Get information about assets attached to the specified empty.

        Args:
            empty_name (str): Name of the empty object

        Returns:
            dict: Result of the operation with success status and asset information
        """
        try:
            # Get the empty object
            empty = bpy.data.objects.get(empty_name)
            if not empty or empty.type != 'EMPTY':
                return {
                    'success': False,
                    'message': f"Invalid empty object: {empty_name}"
                }

            children = get_child_assets(empty)
            if not children:
                return {
                    'success': True,
                    'message': f"No assets found on {empty.name}",
                    'assets': []
                }

            # Collect information about each asset
            assets = []
            for child in children:
                asset_info = {
                    'name': child.name,
                    'type': child.type,
                    'location': [child.location.x, child.location.y, child.location.z],
                    'rotation': [
                        math.degrees(child.rotation_euler.x),
                        math.degrees(child.rotation_euler.y),
                        math.degrees(child.rotation_euler.z)
                    ],
                    'scale': [child.scale.x, child.scale.y, child.scale.z]
                }

                # Add original scale if available
                if "original_scale" in child:
                    asset_info['original_scale'] = child["original_scale"]

                assets.append(asset_info)

            return {
                'success': True,
                'message': f"Found {len(assets)} assets on {empty.name}",
                'assets': assets
            }

        except Exception as e:
            logging.error(f"Failed to get asset info: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f"Failed to get asset info: {str(e)}"
            }
