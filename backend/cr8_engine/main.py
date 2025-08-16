import uvicorn
import json
import websockets
import logging
from urllib.parse import unquote
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.realtime_engine.websockets.session_manager import SessionManager
from app.realtime_engine.websockets.websocket_handler import WebSocketHandler
from app.api.v1.endpoints import blend_files

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Cr8 WebSocket Server",
    description="A lightweight WebSocket server for real-time communication with Blender.",
    version="1.0.0",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dummy settings for CORS


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


@app.get("/health", tags=["health"])
async def health_check():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "healthy"})

# Include API routers
app.include_router(blend_files.router, prefix="/api/v1", tags=["blend-files"])

# Websocket endpoint
session_manager = SessionManager()


@app.websocket("/ws/{username}/{client_type}")
async def websocket_endpoint(websocket: WebSocket, username: str, client_type: str):
    # Track if we've accepted the connection
    connection_accepted = False

    try:
        query_params = websocket.url.query
        blend_file_path = None
        if query_params:
            params = dict(x.split('=') for x in query_params.split('&'))
            # Support both old "blend_file" and new "blend_file_path" parameters
            raw_path = params.get(
                "blend_file_path") or params.get("blend_file")
            # URL decode the path if it exists
            if raw_path:
                blend_file_path = unquote(raw_path)

        await websocket.accept()
        connection_accepted = True

        if client_type == "browser":
            try:
                session = await session_manager.create_browser_session(username, websocket, blend_file_path)
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
