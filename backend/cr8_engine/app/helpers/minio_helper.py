# app/helpers/minio_helper.py

from fastapi import HTTPException, UploadFile
import minio
from minio.error import S3Error
from datetime import datetime
from app.core.config import settings
import io
from typing import Union, List


minio_endpoint = settings.MINIO_ENDPOINT
minio_access_key = settings.MINIO_ACCESS_KEY
minio_secret_key = settings.MINIO_SECRET_KEY
minio_bucket_name = settings.MINIO_BUCKET_NAME


# Initialize MinIO client
minio_client = minio.Minio(
    minio_endpoint,
    access_key=minio_access_key,
    secret_key=minio_secret_key,
    secure=True
)


async def upload_file_to_minio(file: Union[UploadFile, bytes], folder: str, filename: str) -> str:
    """
    Upload a file to MinIO and return its URL

    Args:
        file (Union[UploadFile, bytes]): The file to upload, either as UploadFile or bytes
        folder (str): The folder name in the bucket
        filename (str): The original filename

    Returns:
        str: The URL of the uploaded file

    Raises:
        HTTPException: If file upload fails
    """
    try:
        if isinstance(file, UploadFile):
            file_content = await file.read()
            content_type = file.content_type
        elif isinstance(file, bytes):
            file_content = file
            content_type = "application/octet-stream"  # Default content type for bytes
        else:
            raise ValueError(f"Unsupported file type: {type(file)}")

        file_name = f"{folder}/{datetime.utcnow().timestamp()}_{filename}"

        minio_client.put_object(
            minio_bucket_name,
            file_name,
            io.BytesIO(file_content),
            length=len(file_content),
            content_type=content_type
        )

        url = f"https://{minio_endpoint}/{minio_bucket_name}/{file_name}"
        return url

    except S3Error as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {str(e)}")
    finally:
        if isinstance(file, UploadFile):
            await file.seek(0)
