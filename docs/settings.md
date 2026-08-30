# Common Settings

## Common ENV variables

Settings can come from three places. The more explicit one wins:

```
--config / --interval   >   $CHAOTIC_CONFIG / $CHAOTIC_INTERVAL   >   built-in default
```

Log level (default: `INFO`)

```ini
CHAOTIC_LOG_LEVEL=INFO
```

Path to a [`logging.config` file](https://docs.python.org/3/library/logging.config.html#configuration-file-format)
(default: `./logging.ini` if it exists). When present it takes precedence over
`CHAOTIC_LOG_LEVEL`.

```ini
CHAOTIC_LOG_CONFIG=./logging.ini
```

The repository ships a [`logging.ini`](https://github.com/ngine-io/chaotic/blob/master/logging.ini)
that emits JSON. The container image does not include it, so mount it to switch
a container to JSON logs:

```shell
docker run --rm \
  -v $PWD/logging.ini:/app/logging.ini:ro \
  ghcr.io/ngine-io/chaotic:latest
```

Cloud config to use, also see [_examples/_](https://github.com/ngine-io/chaotic/tree/master/examples)
in the GitHub repo for samples (default: `./config.yaml`). An `http://` or
`https://` URL works as well.

```ini
CHAOTIC_CONFIG=./my-config.yaml
```

With `--periodic`, the interval in minutes (default: `1`)

```ini
CHAOTIC_INTERVAL=60
```

Time zone used to evaluate `excludes`. Containers default to UTC.

```ini
TZ=Europe/Zurich
```

!!! tip "Tip: .env file"
    Settings can be set either by ENV vars or by providing a `.env` file in the
    working directory. Real ENV vars win over the `.env` file.

## Common Configs

Every config has the same four top level keys:

```yaml
---
# Required: which cloud to run against, see the Configs section
kind: vultr

# Optional: select a target and log what would happen, but call no mutating API
dry_run: false

# Optional: provider specific settings, see the Configs section
configs: {}

# Optional: see below
excludes: {}
```

### Exclude times

Define times when the bot should not perform real actions. During an exclude
window the run is **downgraded to a dry-run**, not skipped: chaotic still selects
a target and logs what it would have done, which keeps the logs honest about
what the exclude prevented.

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

| Key            | Format                | Notes                                                    |
| -------------- | --------------------- | -------------------------------------------------------- |
| `weekdays`     | `Mon` … `Sun`         | Abbreviated English weekday names                         |
| `times_of_day` | `HH:MM-HH:MM`         | Both ends inclusive; ranges may wrap around midnight      |
| `days_of_year` | `Jan01`, `Dec24`      | Abbreviated English month plus a two digit day            |

!!! warning "Excludes use local time"
    The windows are evaluated against the local wall clock of the process, so set
    `TZ` when running in a container.
