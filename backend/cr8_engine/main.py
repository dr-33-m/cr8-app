import uvicorn
from sqlmodel import create_engine, SQLModel
from fastapi import FastAPI, WebSocket, status, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import asyncio
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


@app.get("/health", tags=["health"])
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "message": "The server is running"}
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
# app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
# app.include_router(
#     templates.router, prefix="/api/v1/templates", tags=["templates"])

# Websocket endpoint
session_manager = SessionManager()


@app.websocket("/ws/{username}/{client_type}")
async def websocket_endpoint(websocket: WebSocket, username: str, client_type: str, blend_file: str = None):
    await websocket.accept()

    try:
        if client_type == "browser":
            session = await session_manager.create_browser_session(username, websocket, blend_file)
            await websocket.send_json({"status": "connected", "message": "Session created"})

        elif client_type == "blender":
            await session_manager.register_blender(username, websocket)
            await websocket.send_json({"status": "connected", "message": "Blender registered"})

        websocket_handler = WebSocketHandler(session_manager, username)

        try:
            while True:
                data = await websocket.receive_json()
                # Process message with the handler
                await websocket_handler.handle_message(username, data, client_type)

        except WebSocketDisconnect:
            await session_manager.handle_disconnect(username, client_type)

    except Exception as e:
        await websocket.close()
        raise e

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
