# Proxmox Settings

Chaotic will stop a VM (qemu and lxc) stop/start it with a delay of a configurable time (default 60s).

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
