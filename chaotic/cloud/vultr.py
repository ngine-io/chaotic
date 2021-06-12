import os
import random
import time
import requests
from typing import List

from chaotic.cloud import Chaotic
from chaotic.log import log

VULTR_API_KEY: str = os.getenv('VULTR_API_KEY')


class Vultr:

    VULTR_API_URL: str = "https://api.vultr.com/v2"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def query_api(self, method: str, path: str, params: dict = None, json: dict = None) -> requests.Response:
        r = requests.request(
            method=method,
            url=f"{self.VULTR_API_URL}/{path}",
            headers={
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': "application/json",
            },
            params=params,
            json=json,
            timeout=10,
        )
        r.raise_for_status()
        return r

    def list_instances(self, tag=None, label=None) -> List[dict]:
        params = {
            'tag': tag,
            'label': label,
        }
        r = self.query_api('get', 'instances', params=params)
        return r.json().get('instances', dict())

    def halt_instances(self, instance_ids: List[str]) -> None:
        json = {
            'instance_ids': instance_ids,
        }
        self.query_api('post', f'instances/halt', json=json)

    def halt_instance(self, instance_id: str) -> None:
        self.halt_instances(instance_ids=[instance_id])

    def start_instance(self, instance_id: str) -> None:
        self.query_api('post', f'instances/{instance_id}/start')


class VultrChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        self.vultr = Vultr(api_key=VULTR_API_KEY)

    def action(self) -> None:
        tag = self.configs.get('tag')
        log.info(f"Querying with tag: {tag}")
        instances = self.vultr.list_instances(tag=tag)

        if instances:
            instance = random.choice(instances)
            log.info(f"Choose server {instance['label']}")
            if not self.dry_run:
                log.info(f"Stopping server {instance['label']}")
                self.vultr.halt_instance(instance['id'])

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for server {wait_before_restart}")
                time.sleep(wait_before_restart)

                log.info(f"Starting server {instance['label']}")
                self.vultr.start_instance(instance['id'])
        else:
            log.info("No servers found")

        log.info(f"done")
