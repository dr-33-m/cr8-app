# app/services/blender_service.py
import logging
import paramiko
import shlex
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)


class BlenderService:
    @staticmethod
    def create_ssh_client() -> paramiko.SSHClient:
        """Create and configure SSH client with key-based authentication using settings"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            key = paramiko.RSAKey.from_private_key_file(settings.SSH_KEY_PATH)
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

    @staticmethod
    async def launch_instance(username: str, blend_file: str) -> bool:
        """Launch a Blender instance for a specific user session"""
        try:
            client = BlenderService.create_ssh_client()

            try:
                websocket_url = f"ws://{settings.WS_HOST}:{settings.WS_PORT}/ws/{username}/blender"
                safe_url = shlex.quote(websocket_url)

                # Launch Blender
                export_display = 'export DISPLAY=:1'
                cd_command = f'cd "{settings.BLENDER_REMOTE_DIRECTORY}"'
                tmux_session = f"blender_{username}"
                tmux_command = (
                    f"tmux new-session -d -s {tmux_session} "
                    f"'WS_URL={safe_url} blender {shlex.quote(blend_file)} "
                    f"--python-expr \"import bpy; bpy.ops.ws_handler.connect_websocket()\"'"
                )

                full_command = f"{export_display} && {cd_command} && {tmux_command}"
                stdin, stdout, stderr = client.exec_command(full_command)

                error = stderr.read().decode().strip()
                if error:
                    logger.error(f"Blender launch failed: {error}")
                    return False

                if stdout.channel.recv_exit_status() != 0:
                    logger.error(
                        f"Blender launch failed with non-zero exit status")
                    return False

                # Clean up only if launch was successful
                logger.info(f"Launched Blender instance for {username}")
                return True

            finally:
                client.close()

        except Exception as e:
            logger.error(f"Error launching Blender: {str(e)}")
            return False

    @staticmethod
    async def terminate_instance(username: str) -> bool:
        """Terminate a Blender instance for a specific user"""
        try:
            client = BlenderService.create_ssh_client()

            try:
                # Kill the tmux session for this user's Blender instance
                tmux_session_name = f"blender_{username}"
                kill_command = f"tmux kill-session -t {tmux_session_name}"

                stdin, stdout, stderr = client.exec_command(kill_command)

                error = stderr.read().decode().strip()
                if error and "no server running" not in error.lower():
                    logger.error(
                        f"Error terminating Blender for user {username}: {error}")
                    return False

                logger.info(
                    f"Successfully terminated Blender instance for user {username}")
                return True

            finally:
                client.close()

        except Exception as e:
            logger.error(
                f"Error terminating Blender for user {username}: {str(e)}")
            return False

    @staticmethod
    async def check_instance_status(username: str) -> bool:
        """Check if a Blender instance is running for a specific user"""
        try:
            client = BlenderService.create_ssh_client()

            try:
                tmux_session_name = f"blender_{username}"
                check_command = f"tmux has-session -t {tmux_session_name}"

                stdin, stdout, stderr = client.exec_command(check_command)

                # tmux has-session returns 0 if the session exists
                return stdout.channel.recv_exit_status() == 0

            finally:
                client.close()

        except Exception as e:
            logger.error(
                f"Error checking Blender status for user {username}: {str(e)}")
            return False
