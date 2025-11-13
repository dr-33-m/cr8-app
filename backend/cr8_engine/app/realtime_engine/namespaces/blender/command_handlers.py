"""
Command handling and routing for Blender namespace.
"""

import logging
from typing import Dict, Any
from app.lib import MessageType


logger = logging.getLogger(__name__)


class CommandHandlersMixin:
    """Mixin providing command handling for BlenderNamespace."""

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
