# Chaotic Ngine - Chaos for Clouds

Chaotic is a small CLI tool that evaluates a plan describing how it should bring
chaos to your Cloud environment.

Depending on the API used, it may kill allocations (HashiCorp Nomad), or reboot
and stop/start virtual machines in your Cloud environment or on premise Proxmox.

## How it works

1. A **config** (YAML or JSON, on disk or behind a URL) declares the `kind` of
   chaos, whether it is a `dry_run`, provider specific `configs` and optional
   `excludes`.
2. Chaotic instantiates the matching provider and, unless an exclude window is
   active, runs **one** experiment: it picks a single random target and acts on
   it.
3. It can do that once (a cron job) or on an interval (`--periodic`).

```yaml
---
kind: proxmox
dry_run: false
configs:
  filter_tag: chaos-target
  wait_before_restart: 60
excludes:
  weekdays: [Sat, Sun]
```

!!! tip "Start with `dry_run: true`"
    A dry-run performs the whole selection and logs the target it *would* have
    hit, without calling any mutating API. It is the fastest way to check that
    your filters select what you expect.

## Cloud Providers

Currently implemented APIs:

| Providers         | `kind`          | Experiment                     |
| ----------------- | --------------- | ------------------------------ |
| Apache CloudStack | `cloudstack`    | Stop and start an instance     |
| cloudscale.ch     | `cloudscale_ch` | Stop and start a server        |
| DigitalOcean      | `digitalocean`  | Shut down and boot a droplet   |
| HashiCorp Nomad   | `nomad`         | Signal an alloc, or drain nodes |
| Hetzner Cloud     | `hcloud`        | Power a server off and on      |
| Proxmox           | `proxmox`       | Shut down and start a VM or LXC |
| Vultr             | `vultr`         | Halt and start an instance     |

See [Settings](settings.md) for the options every provider shares, and the
per-cloud pages for the rest.
