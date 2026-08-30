"""Tests for the providers built on top of RestartChaotic.

Each one is exercised through the real `action()` template so that both the
target listing and the stop/start calls are covered.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from chaotic.providers.cloudscale_ch import CloudscaleChChaotic
from chaotic.providers.cloudstack import CloudStackChaotic
from chaotic.providers.digitalocean import DigitaloceanChaotic
from chaotic.providers.hcloud import HcloudChaotic
from tests.conftest import make_provider

pytestmark = pytest.mark.usefixtures("no_sleep")


# --------------------------------------------------------------------------- #
# cloudscale.ch
# --------------------------------------------------------------------------- #
def cloudscale_client(servers: list[dict[str, str]] | None) -> MagicMock:
    client = MagicMock()
    client.server.get_all.return_value = servers
    return client


def test_cloudscale_restarts_the_selected_server() -> None:
    client = cloudscale_client([{"uuid": "uuid-1", "name": "web-1"}])
    provider = make_provider(CloudscaleChChaotic, client, filter_tag="chaos=enabled")

    provider.action()

    client.server.get_all.assert_called_once_with(filter_tag="chaos=enabled")
    client.server.stop.assert_called_once_with(uuid="uuid-1")
    client.server.start.assert_called_once_with(uuid="uuid-1")


def test_cloudscale_handles_no_servers(caplog: pytest.LogCaptureFixture) -> None:
    client = cloudscale_client(None)
    make_provider(CloudscaleChChaotic, client).action()

    client.server.stop.assert_not_called()
    assert "No servers found" in caplog.text


def test_cloudscale_client_uses_the_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDSCALE_API_TOKEN", "secret-token")
    created: dict[str, Any] = {}
    monkeypatch.setattr(
        "chaotic.providers.cloudscale_ch.Cloudscale",
        lambda **kwargs: created.update(kwargs) or MagicMock(),
    )

    assert CloudscaleChChaotic().client is not None
    assert created == {"api_token": "secret-token"}


# --------------------------------------------------------------------------- #
# CloudStack
# --------------------------------------------------------------------------- #
TAG = {"key": "chaos", "value": "enabled"}


def cloudstack_client(instances: list[dict[str, str]] | None) -> MagicMock:
    client = MagicMock()
    client.listVirtualMachines.return_value = instances
    return client


def test_cloudstack_restarts_the_selected_instance() -> None:
    client = cloudstack_client([{"id": "vm-1", "name": "app-1"}])
    provider = make_provider(CloudStackChaotic, client, tag=TAG, projectid="proj", zoneid="zone")

    provider.action()

    client.listVirtualMachines.assert_called_once_with(tags=[TAG], projectid="proj", zoneid="zone", fetch_list=True)
    client.stopVirtualMachine.assert_called_once_with(id="vm-1")
    client.startVirtualMachine.assert_called_once_with(id="vm-1")


def test_cloudstack_refuses_to_run_without_a_tag(caplog: pytest.LogCaptureFixture) -> None:
    client = cloudstack_client([{"id": "vm-1", "name": "app-1"}])
    make_provider(CloudStackChaotic, client).action()

    client.listVirtualMachines.assert_not_called()
    client.stopVirtualMachine.assert_not_called()
    assert "refusing to consider all instances" in caplog.text


def test_cloudstack_handles_no_instances(caplog: pytest.LogCaptureFixture) -> None:
    client = cloudstack_client(None)
    make_provider(CloudStackChaotic, client, tag=TAG).action()

    client.stopVirtualMachine.assert_not_called()
    assert "No servers found" in caplog.text


def test_cloudstack_client_uses_the_env_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUDSTACK_API_ENDPOINT", "https://cs.example.com/client/api")
    monkeypatch.setenv("CLOUDSTACK_API_KEY", "key")
    monkeypatch.setenv("CLOUDSTACK_API_SECRET", "secret")
    created: dict[str, Any] = {}
    monkeypatch.setattr(
        "chaotic.providers.cloudstack.CloudStack",
        lambda **kwargs: created.update(kwargs) or MagicMock(),
    )

    assert CloudStackChaotic().client is not None
    assert created == {"endpoint": "https://cs.example.com/client/api", "key": "key", "secret": "secret"}


# --------------------------------------------------------------------------- #
# DigitalOcean
# --------------------------------------------------------------------------- #
def test_digitalocean_restarts_the_selected_droplet() -> None:
    droplet = MagicMock(id=123, name="droplet-1")
    client = MagicMock()
    client.get_all_droplets.return_value = [droplet]
    provider = make_provider(DigitaloceanChaotic, client, tag="chaos:enabled")

    provider.action()

    client.get_all_droplets.assert_called_once_with(tag_name="chaos:enabled")
    droplet.shutdown.assert_called_once_with()
    droplet.power_on.assert_called_once_with()


def test_digitalocean_handles_no_droplets(caplog: pytest.LogCaptureFixture) -> None:
    client = MagicMock()
    client.get_all_droplets.return_value = []
    make_provider(DigitaloceanChaotic, client).action()

    assert "No droplets found" in caplog.text


def test_digitalocean_client_is_the_sdk_manager(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = MagicMock()
    monkeypatch.setattr("chaotic.providers.digitalocean.digitalocean.Manager", lambda: sentinel)
    assert DigitaloceanChaotic().client is sentinel


# --------------------------------------------------------------------------- #
# Hetzner Cloud
# --------------------------------------------------------------------------- #
def test_hcloud_restarts_the_selected_server() -> None:
    server = SimpleNamespace(id=42, name="node-1")
    client = MagicMock()
    client.servers.get_all.return_value = [server]
    provider = make_provider(HcloudChaotic, client, label="chaos=enabled")

    provider.action()

    client.servers.get_all.assert_called_once_with(label_selector="chaos=enabled")
    client.servers.power_off.assert_called_once_with(server)
    client.servers.power_on.assert_called_once_with(server)


def test_hcloud_handles_no_servers(caplog: pytest.LogCaptureFixture) -> None:
    client = MagicMock()
    client.servers.get_all.return_value = []
    make_provider(HcloudChaotic, client).action()

    client.servers.power_off.assert_not_called()
    assert "No servers found" in caplog.text


def test_hcloud_client_uses_the_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HCLOUD_API_TOKEN", "hc-token")
    created: dict[str, Any] = {}
    monkeypatch.setattr(
        "chaotic.providers.hcloud.Client",
        lambda **kwargs: created.update(kwargs) or MagicMock(),
    )

    assert HcloudChaotic().client is not None
    assert created == {"token": "hc-token"}
