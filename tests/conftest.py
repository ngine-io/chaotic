"""Shared fixtures.

The tests never talk to a real API: every provider exposes a lazily built
``client`` :func:`functools.cached_property`, and priming ``instance.__dict__``
replaces it with a fake before the real constructor ever runs.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest

from chaotic.providers.base import Chaotic


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the developer's own environment out of the tests."""
    for name in (
        "CHAOTIC_CONFIG",
        "CHAOTIC_INTERVAL",
        "CHAOTIC_LOG_CONFIG",
        "CHAOTIC_LOG_LEVEL",
        "CLOUDSCALE_API_TOKEN",
        "CLOUDSTACK_API_ENDPOINT",
        "CLOUDSTACK_API_KEY",
        "CLOUDSTACK_API_SECRET",
        "HCLOUD_API_TOKEN",
        "NOMAD_ADDR",
        "NOMAD_HTTP_AUTH",
        "NOMAD_TOKEN",
        "PROXMOX_API_HOST",
        "PROXMOX_API_PASSWORD",
        "PROXMOX_API_TOKEN",
        "PROXMOX_API_USER",
        "PROXMOX_API_VERIFY_SSL",
        "VULTR_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def _capture_logs(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Make chaotic's log output available to every test via ``caplog``."""
    with caplog.at_level(logging.DEBUG, logger="chaotic"):
        yield


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Replace :func:`time.sleep` in the provider base and record the durations."""
    slept: list[float] = []
    monkeypatch.setattr("chaotic.providers.base.time.sleep", slept.append)
    return slept


def recorded_request_kwargs(call: Any) -> dict[str, Any]:
    """Return the kwargs `responses` attached to a recorded call, e.g. its timeout."""
    return dict(getattr(call.request, "req_kwargs"))  # noqa: B009


def make_provider(cls: type[Chaotic], client: Any = None, **configs: Any) -> Any:
    """Build a configured provider with its API client replaced by a fake."""
    provider = cls()
    if client is not None:
        provider.__dict__["client"] = client
    provider.configure(configs=configs)
    return provider
