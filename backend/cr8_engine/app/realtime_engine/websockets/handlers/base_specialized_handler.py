"""
Base class for specialized WebSocket handlers in cr8_engine.
This module provides common functionality for all specialized handlers.
"""

import logging
import uuid
from typing import Dict, Any, Optional


class BaseSpecializedHandler:
    """Base class for specialized WebSocket handlers."""

    def __init__(self, session_manager):
        """
        Initialize the specialized handler.

        Args:
            session_manager: The session manager instance
        """
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)

    async def forward_to_blender(self, username: str, command: str, data: Dict[str, Any], message_id: Optional[str] = None) -> Any:
        """
        Forward a command to the connected Blender client.

        Args:
            username: The username of the client
            command: The command to forward
            data: The data to forward
            message_id: The message ID for tracking

        Returns:
            The session object for further use

        Raises:
            ValueError: If Blender client is not connected
        """
        session = self.session_manager.get_session(username)

        # Check if session exists and Blender is connected
        if not session:
            raise ValueError("No active session found")

        if not session.blender_socket or session.blender_socket_closed:
            # Special handling for template controls - queue the request
            if command == "get_template_controls":
                # Queue the request for later processing
                request_data = {**data, 'command': command}
                if message_id:
                    request_data['message_id'] = message_id

                # Add to pending template requests
                if not hasattr(session, 'pending_template_requests'):
                    session.pending_template_requests = []

                session.pending_template_requests.append(request_data)

                self.logger.info(
                    f"Queued {command} for {username} until Blender connects")

                # Return session without raising error
                return session
            else:
                # For other commands, raise the error
                raise ValueError("Blender client not connected")

        # Generate message_id if not provided
        if not message_id:
            message_id = str(uuid.uuid4())
            self.logger.debug(f"Generated message_id: {message_id}")

        # Add to pending requests for tracking
        self.session_manager.add_pending_request(username, message_id)

        # Prepare the message with message_id for tracking
        blender_message = {**data, 'command': command,
                           'message_id': message_id}

        try:
            # Send to Blender
            await session.blender_socket.send_json(blender_message)
            self.logger.info(f"Forwarded {command} to Blender for {username}")
        except Exception as e:
            # Mark socket as closed if send fails
            session.blender_socket_closed = True
            self.logger.error(f"Error forwarding to Blender: {str(e)}")
            raise ValueError(f"Failed to communicate with Blender: {str(e)}")

        # Return the session for further use
        return session

    async def send_response(self, username: str, command: str, success: bool, data: Dict[str, Any], message: Optional[str] = None, message_id: Optional[str] = None) -> None:
        """
        Send a response to the browser client.

        Args:
            username: The username of the client
            command: The command to respond to
            success: Whether the operation was successful
            data: The data to send
            message: An optional message
            message_id: The message ID for tracking
        """
        session = self.session_manager.get_session(username)
        if not session or not session.browser_socket or session.browser_socket_closed:
            self.logger.warning(
                f"Cannot send response to {username}: No browser socket or socket is closed")
            return

        # Format and send response
        response = {
            'command': command,
            'status': 'success' if success else 'error',
            'data': data
        }

        if message:
            response['message'] = message

        if message_id:
            response['message_id'] = message_id

        try:
            await session.browser_socket.send_json(response)
            self.logger.debug(f"Sent {command} response to {username}")
        except Exception as e:
            session.browser_socket_closed = True
            self.logger.error(f"Error sending response to browser: {str(e)}")

    async def send_error(self, username: str, command: str, error_message: str, message_id: Optional[str] = None) -> None:
        """
        Send an error response to the browser client.

        Args:
            username: The username of the client
            command: The command that failed
            error_message: The error message
            message_id: The message ID for tracking
        """
        await self.send_response(
            username,
            f"{command}_result",
            False,
            {'error': error_message},
            error_message,
            message_id
        )
        self.logger.error(
            f"Error in {command} for {username}: {error_message}")

    async def handle_response(self, username: str, data: Dict[str, Any], client_type: str) -> None:
        """
        Handle a response from Blender.

        Args:
            username: The username of the client
            data: The response data
            client_type: The type of client (browser or blender)
        """
        if client_type != "blender":
            return

        try:
            # Extract message_id
            message_id = data.get('message_id')
            if not message_id:
                self.logger.error("No message_id in response")
                return

            # Find requesting user
            request_username = self.session_manager.get_pending_request(
                message_id)
            if not request_username:
                self.logger.error(
                    f"No pending request for message_id {message_id}")
                return

            # Get session
            session = self.session_manager.get_session(request_username)
            if not session or not session.browser_socket or session.browser_socket_closed:
                self.logger.error(
                    f"No valid session or browser socket for {request_username}")
                # Clean up the pending request even if we can't forward the response
                self.session_manager.remove_pending_request(message_id)
                return

            # Forward response to browser
            try:
                await session.browser_socket.send_json(data)
                self.logger.info(
                    f"Forwarded response to browser for {request_username}")
            except Exception as e:
                session.browser_socket_closed = True
                self.logger.error(
                    f"Error forwarding response to browser: {str(e)}")

            # Clean up
            self.session_manager.remove_pending_request(message_id)

        except Exception as e:
            self.logger.error(f"Error handling response: {e}")
            import traceback
            traceback.print_exc()
