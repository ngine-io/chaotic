# DigitalOcean Settings

Chaotic will stop a droplet selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

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
