import uvicorn
import json
import websockets
from sqlmodel import create_engine, SQLModel
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager, closing
import asyncio
import socket
import time
import logging
import errno
from typing import Tuple
from app.core.config import settings
from app.api.v1.endpoints import users, projects, assets, templates, moodboards
from app.realtime_engine.websockets.session_manager import SessionManager
from app.realtime_engine.websockets.websocket_handler import WebSocketHandler
from app.db.session import get_db
from app.db.base import Base

from app.models import User, Project, Asset, Template, Moodboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    engine = create_engine(settings.postgres_url, echo=True)
    metadata = SQLModel.metadata
    metadata.create_all(engine)  # This will create tables based on your models

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CG Content Platform API",
    version="0.1.0",
    lifespan=lifespan
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def attempt_connection(ip: str, port: int, timeout: float = 1) -> Tuple[int, float]:
    """Attempt to connect to the specified IP and port."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(timeout)
        start_time = time.time()
        result = sock.connect_ex((ip, port))
        response_time = (time.time() - start_time) * 1000
        return result, response_time


@app.get("/health", tags=["health"])
async def health_check():
    try:
        ip = settings.SSH_LOCAL_IP
        port = settings.SSH_PORT
        max_retries = 3
        base_delay = 0.5  # Base delay in seconds

        for attempt in range(max_retries):
            try:
                logger.info(
                    f"Attempting connection to {ip}:{port} (Attempt {attempt + 1}/{max_retries})")
                result, response_time = await attempt_connection(ip, port)

                if result == 0:
                    logger.info(
                        f"Successfully connected to {ip}:{port} in {round(response_time, 2)}ms")
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "status": "healthy",
                            "message": "The server is running",
                            "connection": {
                                "ip": ip,
                                "port": port,
                                "response_time_ms": round(response_time, 2),
                                "attempts": attempt + 1
                            }
                        }
                    )

                # Handle EAGAIN/EWOULDBLOCK specifically
                if result == errno.EAGAIN:
                    if attempt < max_retries - 1:
                        # Exponential backoff
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Resource temporarily unavailable (EAGAIN). Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    error_msg = "Resource temporarily unavailable (EAGAIN) after all retry attempts"
                else:
                    error_msg = f"Failed to connect to {ip}:{port} (Error code: {result})"

                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )

            except socket.timeout:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"Connection timeout. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                error_msg = f"Connection timeout to {ip}:{port} after {max_retries} attempts"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )
            except socket.error as e:
                error_msg = f"Socket error connecting to {ip}:{port}: {str(e)}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )

    except Exception as e:
        logger.error(f"Unexpected error in health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(moodboards.router,
                   prefix="/api/v1/moodboards", tags=["moodboards"])
app.include_router(
    projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(
    templates.router, prefix="/api/v1/templates", tags=["templates"])
# app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])

# Websocket endpoint
session_manager = SessionManager()


@app.websocket("/ws/{username}/{client_type}")
async def websocket_endpoint(websocket: WebSocket, username: str, client_type: str, blend_file: str = None):
    # Track if we've accepted the connection
    connection_accepted = False

    try:
        await websocket.accept()
        connection_accepted = True

        if client_type == "browser":
            try:
                session = await session_manager.create_browser_session(username, websocket, blend_file)
                await websocket.send_json({"status": "connected", "message": "Session created"})
            except ValueError as ve:
                # Handle specific ValueError exceptions gracefully
                error_message = str(ve)
                logger.warning(f"Browser connection rejected: {error_message}")
                try:
                    await websocket.send_json({
                        "status": "error",
                        "message": error_message,
                        "code": "connection_rejected"
                    })
                except Exception as send_error:
                    logger.warning(
                        f"Could not send error response: {str(send_error)}")

                try:
                    await websocket.close()
                except Exception as close_error:
                    logger.warning(
                        f"Error closing websocket: {str(close_error)}")

                return  # Exit early without raising the exception further

        elif client_type == "blender":
            try:
                await session_manager.register_blender(username, websocket)
                try:
                    await websocket.send_json({
                        "command": "connection_confirmation",
                        "status": "connected",
                        "message": "Blender registered"
                    })
                except Exception as send_error:
                    logger.warning(
                        f"Could not send confirmation to Blender: {str(send_error)}")
                    # Even if we can't send confirmation, continue as the connection might still work
            except ValueError as ve:
                logger.warning(f"Blender registration failed: {str(ve)}")
                try:
                    await websocket.send_json({"status": "error", "message": str(ve)})
                except Exception:
                    pass  # Socket might already be closed

                try:
                    await websocket.close()
                except Exception:
                    pass  # Socket might already be closed

                return  # Exit early

        websocket_handler = WebSocketHandler(session_manager, username)

        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    # Process message with the handler
                    await websocket_handler.handle_message(username, data, client_type)
                except json.JSONDecodeError as json_err:
                    logger.warning(f"Invalid JSON received: {str(json_err)}")
                    continue  # Skip this message but keep connection open

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {username}/{client_type}")
            await session_manager.handle_disconnect(username, client_type)

    except ValueError as ve:
        # Handle any other ValueError exceptions
        logger.warning(
            f"WebSocket error for {username}/{client_type}: {str(ve)}")
        if connection_accepted:
            try:
                await websocket.send_json({"status": "error", "message": str(ve)})
            except Exception:
                pass  # Socket might already be closed

            try:
                await websocket.close()
            except Exception:
                pass  # Socket might already be closed

    except websockets.exceptions.ConnectionClosedError as conn_err:
        # Handle connection closed errors gracefully
        logger.warning(
            f"Connection closed: {username}/{client_type}: {str(conn_err)}")
        if client_type == "blender":
            # Notify session manager of Blender disconnect
            await session_manager.handle_disconnect(username, client_type)

    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {str(e)}")
        if connection_accepted:
            try:
                await websocket.send_json({"status": "error", "message": "Internal server error"})
            except Exception:
                pass  # Socket might already be closed

            try:
                await websocket.close()
            except Exception:
                pass  # Socket might already be closed

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
