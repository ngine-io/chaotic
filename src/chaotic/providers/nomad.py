"""HashiCorp Nomad provider.

Requires ``NOMAD_ADDR`` and, depending on the cluster, ``NOMAD_TOKEN`` and
``NOMAD_HTTP_AUTH`` (``user:password``).

Unlike the machine providers, Nomad offers two very different experiments,
selected at random from the ``experiments`` config list:

``job``
    Send a signal (e.g. ``SIGKILL``) to a random running allocation.
``node``
    Drain a share of the eligible client nodes and make them eligible again
    after a while.
"""

from __future__ import annotations

import os
import random
import time
from functools import cached_property
from typing import Any

import requests

from chaotic.errors import ConfigError
from chaotic.log import log
from chaotic.providers.base import Chaotic

DEFAULT_NOMAD_ADDR = "http://127.0.0.1:4646"
API_TIMEOUT_SECONDS = 10
NANOSECONDS_PER_SECOND = 10**9

DEFAULT_DRAIN_DEADLINE_SECONDS = 10
DEFAULT_NODE_WAIT_FOR_SECONDS = 60

EXPERIMENTS = ("job", "node")
"""Experiments this provider implements, each backed by an ``action_<name>`` method."""


class Nomad:
    """Minimal client for the Nomad HTTP API."""

    def __init__(self, api_key: str, api_url: str | None = None, api_auth: str | None = None) -> None:
        self.api_key = api_key
        self.api_url = api_url or DEFAULT_NOMAD_ADDR
        self.api_auth = self._parse_auth(api_auth)

    @staticmethod
    def _parse_auth(api_auth: str | None) -> tuple[str, str] | None:
        """Split a ``user:password`` string into a requests auth tuple."""
        if not api_auth:
            return None
        user, _, password = api_auth.partition(":")
        return user, password

    def query_api(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Send a request and raise on any non-2xx response."""
        response = requests.request(
            method=method,
            url=f"{self.api_url}/v1/{path}",
            headers={
                "X-Nomad-Token": self.api_key,
                "Content-Type": "application/json",
            },
            auth=self.api_auth,
            params=params,
            json=json,
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response

    def list_nodes(self) -> list[dict[str, Any]]:
        """Return client nodes that are neither draining nor already ineligible."""
        response = self.query_api("get", "nodes")
        return [node for node in response.json() if not node["Drain"] and node["SchedulingEligibility"] == "eligible"]

    def drain_node(self, node_id: str, deadline_seconds: int = 10, ignore_system_jobs: bool = True) -> None:
        """Start draining a node, forcing remaining allocations off after the deadline."""
        payload = {
            "DrainSpec": {
                "Deadline": deadline_seconds * NANOSECONDS_PER_SECOND,
                "IgnoreSystemJobs": ignore_system_jobs,
            },
            "Meta": {
                "message": "drained by chaotic",
            },
        }
        self.query_api("post", f"node/{node_id}/drain", json=payload)

    def set_node_eligibility(self, node_id: str, eligible: bool = True) -> None:
        self.query_api(
            "post",
            f"node/{node_id}/eligibility",
            json={"Eligibility": "eligible" if eligible else "ineligible"},
        )

    def list_allocs(self, namespace: str | None = None) -> list[dict[str, Any]]:
        response = self.query_api("get", "allocations", params={"namespace": namespace})
        allocs: list[dict[str, Any]] = response.json()
        return allocs

    def read_alloc(self, alloc_id: str) -> dict[str, Any]:
        alloc: dict[str, Any] = self.query_api("get", f"allocation/{alloc_id}").json()
        return alloc

    def signal_alloc(self, alloc_id: str, signal: str) -> None:
        self.query_api("post", f"client/allocation/{alloc_id}/signal", json={"Signal": signal})

    def list_namespaces(self, prefix: str | None = None) -> list[dict[str, Any]]:
        response = self.query_api("get", "namespaces", params={"prefix": prefix})
        namespaces: list[dict[str, Any]] = response.json()
        return namespaces


class NomadChaotic(Chaotic):
    """Run one of the Nomad chaos experiments."""

    @cached_property
    def client(self) -> Nomad:
        """API client, created on first use so that importing stays side effect free."""
        return Nomad(
            api_key=os.getenv("NOMAD_TOKEN", ""),
            api_url=os.getenv("NOMAD_ADDR", ""),
            api_auth=os.getenv("NOMAD_HTTP_AUTH", ""),
        )

    def action(self) -> None:
        experiments = list(self.configs.get("experiments") or ["job"])

        unknown = [name for name in experiments if name not in EXPERIMENTS]
        if unknown:
            raise ConfigError(f"Unknown nomad experiments {unknown}, supported are: {', '.join(EXPERIMENTS)}")

        experiment = random.choice(experiments)
        log.info("Running experiment %s", experiment)
        getattr(self, f"action_{experiment}")()

    # -- job experiment ----------------------------------------------------- #

    def get_namespace(self) -> str:
        """Pick a random namespace honouring the allow and deny lists."""
        namespaces = [str(ns["Name"]) for ns in self.client.list_namespaces()]

        allowed = self.configs.get("namespace_allowlist")
        if allowed is not None:
            namespaces = [ns for ns in namespaces if ns in allowed]

        denied = self.configs.get("namespace_denylist")
        if denied is not None:
            namespaces = [ns for ns in namespaces if ns not in denied]

        if not namespaces:
            log.info("No namespaces eligible")
            return ""

        namespace = random.choice(namespaces)
        log.info("Selected namespace: %s", namespace)
        return namespace

    def is_opt_out(self, alloc_id: str) -> bool:
        """Return whether the allocation's job opted out via its meta block."""
        opt_key = self.configs.get("job_meta_opt_key")
        if not opt_key:
            return False

        job_meta = self.client.read_alloc(alloc_id=alloc_id).get("Job", {}).get("Meta") or {}
        opt_in = job_meta.get(opt_key)
        return opt_in is not None and (not opt_in or opt_in == "false")

    def _eligible_allocs(self, namespace: str) -> list[dict[str, Any]]:
        allocs = [a for a in self.client.list_allocs(namespace=namespace) if a["ClientStatus"] == "running"]

        job_type_skiplist = self.configs.get("job_type_skiplist")
        if job_type_skiplist:
            allocs = [a for a in allocs if a["JobType"] not in job_type_skiplist]

        job_skiplist = self.configs.get("job_skiplist")
        if job_skiplist:
            allocs = [a for a in allocs if a["JobID"] not in job_skiplist]

        return allocs

    def action_job(self) -> None:
        """Signal a random running allocation in a random eligible namespace."""
        # There is no safe default signal, so an explicit list is mandatory.
        signals = list(self.configs.get("signals") or [])
        if not signals:
            raise ConfigError("The 'job' experiment requires a non-empty 'signals' config")

        namespace = self.get_namespace()
        if namespace:
            allocs = self._eligible_allocs(namespace)
            if not allocs:
                log.info("No allocs found")
            else:
                alloc = random.choice(allocs)
                log.info("Selected alloc: %s (ID: %s) on %s", alloc["Name"], alloc["ID"], alloc["NodeName"])
                if self.is_opt_out(alloc_id=alloc["ID"]):
                    log.info("Job is opt-out configured, skipping")
                else:
                    signal = random.choice(signals)
                    log.info("Selected signal: %s", signal)
                    if not self.dry_run:
                        self.client.signal_alloc(alloc_id=alloc["ID"], signal=signal)

        log.info("done")

    # -- node experiment ---------------------------------------------------- #

    def _eligible_nodes(self) -> list[dict[str, Any]]:
        nodes = self.client.list_nodes()

        node_skiplist = self.configs.get("node_skiplist")
        if node_skiplist:
            nodes = [node for node in nodes if node["Name"] not in node_skiplist]

        node_class_skiplist = self.configs.get("node_class_skiplist")
        if node_class_skiplist:
            nodes = [node for node in nodes if node["NodeClass"] not in node_class_skiplist]

        return nodes

    def _drain_count(self, node_count: int) -> int:
        """How many nodes to drain in this run: a percentage, or a single node."""
        percent = int(self.configs.get("node_drain_amount_in_percent", 0))
        if percent <= 0:
            return 1
        return min(node_count, round(node_count * percent / 100) or 1)

    def action_node(self) -> None:
        """Drain a share of the eligible nodes, then make them eligible again."""
        nodes = self._eligible_nodes()
        if not nodes:
            log.info("No nodes found")
            log.info("done")
            return

        draining = random.sample(nodes, self._drain_count(len(nodes)))

        deadline_seconds = int(self.configs.get("node_drain_deadline_seconds", DEFAULT_DRAIN_DEADLINE_SECONDS))
        ignore_system_jobs = not bool(self.configs.get("node_drain_system_jobs", False))
        for node in draining:
            log.info("Drain node: %s", node["Name"])
            if not self.dry_run:
                self.client.drain_node(
                    node_id=node["ID"],
                    deadline_seconds=deadline_seconds,
                    ignore_system_jobs=ignore_system_jobs,
                )

        node_wait_for = int(self.configs.get("node_wait_for", DEFAULT_NODE_WAIT_FOR_SECONDS))
        log.info("Sleeping for %s seconds", node_wait_for)
        if not self.dry_run:
            time.sleep(node_wait_for)

        for node in draining:
            log.info("Set node to be eligible: %s", node["Name"])
            if not self.dry_run:
                self.client.set_node_eligibility(node_id=node["ID"], eligible=True)

        log.info("done")
