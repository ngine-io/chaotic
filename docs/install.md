# Install

## Python PyPi

The package is hosted on [PyPi](https://pypi.org/project/chaotic-ngine/) and
requires Python 3.10 or newer.

```shell
pip install chaotic-ngine
```

With [uv](https://docs.astral.sh/uv/), to keep it out of your system Python:

```shell
uv tool install chaotic-ngine
```

Or run it without installing at all:

```shell
uvx chaotic-ngine --config my-config.yaml
```

## Container Image Repository

The image is hosted on [ghcr.io](https://github.com/ngine-io/chaotic/pkgs/container/chaotic)
and is built for `linux/amd64` and `linux/arm64`.

```shell
docker pull ghcr.io/ngine-io/chaotic:latest
```

Tags follow the releases: `latest`, `1.2.3` and `1.2` are all available.

## From source

See [Development](development.md).
