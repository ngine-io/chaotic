# cloudscale.ch Settings

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).


## ENV Variables

```ini
CLOUDSCALE_API_TOKEN=<...>
```

## Config.yml

```yaml
kind: cloudscale_ch
dry_run: false
configs:
  # Optional: filter by tag
  filter_tag: "chaos=enabled"

```
