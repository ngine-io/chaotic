import os
from functools import cached_property
import random
import time

from cloudscale import Cloudscale

from chaotic.providers.base import Chaotic
from chaotic.log import log

class CloudscaleChChaotic(Chaotic):

    @cached_property
    def client(self) -> Cloudscale:
        """API client, created on first use so that importing stays side effect free."""
        return Cloudscale(api_token=os.getenv("CLOUDSCALE_API_TOKEN", ""))

    def action(self) -> None:
        filter_tag = self.configs.get('filter_tag')
        log.info(f"Querying with filter_tag: {filter_tag}")
        servers = self.client.server.get_all(filter_tag=filter_tag)
        if servers:
            server = random.choice(servers)
            log.info(f"Choose server {server['name']}")
            if not self.dry_run:
                log.info(f"Stopping server {server['name']}")
                self.client.server.stop(uuid=server['uuid'])

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {server['name']}")
                self.client.server.start(uuid=server['uuid'])
        else:
            log.info("No servers found")

        log.info(f"done")
