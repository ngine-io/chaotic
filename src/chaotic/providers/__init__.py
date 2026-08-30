"""Chaos providers, one module per API."""

from chaotic.providers.base import Chaotic
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
    "VultrChaotic",
]
