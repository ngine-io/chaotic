"""Hetzner Cloud provider.

Requires ``HCLOUD_API_TOKEN``.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import cached_property

from hcloud import Client

from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target


class HcloudChaotic(RestartChaotic):
    """Power a random Hetzner Cloud server off and on again."""

    @cached_property
    def client(self) -> Client:
        """API client, created on first use so that importing stays side effect free."""
        return Client(token=os.getenv("HCLOUD_API_TOKEN", ""))

    def list_targets(self) -> Sequence[Target]:
        label = self.configs.get("label")
        log.info("Querying with label: %s", label)
        servers = self.client.servers.get_all(label_selector=label) or []
        return [Target(id=str(server.id), name=str(server.name), raw=server) for server in servers]

    def stop(self, target: Target) -> None:
        self.client.servers.power_off(target.raw)

    def start(self, target: Target) -> None:
        self.client.servers.power_on(target.raw)
