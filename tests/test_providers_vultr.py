"""Tests for the Vultr API client and provider."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import requests
import responses

from chaotic.providers.vultr import VULTR_API_URL, Vultr, VultrChaotic
from tests.conftest import make_provider, recorded_request_kwargs

INSTANCE = {"id": "inst-1", "label": "web-1"}


@pytest.fixture
def api() -> Vultr:
    return Vultr(api_key="vultr-key")


@responses.activate
def test_list_instances_sends_key_and_filters(api: Vultr) -> None:
    responses.get(f"{VULTR_API_URL}/instances", json={"instances": [INSTANCE]})

    assert api.list_instances(tag="chaos", label="web-1") == [INSTANCE]

    request = responses.calls[0].request
    assert request.headers["Authorization"] == "Bearer vultr-key"
    assert "tag=chaos" in str(request.url)
    assert "label=web-1" in str(request.url)


@responses.activate
def test_list_instances_defaults_to_empty(api: Vultr) -> None:
    responses.get(f"{VULTR_API_URL}/instances", json={})
    assert api.list_instances() == []


@responses.activate
def test_halt_instance_posts_a_list(api: Vultr) -> None:
    responses.post(f"{VULTR_API_URL}/instances/halt", json={})
    api.halt_instance("inst-1")
    assert responses.calls[0].request.body == b'{"instance_ids": ["inst-1"]}'


@responses.activate
def test_halt_instances_accepts_many(api: Vultr) -> None:
    responses.post(f"{VULTR_API_URL}/instances/halt", json={})
    api.halt_instances(["a", "b"])
    assert responses.calls[0].request.body == b'{"instance_ids": ["a", "b"]}'


@responses.activate
def test_start_instance_targets_the_instance(api: Vultr) -> None:
    responses.post(f"{VULTR_API_URL}/instances/inst-1/start", json={})
    api.start_instance("inst-1")
    assert responses.calls[0].request.url == f"{VULTR_API_URL}/instances/inst-1/start"


@responses.activate
def test_api_errors_are_raised(api: Vultr) -> None:
    responses.get(f"{VULTR_API_URL}/instances", status=401)
    with pytest.raises(requests.HTTPError):
        api.list_instances()


@responses.activate
def test_requests_carry_a_timeout(api: Vultr) -> None:
    responses.get(f"{VULTR_API_URL}/instances", json={"instances": []})
    api.list_instances()
    assert recorded_request_kwargs(responses.calls[0])["timeout"] == 10


def test_provider_restarts_the_selected_instance(no_sleep: list[float]) -> None:
    client = MagicMock()
    client.list_instances.return_value = [INSTANCE]
    provider = make_provider(VultrChaotic, client, tag="chaos", wait_before_restart=3)

    provider.action()

    client.list_instances.assert_called_once_with(tag="chaos")
    client.halt_instance.assert_called_once_with("inst-1")
    client.start_instance.assert_called_once_with("inst-1")
    assert no_sleep == [3]


def test_provider_handles_no_instances(caplog: pytest.LogCaptureFixture) -> None:
    client = MagicMock()
    client.list_instances.return_value = []
    make_provider(VultrChaotic, client).action()

    client.halt_instance.assert_not_called()
    assert "No servers found" in caplog.text


def test_provider_client_uses_the_env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VULTR_API_KEY", "from-env")
    assert VultrChaotic().client.api_key == "from-env"
