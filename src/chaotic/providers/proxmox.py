"""Proxmox VE provider.

Requires ``PROXMOX_API_HOST`` plus one of two authentication styles:

* user and password: ``PROXMOX_API_USER=root@pam`` and ``PROXMOX_API_PASSWORD``
* API token: ``PROXMOX_API_USER=api@pam!myTokenName`` and ``PROXMOX_API_TOKEN``
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from functools import cached_property
from typing import Any

from proxmoxer import ProxmoxAPI

from chaotic.errors import ConfigError
from chaotic.log import log
from chaotic.providers.base import RestartChaotic, Target

LXC_TYPE = "lxc"
RUNNING_STATUS = "running"
TAG_SEPARATOR = ";"


def _tags(vm: dict[str, Any]) -> list[str]:
    """Split a Proxmox resource's ``tags`` field into a list."""
    return [tag for tag in (vm.get("tags") or "").split(TAG_SEPARATOR) if tag]


class ProxmoxChaotic(RestartChaotic):
    """Shut down and start a random running VM or container."""

    target_noun = "VM"

    @cached_property
    def client(self) -> ProxmoxAPI:
        """API client, created on first use so that importing stays side effect free."""
        return self._build_client()

    def _build_client(self) -> ProxmoxAPI:
        host = os.getenv("PROXMOX_API_HOST", "")
        if not host:
            raise ConfigError("PROXMOX_API_HOST must be set")
        user = os.getenv("PROXMOX_API_USER", "root@pam")
        token = os.getenv("PROXMOX_API_TOKEN", "")
        password = os.getenv("PROXMOX_API_PASSWORD", "")
        # Note: this is truthiness on the raw string, so *any* non-empty value —
        # including "false" — enables verification. Kept as-is for backwards
        # compatibility with existing deployments.
        verify_ssl = bool(os.getenv("PROXMOX_API_VERIFY_SSL", ""))

        if "!" in user:
            log.info("Using API token authentication")
            if not token:
                raise ConfigError("PROXMOX_API_TOKEN must be set when using token authentication")
            if password:
                raise ConfigError("PROXMOX_API_PASSWORD must NOT be set when using token authentication")
            api_user, _, token_name = user.partition("!")
            if not token_name:
                raise ConfigError(
                    "PROXMOX_API_USER must include a token name after '!' when using token authentication"
                )
        else:
            log.info("Using user/password authentication")
            if not password:
                raise ConfigError("PROXMOX_API_PASSWORD must be set when not using token authentication")
            if token:
                raise ConfigError("PROXMOX_API_TOKEN must NOT be set when not using token authentication")
            api_user, token_name = user, ""
        log.info("Proxmox host: %s", host)
        log.info("Proxmox user: %s", api_user)
        log.info("Proxmox verify SSL: %s", verify_ssl)
        log.info("Connecting to Proxmox API")

        return ProxmoxAPI(
            host=host,
            user=api_user,
            password=password or None,
            token_name=token_name or None,
            token_value=token or None,
            verify_ssl=verify_ssl,
        )

    def _status(self, vm: dict[str, Any]) -> Any:
        """Return the ``status`` endpoint for a VM, regardless of its type."""
        node = self.client.nodes(vm["node"])
        guest = node.lxc(vm["vmid"]) if vm["type"] == LXC_TYPE else node.qemu(vm["vmid"])
        return guest.status

    def list_targets(self) -> Sequence[Target]:
        denylist = self.configs.get("denylist") or []
        skip_tag = self.configs.get("skip_tag")
        filter_tag = self.configs.get("filter_tag")

        targets: list[Target] = []
        for vm in self.client.cluster.resources.get(type="vm") or []:
            tags = _tags(vm)

            if filter_tag and filter_tag not in tags:
                log.debug(
                    "VM %s does not have filter_tag '%s', skipping",
                    vm["name"],
                    filter_tag,
                )
                continue
            if vm["status"] != RUNNING_STATUS:
                log.debug("VM %s not running, skipping", vm["name"])
                continue
            if vm["name"] in denylist:
                log.debug("VM %s in denylist, skipping", vm["name"])
                continue
            if skip_tag and skip_tag in tags:
                log.debug("VM %s has skip_tag '%s', skipping", vm["name"], skip_tag)
                continue

            targets.append(Target(id=str(vm["vmid"]), name=vm["name"], raw=vm))

        return targets

    def skip_reason(self, target: Target) -> str | None:
        """Spare VMs that have not been up for ``min_uptime`` minutes yet."""
        min_uptime = self.configs.get("min_uptime")
        if min_uptime is None:
            return None

        log.debug("VM info: %s", target.raw)
        uptime = self._status(target.raw).current.get()["uptime"]
        if uptime < min_uptime * 60:
            return f"uptime {uptime / 60:.2f} min is below the required {min_uptime} min"
        return None

    def stop(self, target: Target) -> None:
        self._status(target.raw).shutdown.post(forceStop=1)

    def start(self, target: Target) -> None:
        self._status(target.raw).start.post()
