![license](https://img.shields.io/pypi/l/chaotic-ngine.svg)
![python versions](https://img.shields.io/pypi/pyversions/chaotic-ngine.svg)
![status](https://img.shields.io/pypi/status/chaotic-ngine.svg)
[![pypi version](https://img.shields.io/pypi/v/chaotic-ngine.svg)](https://pypi.org/project/chaotic-ngine/)
![PyPI - Downloads](https://img.shields.io/pypi/dw/chaotic-ngine)
[![CI](https://github.com/ngine-io/chaotic/actions/workflows/ci.yml/badge.svg)](https://github.com/ngine-io/chaotic/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

# Chaotic - Chaos for Clouds

Chaotic evaluates a plan, how it will bring chaos in your Cloud environment.

It picks one random target per run and does something unpleasant but recoverable
to it: stop and start a virtual machine, signal a HashiCorp Nomad allocation, or
drain a Nomad client node.

## Quick start

```shell
pip install chaotic-ngine
```

```yaml
# config.yaml
---
kind: proxmox
dry_run: true
configs:
  filter_tag: chaos-target
excludes:
  weekdays: [Sat, Sun]
```

```shell
chaotic-ngine --config config.yaml
```

Flip `dry_run` to `false` once the logs show it selecting what you expect.

## Supported clouds

Apache CloudStack, cloudscale.ch, DigitalOcean, HashiCorp Nomad, Hetzner Cloud,
Proxmox and Vultr.

## Documentation

Please visit https://ngine-io.github.io/chaotic/

Contributing and local development: see
[docs/development.md](docs/development.md).

## License

MIT License
