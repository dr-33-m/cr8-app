"""
Manifest file loading and parsing for AI addon manifests.
Handles loading JSON manifest files and creating AddonManifest objects.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_manifest_file(manifest_path: Path, addon_path: Path, addon_manifest_class):
    """
    Load and parse an addon manifest file.
    
    Args:
        manifest_path: Path to the addon_ai.json manifest file
        addon_path: Path to the addon directory
        addon_manifest_class: AddonManifest class to instantiate
        
    Returns:
        AddonManifest object if successful, None otherwise
    """
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_data = json.load(f)

        addon_id = manifest_data.get('addon_info', {}).get('id')
        if not addon_id:
            logger.error(
                f"No addon ID found in manifest at {manifest_path}"
            )
            return None

        return addon_manifest_class(addon_id, manifest_data, addon_path)

    except json.JSONDecodeError as e:
        logger.error(
            f"JSON parsing error in {manifest_path}: {str(e)}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Error loading manifest {manifest_path}: {str(e)}"
        )
        return None
