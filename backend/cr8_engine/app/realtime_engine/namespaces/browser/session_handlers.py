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
from .singleton import get_open_projects, EMPTY_PROJECT

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
            blend_object_key = session.get('blend_object_key')
            recovery_mode = data.get('recovery', False) if data else False
            requested_project = blend_object_key or EMPTY_PROJECT
            open_projects = get_open_projects()

            self.logger.info(f"Browser ready signal from {username} (recovery: {recovery_mode})")

            # Blender already running for this user?
            if await self.is_blender_in_room(username):
                tracked = open_projects.get(username)
                # Reconnect (leave the running Blender alone) when this is a
                # network-recovery reconnect, when we can't prove which project is
                # running (tracked is None — e.g. after an engine restart, so a
                # refresh never destroys a live instance), or when it's the same
                # project (a page refresh / re-open of the same file).
                if recovery_mode or tracked is None or tracked == requested_project:
                    self.logger.info(f"Blender already in room for {username}, reconnecting")
                    await self.notify_existing_blender_connection(sid)
                    return

                # Different project chosen → save the outgoing file, tear the old
                # Blender down, then fall through to launch the new one.
                self.logger.info(
                    f"Project switch for {username}: {tracked} -> {requested_project}")
                if tracked and tracked != EMPTY_PROJECT:
                    try:
                        logto_id = session.get('logto_id')
                        user_id = (await self._resolve_db_user_id(logto_id)
                                   if logto_id else None)
                        if user_id:
                            save_filename = tracked.rsplit('/', 1)[-1]
                            ok, message = await self._perform_multipart_save(
                                username, user_id, save_filename)
                            self.logger.info(
                                f"Pre-switch save for {username}: "
                                f"{'ok' if ok else message}")
                        else:
                            self.logger.warning(
                                f"Pre-switch save skipped for {username}: no user id")
                    except Exception as e:
                        self.logger.error(f"Pre-switch save failed for {username}: {e}")

                await BlenderService.terminate_instance(username)
                open_projects.pop(username, None)

            # If we get here, no (usable) Blender in room - safe to launch
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
            
            # Create a callback that forwards VastAI instance status to the browser
            async def instance_status_callback(status: str, elapsed: int):
                status_msg = create_system_message(
                    message_type=MessageType.INSTANCE_STATUS,
                    status=status,
                    message=f"GPU instance {status}",
                    data={"elapsed": elapsed},
                    source='backend'
                )
                await self.emit(MessageType.INSTANCE_STATUS.value, status_msg.to_dict(), to=sid)

            # Launch Blender instance
            result = await BlenderService.launch_instance(
                username, blend_file,
                status_callback=instance_status_callback,
                blend_object_key=blend_object_key,
            )

            if result != "success":
                reason = result or "unknown"
                self.logger.error(f"Failed to launch Blender for {username}: {reason}")
                # Send typed INSTANCE_STATUS error so frontend can show specific message
                error_status_msg = create_system_message(
                    message_type=MessageType.INSTANCE_STATUS,
                    status="error",
                    message=f"Failed to launch: {reason}",
                    data={"reason": reason, "recoverable": reason != "no_gpu"},
                    source='backend'
                )
                await self.emit(MessageType.INSTANCE_STATUS.value, error_status_msg.to_dict(), to=sid)
                session['state'] = 'error'
                await self.save_session(sid, session)
                return
            
            # Update state to waiting for Blender connection
            session['state'] = 'waiting_for_blender'
            await self.save_session(sid, session)

            # Remember which project this Blender was launched with, so a later
            # workspace open can tell a same-project reconnect from a real switch.
            open_projects[username] = requested_project

            self.logger.info(f"Blender launched for {username}, waiting for connection")
            
        except Exception as e:
            self.logger.error(f"Error in browser_ready: {str(e)}")
            # Send typed error status so frontend shows actionable UI
            error_status_msg = create_system_message(
                message_type=MessageType.INSTANCE_STATUS,
                status="error",
                message=str(e),
                data={"reason": "unknown", "recoverable": True},
                source='backend'
            )
            await self.emit(MessageType.INSTANCE_STATUS.value, error_status_msg.to_dict(), to=sid)

    async def on_exit_workspace(self, sid: str, data: Optional[Dict] = None):
        """
        User is leaving the workspace deliberately (via the Exit button, after any
        final save). Shut their Blender/instance down now rather than leaving it
        for the disconnect grace timer — this also ends the WebRTC stream.
        """
        try:
            session = await self.get_session(sid)
            if not session:
                return
            username = session['username']
            self.logger.info(f"Exit workspace requested by {username}")
            get_open_projects().pop(username, None)
            await BlenderService.terminate_instance(username)
        except Exception as e:
            self.logger.error(f"Error in exit_workspace: {str(e)}")

    async def on_cancel_launch(self, sid: str, data: Optional[Dict] = None):
        """Handle cancel launch request from the browser."""
        try:
            session = await self.get_session(sid)
            if not session:
                return

            username = session['username']
            self.logger.info(f"Cancel launch requested by {username}")

            # Two-pronged, safe to call both: cancel_launch() interrupts an
            # in-flight provisioning attempt (v2 engine only) at its next
            # await point instead of letting it run to completion unattended;
            # terminate_instance() releases an assignment that already
            # succeeded. Whichever applies takes effect — neither is a no-op
            # for the wrong case.
            await BlenderService.cancel_launch(username)
            await BlenderService.terminate_instance(username)

            # Send cancelled status to browser
            cancelled_msg = create_system_message(
                message_type=MessageType.INSTANCE_STATUS,
                status="cancelled",
                message="Launch cancelled",
                data={"reason": "user_cancelled"},
                source='backend'
            )
            await self.emit(MessageType.INSTANCE_STATUS.value, cancelled_msg.to_dict(), to=sid)

            session['state'] = 'cancelled'
            await self.save_session(sid, session)

        except Exception as e:
            self.logger.error(f"Error in cancel_launch: {str(e)}")
