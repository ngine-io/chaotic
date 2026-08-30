"""Tests for the Proxmox provider."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from chaotic.errors import ConfigError
from chaotic.providers.proxmox import ProxmoxChaotic, _tags
from tests.conftest import make_provider


def vm(name: str, **overrides: Any) -> dict[str, Any]:
    return {
        "vmid": 100,
        "name": name,
        "node": "pve1",
        "type": "qemu",
        "status": "running",
        **overrides,
    }


def proxmox_client(vms: list[dict[str, Any]], uptime: int = 999999) -> MagicMock:
    """A client whose `nodes(...).qemu|lxc(...).status` chain is a single mock."""
    client = MagicMock()
    client.cluster.resources.get.return_value = vms
    client.nodes.return_value.qemu.return_value.status.current.get.return_value = {"uptime": uptime}
    client.nodes.return_value.lxc.return_value.status.current.get.return_value = {"uptime": uptime}
    return client


def status_of(client: MagicMock, vm_type: str = "qemu") -> Any:
    guest = client.nodes.return_value.qemu if vm_type == "qemu" else client.nodes.return_value.lxc
    return guest.return_value.status


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({}, []),
        ({"tags": None}, []),
        ({"tags": ""}, []),
        ({"tags": "chaos-target"}, ["chaos-target"]),
        ({"tags": "a;b;c"}, ["a", "b", "c"]),
        ({"tags": "a;;b"}, ["a", "b"]),
    ],
)
def test_tags_parsing(raw: dict[str, Any], expected: list[str]) -> None:
    assert _tags(raw) == expected


def test_restarts_a_qemu_vm(no_sleep: list[float]) -> None:
    client = proxmox_client([vm("web-1")])
    provider = make_provider(ProxmoxChaotic, client, wait_before_restart=4)

    provider.action()

    status = status_of(client)
    status.shutdown.post.assert_called_once_with(forceStop=1)
    status.start.post.assert_called_once_with()
    assert no_sleep == [4]


def test_restarts_an_lxc_container(no_sleep: list[float]) -> None:
    client = proxmox_client([vm("ct-1", type="lxc")])
    make_provider(ProxmoxChaotic, client).action()

    status = status_of(client, "lxc")
    status.shutdown.post.assert_called_once_with(forceStop=1)
    status.start.post.assert_called_once_with()


def test_only_running_vms_are_candidates(caplog: pytest.LogCaptureFixture) -> None:
    client = proxmox_client([vm("stopped", status="stopped")])
    make_provider(ProxmoxChaotic, client).action()

    status_of(client).shutdown.post.assert_not_called()
    assert "No VMs found" in caplog.text


def test_filter_tag_selects_only_matching_vms(no_sleep: list[float]) -> None:
    client = proxmox_client([vm("untagged"), vm("tagged", tags="chaos-target")])
    provider = make_provider(ProxmoxChaotic, client, filter_tag="chaos-target")

    assert [target.name for target in provider.list_targets()] == ["tagged"]


def test_skip_tag_wins_over_filter_tag() -> None:
    client = proxmox_client([vm("both", tags="chaos-target;chaos-skip")])
    provider = make_provider(ProxmoxChaotic, client, filter_tag="chaos-target", skip_tag="chaos-skip")

    assert provider.list_targets() == []


def test_denylist_excludes_by_name() -> None:
    client = proxmox_client([vm("keep-me"), vm("db-1")])
    provider = make_provider(ProxmoxChaotic, client, denylist=["db-1"])

    assert [target.name for target in provider.list_targets()] == ["keep-me"]


def test_empty_cluster_resources() -> None:
    client = proxmox_client([])
    client.cluster.resources.get.return_value = None
    assert make_provider(ProxmoxChaotic, client).list_targets() == []


def test_min_uptime_spares_young_vms(caplog: pytest.LogCaptureFixture, no_sleep: list[float]) -> None:
    client = proxmox_client([vm("fresh")], uptime=10 * 60)
    provider = make_provider(ProxmoxChaotic, client, min_uptime=60)

    provider.action()

    status_of(client).shutdown.post.assert_not_called()
    assert "uptime 10.00 min is below the required 60 min" in caplog.text
    assert no_sleep == []


def test_min_uptime_allows_old_enough_vms(no_sleep: list[float]) -> None:
    client = proxmox_client([vm("old")], uptime=120 * 60)
    provider = make_provider(ProxmoxChaotic, client, min_uptime=60)

    provider.action()

    status_of(client).shutdown.post.assert_called_once_with(forceStop=1)


def test_without_min_uptime_the_api_is_not_queried() -> None:
    client = proxmox_client([vm("web-1")])
    provider = make_provider(ProxmoxChaotic, client)

    assert provider.skip_reason(provider.list_targets()[0]) is None
    status_of(client).current.get.assert_not_called()


def test_dry_run_never_touches_the_api(no_sleep: list[float]) -> None:
    client = proxmox_client([vm("web-1")])
    provider = ProxmoxChaotic()
    provider.__dict__["client"] = client
    provider.configure(dry_run=True)

    provider.action()

    status_of(client).shutdown.post.assert_not_called()
    status_of(client).start.post.assert_not_called()


# --------------------------------------------------------------------------- #
# Client construction and credential validation
# --------------------------------------------------------------------------- #
@pytest.fixture
def captured_api(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    created: dict[str, Any] = {}
    monkeypatch.setattr(
        "chaotic.providers.proxmox.ProxmoxAPI",
        lambda **kwargs: created.update(kwargs) or MagicMock(),
    )
    monkeypatch.setenv("PROXMOX_API_HOST", "pve1.example.com")
    return created


def test_token_auth(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_USER", "api@pam!chaotic")
    monkeypatch.setenv("PROXMOX_API_TOKEN", "token-value")

    assert ProxmoxChaotic().client is not None
    assert captured_api["user"] == "api@pam"
    assert captured_api["token_name"] == "chaotic"
    assert captured_api["token_value"] == "token-value"
    assert captured_api["password"] is None


def test_password_auth(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_USER", "root@pam")
    monkeypatch.setenv("PROXMOX_API_PASSWORD", "hunter2")

    assert ProxmoxChaotic().client is not None
    assert captured_api["user"] == "root@pam"
    assert captured_api["password"] == "hunter2"
    assert captured_api["token_name"] is None
    assert captured_api["token_value"] is None


def test_password_auth_is_the_default_user(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_PASSWORD", "hunter2")
    assert ProxmoxChaotic().client is not None
    assert captured_api["user"] == "root@pam"


def test_token_auth_requires_a_token(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_USER", "api@pam!chaotic")
    with pytest.raises(ConfigError, match="PROXMOX_API_TOKEN must be set"):
        _ = ProxmoxChaotic().client


def test_token_auth_rejects_a_password(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_USER", "api@pam!chaotic")
    monkeypatch.setenv("PROXMOX_API_TOKEN", "token-value")
    monkeypatch.setenv("PROXMOX_API_PASSWORD", "hunter2")
    with pytest.raises(ConfigError, match="PROXMOX_API_PASSWORD must NOT be set"):
        _ = ProxmoxChaotic().client


def test_password_auth_requires_a_password(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_USER", "root@pam")
    with pytest.raises(ConfigError, match="PROXMOX_API_PASSWORD must be set"):
        _ = ProxmoxChaotic().client


def test_password_auth_rejects_a_token(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_USER", "root@pam")
    monkeypatch.setenv("PROXMOX_API_PASSWORD", "hunter2")
    monkeypatch.setenv("PROXMOX_API_TOKEN", "token-value")
    with pytest.raises(ConfigError, match="PROXMOX_API_TOKEN must NOT be set"):
        _ = ProxmoxChaotic().client


@pytest.mark.parametrize(("value", "expected"), [(None, False), ("", False), ("1", True), ("true", True)])
def test_verify_ssl_is_plain_truthiness(
    monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any], value: str | None, expected: bool
) -> None:
    # Documented quirk kept for backwards compatibility: any non-empty value,
    # including "false", enables certificate verification.
    monkeypatch.setenv("PROXMOX_API_PASSWORD", "hunter2")
    if value is not None:
        monkeypatch.setenv("PROXMOX_API_VERIFY_SSL", value)

    assert ProxmoxChaotic().client is not None
    assert captured_api["verify_ssl"] is expected


def test_client_is_built_only_once(monkeypatch: pytest.MonkeyPatch, captured_api: dict[str, Any]) -> None:
    monkeypatch.setenv("PROXMOX_API_PASSWORD", "hunter2")
    provider = ProxmoxChaotic()
    assert provider.client is provider.client
