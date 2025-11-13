"""Notification event handlers for BrowserNamespace."""

import logging
from typing import Dict, Any
from app.lib import (
    MessageType,
    create_success_response,
    create_error_response,
    generate_message_id,
)

logger = logging.getLogger(__name__)


class NotificationHandlersMixin:
    """Mixin for notification-related event handlers."""

    async def send_agent_error(self, username: str, error_data: Dict[str, Any]):
        """
        Send agent error notification to browser client using standardized message.
        
        Args:
            username: Username of the browser client
            error_data: Error response dict with error_code, user_message, technical_message, etc.
        """
        try:
            browser_sid = self.username_to_sid.get(username)
            if not browser_sid:
                self.logger.warning(f"No browser session found for {username}")
                return
            
            # Create standardized error message
            error_msg = create_error_response(
                error_code=error_data.get('error_code', 'AGENT_ERROR'),
                user_message=error_data.get('user_message', 'An error occurred during execution'),
                technical_message=error_data.get('technical_message', ''),
                message_id=error_data.get('message_id', generate_message_id()),
                recovery_suggestions=error_data.get('recovery_suggestions'),
                source='backend',
                route='agent'
            )
            
            await self.emit(
                MessageType.AGENT_ERROR.value,
                error_msg.to_dict(),
                to=browser_sid
            )
            self.logger.info(f"Sent {MessageType.AGENT_ERROR.value} to {username}: {error_data.get('user_message')}")
            
        except Exception as e:
            self.logger.error(f"Error sending agent error: {str(e)}")
    
    async def send_inbox_cleared(self, username: str):
        """
        Send inbox_cleared notification to browser client using standardized message.
        
        Args:
            username: Username of the browser client
        """
        try:
            browser_sid = self.username_to_sid.get(username)
            if not browser_sid:
                self.logger.warning(f"No browser session found for {username}")
                return
            
            # Create standardized success message for inbox clearing
            clear_inbox_msg = create_success_response(
                data={'message': 'Inbox cleared after successful processing'},
                message_id=generate_message_id(),
                source='backend',
                route='agent'  # This is an agent-initiated notification
            )
            # Override type to INBOX_CLEARED
            clear_inbox_msg.type = MessageType.INBOX_CLEARED
            
            await self.emit(
                MessageType.INBOX_CLEARED.value, 
                clear_inbox_msg.to_dict(), 
                to=browser_sid
            )
            self.logger.info(f"Sent {MessageType.INBOX_CLEARED.value} to {username}")
            
            # Also trigger scene context refresh for B.L.A.Z.E commands
            await self._trigger_scene_refresh(username)
            
        except Exception as e:
            self.logger.error(f"Error sending inbox_cleared: {str(e)}")
    
    async def _trigger_scene_refresh(self, username: str):
        """
        Trigger scene context refresh by calling list_scene_objects.
        
        Args:
            username: Username of the client
        """
        try:
            browser_sid = self.username_to_sid.get(username)
            if not browser_sid:
                self.logger.warning(f"No browser session found for {username}")
                return
            
            # Get browser session
            session = await self.get_session(browser_sid)
            if not session:
                self.logger.warning(f"No session found for {username}")
                return
            
            blender_sid = session.get('blender_sid')
            if not blender_sid:
                self.logger.warning(f"No Blender session found for {username}")
                return
            
            # Send list_scene_objects command to Blender
            refresh_message_id = generate_message_id()
            refresh_command = {
                'type': 'addon_command',
                'addon_id': 'multi_registry_assets',
                'command': 'list_scene_objects',
                'params': {},
                'message_id': refresh_message_id,
                'metadata': {'route': 'direct'}
            }
            
            # Forward to Blender namespace
            blender_namespace = self.server.namespace_handlers.get('/blender')
            if blender_namespace:
                success = await blender_namespace.send_command_to_blender(username, refresh_command)
                if success:
                    self.logger.info(f"Triggered scene context refresh for {username}")
                else:
                    self.logger.error(f"Failed to trigger scene context refresh for {username}")
            else:
                self.logger.error(f"Blender namespace not found for scene refresh for {username}")
                
        except Exception as e:
            self.logger.error(f"Error triggering scene refresh: {str(e)}")
