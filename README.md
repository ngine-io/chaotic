# Chaotic - Chaos for Clouds

Chaotic evaluates a plan, how it will bring chaos in your Cloud environment.

Depending on the Cloud API, it may kill allocations (Hashicorp Nomad), reboot or stops/start virtual machines in Public Clouds.

## Clouds

Currently implemented Clouds:

- Hashicorp Nomad

Planned:

- Hetzner Cloud
- cloudscale.ch
- Exoscale
- Vultr
- Digital Ocean

## Install

```
pip install https://github.com/ngine-io/chaotic/archive/master.zip
```

## Configure

### Nomad

```
export NOMAD_ADDR=http://nomad.example.com:4646
```

#### Create a config.yaml

```yaml
---
kind: nomad
dry_run: true
configs:
  namespace_allowlist:
    - example-prod
    - foobar-prod
  signals:
    - SIGKILL
```
