from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
import paramiko
from pydantic import BaseModel
from app.db.session import get_db
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class BlenderLaunchRequest(BaseModel):
    blend_file: str  # Name of the .blend file to launch


def create_ssh_client() -> paramiko.SSHClient:
    """Create and configure SSH client with key-based authentication using settings"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        key = paramiko.RSAKey.from_private_key_file(
            settings.SSH_KEY_PATH)
        client.connect(
            hostname=settings.SSH_LOCAL_IP,
            username=settings.SSH_USERNAME,
            pkey=key,
            port=settings.SSH_PORT
        )
        return client
    except Exception as e:
        logger.error(f"SSH connection failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"SSH connection failed: {str(e)}"
        )


@router.post("/launch")
async def launch_blender(
    request: BlenderLaunchRequest,
    db: Client = Depends(get_db)
) -> Any:
    """
    Launch Blender on remote workstation with specified blend file.
    """
    try:
        if not db:
            raise HTTPException(
                status_code=500,
                detail="Database connection not available"
            )

        client = create_ssh_client()

        try:
            # Construct and execute command using settings and user-specified blend file
            export_display_command = 'export DISPLAY=:1'
            cd_command = f'cd "{settings.BLENDER_REMOTE_DIRECTORY}"'
            tmux_command = f"tmux new-session -d 'blender {request.blend_file}'"
            full_command = f"{export_display_command} && {cd_command} && {tmux_command}"

            stdin, stdout, stderr = client.exec_command(full_command)

            # Check for immediate errors
            error = stderr.read().decode().strip()
            if error:
                logger.error(f"Command execution failed: {error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Command execution failed: {error}"
                )

            # Check command exit status
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                logger.error(f"Command exited with status: {exit_status}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Command exited with status: {exit_status}"
                )

            return {
                "status": "success",
                "message": "Blender launch initiated",
                "blend_file": request.blend_file
            }

        finally:
            client.close()

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Full error details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error launching Blender: {str(e)}"
        )
