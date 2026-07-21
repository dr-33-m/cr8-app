"""
Still-image render handler.

Runs on Blender's main thread — the router's command-queue drainer is a bpy
timer, so this is already the main thread, and `bpy.ops.render.render` blocks it
for the duration. That is the same risk profile as the existing multipart save
(which blocks for up to 20 minutes in production): socket.io heartbeats ride the
engineio background thread and survive. The browser holds a blocking overlay for
the same reason.

The scene is treated as borrowed. Every property this touches is snapshotted
first and restored in a `finally`, because a render must not leave the artist's
project on a different engine, resolution or camera than they left it.
"""

import glob
import logging
import os
import time
import uuid

import bpy

from ..profiles import (
    THUMB_LONG_EDGE,
    THUMB_QUALITY,
    apply_output_settings,
    apply_profile,
    compute_dimensions,
    configure_cycles_device,
    resolve_engine,
    CYCLES,
)
from ..upload import upload_multipart, upload_single

logger = logging.getLogger(__name__)


def _error(message: str, code: str) -> dict:
    """Addon-standard error. status='error' makes the router emit
    command_failed, which the engine's request_and_wait resolves with this
    payload — so the reason survives all the way to the browser."""
    logger.error(f"{code}: {message}")
    return {
        'status': 'error',
        'ok': False,
        'message': message,
        'error_code': code,
    }


def _resolve_camera(scene, camera_name):
    """Chosen camera, else the scene's active camera. Never silently renders
    from the wrong one: an explicitly requested camera that isn't there is an
    error, not a fallback."""
    if camera_name:
        camera = scene.objects.get(camera_name)
        if camera is None:
            return None, f"Camera '{camera_name}' is not in this scene"
        if camera.type != 'CAMERA':
            return None, f"'{camera_name}' is not a camera"
        return camera, None

    if scene.camera is not None:
        return scene.camera, None
    return None, "This scene has no camera to render from"


def _snapshot(scene):
    """Capture everything apply_* is about to write."""
    render = scene.render
    image_settings = render.image_settings
    cycles = getattr(scene, 'cycles', None)
    eevee = getattr(scene, 'eevee', None)

    def grab(obj, names):
        if obj is None:
            return {}
        return {n: getattr(obj, n) for n in names if hasattr(obj, n)}

    from ..profiles import CYCLES_PROFILE, EEVEE_PROFILE

    return {
        'engine': render.engine,
        'camera': scene.camera,
        'filepath': render.filepath,
        'render': grab(render, ('resolution_x', 'resolution_y',
                                'resolution_percentage', 'use_file_extension')),
        'image_settings': grab(
            image_settings,
            ('file_format', 'color_mode', 'color_depth', 'compression'),
        ),
        'cycles': grab(cycles, tuple(CYCLES_PROFILE) + ('device', 'time_limit')),
        'eevee': grab(eevee, tuple(EEVEE_PROFILE)),
    }


def _restore(scene, snap):
    """Best-effort restore. Each property is independent — one that can no
    longer be set must not abandon the rest of the scene mid-restore."""
    render = scene.render

    def put(obj, values):
        if obj is None:
            return
        for name, value in values.items():
            try:
                setattr(obj, name, value)
            except Exception as e:
                logger.warning(f"Could not restore '{name}': {e}")

    put(render, snap.get('render', {}))
    put(render.image_settings, snap.get('image_settings', {}))
    put(getattr(scene, 'cycles', None), snap.get('cycles', {}))
    put(getattr(scene, 'eevee', None), snap.get('eevee', {}))
    for attr, value in (('engine', snap.get('engine')), ):
        try:
            setattr(render, attr, value)
        except Exception as e:
            logger.warning(f"Could not restore render.{attr}: {e}")
    try:
        scene.camera = snap.get('camera')
        render.filepath = snap.get('filepath', '')
    except Exception as e:
        logger.warning(f"Could not restore camera/filepath: {e}")


def _still_output_path(scene, base_path: str) -> str:
    """Where render(write_still=True) actually wrote the frame.

    Deliberately NOT scene.render.frame_path(): that returns the animation-style
    path with frame numbering appended (/tmp/x0001.png), while a still render
    writes exactly filepath + extension (/tmp/x.png). The two differ silently,
    and trusting frame_path makes a perfectly good render look like it vanished.

    file_extension is derived from the current output format rather than
    hardcoded, so changing the format doesn't strand this. The glob is a
    last-resort fallback for a build that surprises us again.
    """
    candidate = base_path + scene.render.file_extension
    if os.path.exists(candidate):
        return candidate
    matches = sorted(glob.glob(base_path + '*'))
    if matches:
        logger.warning(f"Render landed at {matches[0]}, expected {candidate}")
        return matches[0]
    return candidate


