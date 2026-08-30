# Hetzner Cloud Settings

Chaotic will pick a random server, optionally narrowed down by a label selector,
and power it off and on again with a delay of a configurable time (default 60s).

## ENV Variables

```ini
HCLOUD_API_TOKEN=...
```

## Config.yml

```yaml
---
kind: hcloud
dry_run: false
configs:

  # Optional server label filter
  label: "chaos=enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

`label` is a Hetzner
[label selector](https://docs.hetzner.cloud/reference/cloud#label-selector), so
expressions like `chaos` (key exists) or `chaos!=disabled` work as well.

!!! warning "Without `label`, every server is a candidate"
    Set a label selector unless the whole project is meant to be chaos territory.
