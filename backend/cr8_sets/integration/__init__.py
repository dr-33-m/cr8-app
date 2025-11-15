"""
B.L.A.Z.E integration layer for multi-registry system.

Provides wrapper functions that B.L.A.Z.E calls, converting between
B.L.A.Z.E's interface and the registry-agnostic handlers.

Functions are organized into specialized modules within the blaze/ subdirectory:
- asset_functions: Asset search, download, and management
- scene_functions: Scene querying and object transformations
- inbox_functions: Inbox processing
- registry: Central registry of all AI command handlers
"""

from .blaze import (
    # Polyhaven-specific functions
    search_polyhaven_assets,
    download_polyhaven_asset,
    find_and_add_polyhaven_asset,
    get_polyhaven_categories,
    apply_polyhaven_texture_to_object,
    # Generic multi-registry functions
    search_assets,
    download_asset,
    get_categories,
    # Scene spatial functions
    list_scene_objects,
    get_objects_by_type,
    transform_resize,
    transform_translate,
    transform_rotate,
    set_active_object,
    focus_on_active_object,
    select_object,
    delete_object,
    # Inbox processing
    process_inbox_assets,
    # AI command handlers registry
    AI_COMMAND_HANDLERS,
)

__all__ = [
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
    "AI_COMMAND_HANDLERS",
]
