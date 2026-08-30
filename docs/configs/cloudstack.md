# Apache CloudStack Settings

Chaotic will pick a random instance carrying the configured tag and stop and
start it with a delay of a configurable time (default 60s).

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

  # Required, filter tag
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

!!! warning "`tag` is required"
    Unlike the other clouds, CloudStack has no cheap way to scope a query to
    "machines meant for chaos". Without a `tag`, every instance in the account
    would be a candidate, so chaotic refuses to run and logs a warning instead.