def _write_thumbnail(source_path: str, thumb_path: str) -> bool:
    """Scale a copy down for the library grid. Never fatal — the full render is
    already on disk and a missing thumbnail is a placeholder, not a lost render."""
    image = None
    try:
        image = bpy.data.images.load(source_path)
        width, height = image.size
        if not width or not height:
            return False

        if width >= height:
            new_w = min(THUMB_LONG_EDGE, width)
            new_h = max(1, int(round(new_w * height / width)))
        else:
            new_h = min(THUMB_LONG_EDGE, height)
            new_w = max(1, int(round(new_h * width / height)))

        image.scale(new_w, new_h)
        image.file_format = 'JPEG'
        image.filepath_raw = thumb_path
        image.save()
        return True
    except Exception as e:
        logger.warning(f"Thumbnail generation failed: {e}")
        return False
    finally:
        if image is not None:
            try:
                bpy.data.images.remove(image)
            except Exception:
                pass


def _cleanup(*paths):
    for path in paths:
        if not path:
            continue
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Could not remove temp file {path}: {e}")


def handle_render_image(camera=None, engine='EEVEE', resolution='hd',
                        aspect='16:9', multipart=None, thumb_url=None,
                        **_ignored) -> dict:
    """
    Render the current frame from a camera and upload it to cloud storage.

    Called through the addon registry with keyword arguments. `multipart` and
    `thumb_url` are pre-signed by the engine; nothing here holds credentials.
    Extra keyword arguments are tolerated so an engine that learns to send a new
    field doesn't break a Blender image that predates it.
    """
    scene = bpy.context.scene
    started = time.time()

    resolved_camera, camera_error = _resolve_camera(scene, camera)
    if resolved_camera is None:
        return _error(camera_error, 'NO_CAMERA')

    if not multipart:
        return _error('No upload target was provided for this render',
                      'NO_UPLOAD_TARGET')

    width, height = compute_dimensions(resolution, aspect)
    engine_id = resolve_engine(scene, engine)

    snap = _snapshot(scene)
    token = uuid.uuid4().hex
    output_path = None
    thumb_path = f"/tmp/cr8_render_{token}.thumb.jpg"

    try:
        scene.camera = resolved_camera
        scene.render.engine = engine_id
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        apply_output_settings(scene)
        apply_profile(scene, engine_id)

        if engine_id == CYCLES:
            try:
                prefs = bpy.context.preferences.addons['cycles'].preferences
                configure_cycles_device(prefs)
            except Exception as e:
                logger.warning(f"Could not configure Cycles device: {e}")

        base_path = f"/tmp/cr8_render_{token}"
        scene.render.filepath = base_path
        scene.render.use_file_extension = True

        logger.info(
            f"Rendering {width}x{height} on {engine_id} "
            f"from camera '{resolved_camera.name}'"
        )
        bpy.ops.render.render(write_still=True)

        output_path = _still_output_path(scene, base_path)
        if not os.path.exists(output_path):
            return _error('Blender finished but wrote no image', 'NO_OUTPUT')

        thumb_ok = _write_thumbnail(output_path, thumb_path)

        ok, result = upload_multipart(output_path, multipart)
        if not ok:
            return _error(result.get('message', 'Upload failed'), 'UPLOAD_FAILED')

        if thumb_ok:
            thumb_ok = upload_single(thumb_path, thumb_url)

        elapsed = int(time.time() - started)
        logger.info(f"Render complete in {elapsed}s ({len(result['parts'])} part(s))")
        return {
            'status': 'success',
            'ok': True,
            'parts': result['parts'],
            'thumb_ok': thumb_ok,
            'width': width,
            'height': height,
            'engine': engine_id,
            'camera': resolved_camera.name,
            'seconds': elapsed,
            'message': 'Render saved',
        }

    except Exception as e:
        logger.error(f"Render failed: {e}", exc_info=True)
        return _error(f"Render failed: {e}", 'RENDER_FAILED')
    finally:
        _restore(scene, snap)
        _cleanup(output_path, thumb_path)
