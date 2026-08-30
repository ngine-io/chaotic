# Running

## Chaotic CLI

```shell
chaotic-ngine -h
```

```
usage: chaotic-ngine [-h] [--periodic] [--interval INTERVAL] [--version] [--config CONFIG]

Chaos for Clouds.

options:
  -h, --help           show this help message and exit
  --periodic           run periodic
  --interval INTERVAL  set interval in minutes, or $CHAOTIC_INTERVAL, default 1
  --version            show version
  --config CONFIG      use config file, or $CHAOTIC_CONFIG, default: config.yaml
```

### Run Modes

With no arguments given, Chaotic runs as a "one shot", meant to be executed as a
_cron job_.

```shell
chaotic-ngine --config my-config.yaml
```

Passing `--periodic` runs it as a daemon/service with a configurable interval
`--interval 5` in minutes (1 is the default).

```shell
chaotic-ngine --periodic --interval 5 --config my-config.yaml
```

!!! tip
    The config is re-read on every interval, no need to restart the service after
    changing the config.

### Exit codes

| Mode        | Behaviour on failure                                                   |
| ----------- | ---------------------------------------------------------------------- |
| one shot    | Logs the error and exits `1`, so cron and Kubernetes Jobs see a failure |
| `--periodic`| Logs the error and keeps the schedule running, so a flaky API or a temporarily broken config does not kill the daemon |

`Ctrl+C` stops a periodic run cleanly and exits `0`.

### Remote configs

`--config` also accepts an `http://` or `https://` URL, which is handy for
keeping the plan in a central place:

```shell
chaotic-ngine --config https://config.example.com/chaos/nomad.yaml
```

The response is parsed as YAML or JSON. The request has a 30 second timeout, and
the config is fetched again on every interval.

## Docker / Container

We provide docker images as `ghcr.io/ngine-io/chaotic:latest`.

The image runs as UID `1000` and expects the config at `/app/config.yaml`, which
is where the built-in dry-run placeholder lives.

### One Shot Docker run

```shell
docker run -ti --rm \
  -v $PWD/examples/config_nomad.yaml:/app/config.yaml:ro \
  -e TZ=Europe/Zurich \
  -e NOMAD_ADDR=$NOMAD_ADDR \
  --name chaotic-one-shot \
  ghcr.io/ngine-io/chaotic:latest
```

### Periodic

```shell
docker run -ti --rm \
  -v $PWD/examples/config_vultr.yaml:/app/config.yaml:ro \
  -e TZ=Europe/Zurich \
  -e VULTR_API_KEY=$VULTR_API_KEY \
  --name chaotic-periodic \
  ghcr.io/ngine-io/chaotic:latest --periodic --interval 60
```

!!! tip "Set `TZ`"
    `excludes` are evaluated against the container's local wall clock. Without
    `TZ` the container runs in UTC, and a `22:00-08:00` exclude will not line up
    with your working hours.

### Docker Compose

A minimal compose file would look like:

```yaml
---
services:
  chaotic:
    image: ghcr.io/ngine-io/chaotic:latest
    command: --periodic
    restart: unless-stopped
    environment:
      - TZ=Europe/Zurich
      - CHAOTIC_INTERVAL=60
      - CHAOTIC_LOG_LEVEL=INFO
      - CHAOTIC_CONFIG=/app/config.yml
      # Cloud specific ENV vars for auth
      - VULTR_API_KEY=...
    volumes:
      - "./vultr-config.yml:/app/config.yml:ro"
```

## Kubernetes CronJob

```yaml
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: chaotic
spec:
  schedule: "0 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: Never
          containers:
            - name: chaotic
              image: ghcr.io/ngine-io/chaotic:latest
              args: ["--config", "/config/config.yaml"]
              env:
                - name: TZ
                  value: Europe/Zurich
                - name: VULTR_API_KEY
                  valueFrom:
                    secretKeyRef:
                      name: chaotic
                      key: vultr-api-key
              volumeMounts:
                - name: config
                  mountPath: /config
                  readOnly: true
          volumes:
            - name: config
              configMap:
                name: chaotic
```
