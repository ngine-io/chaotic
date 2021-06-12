import os
import requests
import random
from typing import List

from chaotic.cloud import Chaotic
from chaotic.log import log

NOMAD_ADDR: str = os.getenv('NOMAD_ADDR')
NOMAD_NAMESPACE: str = os.getenv('NOMAD_NAMESPACE')
NOMAD_TOKEN: str = os.getenv('NOMAD_TOKEN')
NOMAD_HTTP_AUTH: str = os.getenv('NOMAD_HTTP_AUTH')


class Nomad:

    def __init__(self, api_key: str, api_url: str = None, api_auth: str = None) -> None:
        self.api_key = api_key
        self.api_url = api_url or "http://localhost:4646"
        self.api_auth = tuple(api_auth.split(':')) if api_auth else None

    def query_api(self, method: str, path: str, params: dict = None, json: dict = None) -> requests.Response:
        r = requests.request(
            method=method,
            url=f"{self.api_url}/v1/{path}",
            headers={
                'X-Nomad-Token': self.api_key,
                'Content-Type': "application/json",
            },
            auth=self.api_auth,
            params=params,
            json=json,
            timeout=10,
        )
        r.raise_for_status()
        return r

    def list_allocs(self, namespace: str = None) -> List[dict]:
        params = {
            'namespace': namespace,
        }
        r = self.query_api('get', 'allocations', params=params)
        return r.json()

    def signal_alloc(self, alloc_id: str, signal: str) -> None:
        json = {
            'Signal': signal,
        }
        self.query_api('post', f'client/allocation/{alloc_id}/signal', json=json)


class NomadChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        self.nomad = Nomad(
            api_key=NOMAD_TOKEN,
            api_url=NOMAD_ADDR,
            api_auth=NOMAD_HTTP_AUTH,
        )

    def _get_namespace(self) -> str:
        if NOMAD_NAMESPACE:
            namespace = NOMAD_NAMESPACE
        else:
            allowed_ns = self.configs.get('namespace_allowlist')
            namespace = random.choice(allowed_ns) if allowed_ns else None

        log.info(f"Selected namespace: {namespace}")
        return namespace

    def action(self) -> None:
        namespace = self._get_namespace()
        allocs = self.nomad.list_allocs(namespace=namespace)
        if allocs:
            alloc = random.choice(allocs)
            log.info(f"Selected alloc: {alloc['JobID']} (ID: {alloc['ID']}) on {alloc['NodeName']}")
            signal = random.choice(self.configs['signals'])
            log.info(f"Selected signal: {signal}")
            if not self.dry_run:
                self.nomad.signal_alloc(alloc_id=alloc['ID'], signal=signal)
        else:
            log.info("No allocs found")

        log.info(f"done")
