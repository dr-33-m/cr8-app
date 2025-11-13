"""
Local Tools for B.L.A.Z.E Agent
System operation tools that the AI can autonomously call.
"""

import logging
from typing import Dict, Any
from pydantic_ai import RunContext

logger = logging.getLogger(__name__)


async def clear_inbox(ctx: RunContext[Dict[str, Any]]) -> str:
    """
    B.L.A.Z.E tool: Clear the user's inbox after successful asset processing.
    
    This is a local system operation tool that the AI can call autonomously
    after verifying that assets have been successfully downloaded and added to the scene.
    
    Args:
        ctx: Pydantic AI RunContext containing agent dependencies
        
    Returns:
        Success message confirming inbox was cleared
    """
    try:
        # Get browser_namespace from deps
        browser_namespace = ctx.deps.get('browser_namespace')
        if not browser_namespace:
            logger.error("browser_namespace not found in deps")
            return "Error: Could not access browser namespace to clear inbox"
        
        # Get agent_instance from deps
        agent_instance = ctx.deps.get('agent_instance')
        if not agent_instance:
            logger.error("agent_instance not found in deps")
            return "Error: Could not access agent instance"
        
        # Get username from agent instance
        username = agent_instance.current_username
        if not username:
            logger.error("No current username set")
            return "Error: No active user session"
        
        # Emit inbox_cleared event to browser
        await browser_namespace.send_inbox_cleared(username)
        
        logger.info(f"Successfully cleared inbox for {username}")
        return f"Inbox cleared successfully for {username}. The frontend has been notified."
        
    except Exception as e:
        logger.error(f"Error clearing inbox: {str(e)}")
        return f"Error clearing inbox: {str(e)}"
