# Vultr Settings

Chaotic will pick a random instance, optionally narrowed down by a tag, and halt
and start it with a delay of a configurable time (default 60s).

## ENV Variables

```ini
VULTR_API_KEY="..."
```

## Config.yml

```yaml
---
kind: vultr
dry_run: true
configs:

  # Optional instance tag filter
  tag: "chaos=enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

!!! warning "Without `tag`, every instance is a candidate"
    Set a tag unless the whole account is meant to be chaos territory.
