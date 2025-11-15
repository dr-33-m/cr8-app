"""
Inbox processing B.L.A.Z.E integration functions.

Provides functions for processing and downloading assets from the user's inbox.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ...handlers import process_inbox_batch

logger = logging.getLogger(__name__)


# ============================================================================
# Inbox Processing
# ============================================================================


def process_inbox_assets(
    resolution: str = "1k",
    import_to_scene: bool = True,
    clear_inbox_after_processing: bool = True,
    inbox_items: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Process and download assets from the user's inbox context.
    
    Args:
        resolution: Asset resolution quality
        import_to_scene: Whether to import to scene
        clear_inbox_after_processing: Whether to clear inbox after
        inbox_items: List of inbox items to process
        
    Returns:
        JSON string with batch processing results
    """
    try:
        if inbox_items is None:
            inbox_items = []
        
        result = process_inbox_batch(
            inbox_items=inbox_items,
            resolution=resolution,
            import_to_scene=import_to_scene,
        )
        
        result["clear_inbox_after_processing"] = clear_inbox_after_processing
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Process inbox assets failed: {e}")
        return json.dumps({
            "success": False,
            "message": f"Failed to process inbox assets: {str(e)}",
            "processed_count": 0,
            "failed_count": 0,
            "results": [],
        })
