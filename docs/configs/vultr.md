# Vultr Settings

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

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
  tag: "chaos=enabled"

```
