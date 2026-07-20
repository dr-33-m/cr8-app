"""
VastAIClient.get_instance_info parsing tests — no network, mocked httpx
responses. Regression coverage for a real production incident: a destroyed
instance's GET returns 200 with `{"instances": null}`, not a 404, and the
original parsing fell through to returning the whole outer response dict
instead of None — which meant the teardown worker's "not found = confirm
absent" check never fired, even though the instance was already gone.

Run:  venv/bin/python -m pytest tests/test_provisioning_vastai_client.py -v
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.provisioning.config import ProvisioningConfig
from app.services.provisioning.vastai_client import VastAIClient


def make_client_with_mocked_get(json_body, status_code=200):
    client = object.__new__(VastAIClient)  # skip __init__ (no real HTTP client/SSH key needed)
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_body
    if status_code >= 400:
        response.raise_for_status.side_effect = httpx.HTTPStatusError("error", request=MagicMock(), response=response)
    else:
        response.raise_for_status.return_value = None
    client.client = MagicMock()
    client.client.get = AsyncMock(return_value=response)
    return client


class TestGetInstanceInfoParsing:
    async def test_destroyed_instance_returns_none_not_the_outer_dict(self):
        """The exact production shape: 200 OK, {"instances": null}."""
        client = make_client_with_mocked_get({"instances": None})
        result = await client.get_instance_info(123)
        assert result is None

    async def test_empty_instances_dict_also_returns_none(self):
        """VastAI's not-found shape isn't explicitly documented — defend
        against {"instances": {}} too, not just {"instances": null}."""
        client = make_client_with_mocked_get({"instances": {}})
        result = await client.get_instance_info(123)
        assert result is None

    async def test_healthy_instance_returns_the_nested_dict(self):
        client = make_client_with_mocked_get({"instances": {"id": 123, "actual_status": "running"}})
        result = await client.get_instance_info(123)
        assert result == {"id": 123, "actual_status": "running"}

    async def test_flat_shape_response_falls_back_to_the_whole_payload(self):
        """Some VastAI endpoints put fields at the top level with no
        'instances' key at all — that's a different shape than 'instances': null
        and should still work."""
        client = make_client_with_mocked_get({"id": 123, "actual_status": "running"})
        result = await client.get_instance_info(123)
        assert result == {"id": 123, "actual_status": "running"}

    async def test_404_returns_none(self):
        client = make_client_with_mocked_get({}, status_code=404)
        result = await client.get_instance_info(123)
        assert result is None


def make_client_with_mocked_post(allowed_geolocations=None):
    """search_offers reads self.provisioning_config directly — __init__ is
    skipped (no real HTTP client/SSH key needed), so it must be set by hand."""
    client = object.__new__(VastAIClient)
    ProvisioningConfig.reset()
    config = ProvisioningConfig.get()
    if allowed_geolocations is not None:
        config.ALLOWED_GEOLOCATIONS = allowed_geolocations
    client.provisioning_config = config

    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"offers": []}
    client.client = MagicMock()
    client.client.post = AsyncMock(return_value=response)
    return client


class TestGeolocationFilter:
    async def test_configured_country_list_is_applied(self):
        client = make_client_with_mocked_post(allowed_geolocations=["DE", "NL", "PL"])
        await client.search_offers("RTX 3090")

        sent_body = client.client.post.call_args.kwargs["json"]
        assert sent_body["geolocation"] == {"in": ["DE", "NL", "PL"]}

    async def test_empty_allowed_list_disables_the_filter(self):
        client = make_client_with_mocked_post(allowed_geolocations=[])
        await client.search_offers("RTX 3090")

        sent_body = client.client.post.call_args.kwargs["json"]
        assert "geolocation" not in sent_body

    async def test_machine_ids_filter_takes_precedence_over_geolocation(self):
        """A specific-machine search (the fast-launch ledger's first try) is a
        stronger signal than the machine's country — geolocation is skipped
        entirely rather than redundantly (and possibly conflictingly) applied."""
        client = make_client_with_mocked_post(allowed_geolocations=["DE"])
        await client.search_offers("RTX 3090", machine_ids=[111, 222])

        sent_body = client.client.post.call_args.kwargs["json"]
        assert sent_body["machine_id"] == {"in": [111, 222]}
        assert "geolocation" not in sent_body
