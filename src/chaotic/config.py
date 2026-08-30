"""Loading and validating a chaos plan.

A plan is a small YAML or JSON document that can live on disk or behind an HTTP
endpoint::

    kind: proxmox
    dry_run: false
    configs:
      filter_tag: chaos-target
    excludes:
      weekdays: [Sat, Sun]

Loading is deliberately separated from running so that a bad plan fails with a
precise message before any cloud API is touched.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv

from chaotic.errors import ConfigError

DEFAULT_CONFIG_SOURCE = "config.yaml"
"""Config source used when neither ``--config`` nor ``$CHAOTIC_CONFIG`` is set."""

HTTP_TIMEOUT_SECONDS = 30
"""Timeout for fetching a remote config, so a hung endpoint cannot wedge a run."""

YAML_SUFFIXES = (".yaml", ".yml")
JSON_SUFFIXES = (".json",)


def load_env(dotenv_path: str | Path = ".env") -> None:
    """Load a ``.env`` file into the process environment, if one exists.

    Existing environment variables always win over the file.
    """
    load_dotenv(dotenv_path=Path(dotenv_path))


@dataclass(frozen=True, slots=True)
class ChaosConfig:
    """A validated chaos plan."""

    kind: str
    """Provider to run, e.g. ``proxmox`` or ``nomad``."""

    dry_run: bool = False
    """When true, log the intended action but never call a mutating API."""

    configs: Mapping[str, Any] = field(default_factory=dict)
    """Provider specific settings."""

    excludes: Mapping[str, Any] = field(default_factory=dict)
    """Time windows that downgrade a run to a dry-run, see :mod:`chaotic.excludes`."""

    @classmethod
    def from_mapping(cls, raw: Any) -> ChaosConfig:
        """Build a config from a parsed document.

        Raises:
            ConfigError: If the document is empty, not a mapping, or misses ``kind``.
        """
        if not raw:
            raise ConfigError("Empty config")

        if not isinstance(raw, Mapping):
            raise ConfigError(f"Config must be a mapping, got {type(raw).__name__}")

        kind = raw.get("kind")
        if not kind:
            raise ConfigError("No kind defined in config")

        return cls(
            kind=str(kind),
            dry_run=bool(raw.get("dry_run") or False),
            configs=raw.get("configs") or {},
            excludes=raw.get("excludes") or {},
        )


def _parse(text: str, *, prefer_json: bool) -> Any:
    """Parse a config document.

    YAML is a superset of JSON, so :func:`yaml.safe_load` handles both; the
    ``prefer_json`` hint only exists to produce better error messages.
    """
    try:
        if prefer_json:
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise ConfigError(f"Could not parse config: {exc}") from exc


def _load_remote(url: str, timeout: float) -> Any:
    try:
        response = requests.get(url=url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ConfigError(f"Could not fetch config from {url}: {exc}") from exc

    content_type = response.headers.get("Content-Type", "")
    prefer_json = "json" in content_type or url.endswith(JSON_SUFFIXES)
    return _parse(response.text, prefer_json=prefer_json)


def _load_file(source: str) -> Any:
    path = Path(source)
    suffix = path.suffix.lower()
    if suffix not in YAML_SUFFIXES + JSON_SUFFIXES:
        supported = ", ".join(YAML_SUFFIXES + JSON_SUFFIXES)
        raise ConfigError(f"Unsupported config file {source!r}, expected one of: {supported}")

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"Could not read config file {source!r}: {exc}") from exc

    return _parse(text, prefer_json=suffix in JSON_SUFFIXES)


def load_config(source: str, timeout: float = HTTP_TIMEOUT_SECONDS) -> ChaosConfig:
    """Load a chaos plan from a file path or an ``http(s)://`` URL.

    Raises:
        ConfigError: For anything that makes the plan unusable.
    """
    is_remote = source.startswith(("http://", "https://"))
    raw = _load_remote(source, timeout=timeout) if is_remote else _load_file(source)
    return ChaosConfig.from_mapping(raw)
