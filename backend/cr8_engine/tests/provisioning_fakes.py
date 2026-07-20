"""
Minimal fakes for VastAIClient/SSHClient used across the provisioning test
suite — not a test file itself (no test_ prefix), just shared doubles.
"""

from app.services.provisioning.ssh_client import LaunchError


class FakeVastAIClient:
    def __init__(self):
        self.instances: dict[int, dict] = {}
        self.destroyed_ids: list[int] = []
        self.attach_calls: list[int] = []
        self._destroy_confirms_after: dict[int, int] = {}
        self._destroy_call_count: dict[int, int] = {}
        self._vanish_after: dict[int, int] = {}
        self._next_offer_id = 999001
        self._available_offers: list[dict] | None = None

    def set_available_offers(self, offers: list[dict]):
        """Override what search_offers returns, for precise control over
        machine_id-filtered searches — e.g.
        [{"id": 555, "gpu_name": "RTX 3090", "dph_total": 0.4, "machine_id": 42}].
        Left unset, search_offers falls back to its single-default-offer
        behavior (unaffected — existing tests don't need to know this exists)."""
        self._available_offers = offers

    def set_instance(self, instance_id: int, **fields):
        self.instances[instance_id] = {"id": instance_id, **fields}

    def remove_instance(self, instance_id: int):
        self.instances.pop(instance_id, None)

    def confirm_destroy_after(self, instance_id: int, calls: int):
        """The instance won't report a terminal status (or disappear) until
        destroy_instance has been called this many times — simulates VastAI
        taking a moment to actually tear the container down."""
        self._destroy_confirms_after[instance_id] = calls
        self._destroy_call_count[instance_id] = 0

    def vanish_after(self, instance_id: int, calls: int):
        """The instance fully disappears from get_instance_info (mirrors the
        real observed production behavior: 200 OK with {"instances": null},
        not a terminal actual_status) after destroy_instance has been called
        this many times."""
        self._vanish_after[instance_id] = calls
        self._destroy_call_count[instance_id] = 0

    async def search_offers(self, gpu_name: str, num_gpus: int = 1, machine_ids: list[int] | None = None) -> list[dict]:
        if self._available_offers is not None:
            offers = self._available_offers
            if machine_ids is not None:
                offers = [o for o in offers if o.get("machine_id") in machine_ids]
            return offers
        if machine_ids is not None:
            # Default: no known-fast machine happens to be available right
            # now — forces the caller to fall back to the general search,
            # matching real life (a "known fast" machine isn't always for rent).
            return []
        return [{"id": self._next_offer_id, "gpu_name": gpu_name, "dph_total": 0.5, "machine_id": self._next_offer_id}]

    async def accept_offer(self, offer_id: int, template_hash_id: str, disk_gb: int):
        # Mirrors real VastAI: each successful launch consumes that offer —
        # the NEXT search_offers call (e.g. a retry after this instance was
        # destroyed) returns a genuinely fresh id, matching production where
        # two launches never collide on the same instance id.
        self._next_offer_id += 1
        if offer_id not in self.instances:
            # Auto-register a healthy default so a test exercising a SECOND
            # fresh launch (e.g. instance-fatal retry) doesn't need to
            # pre-seed every possible id — tests that call set_instance()
            # before launching still take full precedence (this only fires
            # when nothing was set yet).
            self.instances[offer_id] = {
                "id": offer_id, "actual_status": "running", "ssh_host": "1.2.3.4", "ssh_port": 2222,
            }
        return offer_id

    async def attach_ssh_key(self, instance_id: int) -> bool:
        self.attach_calls.append(instance_id)
        return True

    async def get_instance_info(self, instance_id: int):
        return self.instances.get(instance_id)

    async def destroy_instance(self, instance_id: int) -> bool:
        self.destroyed_ids.append(instance_id)
        threshold = self._destroy_confirms_after.get(instance_id)
        vanish_threshold = self._vanish_after.get(instance_id)
        if threshold is not None or vanish_threshold is not None:
            self._destroy_call_count[instance_id] += 1
        if threshold is not None and self._destroy_call_count[instance_id] >= threshold:
            self.instances[instance_id]["actual_status"] = "exited"
        if vanish_threshold is not None and self._destroy_call_count[instance_id] >= vanish_threshold:
            self.instances.pop(instance_id, None)
        return True

    async def recycle_instance(self, instance_id: int) -> bool:
        return True

    async def list_instances(self) -> list[dict]:
        return list(self.instances.values())

    def get_gpu_for_tier(self, tier: str):
        return "RTX 3090"

    async def close(self):
        pass


class FakeSSHClient:
    def __init__(self, launch_pid: int = 4242, launch_error: LaunchError | None = None):
        self.launch_pid = launch_pid
        self.launch_error = launch_error
        self.connected_instances: list[int] = []
        self.killed: list[tuple[int, str, int]] = []
        self.orphan_kills: list[tuple[int, str]] = []

    def set_ssh_key(self, key):
        pass

    async def get_connection(self, instance_id: int, host: str, port: int):
        self.connected_instances.append(instance_id)
        return object()

    async def launch_blender(self, instance_id, username, status_callback=None, auth_token=None, launch_env=None):
        if self.launch_error is not None:
            raise self.launch_error
        return self.launch_pid

    async def is_blender_running(self, instance_id, username, pid) -> bool:
        return True

    async def kill_blender(self, instance_id, username, pid) -> bool:
        self.killed.append((instance_id, username, pid))
        return True

    async def kill_orphaned_blender(self, instance_id, username) -> bool:
        self.orphan_kills.append((instance_id, username))
        return True

    async def close_connection(self, instance_id):
        pass

    async def close_all(self):
        pass
