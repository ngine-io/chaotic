"""Chaos providers, one module per API."""

from __future__ import annotations

from chaotic.providers.base import Chaotic, RestartChaotic, Target
from chaotic.providers.cloudscale_ch import CloudscaleChChaotic
from chaotic.providers.cloudstack import CloudStackChaotic
from chaotic.providers.digitalocean import DigitaloceanChaotic
from chaotic.providers.hcloud import HcloudChaotic
from chaotic.providers.nomad import NomadChaotic
from chaotic.providers.proxmox import ProxmoxChaotic
from chaotic.providers.vultr import VultrChaotic

__all__ = [
    "Chaotic",
    "CloudStackChaotic",
    "CloudscaleChChaotic",
    "DigitaloceanChaotic",
    "HcloudChaotic",
    "NomadChaotic",
    "ProxmoxChaotic",
    "RestartChaotic",
    "Target",
    "VultrChaotic",
]
