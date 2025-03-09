"""
Command handlers for WebSocket communication in cr8_engine.
Each handler module contains related command handlers for a specific domain.
"""

# Import handlers as they are implemented
from .animation_handler import AnimationHandler
from .asset_handler import AssetHandler
from .template_handler import TemplateHandler
from .preview_handler import PreviewHandler
from .base_specialized_handler import BaseSpecializedHandler

# Will be populated as handlers are implemented
__all__ = [
    'AnimationHandler',
    'AssetHandler',
    'TemplateHandler',
    'PreviewHandler',
    'BaseSpecializedHandler'
]
