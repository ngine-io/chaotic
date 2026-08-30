# cloudscale.ch Settings

Chaotic will pick a random server, optionally narrowed down by a filter tag, and
stop and start it with a delay of a configurable time (default 60s).

## ENV Variables

```ini
CLOUDSCALE_API_TOKEN=<...>
```

## Config.yml

```yaml
---
kind: cloudscale_ch
dry_run: false
configs:
  # Optional: filter by tag
  filter_tag: "chaos=enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

!!! warning "Without `filter_tag`, every server is a candidate"
    Set a tag unless the whole project is meant to be chaos territory.
