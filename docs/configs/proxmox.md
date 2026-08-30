# Proxmox Settings

Chaotic will pick a random **running** VM (qemu) or container (lxc) and stop and
start it with a delay of a configurable time (default 60s).

## ENV Variables

Auth using user and password:

```ini
PROXMOX_API_HOST=pve1.example.com
PROXMOX_API_USER=root@pam
PROXMOX_API_PASSWORD=...
```

Auth using API token (note the _!myTokenName_ in `PROXMOX_API_USER`):

```ini
PROXMOX_API_HOST=pve1.example.com
PROXMOX_API_USER=api@pam!myTokenName
PROXMOX_API_TOKEN=...
```

The two styles are mutually exclusive: setting both `PROXMOX_API_PASSWORD` and
`PROXMOX_API_TOKEN` is rejected with an error rather than silently picking one.

Optional, TLS certificate verification (default: off):

```ini
PROXMOX_API_VERIFY_SSL=1
```

!!! warning "`PROXMOX_API_VERIFY_SSL` is not a boolean"
    Any **non-empty** value enables verification, including `PROXMOX_API_VERIFY_SSL=false`.
    To turn verification off, leave the variable unset or set it to the empty
    string. This quirk is kept for backwards compatibility with existing
    deployments.

    Chaotic loads the operating system trust store at start up, so a certificate
    from an internal CA that the host trusts works without further configuration.

## Config.yml

```yaml
---
kind: proxmox
dry_run: false
configs:

  # Optional: Do not shutdown VMs having a lower uptime in minutes
  min_uptime: 60

  # Optional: Tag to select VMs for chaos actions
  filter_tag: chaos-target

  # Optional: Tag to skip VMs from chaos actions, even if they have the filter_tag
  skip_tag: chaos-skip

  # Optional: Do not shutdown VMs in this name list
  denylist:
    - my-single-vm

  # Optional: 60 seconds is the default
  wait_before_restart: 60
```

A VM is a candidate only when **all** of these hold:

1. its status is `running`,
2. it carries `filter_tag`, if one is configured,
3. its name is not in `denylist`,
4. it does not carry `skip_tag`.

`min_uptime` is checked *after* a VM has been chosen, so a run may end without
touching anything, and that is logged.

!!! note "Shutdowns are forced"
    Chaotic calls the shutdown endpoint with `forceStop=1`, so a guest that
    ignores the ACPI request is still stopped. It is a chaos tool, after all.
