# app/services/blender_service.py
import logging
import paramiko
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
                # Construct the websocket URL for this specific user's Blender instance
                websocket_url = f"ws://{settings.WS_HOST}:{settings.WS_PORT}/ws/{username}/blender"

                # Create a Python script that will be executed by Blender to set up the websocket
                blender_script = (
                    f"import bpy\n"
                    f"import sys\n"
                    f"sys.path.append('{settings.BLENDER_ADDONS_PATH}')\n"
                    f"from websocket_client import websocket_handler\n"
                    f"websocket_handler.initialize('{websocket_url}')\n"
                    f"websocket_handler.connect()"
                )

                # Save the script to a temporary file on the remote machine
                script_path = f"/tmp/blender_script_{username}.py"
                script_command = f"echo '{blender_script}' > {script_path}"
                stdin, stdout, stderr = client.exec_command(script_command)

                if stderr.read():
                    raise Exception("Failed to create script file")

                # Construct and execute the Blender launch command
                export_display_command = 'export DISPLAY=:1'
                cd_command = f'cd "{settings.BLENDER_REMOTE_DIRECTORY}"'

                # Launch Blender with the script and blend file in a new tmux session
                tmux_session_name = f"blender_{username}"
                tmux_command = (
                    f"tmux new-session -d -s {tmux_session_name} "
                    f"'blender {blend_file} --python {script_path}'"
                )

                full_command = f"{export_display_command} && {cd_command} && {tmux_command}"

                stdin, stdout, stderr = client.exec_command(full_command)

                # Check for errors
                error = stderr.read().decode().strip()
                if error:
                    logger.error(
                        f"Blender launch failed for user {username}: {error}")
                    return False

                # Check command exit status
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    logger.error(
                        f"Blender launch exited with status {exit_status} for user {username}")
                    return False

                # Clean up the temporary script
                client.exec_command(f"rm {script_path}")

                logger.info(
                    f"Successfully launched Blender instance for user {username}")
                return True

            finally:
                client.close()

        except Exception as e:
            logger.error(
                f"Error launching Blender for user {username}: {str(e)}")
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
