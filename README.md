![license](https://img.shields.io/pypi/l/chaotic-ngine.svg)
![python versions](https://img.shields.io/pypi/pyversions/chaotic-ngine.svg)
![status](https://img.shields.io/pypi/status/chaotic-ngine.svg)
[![pypi version](https://img.shields.io/pypi/v/chaotic-ngine.svg)](https://pypi.org/project/chaotic-ngine/)
![PyPI - Downloads](https://img.shields.io/pypi/dw/chaotic-ngine)

# Chaotic - Chaos for Clouds

Chaotic evaluates a plan, how it will bring chaos in your Cloud environment.

Depending on the Cloud API used, it may kill allocations (Hashicorp Nomad), reboot or stop/start virtual machines in your Cloud environment.

## Clouds

Currently implemented Clouds:

- cloudscale.ch
- DigitalOcean
- Hetzner Cloud
- Hashicorp Nomad
- Vultr
- Exoscale
- CloudStack

## Install

```
pip3 install -U chaotic-ngine
```

## Configure

Create a file named `config.yaml` or use the env var `CHAOTIC_CONFIG` to point to a config file:

```
export CHAOTIC_CONFIG=config_nomad.yaml
```

### Exclude times

Define times when the bot should not doing real actions (it will run in dry-run):

```yaml
---
kind: ...
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
    - Aug01
    - Dec24
  ```

### Exoscale

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

```
export EXOSCALE_API_KEY="..."
export EXOSCALE_API_SECRET="..."
```

```yaml
---
kind: exoscale
dry_run: false
configs:

  # Optional, filter tag
  tag:
    key: chaos
    value: enabled

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

### CloudStack

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

```
export CLOUDSTACK_API_KEY="..."
export CLOUDSTACK_API_SECRET="..."
export CLOUDSTACK_API_ENDPOINT="..."
```

```yaml
---
kind: cloudstack
dry_run: false
configs:

  # Optional, filter tag
  tag:
    key: chaos
    value: enabled

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

### Vultr

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

```
export VULTR_API_KEY="..."
```

```yaml
---
kind: vultr
dry_run: true
configs:

  # Optional instance tag filter
  tag: "chaos=opt-in"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

### Cloudscale.ch

Chaotic will stop a server selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).


#### Config

```
export CLOUDSCALE_API_TOKEN="..."
```

```yaml
---
kind: cloudscale_ch
dry_run: true
configs:

  # Optional server tag filter
  filter_tag: "chaos=opt-in"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

### Hetzner Cloud

Chaotic will stop a server selected by an optional filter label and stop/start it with a delay of a configurable time (default 60s).

#### Config

```
export HCLOUD_API_TOKEN=...
```

```yaml
---
kind: hcloud
dry_run: false
configs:

  # Optional server label filter
  label: "chaos=enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

### DigitalOcean Cloud

Chaotic will stop a droplet selected by an optional filter tag and stop/start it with a delay of a configurable time (default 60s).

#### Config

```
export DIGITALOCEAN_ACCESS_TOKEN=...
```

```yaml
---
kind: digitalocean
dry_run: false
configs:

  # Optional droplet tag filter
  tag: "chaos:enabled"

  # Optional, 60 seconds is the default
  wait_before_restart: 60
```

### Nomad

Chaotic will send an allocation signal to an allocation in the available namespaces selected by an allow list.

#### Config

```
export NOMAD_ADDR=http://nomad.example.com:4646
```

```yaml
---
kind: nomad
dry_run: true
configs:

  # Signals to choose from
  signals:
    - SIGKILL

  # Optional: namespace allowlist
  namespace_allowlist:
    - example-prod
    - foobar-prod

  # Optional: namespace denylist
  namespace_denylist:
    - default
```

## Run

```
chaos-ngine
```

What you should see (cloudscale.ch):
```
2021-06-09 09:01:25,433 - cloudscale.log:INFO:Started, version: 0.6.2
2021-06-09 09:01:25,433 - cloudscale.log:INFO:Using profile default
2021-06-09 09:01:25,433 - cloudscale.log:INFO:API Token used: xyz...
2021-06-09 09:01:25,433 - chatic:INFO:Querying with filter_tag: None
2021-06-09 09:01:25,433 - cloudscale.log:INFO:HTTP GET to https://api.cloudscale.ch/v1/servers
2021-06-09 09:01:25,651 - cloudscale.log:INFO:HTTP status code 200
2021-06-09 09:01:25,652 - chatic:INFO:Choose server app3
2021-06-09 09:01:25,653 - chatic:INFO:Stopping server app3
2021-06-09 09:01:25,653 - cloudscale.log:INFO:HTTP POST to https://api.cloudscale.ch/v1/servers/d5628484-a6eb-4ea9-b3ef-ba8da2bb9fe0/stop
2021-06-09 09:01:26,336 - cloudscale.log:INFO:HTTP status code 204
2021-06-09 09:01:26,336 - chatic:INFO:Sleeping for server 60
2021-06-09 09:02:26,393 - cloudscale.log:INFO:HTTP POST to https://api.cloudscale.ch/v1/servers/d5628484-a6eb-4ea9-b3ef-ba8da2bb9fe0/start
2021-06-09 09:02:26,955 - cloudscale.log:INFO:HTTP status code 204
2021-06-09 09:02:26,956 - chatic:INFO:done
```
