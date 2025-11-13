"""
Connection and disconnection handlers for browser namespace.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional
from app.services.blender_service import BlenderService
from app.lib import (
    MessageType,
    create_system_message,
)
from .singleton import get_cleanup_timers


logger = logging.getLogger(__name__)


class ConnectionHandlersMixin:
    """Mixin providing connection/disconnection handling for BrowserNamespace."""

    async def is_blender_in_room(self, username: str) -> bool:
        """Check if Blender client is in user's room"""
        user_room = f"user_{username}"
        blender_namespace = self.server.namespace_handlers.get('/blender')
        if not blender_namespace:
            return False

        # Check room members in blender namespace
        try:
            room_sids = list(self.server.manager.get_participants('/blender', user_room))
            return len(room_sids) > 0
        except Exception as e:
            self.logger.error(f"Error checking room participants: {e}")
            return False

    async def on_connect(self, sid: str, environ: Dict, auth: Optional[Dict]) -> bool:
        """
        Handle browser client connection.

        Args:
            sid: Socket.IO session ID
            environ: WSGI environment dict
            auth: Authentication data from client

        Returns:
            True to accept connection, False to reject
        """
        try:
            # DEBUG: Log what we receive
            self.logger.info(f"=== CONNECTION ATTEMPT ===")
            self.logger.info(f"SID: {sid}")
            self.logger.info(f"Auth type: {type(auth)}")
            self.logger.info(f"Auth value: {auth}")
            self.logger.info(f"Environ keys: {list(environ.keys())}")

            # Extract connection details from auth
            if not auth:
                self.logger.error("No authentication data provided")
                return False

            username = auth.get('username')
            blend_file_path = auth.get('blend_file_path')

            self.logger.info(f"Extracted username: {username}")
            self.logger.info(f"Extracted blend_file_path: {blend_file_path}")

            if not username:
                self.logger.error("No username provided in auth")
                return False

            self.logger.info(f"Browser connecting: {username} (sid: {sid})")

            # Cancel any pending cleanup for this user
            cleanup_timers = get_cleanup_timers()
            if username in cleanup_timers:
                cleanup_timers[username].cancel()
                del cleanup_timers[username]
                self.logger.info(f"Cancelled cleanup timer for {username}")

            # Check if user already has an active session
            existing_sid = self.username_to_sid.get(username)
            if existing_sid and existing_sid != sid:
                # Get existing session
                try:
                    existing_session = await self.get_session(existing_sid)
                    if existing_session:
                        # User is reconnecting - update the mapping
                        self.logger.info(f"User {username} reconnecting, updating session")
                        self.username_to_sid[username] = sid
                except:
                    # Old session doesn't exist, proceed with new one
                    pass

            # Store username mapping
            self.username_to_sid[username] = sid

            # Create session data
            session_data = {
                'username': username,
                'blend_file': blend_file_path,
                'browser_sid': sid,
                'blender_sid': None,
                'state': 'waiting_for_browser_ready',
                'addon_registry': None,  # Store registry data (serializable dict)
                'user_room': f"user_{username}"
            }

            # Save session
            await self.save_session(sid, session_data)

            # Add browser to user-specific room
            await self.enter_room(sid, session_data['user_room'])

            self.logger.info(f"Browser connected: {username} in room {session_data['user_room']}")

            # Send connection acknowledgment using standardized message
            session_created_msg = create_system_message(
                message_type=MessageType.SESSION_CREATED,
                status='connected',
                message='Session created',
                data={'username': username},
                source='backend'
            )
            await self.emit(MessageType.SESSION_CREATED.value, session_created_msg.to_dict(), to=sid)

            return True

        except Exception as e:
            self.logger.error(f"Error in browser connect: {str(e)}")
            return False

    async def notify_existing_blender_connection(self, sid: str):
        """Notify browser of existing Blender connection and link sessions"""
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return

            username = session['username']

            # Find Blender client using username mapping (cleaner approach)
            blender_namespace = self.server.namespace_handlers.get('/blender')
            if not blender_namespace:
                self.logger.error("Blender namespace not found")
                return

            # Use username_to_sid mapping instead of room participants
            blender_sid = blender_namespace.username_to_sid.get(username)
            if not blender_sid:
                self.logger.error(f"No Blender SID found for {username}")
                return

            self.logger.info(f"Found Blender client {blender_sid} for user {username}")

            # Get Blender session to access registry data
            try:
                blender_session = await blender_namespace.get_session(blender_sid)
                if not blender_session:
                    self.logger.error(f"No session found for Blender sid {blender_sid}")
                    return
            except Exception as e:
                self.logger.error(f"Error getting Blender session: {e}")
                return

            # Link sessions: Update browser session with Blender SID
            session['blender_sid'] = blender_sid
            session['state'] = 'connected'

            # Restore addon_registry from Blender session (persists across server restarts)
            if 'addon_registry' in blender_session:
                session['addon_registry'] = blender_session['addon_registry']
                self.logger.info(f"Restored addon_registry from Blender session")

            await self.save_session(sid, session)
            self.logger.info(f"Linked browser {sid} to Blender {blender_sid}")

            # Update Blender session with new browser SID
            blender_session['browser_sid'] = sid
            await blender_namespace.save_session(blender_sid, blender_session)

            # Notify browser that existing Blender is connected
            connected_msg = create_system_message(
                message_type=MessageType.BLENDER_CONNECTED,
                status='connected',
                message='Reconnected to existing Blender session',
                source='backend'
            )
            await self.emit(MessageType.BLENDER_CONNECTED.value, connected_msg.to_dict(), to=sid)

            self.logger.info(f"Sent existing Blender connection notification to {username}")

        except Exception as e:
            self.logger.error(f"Error notifying existing connection: {str(e)}")

    async def on_disconnect(self, sid: str, reason: str):
        """
        Handle browser client disconnection with cleanup timer.

        Args:
            sid: Socket.IO session ID
            reason: Disconnection reason
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.warning(f"No session found for disconnecting sid {sid}")
                return

            username = session['username']
            user_room = session['user_room']

            self.logger.info(f"Browser disconnected: {username} (reason: {reason})")

            # Remove from username mapping
            if self.username_to_sid.get(username) == sid:
                del self.username_to_sid[username]

            # Leave room
            await self.leave_room(sid, user_room)

            # Notify Blender client if connected
            blender_sid = session.get('blender_sid')
            if blender_sid:
                await self.emit('browser_disconnected', {
                    'username': username,
                    'reason': reason
                }, room=user_room, skip_sid=sid)

            # Start cleanup timer
            async def cleanup_blender():
                try:
                    await asyncio.sleep(300)  # 5 minutes
                    # Check if browser reconnected
                    if username not in self.username_to_sid:
                        self.logger.info(f"Cleaning up Blender for {username} after 5 minutes")
                        await BlenderService.terminate_instance(username)
                    else:
                        self.logger.info(f"Browser reconnected for {username}, skipping cleanup")
                except Exception as e:
                    self.logger.error(f"Error in cleanup timer: {e}")
                finally:
                    # Remove timer from cleanup dict
                    cleanup_timers = get_cleanup_timers()
                    if username in cleanup_timers:
                        del cleanup_timers[username]

            # Store cleanup timer
            cleanup_timers = get_cleanup_timers()
            if username in cleanup_timers:
                # Cancel existing timer
                cleanup_timers[username].cancel()

            cleanup_timers[username] = asyncio.create_task(cleanup_blender())

        except Exception as e:
            self.logger.error(f"Error in browser disconnect: {str(e)}")
