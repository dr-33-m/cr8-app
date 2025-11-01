import subprocess
import asyncio
import logging
import os
from typing import Dict, Optional


class BlenderService:
    _instances: Dict[str, subprocess.Popen] = {}
    logger = logging.getLogger(__name__)

    @classmethod
    async def launch_instance(cls, username: str, blend_file_path: str = None) -> bool:
        if username in cls._instances and cls._instances[username].poll() is None:
            cls.logger.info(
                f"Blender instance for {username} is already running.")
            return True

        try:
            # Validate that the blend file exists
            if not os.path.exists(blend_file_path or ""):
                cls.logger.error(f"Blend file not found: {blend_file_path}")
                return False

            # Get Blender executable path from environment variable
            blender_path = os.getenv('BLENDER_EXECUTABLE_PATH')
            if not blender_path:
                raise ValueError(
                    "BLENDER_EXECUTABLE_PATH environment variable is not set")

            command = [
                blender_path,
                blend_file_path,
                "--python-expr",
                "import bpy; bpy.ops.ws_handler.connect_websocket()",
            ]

            # Set the WebSocket URL as an environment variable for the Blender process
            env = os.environ.copy()
            env["WS_URL"] = f"ws://localhost:8000/ws/{username}/blender"
            env["CR8_USERNAME"] = username

            process = subprocess.Popen(
                command, env=env)
            cls._instances[username] = process
            cls.logger.info(
                f"Launched Blender instance for {username} with PID {process.pid}")
            return True
        except FileNotFoundError:
            cls.logger.error(
                "'blender' command not found. Make sure Blender is installed and in your PATH.")
            return False
        except Exception as e:
            cls.logger.error(f"Failed to launch Blender for {username}: {e}")
            return False

    @classmethod
    async def check_instance_status(cls, username: str) -> bool:
        if username in cls._instances:
            return cls._instances[username].poll() is None
        return False

    @classmethod
    async def terminate_instance(cls, username: str) -> bool:
        if username in cls._instances:
            process = cls._instances[username]
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                cls.logger.info(f"Terminated Blender instance for {username}")
            del cls._instances[username]
            return True
        return False
