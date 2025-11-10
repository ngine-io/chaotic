# Common Settings

## Common ENV variables

Log Level (default: info)

```ini
CHAOTIC_LOG_LEVEL=INFO
```

Cloud config to use, (also see _examples/_ in GitHub repo for samples) (default: ./config.yaml)

```ini
CHAOTIC_CONFIG=./my-config.yaml
```

If `--periodic` the interval in minues can be given by ENV or `--interval` (default: 1)

```ini
CHAOTIC_INTERVAL=60
```

!!! tip "Tip: .env file"
    Settings can be set either by ENV vars or by providing a `.env` file


## Common Configs

### Exclude times

Define times when the bot should not doing real actions (it will run in dry-run though):

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

### DigitalOcean API access token

```ini
DIGITALOCEAN_ACCESS_TOKEN=<...>
```

### Hetzner Cloud API token

```ini
HCLOUD_API_TOKEN=<...>
```

### Vultr API key

```ini
VULTR_API_KEY=<...>
```

### Proxmox

```ini
PROXMOX_API_HOST=pve1.example.com
PROXMOX_VERIFY_SSL=true
```

Password auth:

```ini
PROXMOX_API_HOST=pve1.example.com
PROXMOX_API_USER=root@pam
PROXMOX_API_PASSWORD=<...>
```

API token auth:

```ini
PROXMOX_API_HOST=pve1.example.com
PROXMOX_API_USER=api@pam!myTokenName
PROXMOX_API_TOKEN=<...>
```
