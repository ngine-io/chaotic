# Common Settings

## Common ENV variables

Log Level (default: info)

```ini
CHAOTIC_LOG_LEVEL=INFO
```

Cloud config to use, (also see _examples/_ in GitHub repo for samples) (default: ./config.yaml)

```ini
CHAOTIC_CONFIG=./my-config.yaml
```

If `--periodic` the interval in minues can be given by ENV or `--interval` (default: 1)

```ini
CHAOTIC_INTERVAL=60
```

!!! tip "Tip: .env file"
    Settings can be set either by ENV vars or by providing a `.env` file


## Common Configs

### Exclude times

Define times when the bot should not doing real actions (it will run in dry-run though):

```yaml
---
kind: ...
dry_run: false
excludes:
  weekdays:
    - Sun
    - Sat
  times_of_day:
    - 22:00-08:00
    - 11:00-14:00
  days_of_year:
    - Jan01
    - Apr01
    - May01
    - Jul04
    - Aug01
    - Dec24

```
