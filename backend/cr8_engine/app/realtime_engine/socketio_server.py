"""
Socket.IO Server Setup for cr8_engine
Configures and initializes the Socket.IO server with namespaces.
"""

import socketio
import logging
from .namespaces import BrowserNamespace, BlenderNamespace


logger = logging.getLogger(__name__)


def create_socketio_server() -> socketio.AsyncServer:
    """
    Create and configure the Socket.IO server.
    
    Returns:
        Configured AsyncServer instance
    """
    logger.info("=== CREATING SOCKET.IO SERVER ===")
    
    # Create AsyncServer with ASGI support
    sio = socketio.AsyncServer(
        async_mode='asgi',
        cors_allowed_origins='*',
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    
    logger.info(f"Socket.IO server instance created: {sio}")
    logger.info(f"CORS origins: *")
    logger.info(f"Logger enabled: True")
    logger.info(f"EngineIO logger enabled: True")
    
    # Add default namespace handler
    class DefaultNamespace(socketio.AsyncNamespace):
        async def on_connect(self, sid, environ, auth):
            logger.info(f"=== DEFAULT NAMESPACE CONNECT ===")
            logger.info(f"SID: {sid}")
            logger.info(f"Auth: {auth}")
            return True
    
    default_ns = DefaultNamespace('/')
    sio.register_namespace(default_ns)
    logger.info(f"Registered default namespace: {default_ns}")
    
    # Register custom namespaces
    browser_ns = BrowserNamespace('/browser')
    blender_ns = BlenderNamespace('/blender')
    
    # Initialize the shared BlazeAgent singleton with namespace references
    # This must be done BEFORE registering namespaces since BrowserNamespace.__init__ calls get_shared_blaze_agent()
    from .namespaces.browser_namespace import initialize_shared_blaze_agent
    initialize_shared_blaze_agent(browser_ns, blender_ns)
    logger.info("Initialized shared BlazeAgent singleton with namespace references")
    
    sio.register_namespace(browser_ns)
    sio.register_namespace(blender_ns)
    
    logger.info(f"Registered browser namespace: {browser_ns}")
    logger.info(f"Registered blender namespace: {blender_ns}")
    logger.info(f"Total namespaces: {list(sio.namespace_handlers.keys())}")
    logger.info("=== SOCKET.IO SERVER CREATION COMPLETE ===")
    
    return sio


def create_socketio_app(sio: socketio.AsyncServer):
    """
    Create standalone Socket.IO ASGI application.
    
    Args:
        sio: Socket.IO server instance
        
    Returns:
        Socket.IO ASGI application
    """
    logger.info("=== CREATING SOCKET.IO ASGI APP ===")
    logger.info(f"Socket.IO server: {sio}")
    
    # Create standalone Socket.IO ASGI app with explicit path
    # CRITICAL: socketio_path must match the full mounted path in FastAPI
    # FastAPI mounts at /ws, so Socket.IO expects /ws/socket.io
    socket_app = socketio.ASGIApp(
        sio,
        socketio_path="/ws/socket.io"
    )
    
    logger.info(f"ASGI app created: {socket_app}")
    logger.info(f"Socket.IO path configured: /ws/socket.io")
    logger.info("=== SOCKET.IO ASGI APP CREATION COMPLETE ===")
    
    return socket_app
