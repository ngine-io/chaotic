# Hetzner Cloud Settings

Chaotic will stop a server selected by an optional filter label and stop/start it with a delay of a configurable time (default 60s).

## ENV Variables

```ini
HCLOUD_API_TOKEN=...
```

## Config.yml

```yaml
kind: hcloud
dry_run: false
configs:

  # Optional server label filter
  label: "chaos=enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```
