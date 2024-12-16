import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.core.config import settings
# from app.api.v1.endpoints import users, projects, assets, templates
from app.realtime_engine.server import WebSocketServer
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup events
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CG Content Platform API",
    version="0.1.0",
    lifespan=lifespan
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
# app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
# app.include_router(
#     projects.router, prefix="/api/v1/projects", tags=["projects"])
# app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])
# app.include_router(
#     templates.router, prefix="/api/v1/templates", tags=["templates"])

# Websocket endpoint
ws_server = WebSocketServer()


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await ws_server.handle_websocket(websocket, client_id)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
