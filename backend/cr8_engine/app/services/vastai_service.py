"""
VastAI Service — Async HTTP client for the VastAI REST API.
Handles searching offers, launching instances, polling status, and destroying instances.

Instances are launched using a VastAI template (VASTAI_TEMPLATE_HASH_ID) which bundles
the Docker image, onstart script, environment variables, and SSH configuration.
Create the template once on https://cloud.vast.ai/templates/ — see TEMPLATE_SETUP.md.

SSH keys are generated at startup and attached to each new instance via the API,
so no key files need to be managed on disk.
"""

import logging
import time
from typing import Optional

import asyncio
import httpx
import asyncssh

from .config import DeploymentConfig, TIER_GPU_MAP

logger = logging.getLogger(__name__)

BASE_URL = "https://console.vast.ai/api/v0"


class VastAIService:
    """Manages VastAI GPU instances via the REST API."""

    def __init__(self):
        config = DeploymentConfig.get()
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {config.VASTAI_API_KEY}"},
            timeout=30.0,
        )

        # Generate an ephemeral Ed25519 SSH keypair for this engine session.
        # Ed25519 is preferred over RSA: smaller, faster, and accepted by all modern OpenSSH versions.
        self._ssh_key = asyncssh.generate_private_key("ssh-ed25519", comment="cr8-engine")
        self._ssh_pubkey = self._ssh_key.export_public_key().decode()
        logger.info("VastAI service initialized (REST API, ephemeral SSH key generated)")

    @property
    def ssh_private_key(self) -> asyncssh.SSHKey:
        """The private key for SSH connections to VastAI instances."""
        return self._ssh_key

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def search_offers(self, gpu_name: str, num_gpus: int = 1) -> list[dict]:
        """
        Search for available GPU offers matching the given GPU name.

        Args:
            gpu_name: VastAI GPU name (e.g., "RTX 3090", "RTX 4090")
            num_gpus: Number of GPUs required (default: 1)

        Returns:
            List of available offers sorted by price (cheapest first)
        """
        logger.info(f"Searching VastAI offers: gpu={gpu_name}, num_gpus={num_gpus}")

        try:
            resp = await self.client.post("/bundles/", json={
                "gpu_name": {"in": [gpu_name]},
                "num_gpus": {"gte": num_gpus},
                "reliability": {"gte": 0.95},
                "verified": {"eq": True},
                "rentable": {"eq": True},
                "type": "ondemand",
                "limit": 10,
            })
            resp.raise_for_status()
            data = resp.json()

            offers = data.get("offers", [])
            # Sort by total price (cheapest first)
            offers.sort(key=lambda o: o.get("dph_total", float("inf")))
            logger.info(f"Found {len(offers)} offers for {gpu_name}")
            return offers

        except httpx.HTTPError as e:
            logger.error(f"Failed to search VastAI offers: {e}")
            return []

    async def launch_instance(self, gpu_name: str, disk_gb: int = 40) -> Optional[int]:
        """
        Launch a new VastAI instance using the configured template.

        Two-step process:
        1. Search for available offers matching the GPU
        2. Accept the best (cheapest) offer with our template

        Args:
            gpu_name: VastAI GPU name (e.g., "RTX 3090")
            disk_gb: Disk space in GB (default: 40)

        Returns:
            Instance ID if successful, None if failed
        """
        template_hash_id = self.config.VASTAI_TEMPLATE_HASH_ID
        logger.info(f"Launching VastAI instance: gpu={gpu_name}, template={template_hash_id}")

        try:
            # Step 1: Find offers
            offers = await self.search_offers(gpu_name)
            if not offers:
                logger.error(f"No available offers for {gpu_name}")
                return None

            # Step 2: Validate template with the first offer before trying the rest.
            # "invalid template hash" is a config error that affects ALL offers —
            # fail fast instead of burning through every offer and hitting rate limits.
            first_offer = offers[0]
            try:
                resp = await self.client.put(f"/asks/{first_offer['id']}/", json={
                    "template_hash_id": template_hash_id,
                    "disk": disk_gb,
                })
                resp.raise_for_status()
                result = resp.json()

                instance_id = result.get("new_contract")
                if instance_id:
                    logger.info(f"VastAI instance launched: id={int(instance_id)}")
                    return int(instance_id)

                logger.warning(f"No instance ID in response for offer {first_offer['id']}: {result}")

            except httpx.HTTPStatusError as e:
                body = e.response.text
                # Parse JSON error body if possible
                if "invalid template hash" in body or "template not accessible" in body:
                    logger.error(
                        f"VASTAI_TEMPLATE_HASH_ID '{template_hash_id}' is invalid. "
                        f"Update it in .env after editing the VastAI template."
                    )
                    return None
                logger.warning(f"Offer {first_offer['id']} rejected: {body}")

            # Step 3: Try remaining offers
            for offer in offers[1:]:
                offer_id = offer["id"]
                logger.info(
                    f"Accepting offer {offer_id}: "
                    f"{offer.get('num_gpus', '?')}x {offer.get('gpu_name', '?')} "
                    f"@ ${offer.get('dph_total', '?'):.3f}/hr"
                )

                try:
                    resp = await self.client.put(f"/asks/{offer_id}/", json={
                        "template_hash_id": template_hash_id,
                        "disk": disk_gb,
                    })
                    resp.raise_for_status()
                    result = resp.json()

                    instance_id = result.get("new_contract")
                    if instance_id:
                        logger.info(f"VastAI instance launched: id={int(instance_id)}")
                        return int(instance_id)

                    logger.warning(f"No instance ID in response for offer {offer_id}: {result}")

                except httpx.HTTPStatusError as e:
                    body = e.response.text
                    logger.warning(f"Offer {offer_id} rejected: {body}")

                    if e.response.status_code == 429:
                        logger.warning("Rate limited by VastAI, waiting 5s...")
                        await asyncio.sleep(5)

            logger.error(f"All offers exhausted for {gpu_name}")
            return None

        except Exception as e:
            logger.error(f"Failed to launch VastAI instance: {e}")
            return None

    async def attach_ssh_key(self, instance_id: int) -> bool:
        """
        Attach the SSH public key to a running VastAI instance.
        Must be called AFTER wait_for_ready() — VastAI only applies the key to running containers.

        Uses PUT /instances/{id}/ with {"ssh_key": pubkey} — the correct VastAI API endpoint.

        Args:
            instance_id: VastAI instance ID

        Returns:
            True if attached successfully
        """
        logger.info(f"Attaching SSH key to instance {instance_id}")
        try:
            resp = await self.client.post(
                f"/instances/{instance_id}/ssh/",
                json={"ssh_key": self._ssh_pubkey},
            )
            resp.raise_for_status()
            logger.info(f"SSH key attached to instance {instance_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to attach SSH key to instance {instance_id}: {e}")
            return False

    async def get_instance_info(self, instance_id: int) -> Optional[dict]:
        """
        Get details for a specific instance including IP and port mappings.

        Args:
            instance_id: VastAI instance ID

        Returns:
            Instance info dict or None if not found
        """
        try:
            resp = await self.client.get(f"/instances/{instance_id}/")
            resp.raise_for_status()
            data = resp.json()

            # API returns {"instances": {...}} for single instance
            instance = data.get("instances") if isinstance(data.get("instances"), dict) else data
            return instance

        except httpx.HTTPError as e:
            logger.error(f"Failed to get instance info for {instance_id}: {e}")
            return None

    async def wait_for_ready(self, instance_id: int, timeout: int = 600, poll_interval: int = 10, status_callback=None) -> Optional[dict]:
        """
        Poll instance status until it's running and SSH is available.

        Args:
            instance_id: VastAI instance ID
            timeout: Maximum wait time in seconds
            poll_interval: Seconds between status checks
            status_callback: Optional async callable(status: str, elapsed: int)

        Returns:
            Dict with {host, ssh_port, status} when ready, None if timeout
        """
        CREATED_STUCK_TIMEOUT = 120  # seconds before we consider a "created" instance dead

        logger.info(f"Waiting for instance {instance_id} to be ready (timeout={timeout}s)")
        start_time = time.time()
        empty_status_count = 0
        created_since: Optional[float] = None

        while time.time() - start_time < timeout:
            info = await self.get_instance_info(instance_id)

            if info is None:
                logger.warning(f"Instance {instance_id} not found, retrying...")
                await asyncio.sleep(poll_interval)
                continue

            status = info.get("actual_status") or info.get("status_msg") or "loading"
            elapsed = int(time.time() - start_time)
            logger.info(f"Instance {instance_id} status: '{status}' ({elapsed}s elapsed)")

            # Detect destroyed/gone instances: VastAI returns 200 but with empty status.
            # After 3 consecutive empty polls, the instance is dead — bail early.
            if not status:
                empty_status_count += 1
                if empty_status_count >= 3:
                    logger.error(
                        f"Instance {instance_id} returned empty status {empty_status_count} times — "
                        f"instance is likely destroyed on VastAI"
                    )
                    return None
            else:
                empty_status_count = 0

            # Detect stuck "created" instances: VastAI accepted the offer but the host
            # never started the container. Bail early so the manager can retry on a new host.
            if status == "created":
                if created_since is None:
                    created_since = time.time()
                elif time.time() - created_since >= CREATED_STUCK_TIMEOUT:
                    logger.error(
                        f"Instance {instance_id} stuck in 'created' state for "
                        f"{CREATED_STUCK_TIMEOUT}s — host likely inactive, bailing"
                    )
                    return None
            else:
                created_since = None

            if status_callback:
                try:
                    await status_callback(status, elapsed)
                except Exception:
                    pass  # Never let callback errors break the polling loop

            if status == "running":
                ssh_host = info.get("ssh_host") or info.get("public_ipaddr")
                ssh_port = info.get("ssh_port") or info.get("direct_port_start")

                if ssh_host and ssh_port:
                    connection_info = {
                        "host": ssh_host,
                        "ssh_port": int(ssh_port),
                        "status": "running",
                        "instance_id": instance_id,
                    }
                    logger.info(
                        f"Instance {instance_id} ready: "
                        f"host={ssh_host}, ssh_port={ssh_port}"
                    )
                    return connection_info
                else:
                    logger.debug("Instance running but SSH details not yet available")

            await asyncio.sleep(poll_interval)

        logger.error(f"Instance {instance_id} did not become ready within {timeout}s")
        return None

    async def recycle_instance(self, instance_id: int) -> bool:
        """
        Recycle a VastAI instance — destroys and recreates the container in place
        without losing the GPU slot. Useful for SSH/container issues where the
        underlying GPU is fine but the container is in a bad state.

        Uses PUT /api/v0/instances/recycle/{id}/

        Args:
            instance_id: VastAI instance ID

        Returns:
            True if recycle initiated successfully
        """
        logger.info(f"Recycling VastAI instance {instance_id}")
        try:
            resp = await self.client.put(f"/instances/recycle/{instance_id}/")
            resp.raise_for_status()
            result = resp.json()
            if result.get("success"):
                logger.info(f"VastAI instance {instance_id} recycle initiated")
                return True
            logger.warning(f"Recycle response for instance {instance_id}: {result}")
            return False
        except httpx.HTTPError as e:
            logger.error(f"Failed to recycle instance {instance_id}: {e}")
            return False

    async def destroy_instance(self, instance_id: int) -> bool:
        """
        Destroy a VastAI instance permanently.

        Args:
            instance_id: VastAI instance ID

        Returns:
            True if destroyed successfully
        """
        logger.info(f"Destroying VastAI instance {instance_id}")
        try:
            resp = await self.client.delete(f"/instances/{instance_id}/")
            resp.raise_for_status()
            logger.info(f"VastAI instance {instance_id} destroyed")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to destroy instance {instance_id}: {e}")
            return False

    async def list_instances(self) -> list[dict]:
        """
        List all active VastAI instances.

        Returns:
            List of instance info dicts
        """
        try:
            resp = await self.client.get("/instances/")
            resp.raise_for_status()
            data = resp.json()
            instances = data.get("instances", [])
            return instances if isinstance(instances, list) else []
        except httpx.HTTPError as e:
            logger.error(f"Failed to list instances: {e}")
            return []

    def get_gpu_for_tier(self, tier: str) -> Optional[str]:
        """
        Get the VastAI GPU name for a subscription tier.

        Args:
            tier: Subscription tier ("creator", "pro", "studio")

        Returns:
            GPU name string or None if invalid tier
        """
        gpu = TIER_GPU_MAP.get(tier)
        if not gpu:
            logger.error(f"Unknown tier: {tier}. Valid tiers: {list(TIER_GPU_MAP.keys())}")
        return gpu
