# DigitalOcean Settings

Chaotic will pick a random droplet, optionally narrowed down by a tag, and shut
it down and power it on again with a delay of a configurable time (default 60s).

## ENV Variables

```ini
DIGITALOCEAN_ACCESS_TOKEN=...
```

## Config.yml

```yaml
---
kind: digitalocean
dry_run: false
configs:

  # Optional droplet tag filter
  tag: "chaos:enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

!!! warning "Without `tag`, every droplet is a candidate"
    Set a tag unless the whole account is meant to be chaos territory.
