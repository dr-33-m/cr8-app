"""
Asset operation handlers for multi-registry system.

Provides registry-agnostic handlers for common asset operations:
- Search and discovery
- Download and import
- Scoring and ranking
- Batch processing
"""

from .asset_operations import (
    search_assets,
    download_asset,
    get_categories,
    apply_texture_to_object,
    find_and_add_asset,
)
from .scoring import calculate_relevance, score_and_rank_assets
from .inbox_processor import process_inbox_batch

__all__ = [
    "search_assets",
    "download_asset",
    "get_categories",
    "apply_texture_to_object",
    "find_and_add_asset",
    "calculate_relevance",
    "score_and_rank_assets",
    "process_inbox_batch",
]
