import os
import random
import time
from typing import List, Optional

import requests

from chaotic.cloud import Chaotic
from chaotic.log import log

NOMAD_ADDR: str = os.getenv("NOMAD_ADDR", "")
NOMAD_TOKEN: str = os.getenv("NOMAD_TOKEN", "")
NOMAD_HTTP_AUTH: str = os.getenv("NOMAD_HTTP_AUTH", "")


class Nomad:
    def __init__(self, api_key: str, api_url: Optional[str] = None, api_auth: Optional[str] = None) -> None:
        self.api_key = api_key
        self.api_url = api_url or "http://127.0.0.1:4646"
        self.api_auth = tuple(api_auth.split(":")) if api_auth else None

    def query_api(self, method: str, path: str, params: Optional[dict] = None, json: Optional[dict] = None) -> requests.Response:
        r = requests.request(
            method=method,
            url=f"{self.api_url}/v1/{path}",
            headers={
                "X-Nomad-Token": self.api_key,
                "Content-Type": "application/json",
            },
            auth=self.api_auth,
            params=params,
            json=json,
            timeout=10,
        )
        r.raise_for_status()
        return r

    def list_nodes(self) -> List[dict]:
        r = self.query_api("get", "nodes")
        nodes = [node for node in r.json() if not node["Drain"] and node["SchedulingEligibility"] == "eligible"]
        return nodes

    def drain_node(self, node_id: str, deadline_seconds: int = 10, ignore_system_jobs: bool = True) -> None:
        json = {
            "DrainSpec": {
                "Deadline": deadline_seconds * 60 * 10**8,
                "IgnoreSystemJobs": ignore_system_jobs,
            },
            "Meta": {
                "message": "drained by chaotic",
            },
        }
        self.query_api("post", f"node/{node_id}/drain", json=json)

    def set_node_eligibility(self, node_id: str, eligible: bool = True) -> None:
        json = {
            "Eligibility": "eligible" if eligible else "ineligible",
        }
        self.query_api("post", f"node/{node_id}/eligibility", json=json)

    def list_allocs(self, namespace: Optional[str] = None) -> List[dict]:
        params = {
            "namespace": namespace,
        }
        r = self.query_api("get", "allocations", params=params)
        allocs = [alloc for alloc in r.json() if alloc["ClientStatus"] == "running"]
        return allocs

    def read_alloc(self, alloc_id: str) -> dict:
        r = self.query_api("get", f"allocation/{alloc_id}")
        return r.json()

    def signal_alloc(self, alloc_id: str, signal: str) -> None:
        json = {
            "Signal": signal,
        }
        self.query_api("post", f"client/allocation/{alloc_id}/signal", json=json)

    def list_namespaces(self, prefix: Optional[str] = None) -> List[dict]:
        params = {
            "prefix": prefix,
        }
        r = self.query_api("get", "namespaces", params=params)
        return r.json()


class NomadChaotic(Chaotic):
    def __init__(self) -> None:
        super().__init__()
        self.nomad = Nomad(
            api_key=NOMAD_TOKEN,
            api_url=NOMAD_ADDR,
            api_auth=NOMAD_HTTP_AUTH,
        )

    def get_namespace(self) -> str:
        namespaces = [ns["Name"] for ns in self.nomad.list_namespaces()]

        allowed_ns = self.configs.get("namespace_allowlist")
        if allowed_ns is not None:
            namespaces = [ns for ns in namespaces if ns in allowed_ns]

        denied_ns = self.configs.get("namespace_denylist")
        if denied_ns is not None:
            namespaces = [ns for ns in namespaces if ns not in denied_ns]

        if not namespaces:
            log.info(f"No namespaces eligible")
            return ""

        namespace = random.choice(namespaces)

        log.info(f"Selected namespace: {namespace}")
        return namespace

    def is_opt_out(self, alloc_id: str) -> bool:
        opt_in_key = self.configs.get("job_meta_opt_key")
        if opt_in_key:
            alloc_details = self.nomad.read_alloc(alloc_id=alloc_id)
            job_meta = alloc_details["Job"]["Meta"]
            if job_meta:
                opt_in = job_meta.get(opt_in_key)
                return opt_in is not None and (not opt_in or opt_in == "false")
        return False

    def action(self) -> None:
        experiments = self.configs.get("experiments", ["job"])
        exp = random.choice(experiments)
        log.info(f"Running experiment {exp}")
        method_name = f"action_{exp}"
        func = getattr(self, method_name)
        if func:
            func()

    def action_job(self) -> None:
        namespace = self.get_namespace()
        if namespace:
            allocs = self.nomad.list_allocs(namespace=namespace)

            job_type_skiplist = self.configs.get("job_type_skiplist")
            if job_type_skiplist:
                allocs = [alloc for alloc in allocs if alloc["JobType"] not in job_type_skiplist]

            job_skiplist = self.configs.get("job_skiplist")
            if job_skiplist:
                allocs = [alloc for alloc in allocs if alloc["JobID"] not in job_skiplist]

            if allocs:
                alloc = random.choice(allocs)
                log.info(f"Selected alloc: {alloc['Name']} (ID: {alloc['ID']}) on {alloc['NodeName']}")
                if not self.is_opt_out(alloc_id=alloc["ID"]):
                    signal = random.choice(self.configs["signals"])
                    log.info(f"Selected signal: {signal}")
                    if not self.dry_run:
                        self.nomad.signal_alloc(alloc_id=alloc["ID"], signal=signal)
                else:
                    log.info("Job is opt-out configured, skipping")

            else:
                log.info("No allocs found")

        log.info(f"done")

    def action_node(self) -> None:
        nodes = self.nomad.list_nodes()

        node_skiplist = self.configs.get("node_skiplist")
        if node_skiplist:
            nodes = [node for node in nodes if node["Name"] not in node_skiplist]

        node_class_skiplist = self.configs.get("node_class_skiplist")
        if node_class_skiplist:
            nodes = [node for node in nodes if node["NodeClass"] not in node_class_skiplist]

        if nodes:
            # How many nodes to drain in this run
            node_drain_amount_in_percent = int(self.configs.get("node_drain_amount_in_percent", 0))
            amount_of_nodes = 1
            if node_drain_amount_in_percent and node_drain_amount_in_percent > 0:
                amount_of_nodes = round(len(nodes) * node_drain_amount_in_percent / 100) or 1

            nodes_drain = nodes.copy()
            nodes_eligible = list()
            for i in range(amount_of_nodes):
                node = nodes_drain.pop(random.randrange(len(nodes_drain)))
                nodes_eligible.append(node)

                log.info(f"Drain node: {node['Name']}")

                if not self.dry_run:
                    deadline_seconds = int(self.configs.get("node_drain_deadline_seconds", 10))
                    ignore_system_jobs = not bool(self.configs.get("node_drain_system_jobs", False))
                    self.nomad.drain_node(
                        node_id=node["ID"],
                        deadline_seconds=deadline_seconds,
                        ignore_system_jobs=ignore_system_jobs,
                    )

            node_wait_for = int(self.configs.get("node_wait_for", 60))
            log.info(f"Sleeping for {node_wait_for} seconds")
            if not self.dry_run:
                time.sleep(node_wait_for)

            for i in range(amount_of_nodes):
                node = nodes_eligible.pop(random.randrange(len(nodes_eligible)))
                log.info(f"Set node to be eligible: {node['Name']}")
                if not self.dry_run:
                    self.nomad.set_node_eligibility(
                        node_id=node["ID"],
                        eligible=True,
                    )

        log.info(f"done")
