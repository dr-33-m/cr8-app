"""
B.L.A.Z.E integration module.

Provides wrapper functions that B.L.A.Z.E calls, converting between
B.L.A.Z.E's interface and the registry-agnostic handlers.

Organized into specialized submodules:
- asset_functions: Asset search, download, and management
- scene_functions: Scene querying and object transformations
- inbox_functions: Inbox processing
- registry: Central registry of all AI command handlers
"""

from .registry import AI_COMMAND_HANDLERS
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

__all__ = [
    "AI_COMMAND_HANDLERS",
    "search_polyhaven_assets",
    "download_polyhaven_asset",
    "find_and_add_polyhaven_asset",
    "get_polyhaven_categories",
    "apply_polyhaven_texture_to_object",
    "search_assets",
    "download_asset",
    "get_categories",
    "list_scene_objects",
    "get_objects_by_type",
    "transform_resize",
    "transform_translate",
    "transform_rotate",
    "set_active_object",
    "focus_on_active_object",
    "select_object",
    "delete_object",
    "process_inbox_assets",
]
