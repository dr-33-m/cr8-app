import subprocess
import asyncio
import logging
import os
import json
import psutil
from typing import Dict, Optional
from pathlib import Path

from .config import DeploymentConfig
from .instance_manager import ProvisionError

# Deferred operator call — bpy.app.timers fires on the main loop, after all addons
# in extensions/user_default/ are loaded and registered. --python-expr runs during
# init (too early), so we schedule the operator call for 1s after the event loop starts.
_BLENDER_CONNECT_EXPR = (
    "import bpy; "
    "bpy.app.timers.register("
    "lambda: (bpy.ops.ws_handler.connect_websocket(), None)[-1], "
    "first_interval=1.0"
    ")"
)


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
    _instance_manager = None  # Lazy-initialized for remote mode
    logger = logging.getLogger(__name__)

    @classmethod
    def _get_instance_manager(cls):
        """Lazy-initialize the InstanceManager (only needed in remote mode)."""
        if cls._instance_manager is None:
            from .instance_manager import InstanceManager
            cls._instance_manager = InstanceManager()
        return cls._instance_manager

    @classmethod
    async def launch_instance(cls, username: str, blend_file_path: str = None, status_callback=None) -> Optional[str]:
        """Launch a Blender instance. Routes to local or remote based on LAUNCH_MODE.

        Returns:
            "success" if launched, or a failure reason string:
            "timeout", "ssh_failed", "blender_failed", "no_gpu", "local_failed"
        """
        config = DeploymentConfig.get()
        if config.LAUNCH_MODE == "remote":
            return await cls._launch_remote(username, blend_file_path, status_callback=status_callback)
        return await cls._launch_local(username, blend_file_path)

    @classmethod
    async def check_instance_status(cls, username: str) -> bool:
        """Check if a Blender instance is running for the user."""
        config = DeploymentConfig.get()
        if config.LAUNCH_MODE == "remote":
            return await cls._check_status_remote(username)
        return await cls._check_status_local(username)

    @classmethod
    async def terminate_instance(cls, username: str) -> bool:
        """Terminate a Blender instance for the user."""
        config = DeploymentConfig.get()
        if config.LAUNCH_MODE == "remote":
            return await cls._terminate_remote(username)
        return await cls._terminate_local(username)

    # --- Remote mode (VastAI) ---

    @classmethod
    async def _launch_remote(cls, username: str, blend_file_path: str = None, status_callback=None) -> Optional[str]:
        """Launch Blender on a VastAI GPU instance via SSH."""
        try:
            manager = cls._get_instance_manager()
            assignment = await manager.provision_for_user(username, tier="creator", status_callback=status_callback)
            cls.logger.info(
                f"Remote Blender launched for {username} on instance {assignment.instance_id} "
                f"(PID {assignment.blender_pid})"
            )
            return "success"
        except ProvisionError as e:
            cls.logger.error(f"Failed to launch remote Blender for {username}: {e}")
            return e.reason
        except Exception as e:
            cls.logger.error(f"Failed to launch remote Blender for {username}: {e}")
            return "blender_failed"

    @classmethod
    async def _check_status_remote(cls, username: str) -> bool:
        """Check if user has a running Blender on a VastAI instance."""
        try:
            manager = cls._get_instance_manager()
            assignment = await manager.get_user_assignment(username)
            return assignment is not None
        except Exception:
            return False

    @classmethod
    async def _terminate_remote(cls, username: str) -> bool:
        """Terminate user's Blender on a VastAI instance via SSH."""
        try:
            manager = cls._get_instance_manager()
            return await manager.release_user(username)
        except Exception as e:
            cls.logger.error(f"Failed to terminate remote Blender for {username}: {e}")
            return False

    # --- Local mode (subprocess) ---

    @classmethod
    async def _launch_local(cls, username: str, blend_file_path: str = None) -> Optional[str]:
        """Launch Blender as a local subprocess (existing behavior)."""
        # Check if instance is already running
        if username in cls._instances:
            process = cls._instances[username]
            if process.poll() is None:
                cls.logger.info(
                    f"Blender instance for {username} is already running.")
                return "success"
            else:
                # Process has died, clean up
                del cls._instances[username]

        try:
            # Get Blender executable path from environment variable
            blender_path = os.getenv('BLENDER_EXECUTABLE_PATH')
            if not blender_path:
                raise ValueError(
                    "BLENDER_EXECUTABLE_PATH environment variable is not set")

            if blend_file_path:
                # Validate that the blend file exists
                if not os.path.exists(blend_file_path):
                    cls.logger.error(f"Blend file not found: {blend_file_path}")
                    return "local_failed"
                command = [
                    blender_path,
                    blend_file_path,
                    "--python-expr",
                    _BLENDER_CONNECT_EXPR,
                ]
            else:
                # Launch with empty default scene
                cls.logger.info(f"Launching Blender with empty project for {username}")
                command = [
                    blender_path,
                    "--python-expr",
                    _BLENDER_CONNECT_EXPR,
                ]

            # Set environment variables for the Blender process
            env = os.environ.copy()
            env["WS_URL"] = "http://localhost:8000"
            env["CR8_USERNAME"] = username

            # Generate internal auth token in remote mode
            config = DeploymentConfig.get()
            if config.LAUNCH_MODE == "remote":
                from app.auth.internal_token import generate_blender_token
                env["CR8_AUTH_TOKEN"] = generate_blender_token(username)

            env["CR8_SIGNALLER_URI"] = os.getenv("SIGNALLER_URI", "ws://127.0.0.1:8443")
            # Use headless X server on display :2 (GPU-accelerated, no physical display)
            env["DISPLAY"] = os.getenv("BLENDER_DISPLAY", ":2")

            # Open log file to capture Blender's output
            log_file_path = Path.cwd() / "blender_instance.log"
            cls.logger.info(f"Redirecting Blender output to {log_file_path}")
            log_file = open(log_file_path, "a")

            # Write separator with timestamp to log file
            import datetime
            log_file.write(f"\n{'='*80}\n")
            log_file.write(f"Blender instance for {username} started at {datetime.datetime.now()}\n")
            log_file.write(f"{'='*80}\n")
            log_file.flush()

            process = subprocess.Popen(
                command,
                env=env,
                stdout=log_file,
                stderr=subprocess.STDOUT
            )
            cls._instances[username] = process
            # Add to process cache for persistence across restarts
            cls._process_cache.add(username, process.pid)
            cls.logger.info(
                f"Launched Blender instance for {username} with PID {process.pid}")
            return "success"
        except FileNotFoundError:
            cls.logger.error(
                "'blender' command not found. Make sure Blender is installed and in your PATH.")
            return "local_failed"
        except Exception as e:
            cls.logger.error(f"Failed to launch Blender for {username}: {e}")
            return "local_failed"

    @classmethod
    async def _check_status_local(cls, username: str) -> bool:
        """Check if a local Blender subprocess is running."""
        if username in cls._instances:
            process = cls._instances[username]
            if process.poll() is None:
                return True
            else:
                # Process has died, clean up
                del cls._instances[username]
        return False

    @classmethod
    async def _terminate_local(cls, username: str) -> bool:
        """Terminate a local Blender subprocess."""
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
