import random
import time
from functools import cached_property

import digitalocean

from chaotic.providers.base import Chaotic
from chaotic.log import log


class DigitaloceanChaotic(Chaotic):

    @cached_property
    def client(self) -> digitalocean.Manager:
        """API client, created on first use so that importing stays side effect free."""
        return digitalocean.Manager()

    def action(self) -> None:
        tag = self.configs.get('tag')
        log.info(f"Querying with tag: {tag}")
        droplets = self.client.get_all_droplets(tag_name=tag)

        if droplets:
            droplet = random.choice(droplets)
            log.info(f"Choose server {droplet.name}")
            if not self.dry_run:
                log.info(f"Stopping server {droplet.name}")
                droplet.shutdown()

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {droplet.name}")
                droplet.power_on()

        else:
            log.info("No servers found")

        log.info(f"done")
