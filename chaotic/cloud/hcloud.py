import os
import random
import time
from hcloud import Client, APIException

from chaotic.cloud import Chaotic
from chaotic.log import log

HCLOUD_API_TOKEN: str = os.getenv('HCLOUD_API_TOKEN')

class HcloudChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        self.hcloud = Client(token=HCLOUD_API_TOKEN)

    def action(self) -> None:
        label = self.configs.get('label')
        log.info(f"Querying with label: {label}")
        servers = self.hcloud.servers.get_all(label_selector=label)

        if servers:
            server = random.choice(servers)
            log.info(f"Choose server {server.name}")
            if not self.dry_run:
                log.info(f"Stopping server {server.name}")
                self.hcloud.servers.power_off(server)

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {server.name}")
                self.hcloud.servers.power_on(server)
        else:
            log.info("No servers found")

        log.info(f"done")
