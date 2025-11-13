"""
Browser Namespace Handler for Socket.IO
Handles all browser client connections and events.
"""

import logging
import socketio
import time
import asyncio
from typing import Dict, Any, Optional
from app.blaze.agent import BlazeAgent
from app.services.blender_service import BlenderService
from app.lib import (
    MessageType,
    create_system_message,
    create_success_response,
    create_error_response,
    generate_message_id,
)


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


class BrowserNamespace(socketio.AsyncNamespace):
    """Namespace handler for browser clients."""
    
    def __init__(self, namespace: str = '/browser'):
        super().__init__(namespace)
        self.logger = logging.getLogger(__name__)
        # Store username to sid mapping for finding sessions
        self.username_to_sid: Dict[str, str] = {}
    
    @property
    def blaze_agent(self):
        """Get reference to shared BlazeAgent singleton (lazy initialization)."""
        return get_shared_blaze_agent()
    
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
            if username in _cleanup_timers:
                _cleanup_timers[username].cancel()
                del _cleanup_timers[username]
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
            
            # Copy addon registry from Blender's browser session if available
            if 'browser_sid' in blender_session:
                blender_browser_sid = blender_session['browser_sid']
                if blender_browser_sid:
                    try:
                        blender_browser_session = await self.get_session(blender_browser_sid)
                        if blender_browser_session and 'addon_registry' in blender_browser_session:
                            session['addon_registry'] = blender_browser_session['addon_registry']
                            self.logger.info(f"Copied addon registry from previous browser session")
                    except Exception as e:
                        self.logger.error(f"Error copying addon registry: {e}")
            
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
    
    async def on_command_sent(self, sid: str, data: Dict[str, Any]):
        """
        Handle standardized command_sent events from browser.
        Extracts command from SocketMessage and forwards to Blender.
        
        Args:
            sid: Socket.IO session ID
            data: SocketMessage with CommandPayload
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return
            
            username = session['username']
            message_id = data.get('message_id', generate_message_id())
            payload = data.get('payload', {})
            metadata = data.get('metadata', {})
            route = metadata.get('route', 'direct')  # Extract route from frontend
            refresh_context = metadata.get('refresh_context', False)  # Extract refresh_context from metadata
            
            self.logger.info(f"Received command from {username} with route: {route}: {payload.get('command')}")
            
            # Extract command details from payload
            addon_id = payload.get('addon_id', 'blender_ai_router')
            command = payload.get('command')
            params = payload.get('params', {})
            
            if not command:
                error_msg = create_error_response(
                    error_code='VALIDATION_ERROR',
                    user_message='No command specified',
                    technical_message='Command field missing in payload',
                    message_id=message_id,
                    source='backend',
                    route=route  # Use extracted route
                )
                await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)
                return
            
            # Track refresh_context for this command
            if refresh_context:
                session['pending_refresh'] = session.get('pending_refresh', {})
                session['pending_refresh'][message_id] = {
                    'addon_id': addon_id,
                    'command': command,
                    'timestamp': time.time()
                }
                await self.save_session(sid, session)
                self.logger.info(f"Tracking refresh_context for message_id {message_id}")
            
            # Forward to Blender
            blender_sid = session.get('blender_sid')
            if not blender_sid:
                error_msg = create_error_response(
                    error_code='BLENDER_DISCONNECTED',
                    user_message='Blender is not connected',
                    technical_message='No blender_sid in session',
                    message_id=message_id,
                    source='backend',
                    route=route  # Use extracted route
                )
                await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)
                return
            
            # Create command message for Blender with route metadata
            command_data = {
                'type': 'addon_command',
                'addon_id': addon_id,
                'command': command,
                'params': params,
                'message_id': message_id,
                'metadata': {'route': route}  # Preserve route for response
            }
            
            # Forward to Blender namespace
            blender_namespace = self.server.namespace_handlers.get('/blender')
            if blender_namespace:
                success = await blender_namespace.send_command_to_blender(username, command_data)
                if not success:
                    error_msg = create_error_response(
                        error_code='ROUTING_FAILED',
                        user_message='Failed to send command to Blender',
                        technical_message='send_command_to_blender returned False',
                        message_id=message_id,
                        source='backend',
                        route=route  # Use extracted route
                    )
                    await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)
            else:
                error_msg = create_error_response(
                    error_code='ROUTING_FAILED',
                    user_message='Blender namespace not available',
                    technical_message='Blender namespace not found in server handlers',
                    message_id=message_id,
                    source='backend',
                    route=route  # Use extracted route
                )
                await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)
                
        except Exception as e:
            self.logger.error(f"Error processing command: {str(e)}")
            # Extract route for error response
            metadata = data.get('metadata', {})
            route = metadata.get('route', 'direct')
            error_msg = create_error_response(
                error_code='EXECUTION_FAILED',
                user_message='Error processing command',
                technical_message=str(e),
                message_id=data.get('message_id', generate_message_id()),
                source='backend',
                route=route  # Use extracted route
            )
            await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)
    
    async def on_agent_query_sent(self, sid: str, data: Dict[str, Any]):
        """
        Handle standardized agent_query_sent events from browser.
        Processes natural language queries through B.L.A.Z.E agent.
        
        Args:
            sid: Socket.IO session ID
            data: SocketMessage with AgentQueryPayload
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return
            
            username = session['username']
            message_id = data.get('message_id', generate_message_id())
            payload = data.get('payload', {})
            metadata = data.get('metadata', {})
            
            message = payload.get('message')
            context = payload.get('context', {})
            route = metadata.get('route', 'agent')  # Extract route from frontend
            
            self.logger.info(f"Received agent query from {username} with route: {route}")
            
            if not message:
                error_msg = create_error_response(
                    error_code='VALIDATION_ERROR',
                    user_message='No message provided',
                    technical_message='Message field missing in payload',
                    message_id=message_id,
                    source='backend',
                    route=route  # Use extracted route
                )
                await self.emit(MessageType.AGENT_ERROR.value, error_msg.to_dict(), to=sid)
                return
            
            # Get registry from session to pass as deps
            addon_registry = session.get('addon_registry')
            
            # Process message through shared B.L.A.Z.E agent (returns raw data)
            # Pass the route from frontend so B.L.A.Z.E can use it when sending commands to Blender
            # Pass full context (including scene_objects) instead of just inbox_items
            agent_response = await self.blaze_agent.process_message(
                username, 
                message, 
                'browser',
                context,  # Pass full context instead of just inbox_items
                deps={'addon_registry': addon_registry} if addon_registry else None,
                route=route  # Preserve route from frontend
            )
            
            # Check if response is success or error
            if agent_response.get('status') == 'success':
                # Wrap success response in standardized SocketMessage
                response_msg = create_success_response(
                    data={
                        'message': agent_response.get('message', ''),
                        'context': agent_response.get('context', '')
                    },
                    message_id=message_id,
                    source='backend',
                    route=route  # Use extracted route
                )
                await self.emit(MessageType.AGENT_RESPONSE_READY.value, response_msg.to_dict(), to=sid)
            else:
                # Wrap error response in standardized SocketMessage
                error_msg = create_error_response(
                    error_code=agent_response.get('error_code', 'AGENT_ERROR'),
                    user_message=agent_response.get('user_message', 'An error occurred'),
                    technical_message=agent_response.get('technical_message', ''),
                    message_id=message_id,
                    recovery_suggestions=agent_response.get('recovery_suggestions'),
                    source='backend',
                    route=route  # Use extracted route
                )
                await self.emit(MessageType.AGENT_ERROR.value, error_msg.to_dict(), to=sid)
            
        except Exception as e:
            self.logger.error(f"Error processing agent query: {str(e)}")
            # Extract route for error response
            metadata = data.get('metadata', {})
            route = metadata.get('route', 'agent')
            error_msg = create_error_response(
                error_code='EXECUTION_FAILED',
                user_message='Error processing your message',
                technical_message=str(e),
                message_id=data.get('message_id', generate_message_id()),
                source='backend',
                route=route  # Use extracted route
            )
            await self.emit(MessageType.AGENT_ERROR.value, error_msg.to_dict(), to=sid)
    
    
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
                    if username in _cleanup_timers:
                        del _cleanup_timers[username]
            
            # Store cleanup timer
            if username in _cleanup_timers:
                # Cancel existing timer
                _cleanup_timers[username].cancel()
            
            _cleanup_timers[username] = asyncio.create_task(cleanup_blender())
            
        except Exception as e:
            self.logger.error(f"Error in browser disconnect: {str(e)}")
