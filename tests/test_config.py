"""Tests for loading and validating chaos plans."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests
import responses

from chaotic.config import ChaosConfig, load_config, load_env
from chaotic.errors import ConfigError
from tests.conftest import recorded_request_kwargs

PLAN = {
    "kind": "vultr",
    "dry_run": True,
    "configs": {"tag": "chaos"},
    "excludes": {"weekdays": ["Sun"]},
}


def test_from_mapping_populates_every_field() -> None:
    config = ChaosConfig.from_mapping(PLAN)
    assert config == ChaosConfig(
        kind="vultr",
        dry_run=True,
        configs={"tag": "chaos"},
        excludes={"weekdays": ["Sun"]},
    )


def test_from_mapping_applies_defaults() -> None:
    config = ChaosConfig.from_mapping({"kind": "nomad"})
    assert config.dry_run is False
    assert config.configs == {}
    assert config.excludes == {}


def test_from_mapping_normalises_nulls() -> None:
    config = ChaosConfig.from_mapping({"kind": "nomad", "dry_run": None, "configs": None, "excludes": None})
    assert config.dry_run is False
    assert config.configs == {}


def test_config_is_immutable() -> None:
    config = ChaosConfig(kind="vultr")
    with pytest.raises(AttributeError):
        config.kind = "nomad"  # type: ignore[misc]


@pytest.mark.parametrize("raw", [None, {}, ""])
def test_from_mapping_rejects_empty(raw: object) -> None:
    with pytest.raises(ConfigError, match="Empty config"):
        ChaosConfig.from_mapping(raw)


def test_from_mapping_rejects_non_mapping() -> None:
    with pytest.raises(ConfigError, match="must be a mapping, got list"):
        ChaosConfig.from_mapping(["kind: vultr"])


@pytest.mark.parametrize("raw", [{"dry_run": True}, {"kind": ""}, {"kind": None}])
def test_from_mapping_requires_kind(raw: dict[str, object]) -> None:
    with pytest.raises(ConfigError, match="No kind defined"):
        ChaosConfig.from_mapping(raw)


@pytest.mark.parametrize("suffix", [".yaml", ".yml"])
def test_load_yaml_file(tmp_path: Path, suffix: str) -> None:
    path = tmp_path / f"config{suffix}"
    path.write_text("kind: proxmox\ndry_run: true\nconfigs:\n  min_uptime: 60\n", encoding="utf-8")

    config = load_config(str(path))
    assert config.kind == "proxmox"
    assert config.dry_run is True
    assert config.configs == {"min_uptime": 60}


def test_load_json_file(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(PLAN), encoding="utf-8")

    assert load_config(str(path)).kind == "vultr"


def test_load_file_rejects_unknown_extension(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("kind = 'vultr'", encoding="utf-8")

    with pytest.raises(ConfigError, match="Unsupported config file"):
        load_config(str(path))


def test_load_file_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Could not read config file"):
        load_config(str(tmp_path / "nope.yaml"))


def test_load_file_reports_broken_yaml(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("kind: [unclosed\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="Could not parse config"):
        load_config(str(path))


def test_load_file_reports_broken_json(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ConfigError, match="Could not parse config"):
        load_config(str(path))


def test_yaml_loader_does_not_execute_python_tags(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("kind: !!python/object/apply:os.system ['echo pwned']\n", encoding="utf-8")

    with pytest.raises(ConfigError, match="Could not parse config"):
        load_config(str(path))


@responses.activate
def test_load_remote_json() -> None:
    responses.get("https://example.com/plan", json=PLAN)
    assert load_config("https://example.com/plan").kind == "vultr"


@responses.activate
def test_load_remote_yaml() -> None:
    responses.get(
        "http://example.com/plan.yaml",
        body="kind: hcloud\nconfigs:\n  label: chaos=enabled\n",
        content_type="text/yaml",
    )

    config = load_config("http://example.com/plan.yaml")
    assert config.kind == "hcloud"
    assert config.configs == {"label": "chaos=enabled"}


@responses.activate
def test_load_remote_sends_a_timeout() -> None:
    responses.get("https://example.com/plan", json=PLAN)
    load_config("https://example.com/plan", timeout=5)
    assert recorded_request_kwargs(responses.calls[0])["timeout"] == 5


@responses.activate
def test_load_remote_reports_http_errors() -> None:
    responses.get("https://example.com/plan", status=503)
    with pytest.raises(ConfigError, match="Could not fetch config"):
        load_config("https://example.com/plan")


@responses.activate
def test_load_remote_reports_connection_errors() -> None:
    responses.get("https://example.com/plan", body=requests.ConnectionError("boom"))
    with pytest.raises(ConfigError, match="Could not fetch config"):
        load_config("https://example.com/plan")


def test_load_env_reads_dotenv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHAOTIC_FIXTURE_VAR", raising=False)
    dotenv = tmp_path / ".env"
    dotenv.write_text("CHAOTIC_FIXTURE_VAR=from-dotenv\n", encoding="utf-8")

    load_env(dotenv)

    import os

    assert os.environ["CHAOTIC_FIXTURE_VAR"] == "from-dotenv"
    monkeypatch.delenv("CHAOTIC_FIXTURE_VAR", raising=False)


def test_load_env_tolerates_missing_file(tmp_path: Path) -> None:
    load_env(tmp_path / "does-not-exist.env")
