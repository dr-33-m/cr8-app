"""
VastAI API client — pure HTTP calls only. No waiting/polling loops live here
(that's orchestrator.py's job, driven by the stuck/ceiling policy in
ProvisioningConfig) — this module's job is exactly what one HTTP call can do,
nothing more, so its behavior is trivial to reason about and mock in tests.

Renamed/split from the legacy app/services/vastai_service.py: wait_for_ready's
timeout loop moved to orchestrator.py; everything else here is materially the
same API surface, made a bit more resilient (search_offers now retries
transient failures instead of returning an empty list on the first hiccup).
"""

import logging
from typing import Optional

import httpx
import asyncssh

from ..config import DeploymentConfig, TIER_GPU_MAP
from .config import ProvisioningConfig
from .retry import retry_with_backoff

logger = logging.getLogger(__name__)

BASE_URL = "https://console.vast.ai/api/v0"


class VastAIClient:
    """Thin async wrapper over the VastAI REST API."""

    def __init__(self):
        config = DeploymentConfig.get()
        self.config = config
        self.provisioning_config = ProvisioningConfig.get()
        self.client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {config.VASTAI_API_KEY}"},
            timeout=30.0,
        )

        # Ephemeral Ed25519 SSH keypair for this engine session — smaller/faster
        # than RSA, accepted by all modern OpenSSH versions.
        self._ssh_key = asyncssh.generate_private_key("ssh-ed25519", comment="cr8-engine")
        self._ssh_pubkey = self._ssh_key.export_public_key().decode()
        logger.info("VastAI client initialized (REST API, ephemeral SSH key generated)")

    @property
    def ssh_private_key(self) -> asyncssh.SSHKey:
        return self._ssh_key

    async def close(self):
        await self.client.aclose()

    async def search_offers(
        self, gpu_name: str, num_gpus: int = 1, machine_ids: Optional[list[int]] = None
    ) -> list[dict]:
        """Search for available GPU offers, cheapest first. Retries transient
        failures (network blips, 5xx) — a genuinely empty result is not retried,
        it's a real answer.

        machine_ids: when given, scopes the search to these specific physical
        hosts only (the fast-launch ledger's "try known-fast machines first"
        path) — geolocation is skipped in that case, since a specific machine
        is already a stronger signal than its country. Otherwise applies the
        configured geolocation filter (two-letter country codes — confirmed
        against VastAI's own API docs; there is no continent-level "EU"
        literal) when ProvisioningConfig.ALLOWED_GEOLOCATIONS is non-empty."""

        query: dict = {
            "gpu_name": {"in": [gpu_name]},
            "num_gpus": {"gte": num_gpus},
            "reliability": {"gte": 0.95},
            "verified": {"eq": True},
            "rentable": {"eq": True},
            "type": "ondemand",
            "limit": 10,
        }
        if machine_ids:
            query["machine_id"] = {"in": machine_ids}
        elif self.provisioning_config.ALLOWED_GEOLOCATIONS:
            query["geolocation"] = {"in": self.provisioning_config.ALLOWED_GEOLOCATIONS}

        async def _do_search() -> list[dict]:
            resp = await self.client.post("/bundles/", json=query)
            resp.raise_for_status()
            return resp.json().get("offers", [])

        try:
            offers = await retry_with_backoff(
                _do_search,
                max_attempts=self.provisioning_config.OFFER_SEARCH_MAX_ATTEMPTS,
                base_delay=self.provisioning_config.OFFER_SEARCH_BASE_DELAY_SECONDS,
                retry_on=(httpx.HTTPError,),
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to search VastAI offers after retries: {e}")
            return []

        offers.sort(key=lambda o: o.get("dph_total", float("inf")))
        logger.info(f"Found {len(offers)} offers for {gpu_name}")
        return offers

    async def accept_offer(self, offer_id: int, template_hash_id: str, disk_gb: int) -> Optional[int]:
        """Accept a single offer. Returns the new instance id, or None (including
        on 'invalid template hash' — a config error the caller should treat as
        fatal, not retry against other offers)."""
        try:
            resp = await self.client.put(
                f"/asks/{offer_id}/", json={"template_hash_id": template_hash_id, "disk": disk_gb}
            )
            resp.raise_for_status()
            result = resp.json()
            instance_id = result.get("new_contract")
            if instance_id:
                logger.info(f"VastAI instance launched: id={int(instance_id)}")
                return int(instance_id)
            logger.warning(f"No instance ID in response for offer {offer_id}: {result}")
            return None
        except httpx.HTTPStatusError as e:
            body = e.response.text
            if "invalid template hash" in body or "template not accessible" in body:
                logger.error(
                    f"VASTAI_TEMPLATE_HASH_ID '{template_hash_id}' is invalid. "
                    f"Update it in .env after editing the VastAI template."
                )
                raise
            if e.response.status_code == 429:
                logger.warning("Rate limited by VastAI")
                raise
            logger.warning(f"Offer {offer_id} rejected: {body}")
            return None

    async def attach_ssh_key(self, instance_id: int) -> bool:
        """Must be called AFTER the instance is actually running — VastAI only
        applies the key to a live container."""
        logger.info(f"Attaching SSH key to instance {instance_id}")
        try:
            resp = await self.client.post(f"/instances/{instance_id}/ssh/", json={"ssh_key": self._ssh_pubkey})
            resp.raise_for_status()
            logger.info(f"SSH key attached to instance {instance_id}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to attach SSH key to instance {instance_id}: {e}")
            return False

    async def get_instance_info(self, instance_id: int) -> Optional[dict]:
        """Returns the raw instance dict (including actual_status/cur_state/
        intended_status/next_state), or None if not found/on error.

        A destroyed instance does NOT 404 here — VastAI returns 200 with
        `{"instances": null}`. That must map to None (not-found), which the
        original `data.get("instances") if isinstance(..., dict) else data`
        got backwards: when `instances` is present but null, it fell through
        to returning the outer response dict itself (no `actual_status` key,
        so every downstream `is_terminal`/confirm check saw a permanently
        ambiguous "actual_status=None" instead of a clean not-found signal —
        this was the direct cause of teardown intents that never confirmed
        even after the instance was already gone on VastAI's side)."""
        try:
            resp = await self.client.get(f"/instances/{instance_id}/")
            resp.raise_for_status()
            data = resp.json()
            if "instances" in data:
                instance = data["instances"]
                # Guard against both {"instances": null} (observed in
                # production for a destroyed instance) and a theoretical
                # {"instances": {}} — neither documented explicitly by VastAI,
                # so treat anything that isn't a genuinely populated dict as
                # not-found rather than assuming one specific empty shape.
                return instance if isinstance(instance, dict) and instance else None
            # Some VastAI responses put the instance fields at the top level
            # instead of nesting under "instances" — only fall back to the
            # raw payload in that shape, never when "instances" was present-but-null.
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Failed to get instance info for {instance_id}: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"Failed to get instance info for {instance_id}: {e}")
            return None

    async def recycle_instance(self, instance_id: int) -> bool:
        """Destroys and recreates the container in place, keeping the GPU slot."""
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
        """Best-effort single call — callers must NOT treat a False/exception
        here as 'the instance is gone'. The teardown worker is the only code
        path allowed to conclude that, and only after re-polling get_instance_info
        until the instance is confirmed terminal or 404."""
        logger.info(f"Destroying VastAI instance {instance_id}")
        try:
            resp = await self.client.delete(f"/instances/{instance_id}/")
            resp.raise_for_status()
            logger.info(f"VastAI instance {instance_id} destroy requested")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Already gone — treat as success for the caller's purposes.
                return True
            logger.error(f"Failed to destroy instance {instance_id}: {e}")
            return False
        except httpx.HTTPError as e:
            logger.error(f"Failed to destroy instance {instance_id}: {e}")
            return False

    async def list_instances(self) -> list[dict]:
        """Full list of this account's active instances — the reconciler's
        ground truth for diffing against local state."""
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
        gpu = TIER_GPU_MAP.get(tier)
        if not gpu:
            logger.error(f"Unknown tier: {tier}. Valid tiers: {list(TIER_GPU_MAP.keys())}")
        return gpu
