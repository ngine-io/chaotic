import random
import time

from chaotic.cloud import Chaotic
from chaotic.log import log

from .nomad import NOMAD_ADDR, NOMAD_HTTP_AUTH, NOMAD_TOKEN, Nomad


class NomadNodeChaotic(Chaotic):
    def __init__(self) -> None:
        super().__init__()
        self.nomad = Nomad(
            api_key=NOMAD_TOKEN,
            api_url=NOMAD_ADDR,
            api_auth=NOMAD_HTTP_AUTH,
        )

    def action(self) -> None:
        nodes = self.nomad.list_nodes()

        node_skiplist = self.configs.get("node_skiplist")
        if node_skiplist:
            nodes = [node for node in nodes if node["Name"] not in node_skiplist]

        node_class_skiplist = self.configs.get("node_class_skiplist")
        if node_class_skiplist:
            nodes = [node for node in nodes if node["NodeClass"] not in node_class_skiplist]

        if nodes:
            node = random.choice(nodes)
            log.info(f"Drain node: {node['Name']}")

            if not self.dry_run:
                deadline_seconds = int(self.configs.get("node_drain_deadline_seconds", 10))
                self.nomad.drain_node(node_id=node["ID"], deadline_seconds=deadline_seconds)

            wait_for = int(self.configs.get("wait_for", 60))
            log.info(f"Sleeping for {wait_for} seconds")
            time.sleep(wait_for)

            log.info(f"Set node to be eligible: {node['Name']}")

            if not self.dry_run:
                self.nomad.set_node_eligibility(
                    node_id=node["ID"],
                    eligible=True,
                )

        log.info(f"done")
