"""Tests for the package surface and the shipped example configs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import chaotic
from chaotic import PROVIDERS, ChaosConfig
from chaotic.version import __version__

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted((REPO_ROOT / "examples").glob("*.yaml"))


def test_version_is_exported() -> None:
    assert chaotic.__version__ == __version__


def test_public_api_is_importable() -> None:
    for name in chaotic.__all__:
        assert hasattr(chaotic, name), name


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_configs_are_valid(path: Path) -> None:
    config = ChaosConfig.from_mapping(yaml.safe_load(path.read_text(encoding="utf-8")))
    assert config.kind in PROVIDERS


def test_every_provider_has_an_example() -> None:
    kinds = {ChaosConfig.from_mapping(yaml.safe_load(p.read_text(encoding="utf-8"))).kind for p in EXAMPLES}
    assert kinds == set(PROVIDERS)


def test_docker_default_config_is_a_dry_run() -> None:
    raw = yaml.safe_load((REPO_ROOT / "docker" / "config.yaml").read_text(encoding="utf-8"))
    assert raw["dry_run"] is True


def test_module_entry_point_reports_the_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "chaotic", "--version"],
        capture_output=True,
        text=True,
        check=True,
        cwd=REPO_ROOT,
    )
    assert __version__ in result.stdout
