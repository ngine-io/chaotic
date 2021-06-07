import os
import requests
import random

from chaotic.cloud import Chaotic
from chaotic.log import log

NOMAD_ADDR: str = os.getenv('NOMAD_ADDR')
NOMAD_NAMESPACE: str = os.getenv('NOMAD_NAMESPACE')
NOMAD_TOKEN: str = os.getenv('NOMAD_TOKEN')
NOMAD_HTTP_AUTH: str = os.getenv('NOMAD_HTTP_AUTH')

class NomadChaotic(Chaotic):

    headers: dict = {
        "X-Nomad-Token": NOMAD_TOKEN,
    }

    def _get_auth(self) -> tuple:
        if NOMAD_HTTP_AUTH:
            return tuple(NOMAD_HTTP_AUTH.split(':'))

    def _get_namespace(self) -> str:
        if NOMAD_NAMESPACE:
            namespace = NOMAD_NAMESPACE
        else:
            allowed_ns = self.configs.get('namespace_allowlist')
            namespace = random.choice(allowed_ns) if allowed_ns else None

        log.info(f"Selected namespace: {namespace}")
        return namespace

    def _get_allocation(self) -> dict:
        namespace = self._get_namespace()

        try:
            r = requests.get(
                url=f"{NOMAD_ADDR}/v1/allocations",
                headers=self.headers,
                auth=self._get_auth(),
                timeout=5,
                params={
                    'namespace': namespace,
                },
            )
            r.raise_for_status()
            results = r.json()

        except Exception as err:
            log.error(err)
            return dict()

        if not results:
            log.info(f"No allocs in {namespace} found")
            return dict()

        alloc = random.choice(results)
        log.info(f"Selected alloc: {alloc['JobID']} (ID: {alloc['ID']}) on {alloc['NodeName']}")
        return alloc

    def _signal(self, alloc: dict) -> None:
        if alloc:
            signal = random.choice(self.configs['signals'])
            log.info(f"Selected signal: {signal}")

            if not self.dry_run:
                try:
                    r = requests.post(
                        url=f"{NOMAD_ADDR}/v1/client/allocation/{alloc['ID']}/signal",
                        headers=self.headers,
                        auth=self._get_auth(),
                        timeout=5,
                        json={
                            'Signal': signal
                        },
                    )
                    r.raise_for_status()
                except Exception as err:
                    log.error(err)

        log.info(f"done")

    def action(self) -> None:
        alloc = self._get_allocation()
        self._signal(alloc)
