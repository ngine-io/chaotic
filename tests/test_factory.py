"""Tests for provider lookup."""

from __future__ import annotations

import pytest

from chaotic import PROVIDERS, ChaoticFactory
from chaotic.errors import UnknownProviderError
from chaotic.providers.base import Chaotic


@pytest.mark.parametrize("kind", sorted(PROVIDERS))
def test_every_kind_yields_a_configurable_provider(kind: str) -> None:
    instance = ChaoticFactory().get_instance(kind)
    assert isinstance(instance, Chaotic)
    # No API client may have been built just by instantiating the provider.
    assert "client" not in instance.__dict__


def test_documented_kinds_are_all_registered() -> None:
    assert ChaoticFactory.available() == [
        "cloudscale_ch",
        "cloudstack",
        "digitalocean",
        "hcloud",
        "nomad",
        "proxmox",
        "vultr",
    ]


def test_unknown_kind_lists_the_supported_ones() -> None:
    with pytest.raises(UnknownProviderError, match="Kind 'aws' is not implemented, supported are: cloudscale_ch"):
        ChaoticFactory().get_instance("aws")


@pytest.mark.parametrize("name", ["", None])
def test_missing_kind_is_rejected(name: str) -> None:
    with pytest.raises(UnknownProviderError, match="Cloud name must be provided"):
        ChaoticFactory().get_instance(name)


def test_instances_are_not_shared() -> None:
    factory = ChaoticFactory()
    assert factory.get_instance("vultr") is not factory.get_instance("vultr")


def test_legacy_cloud_classes_alias_still_works() -> None:
    assert ChaoticFactory.CLOUD_CLASSES is PROVIDERS
