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

# Instance saves upload in parts to stay under the Cloudflare tunnel's ~100MB
# request-body cap (RustFS sits behind NAT, so the tunnel is the only ingress —
# there is no VPN path to bypass it). 90MiB leaves headroom under the cap.
SAVE_PART_SIZE_BYTES = 90 * 1024 * 1024


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

    async def _emit_save_failed(self, sid: str, message_id: str, code: str, user_message: str):
        """Report a save failure back to the browser as a command_failed the
        frontend already knows how to match by message_id."""
        error_msg = create_error_response(
            error_code=code,
            user_message=user_message,
            technical_message=user_message,
            message_id=message_id,
            source='backend',
            route='direct',
        )
        await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)

    async def _emit_save_result(self, sid: str, message_id: str, ok: bool, message: str):
        """Report a save outcome as a command_completed carrying the real result
        in payload.data.ok — the shape the frontend's save handler matches on."""
        result = {
            'message_id': message_id,
            'type': MessageType.COMMAND_COMPLETED.value,
            'payload': {'status': 'success', 'data': {'ok': ok, 'message': message}},
            'metadata': {'source': 'backend', 'route': 'direct'},
        }
        await self.emit(MessageType.COMMAND_COMPLETED.value, result, to=sid)

    async def _perform_multipart_save(self, username: str, user_id: str,
                                      filename: str) -> tuple:
        """
        Save the running .blend to cloud storage as a multipart upload.

        RustFS is behind NAT, reachable by instances only through the Cloudflare
        tunnel, which caps request bodies at ~100MB. So the engine creates a
        multipart upload and pre-signs part URLs (public/tunnel host — the same
        one the instance already reaches for downloads), the instance PUTs each
        part under the cap, and the engine completes the upload from the ETags.
        Credentials never leave the engine. Returns (ok: bool, message: str).
        """
        from app.services.storage_service import (
            create_multipart_upload, presign_part, complete_multipart_upload,
            abort_multipart_upload, StorageError, MAX_BLEND_BYTES,
        )

        blender_ns = self.server.namespace_handlers.get('/blender')
        if not blender_ns:
            return False, 'Blender is not connected'

        try:
            created = create_multipart_upload(user_id, filename)
            key = created['key']
            upload_id = created['uploadId']
            # Enough parts to cover the max blend size at this part size, with a
            # margin. presign_part guards its own upper bound.
            n_parts = (MAX_BLEND_BYTES // SAVE_PART_SIZE_BYTES) + 8
            part_urls = [
                presign_part(key, upload_id, i, user_id)
                for i in range(1, n_parts + 1)
            ]
        except StorageError as e:
            return False, str(e)
        except Exception as e:
            self.logger.error(f"Multipart start failed for {username}: {e}")
            return False, 'Could not start the save'

        self.logger.info(f"Multipart save for {username} -> {key} ({upload_id})")
        resp = await blender_ns.request_and_wait(username, {
            'type': 'addon_command',
            'addon_id': 'blender_ai_router',
            'command': 'save',
            'params': {
                'multipart': {
                    'upload_id': upload_id,
                    'key': key,
                    'part_size': SAVE_PART_SIZE_BYTES,
                    'part_urls': part_urls,
                },
            },
            'metadata': {'route': 'direct'},
        }, timeout=1200)  # up to 20 min — a 2GB upload over the tunnel is slow

        parts = (resp or {}).get('parts')
        ok = bool(resp and resp.get('ok') and parts)
        try:
            if ok:
                complete_multipart_upload(key, upload_id, parts, user_id)
            else:
                abort_multipart_upload(key, upload_id, user_id)
        except Exception as e:
            self.logger.error(f"Multipart finalize failed for {username}: {e}")
            try:
                abort_multipart_upload(key, upload_id, user_id)
            except Exception:
                pass
            return False, 'Save could not be finalized'

        message = (resp or {}).get('message') or ('Saved to cloud' if ok else 'Save failed')
        return ok, message

    async def on_save_file(self, sid: str, data: Dict[str, Any]):
        """
        Save the running Blender file back to cloud storage (RustFS).

        Two modes:
          - Plain Save: overwrite the session's existing blend_object_key.
          - Save As: build a new key under the user's prefix from `filename`, and
            remember it on the session so later plain Saves overwrite the same file.
        The bytes go up as a multipart upload (see _perform_multipart_save).
        """
        from app.services.storage_service import build_key, assert_owned, StorageError

        message_id = data.get('message_id') or generate_message_id()
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return

            username = session['username']
            filename = (data.get('filename') or '').strip()
            key = session.get('blend_object_key')

            logto_id = session.get('logto_id')
            user_id = await self._resolve_db_user_id(logto_id) if logto_id else None
            if not user_id:
                await self._emit_save_failed(
                    sid, message_id, 'AUTH_ERROR',
                    'Could not verify your account to save')
                return

            if filename:
                # Save As — derive the storage key under the caller's own prefix.
                try:
                    key = build_key(user_id, filename)
                except StorageError as e:
                    await self._emit_save_failed(sid, message_id, 'VALIDATION_ERROR', str(e))
                    return
                # Remember the new target so subsequent plain Saves overwrite it.
                session['blend_object_key'] = key
                await self.save_session(sid, session)
                # Keep the project-switch tracker in sync: the running Blender now
                # has this file open, so reopening it later is a reconnect, not a
                # switch that would needlessly relaunch.
                from .singleton import get_open_projects
                get_open_projects()[username] = key

            if not key:
                # New project never named — the frontend routes this to Save As.
                await self._emit_save_failed(
                    sid, message_id, 'NO_TARGET',
                    'Choose a name to save this project')
                return

            # Ownership guard (defence in depth — the key came off the session).
            try:
                assert_owned(key, user_id)
            except StorageError:
                await self._emit_save_failed(
                    sid, message_id, 'AUTH_ERROR', 'That file is not yours to save')
                return

            blender_sid = session.get('blender_sid')
            if not blender_sid:
                await self._emit_save_failed(
                    sid, message_id, 'BLENDER_DISCONNECTED', 'Blender is not connected')
                return

            save_filename = key.rsplit('/', 1)[-1]
            ok, message = await self._perform_multipart_save(username, user_id, save_filename)
            await self._emit_save_result(sid, message_id, ok, message)

        except Exception as e:
            self.logger.error(f"Error processing save_file: {str(e)}")
            await self._emit_save_failed(
                sid, message_id, 'EXECUTION_FAILED', 'Error saving your file')
