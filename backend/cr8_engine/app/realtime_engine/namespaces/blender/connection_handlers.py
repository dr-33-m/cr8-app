"""
Connection and disconnection handlers for Blender namespace.
"""

import logging
from typing import Dict, Any, Optional
from app.lib import (
    MessageType,
    create_system_message,
)


logger = logging.getLogger(__name__)


class ConnectionHandlersMixin:
    """Mixin providing connection/disconnection handling for BlenderNamespace."""

    async def on_connect(self, sid: str, environ: Dict, auth: Optional[Dict]) -> bool:
        """
        Handle Blender client connection.

        Args:
            sid: Socket.IO session ID
            environ: WSGI environment dict
            auth: Authentication data from client

        Returns:
            True to accept connection, False to reject
        """
        try:
            # Extract username from auth
            if not auth:
                self.logger.error("No authentication data provided from Blender")
                return False

            username = auth.get('username')
            if not username:
                self.logger.error("No username provided in Blender auth")
                return False

            self.logger.info(f"Blender connecting: {username} (sid: {sid})")

            # Find the browser session for this username
            # We need to access the browser namespace to get the session
            browser_namespace = self.server.namespace_handlers.get('/browser')
            if not browser_namespace:
                self.logger.error("Browser namespace not found")
                return False

            browser_sid = browser_namespace.username_to_sid.get(username)
            if not browser_sid:
                self.logger.error(f"No browser session found for {username}")
                return False

            # Get browser session
            browser_session = await browser_namespace.get_session(browser_sid)
            if not browser_session:
                self.logger.error(f"Browser session not found for {username}")
                return False

            # Update browser session with Blender sid
            browser_session['blender_sid'] = sid
            browser_session['state'] = 'connected'
            await browser_namespace.save_session(browser_sid, browser_session)

            # Store username mapping for Blender
            self.username_to_sid[username] = sid

            # Create Blender session data
            blender_session = {
                'username': username,
                'browser_sid': browser_sid,
                'user_room': browser_session['user_room']
            }
            await self.save_session(sid, blender_session)

            # Add Blender to user-specific room
            await self.enter_room(sid, blender_session['user_room'])

            self.logger.info(f"Blender connected: {username} in room {blender_session['user_room']}")

            # Notify browser that Blender is connected
            blender_connected_msg = create_system_message(
                message_type=MessageType.BLENDER_CONNECTED,
                status='connected',
                message='Blender instance connected successfully',
                source='backend'
            )
            await browser_namespace.emit(MessageType.BLENDER_CONNECTED.value, blender_connected_msg.to_dict(), to=browser_sid)

            # Send connection confirmation to Blender
            confirmation_msg = create_system_message(
                message_type=MessageType.BLENDER_CONNECTED,
                status='connected',
                message='Blender registered successfully',
                source='backend'
            )
            await self.emit(MessageType.BLENDER_CONNECTED.value, confirmation_msg.to_dict(), to=sid)

            return True

        except Exception as e:
            self.logger.error(f"Error in Blender connect: {str(e)}")
            return False

    async def on_disconnect(self, sid: str, reason: str):
        """
        Handle Blender client disconnection.

        Args:
            sid: Socket.IO session ID
            reason: Disconnection reason
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.warning(f"No session found for disconnecting Blender sid {sid}")
                return

            username = session['username']
            user_room = session['user_room']
            browser_sid = session['browser_sid']

            self.logger.info(f"Blender disconnected: {username} (reason: {reason})")

            # Remove from username mapping
            if self.username_to_sid.get(username) == sid:
                del self.username_to_sid[username]

            # Leave room
            await self.leave_room(sid, user_room)

            # Update browser session
            browser_namespace = self.server.namespace_handlers.get('/browser')
            if browser_namespace and browser_sid:
                try:
                    browser_session = await browser_namespace.get_session(browser_sid)
                    if browser_session:
                        browser_session['blender_sid'] = None
                        browser_session['state'] = 'blender_disconnected'
                        await browser_namespace.save_session(browser_sid, browser_session)

                        # Notify browser using standardized message
                        disconnect_msg = create_system_message(
                            message_type=MessageType.BLENDER_DISCONNECTED,
                            status='disconnected',
                            message='Blender instance disconnected',
                            data={'reason': reason},
                            source='backend'
                        )
                        await browser_namespace.emit(MessageType.BLENDER_DISCONNECTED.value, disconnect_msg.to_dict(), to=browser_sid)
                    else:
                        self.logger.info(f"Browser session already cleaned up for {username}")
                except Exception as e:
                    self.logger.info(f"Browser session unavailable for {username}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error in Blender disconnect: {str(e)}")
