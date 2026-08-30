import os
from functools import cached_property
import random
import time

from hcloud import Client

from chaotic.providers.base import Chaotic
from chaotic.log import log

class HcloudChaotic(Chaotic):

    @cached_property
    def client(self) -> Client:
        """API client, created on first use so that importing stays side effect free."""
        return Client(token=os.getenv("HCLOUD_API_TOKEN", ""))

    def action(self) -> None:
        label = self.configs.get('label')
        log.info(f"Querying with label: {label}")
        servers = self.client.servers.get_all(label_selector=label)

        if servers:
            server = random.choice(servers)
            log.info(f"Choose server {server.name}")
            if not self.dry_run:
                log.info(f"Stopping server {server.name}")
                self.client.servers.power_off(server)

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {server.name}")
                self.client.servers.power_on(server)
        else:
            log.info("No servers found")

        log.info(f"done")
