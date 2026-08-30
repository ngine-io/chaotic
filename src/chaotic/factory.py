"""Mapping from a config ``kind`` to a provider implementation."""

from __future__ import annotations

from chaotic.errors import UnknownProviderError
from chaotic.log import log
from chaotic.providers import (
    Chaotic,
    CloudscaleChChaotic,
    CloudStackChaotic,
    DigitaloceanChaotic,
    HcloudChaotic,
    NomadChaotic,
    ProxmoxChaotic,
    VultrChaotic,
)

PROVIDERS: dict[str, type[Chaotic]] = {
    "cloudscale_ch": CloudscaleChChaotic,
    "cloudstack": CloudStackChaotic,
    "digitalocean": DigitaloceanChaotic,
    "hcloud": HcloudChaotic,
    "nomad": NomadChaotic,
    "proxmox": ProxmoxChaotic,
    "vultr": VultrChaotic,
}
"""Every supported ``kind``. Adding a provider means adding one entry here."""


class ChaoticFactory:
    """Instantiates the provider matching a config ``kind``."""

    CLOUD_CLASSES = PROVIDERS

    @classmethod
    def available(cls) -> list[str]:
        """Return all supported ``kind`` values, sorted."""
        return sorted(PROVIDERS)

    def get_instance(self, name: str) -> Chaotic:
        """Return a fresh, unconfigured provider instance.

        Raises:
            UnknownProviderError: If ``name`` is empty or not a known kind.
        """
        if not name:
            raise UnknownProviderError("Cloud name must be provided")

        try:
            provider = PROVIDERS[name]
        except KeyError as exc:
            raise UnknownProviderError(
                f"Kind '{name}' is not implemented, supported are: {', '.join(self.available())}"
            ) from exc

        log.info("Instantiate %s", name)
        return provider()
