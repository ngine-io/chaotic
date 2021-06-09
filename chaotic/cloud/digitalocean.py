import os
import random
import time
import digitalocean

from chaotic.cloud import Chaotic
from chaotic.log import log


class DigitaloceanChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        self.do = digitalocean.Manager()

    def action(self) -> None:
        tag = self.configs.get('tag')
        log.info(f"Querying with tag: {tag}")
        droplets = self.do.get_all_droplets(tag_name=tag)

        if droplets:
            droplet = random.choice(droplets)
            log.info(f"Choose server {droplet.name}")
            if not self.dry_run:
                log.info(f"Stopping server {droplet.name}")
                droplet.shutdown()

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for server {wait_before_restart}")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {droplet.name}")
                droplet.power_on()

        else:
            log.info("No servers found")

        log.info(f"done")
