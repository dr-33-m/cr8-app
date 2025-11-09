import uvicorn
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.realtime_engine.socketio_server import create_socketio_server, create_socketio_app
from app.api.v1.endpoints import blend_files, polyhaven

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cr8 Server",
    description="Real-time communication server for Blender with Socket.IO",
    version="2.0.0",
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
