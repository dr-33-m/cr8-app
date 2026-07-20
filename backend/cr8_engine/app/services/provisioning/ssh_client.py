"""
SSH client — connects to VastAI instances and drives launch-blender.sh's
CR8:STATUS/CR8:PID/CR8:ERROR protocol.

Renamed/hardened from the legacy app/services/ssh_service.py:
  - get_connection now uses exponential backoff (shared retry helper) instead
    of a flat 5x10s retry.
  - PHASE_TIMEOUTS is sourced from ProvisioningConfig and is now exhaustive
    against every phase launch-blender.sh actually emits; a phase that still
    isn't in the table logs a warning instead of silently taking the default,
    so gaps are visible operationally.
"""

import asyncio
import logging

import asyncssh

from .config import ProvisioningConfig
from .retry import retry_with_backoff

logger = logging.getLogger(__name__)


class LaunchError(Exception):
    """Raised when launch-blender.sh fails with a structured error code."""

    def __init__(self, error_code: str, message: str):
        self.error_code = error_code  # e.g. "xorg_all_drivers_failed", "blender_crashed"
        super().__init__(message)


class SSHClient:
    """Manages SSH connections to VastAI instances and the Blender process lifecycle."""

    def __init__(self):
        self.config = ProvisioningConfig.get()
        self._connections: dict[int, asyncssh.SSHClientConnection] = {}
        self._ssh_key: asyncssh.SSHKey | None = None  # set via set_ssh_key
        logger.info("SSH client initialized")

    def set_ssh_key(self, key: asyncssh.SSHKey):
        self._ssh_key = key

    async def get_connection(self, instance_id: int, host: str, port: int) -> asyncssh.SSHClientConnection:
        """Get or create an SSH connection, reusing a live one when possible."""
        if instance_id in self._connections:
            conn = self._connections[instance_id]
            try:
                result = await asyncio.wait_for(conn.run("echo ok", check=True), timeout=5)
                if result.stdout.strip() == "ok":
                    return conn
            except Exception:
                logger.info(f"Cached SSH connection to instance {instance_id} is stale, reconnecting")
                await self._close_connection_safely(instance_id)

        logger.info(f"Connecting via SSH to instance {instance_id} at {host}:{port}")

        async def _connect() -> asyncssh.SSHClientConnection:
            return await asyncssh.connect(
                host=host,
                port=port,
                username="root",
                client_keys=[self._ssh_key],
                known_hosts=None,  # VastAI instances have dynamic host keys
                connect_timeout=self.config.SSH_CONNECT_TIMEOUT_SECONDS,
            )

        conn = await retry_with_backoff(
            _connect,
            max_attempts=self.config.SSH_CONNECT_MAX_ATTEMPTS,
            base_delay=self.config.SSH_CONNECT_BASE_DELAY_SECONDS,
            factor=self.config.SSH_CONNECT_BACKOFF_FACTOR,
        )
        self._connections[instance_id] = conn
        logger.info(f"SSH connected to instance {instance_id}")
        return conn

    def _phase_timeout(self, status: str) -> int:
        for key, timeout in self.config.BLENDER_PHASE_TIMEOUTS.items():
            if key in status:
                return timeout
        logger.warning(
            f"CR8:STATUS phase '{status}' has no entry in BLENDER_PHASE_TIMEOUTS — "
            f"falling back to the {self.config.BLENDER_DEFAULT_PHASE_TIMEOUT}s default"
        )
        return self.config.BLENDER_DEFAULT_PHASE_TIMEOUT

    async def launch_blender(self, instance_id: int, username: str, status_callback=None,
                             auth_token: str = None, launch_env: dict = None) -> int:
        """Launch a headless Blender process via /opt/cr8/launch-blender.sh, parsing
        its CR8:STATUS/CR8:PID/CR8:ERROR protocol. Raises LaunchError on failure."""
        conn = self._connections.get(instance_id)
        if not conn:
            logger.error(f"No SSH connection for instance {instance_id}")
            raise LaunchError("ssh_error", f"No SSH connection for instance {instance_id}")

        logger.info(f"Launching Blender on instance {instance_id} for user {username}")

        try:
            # Env passed as single-quoted assignments: presigned URLs contain &
            # and =, which a bare shell would otherwise misinterpret. Values are
            # engine-generated (tokens, presigned URLs) and never contain quotes.
            env_vars = dict(launch_env or {})
            if auth_token:
                env_vars["CR8_AUTH_TOKEN"] = auth_token
            env_prefix = "".join(f"{k}='{v}' " for k, v in env_vars.items() if v)
            async with conn.create_process(f"{env_prefix}/opt/cr8/launch-blender.sh {username}") as process:
                pid = None
                error = None
                current_phase = "startup"
                phase_timeout = self.config.BLENDER_DEFAULT_PHASE_TIMEOUT

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
                        phase_timeout = self._phase_timeout(status)
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
        conn = self._connections.get(instance_id)
        if not conn:
            return False
        try:
            result = await asyncio.wait_for(
                conn.run(f"kill -0 {pid} 2>/dev/null && echo running || echo stopped"), timeout=10
            )
            return result.stdout.strip() == "running"
        except Exception as e:
            logger.warning(f"Failed to check Blender status for {username} on instance {instance_id}: {e}")
            return False

    async def kill_orphaned_blender(self, instance_id: int, username: str) -> bool:
        """Best-effort cleanup for a Blender launch that failed without ever
        returning a PID — nothing to kill_blender() by pid, but the failed
        launch may still have left a half-started process behind (e.g. the
        SSH channel dropped mid-launch while Blender itself kept starting up
        remotely). Finds any `blender` process tagged with this exact user's
        CR8_USERNAME env var — set on every blender invocation by
        launch-blender.sh — and kills it. Safe on a multi-tenant shared
        instance: only matches this specific user's marker, never a blind
        `pkill blender` that would also hit other users' live sessions."""
        conn = self._connections.get(instance_id)
        if not conn:
            return False
        cmd = (
            "for p in $(pgrep -x blender 2>/dev/null); do "
            f"tr '\\0' '\\n' < /proc/$p/environ 2>/dev/null | grep -qx 'CR8_USERNAME={username}' "
            "&& kill -9 $p 2>/dev/null; done; true"
        )
        try:
            await asyncio.wait_for(conn.run(cmd), timeout=10)
            return True
        except Exception as e:
            logger.warning(f"Failed to clean up stray Blender for {username} on instance {instance_id}: {e}")
            return False

    async def kill_blender(self, instance_id: int, username: str, pid: int) -> bool:
        conn = self._connections.get(instance_id)
        if not conn:
            logger.error(f"No SSH connection for instance {instance_id}")
            return False
        logger.info(f"Killing Blender (PID {pid}) for {username} on instance {instance_id}")
        try:
            kill_cmd = f"kill {pid} 2>/dev/null; sleep 5; kill -0 {pid} 2>/dev/null && kill -9 {pid} 2>/dev/null; echo done"
            await asyncio.wait_for(conn.run(kill_cmd), timeout=15)
            logger.info(f"Blender (PID {pid}) killed for {username} on instance {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to kill Blender for {username} on instance {instance_id}: {e}")
            return False

    async def count_blender_processes(self, instance_id: int) -> int:
        conn = self._connections.get(instance_id)
        if not conn:
            return 0
        try:
            result = await asyncio.wait_for(conn.run("pgrep -c blender 2>/dev/null || echo 0"), timeout=10)
            count_str = result.stdout.strip()
            return int(count_str) if count_str.isdigit() else 0
        except Exception:
            return 0

    async def close_connection(self, instance_id: int):
        await self._close_connection_safely(instance_id)

    async def close_all(self):
        instance_ids = list(self._connections.keys())
        for instance_id in instance_ids:
            await self._close_connection_safely(instance_id)
        logger.info("All SSH connections closed")

    async def _close_connection_safely(self, instance_id: int):
        conn = self._connections.pop(instance_id, None)
        if conn:
            try:
                conn.close()
                await conn.wait_closed()
            except Exception:
                pass
            logger.info(f"SSH connection to instance {instance_id} closed")
