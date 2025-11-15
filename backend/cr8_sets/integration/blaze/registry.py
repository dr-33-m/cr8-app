"""
B.L.A.Z.E AI Command Handlers Registry.

Central registry of all B.L.A.Z.E integration functions available to the AI.
Aggregates functions from asset, scene, and inbox modules.
"""

from .asset_functions import (
    search_polyhaven_assets,
    download_polyhaven_asset,
    find_and_add_polyhaven_asset,
    get_polyhaven_categories,
    apply_polyhaven_texture_to_object,
    search_assets,
    download_asset,
    get_categories,
)
from .scene_functions import (
    list_scene_objects,
    get_objects_by_type,
    transform_resize,
    transform_translate,
    transform_rotate,
    set_active_object,
    focus_on_active_object,
    select_object,
    delete_object,
)
from .inbox_functions import process_inbox_assets


# ============================================================================
# B.L.A.Z.E AI Command Handlers Registry
# ============================================================================

AI_COMMAND_HANDLERS = {
    # Polyhaven-specific functions
    "search_polyhaven_assets": search_polyhaven_assets,
    "download_polyhaven_asset": download_polyhaven_asset,
    "find_and_add_polyhaven_asset": find_and_add_polyhaven_asset,
    "get_polyhaven_categories": get_polyhaven_categories,
    "apply_polyhaven_texture_to_object": apply_polyhaven_texture_to_object,
    # Generic multi-registry functions
    "search_assets": search_assets,
    "download_asset": download_asset,
    "get_categories": get_categories,
    # Scene spatial functions
    "list_scene_objects": list_scene_objects,
    "get_objects_by_type": get_objects_by_type,
    "transform_resize": transform_resize,
    "transform_translate": transform_translate,
    "transform_rotate": transform_rotate,
    "set_active_object": set_active_object,
    "focus_on_active_object": focus_on_active_object,
    "select_object": select_object,
    "delete_object": delete_object,
    # Inbox processing
    "process_inbox_assets": process_inbox_assets,
}

__all__ = ["AI_COMMAND_HANDLERS"]
