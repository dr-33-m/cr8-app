"""
Socket.IO event handlers for WebSocket communication.
Handles connection, disconnection, and message reception events.
"""

import logging
import queue
from urllib.parse import urlparse, quote, urlunparse

from ..message_types import MessageType
from .blender_handlers import execute_in_main_thread
from .command_handlers import process_message
from .registry_handlers import send_registry_update

logger = logging.getLogger(__name__)

# Thread-safe command queue — receives commands from the socket.io background thread,
# drained one-at-a-time by a persistent Blender main-thread timer.
# This decouples message receipt from message processing, preventing the
# websocket-client _send_lock bottleneck that caused "transport close" disconnects.
_command_queue: queue.Queue = queue.Queue()

# Drainer tick rates. We poll at the active rate while commands are flowing and
# back off once the queue has been empty for a while — a session sitting idle
# does not need 10 wakeups a second, and instance time is billed by the hour.
_DRAIN_INTERVAL_ACTIVE = 0.1
_DRAIN_INTERVAL_IDLE = 1.0
_DRAIN_IDLE_DELAY = 5.0
# Consecutive empty ticks before dropping to the idle rate.
_DRAIN_IDLE_TICKS = int(_DRAIN_IDLE_DELAY / _DRAIN_INTERVAL_ACTIVE)

_drain_idle_countdown = _DRAIN_IDLE_TICKS


def _drain_command_queue():
    """Persistent Blender timer: process one queued command per tick.

    Keeps sio.emit() calls spaced out so websocket-client's _send_lock never
    creates a bottleneck under burst traffic. Defined at module level so
    bpy.app.timers.is_registered() can identify it by identity across reconnects.

    Ticks at 10/s while work is arriving, then backs off to 1/s after ~5s of
    quiet. Any command resets it to the active rate, so the slow rate only ever
    costs latency on the first command after an idle stretch.
    """
    global _drain_idle_countdown

    did_work = False
    try:
        data = _command_queue.get_nowait()
        did_work = True
        # Import handler lazily — avoids circular import at module load time
        from ..websocket_handler import get_handler
        handler = get_handler()
        process_message(data, handler)
    except queue.Empty:
        pass
    except Exception as e:
        logger.error(f"Error processing queued command: {e}")

    if did_work:
        _drain_idle_countdown = _DRAIN_IDLE_TICKS
        return _DRAIN_INTERVAL_ACTIVE

    if _drain_idle_countdown > 0:
        _drain_idle_countdown -= 1
        return _DRAIN_INTERVAL_ACTIVE
    return _DRAIN_INTERVAL_IDLE


# WebRTC viewport stream settings. The pump interval is derived from the same
# fps we hand to bpy.app.streaming.configure() so the two cannot drift apart.
_STREAM_WIDTH = 1920
_STREAM_HEIGHT = 1080
_STREAM_FPS = 30
_REDRAW_INTERVAL = 1.0 / _STREAM_FPS

# Set while the pump is failing, so a persistent fault logs once instead of
# 30 times a second for the life of the session.
_redraw_pump_failing = False


def _redraw_pump():
    """Persistent Blender timer: keep the 3D viewport redrawing while streaming.

    Frames reach the WebRTC pipeline only as a side effect of the viewport
    drawing — the capture hook lives in Blender's draw path, so it never runs
    unless a region is tagged for redraw. On an instance nobody is orbiting the
    camera, which means an idle Blender streams nothing at all and the browser
    sits on a black picture until the user interacts.

    Deliberately does *not* back off when idle, unlike _drain_command_queue:
    idle is exactly when the stream would otherwise stall. Cost is bounded by
    only running while streaming is active, i.e. only during a live session.

    Module level so bpy.app.timers.is_registered() can identify it by identity
    across reconnects.
    """
    global _redraw_pump_failing
    import bpy

    try:
        if not bpy.app.streaming.is_active():
            return None  # streaming stopped — retire the timer

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                # Only the main region carries the viewport we capture; tagging
                # the whole area would redraw headers and toolbars 30x a second.
                for region in area.regions:
                    if region.type == 'WINDOW':
                        region.tag_redraw()
        _redraw_pump_failing = False
    except Exception as e:
        if not _redraw_pump_failing:
            _redraw_pump_failing = True
            logger.warning(f"Redraw pump tick failed (suppressing repeats): {e}")

    return _REDRAW_INTERVAL


