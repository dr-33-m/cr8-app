"""
Render orchestration for BrowserNamespace.

The engine never touches image bytes. It decides where a render belongs, mints
pre-signed URLs, asks Blender to render and upload, then completes or aborts the
multipart upload from the ETags that come back. Credentials stay here.

Renders are filed under the project the session currently has open. A session
with no cloud target has nowhere to file them, which is reported as NO_TARGET so
the browser can route the user through Save As first — the same contract
on_save_file already uses for the same reason.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from app.lib import MessageType, create_error_response, generate_message_id

logger = logging.getLogger(__name__)

# A single frame is far smaller than a .blend, so four parts at the save path's
# part size is ample headroom for a 4K PNG while keeping the number of URLs the
# engine has to sign small.
RENDER_PART_SIZE_BYTES = 90 * 1024 * 1024
RENDER_PART_COUNT = 4

VALID_ENGINES = ("EEVEE", "CYCLES")
VALID_RESOLUTIONS = ("hd", "2k", "4k")
VALID_ASPECTS = ("16:9", "9:16", "1:1", "4:5", "3:2")


class RenderHandlersMixin:
    """Mixin for render-related event handlers."""

    async def _emit_render_failed(self, sid: str, message_id: str, code: str,
                                  user_message: str):
        """Report a render failure as a command_failed the frontend matches by
        message_id — the same shape the save path uses."""
        error_msg = create_error_response(
            error_code=code,
            user_message=user_message,
            technical_message=user_message,
            message_id=message_id,
            source='backend',
            route='direct',
        )
        await self.emit(MessageType.COMMAND_FAILED.value, error_msg.to_dict(), to=sid)

    async def _emit_render_result(self, sid: str, message_id: str, ok: bool,
                                  message: str, data: Dict[str, Any] = None):
        result = {
            'message_id': message_id,
            'type': MessageType.COMMAND_COMPLETED.value,
            'payload': {
                'status': 'success',
                'data': {'ok': ok, 'message': message, **(data or {})},
            },
            'metadata': {'source': 'backend', 'route': 'direct'},
        }
        await self.emit(MessageType.COMMAND_COMPLETED.value, result, to=sid)

    @staticmethod
    def _default_render_name(camera: str) -> str:
        """Timestamp plus camera — sorts chronologically and stays readable in
        a flat listing. Sanitised downstream by build_render_key regardless."""
        stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
        safe_camera = ''.join(
            c for c in (camera or 'camera') if c.isalnum() or c in ' ._-'
        ).strip() or 'camera'
        return f"{stamp}_{safe_camera}"

    async def on_render_image(self, sid: str, data: Dict[str, Any]):
        """
        Render the current frame in the running Blender and store it.

        The heavy work happens on Blender's main thread, so this awaits a single
        request/response for up to RENDER_TIMEOUT_SECONDS while the browser
        holds a blocking overlay.
        """
        from app.services.config import DeploymentConfig
        from app.services.storage_service import (
            StorageError, assert_owned, build_render_key,
            project_slug_from_blend_key, thumb_key_for,
        )

        message_id = data.get('message_id') or generate_message_id()
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return

            username = session['username']

            # Validate the choices rather than passing them through: these end
            # up steering bpy property assignments, and an unexpected value is a
            # clearer error here than a half-configured render there.
            engine = (data.get('engine') or 'EEVEE').upper()
            resolution = (data.get('resolution') or 'hd').lower()
            aspect = data.get('aspect') or '16:9'
            camera = (data.get('camera') or '').strip()

            if engine not in VALID_ENGINES:
                await self._emit_render_failed(
                    sid, message_id, 'VALIDATION_ERROR',
                    f"Unknown render engine '{engine}'")
                return
            if resolution not in VALID_RESOLUTIONS:
                await self._emit_render_failed(
                    sid, message_id, 'VALIDATION_ERROR',
                    f"Unknown resolution '{resolution}'")
                return
            if aspect not in VALID_ASPECTS:
                await self._emit_render_failed(
                    sid, message_id, 'VALIDATION_ERROR',
                    f"Unknown aspect ratio '{aspect}'")
                return

            logto_id = session.get('logto_id')
            user_id = await self._resolve_db_user_id(logto_id) if logto_id else None
            if not user_id:
                await self._emit_render_failed(
                    sid, message_id, 'AUTH_ERROR',
                    'Could not verify your account to save this render')
                return

            blend_key = session.get('blend_object_key')
            if not blend_key:
                # Nowhere to file it. The browser turns this into a Save As.
                await self._emit_render_failed(
                    sid, message_id, 'NO_TARGET',
                    'Save this project before rendering')
                return

            blender_sid = session.get('blender_sid')
            if not blender_sid:
                await self._emit_render_failed(
                    sid, message_id, 'BLENDER_DISCONNECTED',
                    'Blender is not connected')
                return

            try:
                project = project_slug_from_blend_key(blend_key)
                assert_owned(blend_key, user_id)
                name = data.get('name') or self._default_render_name(camera)
                key = build_render_key(user_id, project, name)
                assert_owned(key, user_id)
            except StorageError as e:
                await self._emit_render_failed(
                    sid, message_id, 'VALIDATION_ERROR', str(e))
                return

            ok, message, result = await self._perform_render(
                username, user_id, key,
                camera=camera, engine=engine,
                resolution=resolution, aspect=aspect,
                timeout=DeploymentConfig.get().RENDER_TIMEOUT_SECONDS,
            )

            await self._emit_render_result(
                sid, message_id, ok, message,
                {
                    'key': key,
                    'thumb_key': thumb_key_for(key) if result.get('thumb_ok') else None,
                    'project': project,
                    'width': result.get('width'),
                    'height': result.get('height'),
                } if ok else {},
            )

        except Exception as e:
            self.logger.error(f"Error processing render_image: {str(e)}")
            await self._emit_render_failed(
                sid, message_id, 'EXECUTION_FAILED', 'Error rendering your image')

    async def _perform_render(self, username: str, user_id: str, key: str,
                              camera: str, engine: str, resolution: str,
                              aspect: str, timeout: int) -> tuple:
        """
        Mint upload URLs, drive the render, finalize the upload.

        Returns (ok, message, result). The multipart upload is always resolved —
        completed on success, aborted otherwise — so a failed render never
        leaves a dangling upload holding storage.
        """
        from app.services.storage_service import (
            StorageError, abort_multipart_upload, complete_multipart_upload,
            create_render_upload, presign_part, presign_thumb_put, thumb_key_for,
        )

        blender_ns = self.server.namespace_handlers.get('/blender')
        if not blender_ns:
            return False, 'Blender is not connected', {}

        try:
            created = create_render_upload(key, metadata={
                'engine': engine,
                'resolution': resolution,
                'aspect': aspect,
                'camera': camera or 'active',
            })
            upload_id = created['uploadId']
            part_urls = [
                presign_part(key, upload_id, i, user_id)
                for i in range(1, RENDER_PART_COUNT + 1)
            ]
            thumb_url = presign_thumb_put(thumb_key_for(key))
        except StorageError as e:
            return False, str(e), {}
        except Exception as e:
            self.logger.error(f"Render upload start failed for {username}: {e}")
            return False, 'Could not prepare the render upload', {}

        self.logger.info(
            f"Render for {username} -> {key} ({engine} {resolution} {aspect})")

        resp = await blender_ns.request_and_wait(username, {
            'type': 'addon_command',
            'addon_id': 'cr8_render',
            'command': 'render_image',
            'params': {
                'camera': camera or None,
                'engine': engine,
                'resolution': resolution,
                'aspect': aspect,
                'thumb_url': thumb_url,
                'multipart': {
                    'upload_id': upload_id,
                    'key': key,
                    'part_size': RENDER_PART_SIZE_BYTES,
                    'part_urls': part_urls,
                },
            },
            'metadata': {'route': 'direct'},
        }, timeout=timeout)

        resp = resp or {}
        parts = resp.get('parts')
        ok = bool(resp.get('ok') and parts)

        try:
            if ok:
                complete_multipart_upload(key, upload_id, parts, user_id)
            else:
                abort_multipart_upload(key, upload_id, user_id)
        except Exception as e:
            self.logger.error(f"Render finalize failed for {username}: {e}")
            try:
                abort_multipart_upload(key, upload_id, user_id)
            except Exception:
                pass
            return False, 'Render could not be saved', {}

        if ok:
            return True, resp.get('message') or 'Render saved', resp

        # request_and_wait returns {} on timeout and the addon's error payload
        # otherwise, so prefer the addon's own reason when there is one.
        return False, resp.get('message') or 'Render failed or timed out', resp
