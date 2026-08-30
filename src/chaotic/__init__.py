"""Chaotic - Chaos for Clouds.

Public API::

    from chaotic import ChaoticFactory, load_config

    config = load_config("config.yaml")
    chaos = ChaoticFactory().get_instance(config.kind)
    chaos.configure(configs=config.configs, dry_run=config.dry_run, excludes=config.excludes)
    chaos.action()
"""

from __future__ import annotations

from chaotic.config import ChaosConfig, load_config
from chaotic.errors import ChaoticError, ConfigError, UnknownProviderError
from chaotic.factory import PROVIDERS, ChaoticFactory
from chaotic.providers import (
    Chaotic,
    CloudscaleChChaotic,
    CloudStackChaotic,
    DigitaloceanChaotic,
    HcloudChaotic,
    NomadChaotic,
    ProxmoxChaotic,
    RestartChaotic,
    Target,
    VultrChaotic,
)
from chaotic.version import __version__

__all__ = [
    "PROVIDERS",
    "ChaosConfig",
    "Chaotic",
    "ChaoticError",
    "ChaoticFactory",
    "CloudStackChaotic",
    "CloudscaleChChaotic",
    "ConfigError",
    "DigitaloceanChaotic",
    "HcloudChaotic",
    "NomadChaotic",
    "ProxmoxChaotic",
    "RestartChaotic",
    "Target",
    "UnknownProviderError",
    "VultrChaotic",
    "__version__",
    "load_config",
]
