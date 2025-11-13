"""Command event handlers for BrowserNamespace."""

import logging
import time
from typing import Dict, Any
from app.lib import (
    MessageType,
    create_success_response,
    create_error_response,
    generate_message_id,
)

logger = logging.getLogger(__name__)


class CommandHandlersMixin:
    """Mixin for command-related event handlers."""

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
