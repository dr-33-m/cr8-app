"""
Manifest handling module for AI addon manifests.
Provides manifest loading, validation, and data container classes.
"""

from .addon_manifest import AddonManifest
from .validator import (
    validate_manifest,
    validate_tool,
    validate_parameter,
)
from .loader import load_manifest_file

__all__ = [
    'AddonManifest',
    'validate_manifest',
    'validate_tool',
    'validate_parameter',
    'load_manifest_file',
]