def _ensure_redraw_pump():
    """Register the redraw pump if it is not already running."""
    import bpy

    if bpy.app.timers.is_registered(_redraw_pump):
        return
    bpy.app.timers.register(_redraw_pump, first_interval=0.0)
    logger.info(f"Viewport redraw pump registered at {_STREAM_FPS} fps")


def _stop_redraw_pump():
    """Unregister the redraw pump if it is running."""
    import bpy

    if not bpy.app.timers.is_registered(_redraw_pump):
        return
    bpy.app.timers.unregister(_redraw_pump)
    logger.info("Viewport redraw pump unregistered")


def encode_turn_url(turn_url: str) -> str:
    """URL-encode the password in a TURN URL to handle special characters.
    
    The TURN server password may contain special characters like %^} which are
    invalid in URL syntax. This function percent-encodes the password to ensure
    libnice can parse the TURN URL correctly.
    """
    try:
        parsed = urlparse(turn_url)
        if parsed.password:
            encoded_password = quote(parsed.password, safe='')
            netloc = f"{parsed.username}:{encoded_password}@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            return urlunparse((parsed.scheme, netloc, parsed.path, 
                             parsed.params, parsed.query, parsed.fragment))
    except Exception:
        pass
    return turn_url


def register_event_handlers(handler):
    """
    Register all Socket.IO event handlers on the handler instance.
    
    Args:
        handler: WebSocketHandler instance with sio client
    """
    
    @handler.sio.on('connect', namespace='/blender')
    def on_connect():
        logger.info("Connected to Socket.IO server")
        handler.processing_complete.clear()

        def send_init_message():
            try:
                import bpy
                # Send connection status via Socket.IO emit
                handler.sio.emit(
                    'connection_status',
                    {
                        'status': 'Connected',
                        'message': 'Blender registered'
                    },
                    namespace='/blender'
                )
                logger.info("Sent connection status to server")

                # Send registry update
                send_registry_update(handler.sio)

                # Start the command queue drainer if not already running.
                # One command per ~16ms keeps sio.emit() calls well-spaced so
                # websocket-client's _send_lock never bottlenecks under burst traffic.
                if not bpy.app.timers.is_registered(_drain_command_queue):
                    bpy.app.timers.register(_drain_command_queue, first_interval=0.016)
                    logger.info("Command queue drainer timer registered")

                # Start WebRTC streaming (only once — it has its own signaller connection)
                start_streaming_if_needed()
            except Exception as e:
                logger.error(f"Error in on_connect: {e}")

        def start_streaming_if_needed():
            """Start WebRTC viewport streaming if not already active.

            Streaming uses its own WebSocket connection to the signalling server,
            independent of the Socket.IO connection to the engine. So we only
            start it once and let it persist across Socket.IO reconnects.
            """
            try:
                import bpy
                import os

                # Don't restart if already streaming. The pump is still checked —
                # streaming survives Socket.IO reconnects, so on this path the
                # stream may be live while the pump has been retired.
                if bpy.app.streaming.is_active():
                    logger.info("WebRTC streaming already active, skipping restart")
                    _ensure_redraw_pump()
                    return

                username = os.environ.get("CR8_USERNAME")
                signaller_uri = os.environ.get("CR8_SIGNALLER_URI", "ws://127.0.0.1:8443")
                turn_server = os.environ.get("TURN_SERVER", "")

                if not username:
                    logger.error("CR8_USERNAME not set, cannot start streaming")
                    return

                producer_id = f"blender-{username}"

                logger.info(f"Starting WebRTC streaming with producer_id: {producer_id}")
                logger.info(f"Signaller URI: {signaller_uri}")
                logger.info(f"TURN server: {turn_server or '(none)'}")

                # Configure streaming
                streaming_config = dict(
                    producer_id=producer_id,
                    signaller_uri=signaller_uri,
                    width=_STREAM_WIDTH,
                    height=_STREAM_HEIGHT,
                    fps=_STREAM_FPS,
                )
                if turn_server:
                    # URL-encode the password to handle special characters like %^}
                    encoded_turn = encode_turn_url(turn_server)
                    streaming_config["turn_servers"] = [encoded_turn]
                    logger.info(f"TURN server configured for NAT traversal (URL-encoded)")

                bpy.app.streaming.configure(**streaming_config)

                # Start streaming
                bpy.app.streaming.start()

                logger.info(f"WebRTC streaming started successfully for {username}")

                # Keep the viewport redrawing from here on. Frames only exist as a
                # side effect of the draw path, so without this the pipeline stays
                # empty, webrtcsink never gets anything to encode, and the browser
                # shows black until the user orbits the camera.
                _ensure_redraw_pump()
            except Exception as e:
                logger.error(f"Failed to start WebRTC streaming: {e}")

        execute_in_main_thread(send_init_message, ())

    @handler.sio.on('disconnect', namespace='/blender')
    def on_disconnect(reason):
        import bpy
        logger.info(f"Disconnected from server: {reason}")
        handler.processing_complete.set()
        handler.processing_commands.clear()

        # Flush any queued commands — stale commands from a dead session shouldn't
        # execute after reconnect onto a fresh Blender state.
        flushed = 0
        while not _command_queue.empty():
            try:
                _command_queue.get_nowait()
                flushed += 1
            except queue.Empty:
                break
        if flushed:
            logger.info(f"Flushed {flushed} queued command(s) on disconnect")

        # Same reasoning for in-flight long-running work: the engine-side Futures
        # died with the session, so resolving them later would emit responses for
        # message IDs nobody is waiting on.
        try:
            from ...registry.routing import deferred
            deferred.close_all()
        except Exception as e:
            logger.error(f"Failed to clear deferred commands: {e}")

        # Only stop streaming on intentional disconnects, not transient transport errors.
        # Transport errors trigger Socket.IO reconnection — streaming has its own
        # signaller connection and should persist across reconnects.
        if reason != "transport error":
            try:
                _stop_redraw_pump()
                if bpy.app.streaming.is_active():
                    bpy.app.streaming.stop()
                    logger.info("WebRTC streaming stopped on disconnect")
            except Exception as e:
                logger.error(f"Failed to stop WebRTC streaming: {e}")
        else:
            logger.info("Transport error disconnect — keeping WebRTC streaming active")

        # Start 5-minute cleanup timer when server disconnects
        # We use a Blender timer to check reconnection status instead of time.sleep()
        # to avoid KeyboardInterrupt interrupting the sleep
        def check_and_start_cleanup():
            try:
                logger.info("Checking if Socket.IO reconnection has been exhausted...")
                
                # Check if still disconnected (reconnection exhausted)
                if not handler.sio.connected:
                    logger.warning("Server unreachable after reconnection attempts exhausted")
                    handler.start_server_cleanup_timer()
                    logger.info("Server cleanup timer started successfully")
                else:
                    logger.info("Socket.IO reconnected successfully, cleanup timer not needed")
            except Exception as e:
                logger.error(f"Failed to check reconnection status: {e}", exc_info=True)
            
            return None  # Unregister the timer after execution
        
        # Register a Blender timer to check reconnection status after ~80 seconds
        # This gives Socket.IO time to exhaust all 10 reconnection attempts
        # (10 attempts × max 10s delay = ~80 seconds total)
        try:
            bpy.app.timers.register(
                check_and_start_cleanup,
                first_interval=80.0
            )
            logger.info("Registered reconnection check timer for 80 seconds")
        except Exception as e:
            logger.error(f"Failed to register reconnection check timer: {e}", exc_info=True)
            # Fallback: try to start cleanup immediately if timer registration fails
            try:
                handler.start_server_cleanup_timer()
            except Exception as fallback_error:
                logger.error(f"Fallback cleanup timer also failed: {fallback_error}", exc_info=True)

    @handler.sio.on('connect_error', namespace='/blender')
    def on_connect_error(data):
        logger.error(f"Connection error: {data}")

    @handler.sio.on(MessageType.COMMAND_RECEIVED, namespace='/blender')
    def on_command_received(data):
        """Buffer incoming command for the main-thread queue drainer.

        Never schedules a timer directly — doing so caused burst sio.emit() calls
        that overwhelmed websocket-client's _send_lock and triggered 'transport close'.
        """
        logger.info(f"Queued {MessageType.COMMAND_RECEIVED}: {data.get('command', data.get('type', '?'))}")
        _command_queue.put(data)

    @handler.sio.on('ping', namespace='/blender')
    def on_ping(data):
        """Handle ping events"""
        logger.info(f"Received ping: {data}")

        def execute():
            from .utility_handlers import handle_ping
            handle_ping(data, handler)

        execute_in_main_thread(execute, ())
