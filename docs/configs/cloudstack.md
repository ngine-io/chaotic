# Apache CloudStack Settings

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

## ENV Variables

```ini
CLOUDSTACK_API_ENDPOINT=https://cloud.example.com/client/api
CLOUDSTACK_API_KEY=<...>
CLOUDSTACK_API_SECRET=<...>
```

## Config.yml

```yaml
---
kind: cloudstack
dry_run: false
configs:

  # Optional, filter tag
  tag:
    key: chaos
    value: enabled

  # Optional: filter by zone ID
  zoneid: ...

  # Optional: Use project instead of account
  projectid: ...

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```
