![license](https://img.shields.io/pypi/l/chaotic-ngine.svg)
![python versions](https://img.shields.io/pypi/pyversions/chaotic-ngine.svg)
![status](https://img.shields.io/pypi/status/chaotic-ngine.svg)
[![pypi version](https://img.shields.io/pypi/v/chaotic-ngine.svg)](https://pypi.org/project/chaotic-ngine/)
![PyPI - Downloads](https://img.shields.io/pypi/dw/chaotic-ngine)

# Chaotic - Chaos for Clouds

Chaotic evaluates a plan, how it will bring chaos in your Cloud environment.

Depending on the Cloud API used, it may kill allocations (Hashicorp Nomad), reboot or stop/start virtual machines in your Cloud environment.

With no arguments given, Chaotic runs as a "one shot" meant to be executed as cron job. Passing `--periodic` runs it as daemon with configurable interval `--interval 5` in minutes (1 is the default).
NOTE: The config is re-read on every interval, no need to restart the service after changing the config.

## Clouds

Currently implemented Clouds:

- DigitalOcean
- Vultr
- Hetzner Cloud
- Proxmox KVM
- CloudStack
- Hashicorp Nomad
- Exoscale
- cloudscale.ch

## Install

```
pip3 install -U chaotic-ngine
```

## Configure

Create a file named `config.yaml` or use the env var `CHAOTIC_CONFIG` to point to a config file (also see the example directory):

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

### Nomad Job

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
  experiments:
    - job

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

  # Optional: job type skip list
  job_type_skiplist:
    - system
    - batch
    - sysbatch

  # Optional: job name skip list
  job_skiplist:
    - my-job-name

  # Optional: Add a meta tag in your nomad job "chaotic" = False to opt-out
  job_meta_opt_key: chaotic
```

### Nomad Node

Chaotic will drain a node and set it to be ineligible for some time.

#### Config

```
export NOMAD_ADDR=http://nomad.example.com:4646
```

```yaml
---
kind: nomad
dry_run: true
configs:
  experiments:
    - node

  # Optional: Node drain deadline in seconds, default 10
  node_drain_deadline_seconds: 15

  # Optional: Skip nodes in these classes
  node_class_skiplist:
    - storage

  # Optional: Skip nodes with these names
  node_skiplist:
    - node1
    - node5

  # Optional: Wait for this amount of seconds before set node to be eligible again, default 60
  node_wait_for: 100

  # Optional: Also drain system jobs, default false
  node_drain_system_jobs: true

  # Optional: Drain multiple nodes in one run in percent, fallback 1 node
  node_drain_amount_in_percent: 30

```

### Proxmox KVM

Chaotic will stop a VM stop/start it with a delay of a configurable time (default 60s).

```
export PROXMOX_API_HOST="pve1.example.com"
export PROXMOX_API_USER="root@pam"
export PROXMOX_API_PASSWORD="..."
```

```yaml
---
kind: proxmox_kvm
dry_run: false
configs:

  # Optional: Do not shutdown VMs having a lower uptime in minutes
  min_uptime: 60

  # Optional: Do not shutdown VMs in this name list
  denylist:
    - my-single-vm

  # Optional: 60 seconds is the default
  wait_before_restart: 60
```

## Run

### CLI
```
chaos-ngine
```
### Docker 

One shot:

```
docker run -ti --rm -v $PWD/examples/config_nomad.yaml:/app/config.yaml -e TZ=Europe/Zurich -e NOMAD_ADDR=$NOMAD_ADDR --name chaotic ghcr.io/ngine-io/chaotic:latest
```

As service:

```
docker run -ti --rm -v $PWD/examples/config_nomad.yaml:/app/config.yaml -e TZ=Europe/Zurich -e NOMAD_ADDR=$NOMAD_ADDR --name chaotic ghcr.io/ngine-io/chaotic:latest --periodic
```

## Logs
What you should see (e.g. for kind cloudscale.ch):
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
