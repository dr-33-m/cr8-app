"""
BlazeAgent singleton management for browser namespace.
"""

import logging
import asyncio
from typing import Dict, Optional
from app.blaze.agent import BlazeAgent


logger = logging.getLogger(__name__)

# Singleton BlazeAgent instance - shared across all users
# Following Pydantic AI best practices: agents are stateless and reusable
_shared_blaze_agent: Optional[BlazeAgent] = None

# Cleanup timers for browser disconnects
_cleanup_timers: Dict[str, asyncio.Task] = {}


def initialize_shared_blaze_agent(browser_ns, blender_ns) -> BlazeAgent:
    """Initialize the shared BlazeAgent singleton with namespace references."""
    global _shared_blaze_agent
    if _shared_blaze_agent is None:
        _shared_blaze_agent = BlazeAgent(browser_ns, blender_ns)
        logger.info("Created shared BlazeAgent singleton with namespace references")
    return _shared_blaze_agent


def get_shared_blaze_agent() -> BlazeAgent:
    """Get the shared BlazeAgent singleton."""
    global _shared_blaze_agent
    if _shared_blaze_agent is None:
        raise RuntimeError("BlazeAgent singleton not initialized. Call initialize_shared_blaze_agent first.")
    return _shared_blaze_agent


def get_cleanup_timers() -> Dict[str, asyncio.Task]:
    """Get the cleanup timers dictionary."""
    global _cleanup_timers
    return _cleanup_timers
