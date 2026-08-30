# Hashicorp Nomad Settings

## ENV Variables

```ini
NOMAD_ADDR=http://nomad.example.com:4646
```

Optional, an ACL token and HTTP basic auth credentials:

```ini
NOMAD_TOKEN=...
NOMAD_HTTP_AUTH=user:password
```

`NOMAD_ADDR` defaults to `http://127.0.0.1:4646` when unset.

## Experiments

`experiments` is a list, and **one entry is picked at random per run**. Listing
both `job` and `node` therefore means roughly half the runs signal an allocation
and half drain nodes — it does not mean both happen.

## Config.yml

### Nomad Job

Chaotic will send an allocation signal to a running allocation in the available
namespaces selected by an allow list.

```yaml
---
kind: nomad
dry_run: false
configs:
  experiments:
    - job

  # Required: Signals to choose from
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

`signals` is mandatory: there is no safe default signal to fall back to, so a
`job` experiment without it fails with an error instead of guessing.

With `job_meta_opt_key` set, a job opts out by setting that meta key to `false`:

```hcl
job "my-job" {
  meta {
    chaotic = "false"
  }
}
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

Only nodes that are currently eligible and not already draining are candidates.
Without `node_drain_amount_in_percent`, exactly one node is drained; with it, the
percentage is rounded and clamped to at least one and at most all candidates.

Every node drained in a run is set back to eligible after `node_wait_for`
seconds.

!!! warning "`node_drain_deadline_seconds` changed"
    Up to and including 0.17.0 the deadline sent to Nomad was six times the
    configured value, so `node_drain_deadline_seconds: 15` really meant 90
    seconds. It is now exactly the number of seconds configured. If you tuned
    this value against the old behaviour, divide it by six.
