"""
Blender Namespace Handler for Socket.IO
Handles all Blender client connections and events.
"""

import logging
import socketio
import uuid
import time
import json
from typing import Dict, Any, Optional
from app.lib import (
    MessageType,
    create_system_message,
    create_success_response,
    create_error_response,
    generate_message_id,
)


logger = logging.getLogger(__name__)


class BlenderNamespace(socketio.AsyncNamespace):
    """Namespace handler for Blender clients."""
    
    def __init__(self, namespace: str = '/blender'):
        super().__init__(namespace)
        self.logger = logging.getLogger(__name__)
        # Store username to sid mapping for Blender clients
        self.username_to_sid: Dict[str, str] = {}
    
    @property
    def blaze_agent(self):
        """Get reference to shared BlazeAgent singleton (lazy initialization)."""
        from .browser_namespace import get_shared_blaze_agent
        return get_shared_blaze_agent()
    
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
    
    async def on_command_completed(self, sid: str, data: Dict[str, Any]):
        """
        Handle command_completed events from Blender with route-based forwarding.
        
        Args:
            sid: Socket.IO session ID
            data: Command result data with metadata containing route information
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return
            
            username = session['username']
            browser_sid = session['browser_sid']
            message_id = data.get('message_id')
            
            # Extract route from metadata to determine forwarding
            metadata = data.get('metadata', {})
            route = metadata.get('route', 'direct')  # Default to 'direct' if not specified
            
            self.logger.info(f"Received command_completed for {username} with route: {route}")
            
            # Route-based forwarding
            if route == 'agent':
                # Agent-initiated command: Forward to B.L.A.Z.E only
                # B.L.A.Z.E will process the response and send any necessary notifications
                if message_id:
                    try:
                        self.blaze_agent.handle_command_response(message_id, data)
                        self.logger.info(f"Forwarded agent command response to B.L.A.Z.E for message_id {message_id}")
                    except Exception as e:
                        self.logger.error(f"Error forwarding response to B.L.A.Z.E: {str(e)}")
                else:
                    self.logger.warning(f"Agent command completed but no message_id found")
                    
            elif route == 'direct':
                # Direct command: Forward to browser only
                browser_namespace = self.server.namespace_handlers.get('/browser')
                if browser_namespace and browser_sid:
                    # Check if this command needs scene context refresh
                    needs_refresh = False
                    if message_id:
                        try:
                            # Get browser session to check for pending refresh
                            browser_session = await browser_namespace.get_session(browser_sid)
                            if browser_session and 'pending_refresh' in browser_session:
                                pending_refresh = browser_session['pending_refresh']
                                if message_id in pending_refresh:
                                    needs_refresh = True
                                    # Remove from pending refresh
                                    del pending_refresh[message_id]
                                    await browser_namespace.save_session(browser_sid, browser_session)
                                    self.logger.info(f"Found pending refresh for message_id {message_id}")
                        except Exception as e:
                            self.logger.error(f"Error checking pending refresh: {str(e)}")
                    
                    # Extract event name from message type (REQUIRED)
                    event_name = data.get('type')
                    if not event_name:
                        self.logger.error(f"No 'type' field in message data from Blender: {data}")
                        raise ValueError("Message must include 'type' field for proper routing")

                    await browser_namespace.emit(event_name, data, to=browser_sid)
                    self.logger.info(f"Forwarded {event_name} event to browser for {username}")
                    
                    # Trigger scene refresh if needed
                    if needs_refresh:
                        try:
                            await browser_namespace._trigger_scene_refresh(username)
                            self.logger.info(f"Triggered scene refresh after command completion for {username}")
                        except Exception as e:
                            self.logger.error(f"Error triggering scene refresh: {str(e)}")
                else:
                    self.logger.warning(f"Could not forward response to browser for {username}")
            else:
                self.logger.warning(f"Unknown route '{route}' for command_completed")
            
            
        except Exception as e:
            self.logger.error(f"Error handling command_completed: {str(e)}")
    
    async def on_registry_update(self, sid: str, data: Dict[str, Any]):
        """
        Handle registry update events from Blender AI Router.
        
        Args:
            sid: Socket.IO session ID
            data: Registry update data
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return
            
            username = session['username']
            browser_sid = session['browser_sid']
            
            self.logger.info(f"Received registry update from Blender for {username}")
            
            # Get browser session to store registry data
            browser_namespace = self.server.namespace_handlers.get('/browser')
            if browser_namespace:
                browser_session = await browser_namespace.get_session(browser_sid)
                if browser_session:
                    # Store registry data in browser session (as serializable dict)
                    browser_session['addon_registry'] = data
                    await browser_namespace.save_session(browser_sid, browser_session)
                    self.logger.info(f"Stored registry data in browser session for {username}")
            
            # Send acknowledgment back to Blender
            await self.emit('registry_update_ack', {
                'status': 'processed',
                'message': 'Registry update processed successfully'
            }, to=sid)
            
        except Exception as e:
            self.logger.error(f"Error handling registry update: {str(e)}")
            await self.emit('registry_update_ack', {
                'status': 'error',
                'message': f'Failed to process registry update: {str(e)}'
            }, to=sid)
    
    async def on_browser_command(self, sid: str, data: Dict[str, Any]):
        """
        Handle commands from browser forwarded via Socket.IO emit.
        
        Args:
            sid: Socket.IO session ID
            data: Command data from browser
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return
            
            username = session['username']
            self.logger.info(f"Received browser_command for {username}: {data.get('command')}")
            
            # The Blender client will handle this event through its event handler
            # This method just logs it for debugging purposes
            
        except Exception as e:
            self.logger.error(f"Error handling browser_command: {str(e)}")
    
    async def send_command_to_blender(self, username: str, command_data: Dict[str, Any], route: str = 'direct'):
        """
        Send a command to a connected Blender client using standardized message type.
        
        Args:
            username: Username of the Blender client
            command_data: Command data to send
            route: Route type ('direct' or 'agent') for response routing
        """
        try:
            blender_sid = self.username_to_sid.get(username)
            if not blender_sid:
                self.logger.error(f"No Blender session found for {username}")
                return False
            
            # Add metadata with route information if not already present
            if 'metadata' not in command_data:
                command_data['metadata'] = {
                    'route': route,
                    'source': 'backend'
                }
            elif 'route' not in command_data['metadata']:
                command_data['metadata']['route'] = route
            
            # Emit standardized COMMAND_RECEIVED event to Blender client
            await self.emit(MessageType.COMMAND_RECEIVED.value, command_data, to=blender_sid)
            self.logger.info(f"Sent {MessageType.COMMAND_RECEIVED.value} to Blender for {username}: {command_data.get('command')}, route: {route}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending command to Blender: {str(e)}")
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
