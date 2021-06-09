import os
import random
import time
from cloudscale import Cloudscale, CloudscaleApiException

from chaotic.cloud import Chaotic
from chaotic.log import log

CLOUDSCALE_API_TOKEN: str = os.getenv('CLOUDSCALE_API_TOKEN')

class CloudscaleChChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        self.cloudscale = Cloudscale(api_token=CLOUDSCALE_API_TOKEN)


    def action(self) -> None:
        filter_tag = self.configs.get('filter_tag')
        log.info(f"Querying with filter_tag: {filter_tag}")
        servers = self.cloudscale.server.get_all(filter_tag=filter_tag)
        if servers:
            server = random.choice(servers)
            log.info(f"Choose server {server['name']}")
            if not self.dry_run:
                log.info(f"Stopping server {server['name']}")
                self.cloudscale.server.stop(uuid=server['uuid'])

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for server {wait_before_restart}")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {server['name']}")
                self.cloudscale.server.start(uuid=server['uuid'])
        else:
            log.info("No servers found")

        log.info(f"done")
