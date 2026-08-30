# Changelog

All notable changes to this project are documented here. The format is loosely
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed — behaviour

* **Nomad `node_drain_deadline_seconds` is now honoured exactly.** The deadline
  sent to Nomad was multiplied by six (`seconds * 60 * 10**8` nanoseconds), so
  `15` really meant 90 seconds. Divide any value you tuned against the old
  behaviour by six.
* **`--config` and `--interval` now win over `$CHAOTIC_CONFIG` and
  `$CHAOTIC_INTERVAL`.** Previously the environment variable overrode an
  explicitly passed flag.
* **`$CHAOTIC_INTERVAL` is implemented.** It was documented but never read.
* **`--periodic` survives failures.** A failing run is logged with a traceback
  and the schedule continues, instead of terminating the daemon. One-shot runs
  still exit `1`.
* **The `.`-per-second heartbeat is only printed to an interactive terminal**, so
  it no longer pollutes container logs.
* **Nomad's `job` experiment requires a non-empty `signals` list** and fails with
  a clear error instead of a `KeyError`. An unknown entry in `experiments` is
  likewise reported instead of raising `AttributeError`.
* **CloudStack refuses to run without a `tag`** and logs a warning, rather than
  silently doing nothing.
* **Exclude windows that wrap around midnight now cover 00:00–00:01.** The old
  implementation started the wrapped range at 00:01.
* **Configs are parsed with `yaml.safe_load`.** Python-specific YAML tags are no
  longer executed.
* **Config files must end in `.yaml`, `.yml` or `.json`.** Any other extension is
  reported instead of silently producing an empty config.
* **Remote configs have a 30 second timeout** and are parsed as YAML or JSON,
  rather than JSON only and without a timeout.
* Log messages use `%`-style lazy formatting and slightly reworded target
  selection lines (`Selected server web-1` instead of `Choose server web-1`).

### Changed — API and packaging

* Moved to a `src/` layout and split the monolithic modules: `chaotic.cli`,
  `chaotic.runner`, `chaotic.config`, `chaotic.excludes`, `chaotic.factory`,
  `chaotic.errors`.
* `chaotic.cloud` is now `chaotic.providers`, and `chaotic.app` is now
  `chaotic.cli`. The `chaotic-ngine` console script is unchanged, and
  `from chaotic import ChaoticFactory, ...` still works.
* Providers no longer read credentials or build API clients at import time. The
  client is created on first use, behind a `client` property.
* Six of the seven providers now share one `RestartChaotic` template, which
  removed the duplicated stop/wait/start logic.
* Errors raised on purpose derive from `chaotic.errors.ChaoticError`; the CLI
  logs those as one line and exits `1`, and anything else gets a traceback.
  Proxmox credential problems now raise `ConfigError` instead of `ValueError`.
* `chaotic.log` no longer configures logging or loads `.env` on import; call
  `configure_logging()`.
* Packaging moved from `setup.py` and `requirements*.txt` to `pyproject.toml`
  with hatchling, a `uv.lock`, and PEP 735 dependency groups.
* Tooling: ruff replaces flake8, mypy runs in strict mode, and the test suite
  went from zero tests to full coverage of every provider.
* `python -m chaotic` works as an alternative to the console script.

### Fixed

* `mkdocs.yml` had its `features` list at the top level instead of under
  `theme`, so navigation tabs were never actually enabled.
* The container image is built from a wheel in a multi-stage build and no longer
  ships the sources or the build toolchain.

### Notes

* `PROXMOX_API_VERIFY_SSL` keeps its existing truthiness behaviour: any non-empty
  value, including `false`, enables certificate verification. This is now
  documented rather than changed.
