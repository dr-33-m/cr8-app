"""
Command handlers for WebSocket communication.
Each handler module contains related command handlers for a specific domain.
"""

# Import handlers as they are implemented
from .animation import AnimationHandlers
from .asset import AssetHandlers
from .render import RenderHandlers
from .scene import SceneHandlers
from .template import TemplateHandlers
# etc.

# Will be populated as handlers are implemented
__all__ = ['AnimationHandlers', 'AssetHandlers',
           'RenderHandlers', 'SceneHandlers', 'TemplateHandlers']
