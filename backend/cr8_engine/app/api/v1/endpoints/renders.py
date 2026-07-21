"""
Render library endpoints (remote mode only).

Reads only. Renders are written by the socket path (browser -> engine -> Blender
-> RustFS); this exists so the Library can browse what came out of it.

As with blend files the engine never proxies bytes — it lists keys and hands out
short-lived pre-signed GET URLs the browser fetches directly. Every endpoint
taking a client-supplied key runs it through storage_service.assert_owned, which
is the only thing stopping one user from reading another's renders.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.db.models import User
from app.services import storage_service
from app.services.storage_service import StorageError

logger = logging.getLogger(__name__)

router = APIRouter()


class RenderProjectResponse(BaseModel):
    project: str
    image_count: int
    video_count: int
    cover_url: Optional[str] = None
    last_modified: datetime


class RenderItemResponse(BaseModel):
    key: str
    filename: str
    size: int
    last_modified: datetime
    url: str
    download_url: str
    thumb_url: Optional[str] = None


class RenderMetaResponse(BaseModel):
    size: int
    last_modified: Optional[datetime] = None
    metadata: dict


def _bad_request(e: StorageError) -> HTTPException:
    """StorageError is caller error (bad name, foreign key) — 400, not 500."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/renders/projects", response_model=list[RenderProjectResponse])
async def list_render_projects(user: User = Depends(get_current_user)):
    """Render projects as folders, newest activity first."""
    projects = storage_service.list_render_projects(str(user.id))
    return [
        {
            "project": p["project"],
            "image_count": p["image_count"],
            "video_count": p["video_count"],
            "cover_url": (
                storage_service.presign_view(p["cover_key"]) if p["cover_key"] else None
            ),
            "last_modified": p["last_modified"],
        }
        for p in projects
    ]


@router.get("/renders", response_model=list[RenderItemResponse])
async def list_renders(
    project: str,
    kind: str = Query("images"),
    user: User = Depends(get_current_user),
):
    try:
        items = storage_service.list_renders(str(user.id), project, kind)
    except StorageError as e:
        raise _bad_request(e)

    return [
        {
            **item,
            "url": storage_service.presign_view(item["key"]),
            # Same object, signed to come back as an attachment — see
            # presign_render_download for why a second URL is needed at all.
            "download_url": storage_service.presign_render_download(
                item["key"], item["filename"]
            ),
            # Absent when the best-effort thumbnail upload didn't land; the
            # client falls back to the full image rather than a broken preview.
            "thumb_url": (
                storage_service.presign_view(item["thumb_key"])
                if item.get("thumb_key")
                else None
            ),
        }
        for item in items
    ]


@router.get("/renders/meta", response_model=RenderMetaResponse)
async def get_render_meta(key: str, user: User = Depends(get_current_user)):
    """Settings a render was made with, recorded as object metadata at upload."""
    try:
        return storage_service.head_render(key, str(user.id))
    except StorageError as e:
        raise _bad_request(e)


@router.delete("/renders", status_code=status.HTTP_204_NO_CONTENT)
async def delete_render(key: str, user: User = Depends(get_current_user)):
    try:
        storage_service.delete_render(key, str(user.id))
    except StorageError as e:
        raise _bad_request(e)
