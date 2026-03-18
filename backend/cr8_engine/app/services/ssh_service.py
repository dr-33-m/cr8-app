"""
SSH Service — Async SSH manager using asyncssh for connecting to VastAI instances.
Handles Blender process launching, monitoring, and termination via SSH.
"""

import asyncio
import logging
from typing import Optional

import asyncssh

logger = logging.getLogger(__name__)


class LaunchError(Exception):
    """Raised when launch-blender.sh fails with a structured error code."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code  # e.g. "xorg_all_drivers_failed", "blender_crashed"
        super().__init__(message)


class SSHService:
    """Manages SSH connections to VastAI instances and Blender process lifecycle."""

    def __init__(self):
        self._connections: dict[int, asyncssh.SSHClientConnection] = {}  # instance_id -> connection
        self._ssh_key: asyncssh.SSHKey | None = None  # Set by InstanceManager
        logger.info("SSH service initialized")

    def set_ssh_key(self, key: asyncssh.SSHKey):
        """Set the private key for SSH connections (from VastAIService)."""
        self._ssh_key = key

    async def get_connection(self, instance_id: int, host: str, port: int) -> asyncssh.SSHClientConnection:
        """
        Get or create an SSH connection to a VastAI instance.
        Reuses existing connections when possible.

        Args:
            instance_id: VastAI instance ID (used as cache key)
            host: SSH host address
            port: SSH port (VastAI assigns random external ports)

        Returns:
            Active SSH connection
        """
        # Check for existing valid connection
        if instance_id in self._connections:
            conn = self._connections[instance_id]
            # Verify the connection is still alive by running a simple command
            try:
                result = await asyncio.wait_for(conn.run("echo ok", check=True), timeout=5)
                if result.stdout.strip() == "ok":
                    return conn
            except Exception:
                logger.info(f"Cached SSH connection to instance {instance_id} is stale, reconnecting")
                await self._close_connection_safely(instance_id)

        # Create new connection, retrying to handle authorized_keys propagation delay
        logger.info(f"Connecting via SSH to instance {instance_id} at {host}:{port}")
        max_attempts = 5
        retry_delay = 10  # seconds between retries
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                conn = await asyncssh.connect(
                    host=host,
                    port=port,
                    username="root",
                    client_keys=[self._ssh_key],
                    known_hosts=None,  # VastAI instances have dynamic host keys
                    connect_timeout=30,
                )
                self._connections[instance_id] = conn
                logger.info(f"SSH connected to instance {instance_id}")
                return conn
            except Exception as e:
                last_error = e
                if attempt < max_attempts:
                    logger.warning(f"SSH attempt {attempt}/{max_attempts} failed for instance {instance_id}: {e} — retrying in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"SSH connection failed to instance {instance_id} ({host}:{port}): {e}")
        raise last_error

    async def launch_blender(self, instance_id: int, username: str, status_callback=None, auth_token: str = None) -> int:
        """
        Launch a headless Blender process on a VastAI instance via SSH.

        Calls /opt/cr8/launch-blender.sh which handles the entire prerequisite chain:
        env setup → NVIDIA driver install → Xorg startup → Blender launch.

        The script emits structured CR8: prefixed lines for progress tracking:
          CR8:STATUS:<step>   — progress update
          CR8:PID:<number>    — success, returns the Blender PID
          CR8:ERROR:<reason>  — failure with machine-readable reason

        Args:
            instance_id: VastAI instance ID
            username: cr8 username (used for WebRTC producer ID)
            status_callback: Optional async callback for progress updates

        Returns:
            PID of the launched Blender process

        Raises:
            LaunchError: With error_code indicating what failed (e.g. "xorg_all_drivers_failed")
        """
        conn = self._connections.get(instance_id)
        if not conn:
            logger.error(f"No SSH connection for instance {instance_id}")
            return None

        logger.info(f"Launching Blender on instance {instance_id} for user {username}")

        # Per-phase inactivity timeouts (seconds). The script emits a CR8:STATUS line
        # at the start of each phase, so "no output for N seconds" means that phase hung.
        # Phases that do heavy I/O get more headroom.
        PHASE_TIMEOUTS: dict[str, int] = {
            "nvidia_downloading": 180,  # driver download can be slow on cold instances
            "nvidia_installing":  120,  # kernel module build/install
            "xorg_setup":          60,
        }
        DEFAULT_PHASE_TIMEOUT = 30

        try:
            # Pass auth token as environment variable if available
            env_prefix = f"CR8_AUTH_TOKEN={auth_token} " if auth_token else ""
            async with conn.create_process(f"{env_prefix}/opt/cr8/launch-blender.sh {username}") as process:
                pid = None
                error = None
                current_phase = "startup"
                phase_timeout = DEFAULT_PHASE_TIMEOUT

                while True:
                    try:
                        line = await asyncio.wait_for(process.stdout.readline(), timeout=phase_timeout)
                    except asyncio.TimeoutError:
                        logger.error(
                            f"launch-blender.sh hung for {phase_timeout}s during '{current_phase}' "
                            f"on instance {instance_id}"
                        )
                        raise LaunchError(
                            "timeout",
                            f"launch-blender.sh timed out during '{current_phase}' on instance {instance_id}",
                        )

                    if not line:  # EOF — script exited
                        break

                    line = line.strip()
                    if line.startswith("CR8:PID:"):
                        pid_str = line[len("CR8:PID:"):]
                        if pid_str.isdigit():
                            pid = int(pid_str)
                    elif line.startswith("CR8:ERROR:"):
                        error = line[len("CR8:ERROR:"):]
                    elif line.startswith("CR8:STATUS:"):
                        status = line[len("CR8:STATUS:"):]
                        current_phase = status
                        # Bump timeout for the next phase based on what was just announced
                        phase_timeout = next(
                            (t for k, t in PHASE_TIMEOUTS.items() if k in status),
                            DEFAULT_PHASE_TIMEOUT,
                        )
                        logger.info(f"[instance {instance_id}] {status}")
                        if status_callback:
                            try:
                                await status_callback(status)
                            except Exception:
                                pass

                if pid is not None:
                    logger.info(f"Blender launched on instance {instance_id} for {username} with PID {pid}")
                    return pid

                if error:
                    logger.error(f"launch-blender.sh failed on instance {instance_id}: {error}")
                    raise LaunchError(error, f"launch-blender.sh failed on instance {instance_id}: {error}")

                logger.error(f"launch-blender.sh exited with no PID on instance {instance_id}")
                raise LaunchError("unknown", f"Blender returned no PID on instance {instance_id}")

        except LaunchError:
            raise
        except Exception as e:
            logger.error(f"Failed to run launch-blender.sh on instance {instance_id}: {e}")
            raise LaunchError("ssh_error", f"Failed to run launch-blender.sh: {e}")

    async def is_blender_running(self, instance_id: int, username: str, pid: int) -> bool:
        """
        Check if a specific Blender process is still running on an instance.

        Args:
            instance_id: VastAI instance ID
            username: cr8 username
            pid: Process ID to check

        Returns:
            True if the process is running
        """
        conn = self._connections.get(instance_id)
        if not conn:
            return False

        try:
            result = await asyncio.wait_for(
                conn.run(f"kill -0 {pid} 2>/dev/null && echo running || echo stopped"),
                timeout=10,
            )
            return result.stdout.strip() == "running"
        except Exception as e:
            logger.warning(f"Failed to check Blender status for {username} on instance {instance_id}: {e}")
            return False

    async def kill_blender(self, instance_id: int, username: str, pid: int) -> bool:
        """
        Kill a specific Blender process on an instance.

        Args:
            instance_id: VastAI instance ID
            username: cr8 username
            pid: Process ID to kill

        Returns:
            True if killed successfully
        """
        conn = self._connections.get(instance_id)
        if not conn:
            logger.error(f"No SSH connection for instance {instance_id}")
            return False

        logger.info(f"Killing Blender (PID {pid}) for {username} on instance {instance_id}")

        try:
            # Graceful termination first, then force kill after 5 seconds
            kill_cmd = f"kill {pid} 2>/dev/null; sleep 5; kill -0 {pid} 2>/dev/null && kill -9 {pid} 2>/dev/null; echo done"
            await asyncio.wait_for(conn.run(kill_cmd), timeout=15)
            logger.info(f"Blender (PID {pid}) killed for {username} on instance {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to kill Blender for {username} on instance {instance_id}: {e}")
            return False

    async def count_blender_processes(self, instance_id: int) -> int:
        """
        Count running Blender processes on an instance.

        Args:
            instance_id: VastAI instance ID

        Returns:
            Number of running Blender processes
        """
        conn = self._connections.get(instance_id)
        if not conn:
            return 0

        try:
            result = await asyncio.wait_for(
                conn.run("pgrep -c blender 2>/dev/null || echo 0"),
                timeout=10,
            )
            count_str = result.stdout.strip()
            return int(count_str) if count_str.isdigit() else 0
        except Exception:
            return 0

    async def close_connection(self, instance_id: int):
        """Close SSH connection for a specific instance."""
        await self._close_connection_safely(instance_id)

    async def close_all(self):
        """Close all SSH connections."""
        instance_ids = list(self._connections.keys())
        for instance_id in instance_ids:
            await self._close_connection_safely(instance_id)
        logger.info("All SSH connections closed")

    async def _close_connection_safely(self, instance_id: int):
        """Close an SSH connection, ignoring errors."""
        conn = self._connections.pop(instance_id, None)
        if conn:
            try:
                conn.close()
                await conn.wait_closed()
            except Exception:
                pass
            logger.info(f"SSH connection to instance {instance_id} closed")
