"""
Blend file storage endpoints (remote mode only).

The engine never touches file bytes: it mints presigned URLs and the browser talks
to RustFS directly. Small files take a single PUT; anything larger goes multipart,
which is mandatory rather than an optimisation — the Cloudflare tunnel in front of
RustFS caps request bodies at 100MB, so a 1GB single PUT would 413.

Every endpoint that accepts a client-supplied key runs it through
storage_service.assert_owned. The multipart endpoints matter most here: an
unguarded sign-part would let a caller write into another user's prefix using only
that user's key and an uploadId.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.db.models import User
from app.services import storage_service
from app.services.storage_service import StorageError

logger = logging.getLogger(__name__)

router = APIRouter()


class BlendFileResponse(BaseModel):
    key: str
    filename: str
    size: int
    last_modified: datetime


class UploadUrlRequest(BaseModel):
    filename: str
    size: int


class UploadUrlResponse(BaseModel):
    upload_url: str
    key: str


class CreateMultipartRequest(BaseModel):
    filename: str


class CreateMultipartResponse(BaseModel):
    uploadId: str
    key: str


class SignPartResponse(BaseModel):
    url: str


class UploadedPart(BaseModel):
    PartNumber: int
    Size: int
    ETag: str


class MultipartPart(BaseModel):
    PartNumber: int
    ETag: str


class CompleteMultipartRequest(BaseModel):
    key: str
    uploadId: str
    parts: list[MultipartPart]


class CompleteMultipartResponse(BaseModel):
    location: str


class AbortMultipartRequest(BaseModel):
    key: str
    uploadId: str


def _bad_request(e: StorageError) -> HTTPException:
    """StorageError is caller error (bad name, foreign key, oversized) — 400, not 500."""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/storage/blend-files", response_model=list[BlendFileResponse])
async def list_blend_files(user: User = Depends(get_current_user)):
    """List the current user's stored blend files."""
    return storage_service.list_blend_files(str(user.id))


@router.delete("/storage/blend-files", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blend_file(key: str, user: User = Depends(get_current_user)):
    try:
        storage_service.delete_blend_file(key, str(user.id))
    except StorageError as e:
        raise _bad_request(e)


@router.post("/storage/blend-files/upload-url", response_model=UploadUrlResponse)
async def create_upload_url(
    body: UploadUrlRequest, user: User = Depends(get_current_user)
):
    """Presign a single-PUT upload. Backs Uppy's getUploadParameters (small files)."""
    try:
        return storage_service.presign_upload(str(user.id), body.filename, body.size)
    except StorageError as e:
        raise _bad_request(e)


@router.post("/storage/multipart/create", response_model=CreateMultipartResponse)
async def create_multipart(
    body: CreateMultipartRequest, user: User = Depends(get_current_user)
):
    try:
        return storage_service.create_multipart_upload(str(user.id), body.filename)
    except StorageError as e:
        raise _bad_request(e)


@router.get("/storage/multipart/sign-part", response_model=SignPartResponse)
async def sign_part(
    key: str,
    uploadId: str,
    partNumber: int,
    user: User = Depends(get_current_user),
):
    try:
        url = storage_service.presign_part(key, uploadId, partNumber, str(user.id))
    except StorageError as e:
        raise _bad_request(e)
    return {"url": url}


@router.get("/storage/multipart/list-parts", response_model=list[UploadedPart])
async def list_parts(
    key: str,
    uploadId: str,
    user: User = Depends(get_current_user),
):
    """Parts already uploaded — lets Uppy resume rather than restart."""
    try:
        return storage_service.list_parts(key, uploadId, str(user.id))
    except StorageError as e:
        raise _bad_request(e)


@router.post("/storage/multipart/complete", response_model=CompleteMultipartResponse)
async def complete_multipart(
    body: CompleteMultipartRequest, user: User = Depends(get_current_user)
):
    try:
        return storage_service.complete_multipart_upload(
            body.key,
            body.uploadId,
            [p.model_dump() for p in body.parts],
            str(user.id),
        )
    except StorageError as e:
        raise _bad_request(e)


@router.post("/storage/multipart/abort", status_code=status.HTTP_204_NO_CONTENT)
async def abort_multipart(
    body: AbortMultipartRequest, user: User = Depends(get_current_user)
):
    try:
        storage_service.abort_multipart_upload(body.key, body.uploadId, str(user.id))
    except StorageError as e:
        raise _bad_request(e)
