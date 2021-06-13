import os
import random
import time
from cs import CloudStack

from chaotic.cloud import Chaotic
from chaotic.log import log

CLOUDSTACK_API_ENDPOINT: str = os.getenv('CLOUDSTACK_API_ENDPOINT')
CLOUDSTACK_API_KEY: str = os.getenv('CLOUDSTACK_API_KEY')
CLOUDSTACK_API_SECRET: str = os.getenv('CLOUDSTACK_API_SECRET')


class CloudStackChaotic(Chaotic):

    def __init__(self) -> None:
        self.cs = CloudStack(
            endpoint=CLOUDSTACK_API_ENDPOINT,
            key=CLOUDSTACK_API_KEY,
            secret=CLOUDSTACK_API_SECRET,
        )

    def action(self) -> None:
        tag = self.configs.get('tag')
        log.info(f"Querying with tag: {tag['key']}={tag['value']}")

        instances = self.cs.listVirtualMachines(
            tags=[tag],
            fetch_list=True,
        )
        if instances:
            instance = random.choice(instances)
            log.info(f"Choose server {instance['name']}")
            if not self.dry_run:
                log.info(f"Stopping server {instance['name']}")
                self.cs.stopVirtualMachine(id=instance['id'])
                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {instance['name']}")
                self.cs.startVirtualMachine(id=instance['id'])
        else:
            log.info("No servers found")

        log.info(f"done")
