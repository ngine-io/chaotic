# Running

## Chaotic CLI

```shell
chatic-ngine -h
```

```
usage: chaotic-ngine [-h] [--periodic] [--interval INTERVAL] [--version] [--config CONFIG]

options:
  -h, --help           show this help message and exit
  --periodic           run periodic
  --interval INTERVAL  set interval in minutes
  --version            show version
  --config CONFIG      use config file
```

### Run Modes

With no arguments given, Chaotic runs as a "one shot" meant to be executed as _cron job_.

```shell
chatic-ngine --config my-config.yaml
```

Passing `--periodic` runs it as daemon/service with configurable interval `--interval 5` in minutes (1 is the default).

```shell
chatic-ngine --periodic --interval 5 --config my-config.yaml

```

!!! tip
    The config is re-read on every interval, no need to restart the service after changing the config.


## Docker / Container

We provide docker images as `ghcr.io/ngine-io/chaotic:latest`.

### One Shot Docker run

```shell
docker run -ti --rm
-v $PWD/examples/config_nomad.yaml:/app/config.yaml
-e TZ=Europe/Zurich
-e NOMAD_ADDR=$NOMAD_ADDR
--name chaotic-one-shot
ghcr.io/ngine-io/chaotic:latest
```

### Periodic

```shell
docker run -ti --rm
-v $PWD/examples/config_nomad.yaml:/app/config.yaml
-e TZ=Europe/Zurich
-e VULTR_API_KEY=$VULTR_API_KEY
--name chaotic-periodic
ghcr.io/ngine-io/chaotic:latest --periodic --interval 60
```

### Docker Compose

A minimal docker compose file would look like:

```yaml
---
version: "3.9"
services:
  scalr:
    image: ghcr.io/ngine-io/chaotic:latest
    command: --periodic
    environment:
      - CHAOTIC_INTERVAL=60
      - CHAOTIC_LOG_LEVEL=INFO
      - CHAOTIC_CONFIG=/app/config.yml
      # Cloud specifc ENV vars for auth
      - VULTR_API_KEY=...
    volumes:
      - "./vultr-config.yml:/app/config.yml:ro"
```
