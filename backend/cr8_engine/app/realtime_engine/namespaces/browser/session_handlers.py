"""Session event handlers for BrowserNamespace."""

import logging
from typing import Dict, Optional
from app.services.blender_service import BlenderService
from app.lib import (
    MessageType,
    create_system_message,
    create_error_response,
    generate_message_id,
)

logger = logging.getLogger(__name__)


class SessionHandlersMixin:
    """Mixin for session-related event handlers."""

    async def on_browser_ready(self, sid: str, data: Optional[Dict] = None):
        """
        Handle browser ready signal with smart connection logic.
        
        Args:
            sid: Socket.IO session ID
            data: Optional data from client (may include recovery flag)
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return
            
            username = session['username']
            blend_file = session['blend_file']
            recovery_mode = data.get('recovery', False) if data else False
            
            self.logger.info(f"Browser ready signal from {username} (recovery: {recovery_mode})")
            
            # ALWAYS check if Blender is already in the room (single source of truth)
            if await self.is_blender_in_room(username):
                self.logger.info(f"Blender already in room for {username}, notifying browser")
                await self.notify_existing_blender_connection(sid)
                return
            
            # If we get here, no Blender in room - safe to launch
            self.logger.info(f"No Blender in room for {username}, launching new instance")
            
            # Update session state
            session['state'] = 'launching_blender'
            await self.save_session(sid, session)
            
            # Notify browser that Blender is launching
            launching_msg = create_system_message(
                message_type=MessageType.SESSION_READY,
                status='launching_blender',
                message='Launching Blender instance',
                source='backend'
            )
            await self.emit(MessageType.SESSION_READY.value, launching_msg.to_dict(), to=sid)
            
            # Launch Blender instance
            success = await BlenderService.launch_instance(username, blend_file)
            
            if not success:
                self.logger.error(f"Failed to launch Blender for {username}")
                error_msg = create_error_response(
                    error_code='EXECUTION_FAILED',
                    user_message='Failed to launch Blender instance',
                    technical_message='BlenderService.launch_instance returned False',
                    message_id=generate_message_id(),
                    source='backend',
                    route='direct'
                )
                await self.emit(MessageType.EXECUTION_ERROR.value, error_msg.to_dict(), to=sid)
                session['state'] = 'error'
                await self.save_session(sid, session)
                return
            
            # Update state to waiting for Blender connection
            session['state'] = 'waiting_for_blender'
            await self.save_session(sid, session)
            
            self.logger.info(f"Blender launched for {username}, waiting for connection")
            
        except Exception as e:
            self.logger.error(f"Error in browser_ready: {str(e)}")
            error_msg = create_error_response(
                error_code='EXECUTION_FAILED',
                user_message='Error launching Blender',
                technical_message=str(e),
                message_id=generate_message_id(),
                source='backend',
                route='direct'
            )
            await self.emit(MessageType.EXECUTION_ERROR.value, error_msg.to_dict(), to=sid)
