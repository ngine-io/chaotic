"""Vultr provider.

Requires ``VULTR_API_KEY``. Vultr has no maintained Python SDK, so this module
ships a thin client over the v2 REST API.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import cached_property
from typing import Any

import requests

from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target

VULTR_API_URL = "https://api.vultr.com/v2"
API_TIMEOUT_SECONDS = 10


class Vultr:
    """Minimal client for the Vultr v2 API."""

    def __init__(self, api_key: str, api_url: str = VULTR_API_URL) -> None:
        self.api_key = api_key
        self.api_url = api_url

    def query_api(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Send a request and raise on any non-2xx response."""
        response = requests.request(
            method=method,
            url=f"{self.api_url}/{path}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            params=params,
            json=json,
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response

    def list_instances(self, tag: str | None = None, label: str | None = None) -> list[dict[str, Any]]:
        response = self.query_api("get", "instances", params={"tag": tag, "label": label})
        instances: list[dict[str, Any]] = response.json().get("instances", [])
        return instances

    def halt_instances(self, instance_ids: Sequence[str]) -> None:
        self.query_api("post", "instances/halt", json={"instance_ids": list(instance_ids)})

    def halt_instance(self, instance_id: str) -> None:
        self.halt_instances(instance_ids=[instance_id])

    def start_instance(self, instance_id: str) -> None:
        self.query_api("post", f"instances/{instance_id}/start")


class VultrChaotic(RestartChaotic):
    """Halt and start a random Vultr instance."""

    @cached_property
    def client(self) -> Vultr:
        """API client, created on first use so that importing stays side effect free."""
        return Vultr(api_key=os.getenv("VULTR_API_KEY", ""))

    def list_targets(self) -> Sequence[Target]:
        tag = self.configs.get("tag")
        log.info("Querying with tag: %s", tag)
        instances = self.client.list_instances(tag=tag)
        return [Target(id=instance["id"], name=instance["label"], raw=instance) for instance in instances]

    def stop(self, target: Target) -> None:
        self.client.halt_instance(target.id)

    def start(self, target: Target) -> None:
        self.client.start_instance(target.id)
