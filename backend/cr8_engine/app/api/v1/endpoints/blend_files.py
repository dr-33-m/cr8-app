import os
import glob
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()


class ScanBlendFolderRequest(BaseModel):
    folder_path: str


class BlendFileInfo(BaseModel):
    filename: str
    full_path: str


class ScanBlendFolderResponse(BaseModel):
    blend_files: List[BlendFileInfo]
    total_count: int


@router.post("/scan-blend-folder", response_model=ScanBlendFolderResponse)
async def scan_blend_folder(request: ScanBlendFolderRequest):
    """
    Scan a folder for .blend files and return the list
    """
    folder_path = request.folder_path.strip()

    # Validate that the path exists
    if not os.path.exists(folder_path):
        raise HTTPException(
            status_code=400, detail="Folder path does not exist")

    # Validate that it's actually a directory
    if not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="Path is not a directory")

    try:
        # Search for .blend files in the directory
        blend_pattern = os.path.join(folder_path, "*.blend")
        blend_files = glob.glob(blend_pattern)

        # Create the response data
        blend_file_info = []
        for file_path in sorted(blend_files):
            filename = os.path.basename(file_path)
            blend_file_info.append(BlendFileInfo(
                filename=filename,
                full_path=file_path
            ))

        return ScanBlendFolderResponse(
            blend_files=blend_file_info,
            total_count=len(blend_file_info)
        )

    except PermissionError:
        raise HTTPException(
            status_code=403, detail="Permission denied accessing folder")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error scanning folder: {str(e)}")
