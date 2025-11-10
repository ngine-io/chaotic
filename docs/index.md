# Chaotic Ngine - Chaos for Clouds

Chaotic is a rather simple CLI tool that evaluates a plan, how it will bring chaos in your Cloud environment.

Depending on the Cloud API used, it may kill allocations (Hashicorp Nomad), reboot or stop/start virtual machines in your Cloud environment or on premise Proxmox.

## Clouds

Currently implemented Clouds APIs:

- DigitalOcean
- Vultr
- Hetzner Cloud
- Proxmox
- Apache CloudStack
- Hashicorp Nomad
- cloudscale.ch
