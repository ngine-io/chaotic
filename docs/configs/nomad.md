# Hashicorp Nomad Settings

## ENV Variables

```ini
NOMAD_ADDR=http://nomad.example.com:4646
```

## Config.yml

### Nomad Job

Chaotic will send an allocation signal to an allocation in the available namespaces selected by an allow list.

```yaml
---
kind: nomad
dry_run: false
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

```yaml
---
kind: nomad
dry_run: false
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
