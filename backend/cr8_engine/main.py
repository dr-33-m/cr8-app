import asyncio
import uvicorn
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.realtime_engine.socketio_server import create_socketio_server, create_socketio_app
from app.api.v1.endpoints import blend_files, polyhaven
from app.services.config import DeploymentConfig

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task reference for cleanup
_maintenance_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown lifecycle."""
    global _maintenance_task
    config = DeploymentConfig.get()

    if config.LAUNCH_MODE == "remote":
        logger.info("Remote mode detected — initializing VastAI instance manager")
        errors = config.validate_remote_config()
        if errors:
            for error in errors:
                logger.warning(f"Remote config warning: {error}")

        from app.services.blender_service import BlenderService
        manager = BlenderService._get_instance_manager()
        await manager.initialize()
        _maintenance_task = asyncio.create_task(manager.periodic_maintenance())
        logger.info("VastAI instance manager initialized with background maintenance")

    yield  # App is running

    # Shutdown
    if _maintenance_task:
        _maintenance_task.cancel()
        try:
            await _maintenance_task
        except asyncio.CancelledError:
            pass
    if config.LAUNCH_MODE == "remote":
        from app.services.blender_service import BlenderService
        if BlenderService._instance_manager:
            await BlenderService._instance_manager.shutdown()
    logger.info("Cr8 Server shut down")


# Create FastAPI app
app = FastAPI(
    title="Cr8 Server",
    description="Real-time communication server for Blender with Socket.IO",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS settings
class Settings:
    ALLOWED_HOSTS = ["*"]

settings = Settings()

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "healthy"})

# Include API routers
app.include_router(blend_files.router, prefix="/api/v1", tags=["blend-files"])
app.include_router(polyhaven.router, prefix="/api/v1/polyhaven", tags=["polyhaven"])

# Create Socket.IO server
sio = create_socketio_server()

# Create Socket.IO ASGI app
socket_app = create_socketio_app(sio)

# Mount Socket.IO on FastAPI at /ws path
app.mount("/ws", socket_app)

logger.info("Cr8 Server initialized with Socket.IO mounted at /ws")

if __name__ == "__main__":
    # Run the FastAPI app (Socket.IO is mounted at /ws)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
