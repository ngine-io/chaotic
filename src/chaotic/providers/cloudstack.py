import os
from functools import cached_property
import random
import time

from cs import CloudStack

from chaotic.providers.base import Chaotic
from chaotic.log import log

class CloudStackChaotic(Chaotic):

    @cached_property
    def client(self) -> CloudStack:
        """API client, created on first use so that importing stays side effect free."""
        return CloudStack(
            endpoint=os.getenv("CLOUDSTACK_API_ENDPOINT", ""),
            key=os.getenv("CLOUDSTACK_API_KEY", ""),
            secret=os.getenv("CLOUDSTACK_API_SECRET", ""),
        )

    def action(self) -> None:
        tag = self.configs.get("tag")
        if not tag:
            return

        log.info(f"Querying with tag: {tag['key']}={tag['value']}")

        instances = self.client.listVirtualMachines(
            tags=[tag],
            projectid=self.configs.get('projectid'),
            zoneid=self.configs.get('zoneid'),
            fetch_list=True,
        )
        if instances:
            instance = random.choice(instances)
            log.info(f"Choose server {instance['name']}")
            if not self.dry_run:
                log.info(f"Stopping server {instance['name']}")
                self.client.stopVirtualMachine(id=instance['id'])
                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {instance['name']}")
                self.client.startVirtualMachine(id=instance['id'])
        else:
            log.info("No servers found")

        log.info(f"done")
