import subprocess
import asyncio
import logging
import os
import json
import psutil
from typing import Dict, Optional
from pathlib import Path


class BlenderProcessCache:
    """Simple file-based cache for tracking Blender processes across service restarts"""
    
    def __init__(self):
        self.processes: Dict[str, int] = {}  # username -> PID
        self.cache_file = Path.home() / '.cr8' / 'blender_instances.json'
        self.logger = logging.getLogger(__name__)
        self._ensure_cache_dir()
        self.logger.info(f"Initializing Blender process cache at {self.cache_file}")
        self._load_from_file()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_from_file(self):
        """Load process data from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    # Validate that processes are still running
                    for username, pid in data.items():
                        if self._is_process_running(pid):
                            self.processes[username] = pid
                        else:
                            self.logger.debug(f"Removing stale PID {pid} for {username}")
                    self.logger.info(f"Loaded {len(self.processes)} cached Blender processes")
        except Exception as e:
            self.logger.warning(f"Failed to load process cache: {e}")
    
    def _save_to_file(self):
        """Save process data to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.processes, f)
        except Exception as e:
            self.logger.error(f"Failed to save process cache: {e}")
    
    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running and is Blender"""
        try:
            process = psutil.Process(pid)
            # Check if it's actually a Blender process
            return 'blender' in process.name().lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def add(self, username: str, pid: int):
        """Add a process to cache"""
        self.processes[username] = pid
        self._save_to_file()
    
    def remove(self, username: str):
        """Remove a process from cache"""
        if username in self.processes:
            del self.processes[username]
            self._save_to_file()
    
    def get(self, username: str) -> Optional[int]:
        """Get PID for username, validating it's still running"""
        if username not in self.processes:
            return None
        
        pid = self.processes[username]
        if self._is_process_running(pid):
            return pid
        else:
            # Remove stale entry
            self.remove(username)
            return None
    
    def get_all_processes(self) -> Dict[str, int]:
        """Get all valid processes (validating each one)"""
        valid_processes = {}
        stale_usernames = []
        
        for username, pid in self.processes.items():
            if self._is_process_running(pid):
                valid_processes[username] = pid
            else:
                stale_usernames.append(username)
        
        # Remove stale entries
        for username in stale_usernames:
            self.remove(username)
        
        return valid_processes


class BlenderService:
    _instances: Dict[str, subprocess.Popen] = {}
    _process_cache = BlenderProcessCache()
    logger = logging.getLogger(__name__)

    @classmethod
    async def launch_instance(cls, username: str, blend_file_path: str = None) -> bool:
        # Check if instance is already running
        if username in cls._instances:
            process = cls._instances[username]
            if process.poll() is None:
                cls.logger.info(
                    f"Blender instance for {username} is already running.")
                return True
            else:
                # Process has died, clean up
                del cls._instances[username]

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

            # Set the Socket.IO URL as an environment variable for the Blender process
            env = os.environ.copy()
            env["WS_URL"] = "http://localhost:8000"
            env["CR8_USERNAME"] = username

            process = subprocess.Popen(
                command, env=env)
            cls._instances[username] = process
            # Add to process cache for persistence across restarts
            cls._process_cache.add(username, process.pid)
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
            process = cls._instances[username]
            if process.poll() is None:
                return True
            else:
                # Process has died, clean up
                del cls._instances[username]
        return False

    @classmethod
    async def terminate_instance(cls, username: str) -> bool:
        # First check in-memory instances
        if username in cls._instances:
            process = cls._instances[username]
            if process.poll() is None:
                cls.logger.info(f"Terminating Blender instance for {username}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    cls.logger.warning(f"Force killing Blender instance for {username}")
                    process.kill()
                cls.logger.info(f"Terminated Blender instance for {username}")
            else:
                cls.logger.info(f"Blender instance for {username} already terminated")
            del cls._instances[username]
            cls._process_cache.remove(username)
            return True
        
        # Check process cache as fallback (handles service restarts)
        pid = cls._process_cache.get(username)
        if pid is not None:
            try:
                cls.logger.info(f"Terminating cached Blender instance for {username} (PID: {pid})")
                process = psutil.Process(pid)
                process.terminate()
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    cls.logger.warning(f"Force killing cached Blender instance for {username}")
                    process.kill()
                cls.logger.info(f"Terminated cached Blender instance for {username}")
                cls._process_cache.remove(username)
                return True
            except psutil.NoSuchProcess:
                cls.logger.info(f"Cached Blender instance for {username} already terminated")
                cls._process_cache.remove(username)
                return True
            except Exception as e:
                cls.logger.error(f"Failed to terminate cached Blender instance for {username}: {e}")
                return False
        
        cls.logger.warning(f"No Blender instance found for {username}")
        return False
