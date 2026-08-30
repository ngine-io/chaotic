import os
from functools import cached_property
import random
import time

from proxmoxer import ProxmoxAPI

from chaotic.providers.base import Chaotic
from chaotic.log import log

class ProxmoxChaotic(Chaotic):

    @cached_property
    def client(self) -> ProxmoxAPI:
        """API client, created on first use so that importing stays side effect free."""
        return self._build_client()

    def _build_client(self) -> ProxmoxAPI:
        host = os.getenv("PROXMOX_API_HOST", "")
        user = os.getenv("PROXMOX_API_USER", "root@pam")
        token = os.getenv("PROXMOX_API_TOKEN", "")
        password = os.getenv("PROXMOX_API_PASSWORD", "")
        # Note: this is truthiness on the raw string, so *any* non-empty value —
        # including "false" — enables verification. Kept as-is for backwards
        # compatibility with existing deployments.
        verify_ssl = bool(os.getenv("PROXMOX_API_VERIFY_SSL", ""))

        if '!' in user:
            log.info("Using API token authentication")

            if not token:
                raise ValueError("token must be set when using token authentication")

            if password:
                raise ValueError("password must NOT be set when using token authentication")

            log.debug(f"Proxmox API token: {token[0:3]}***")
            token_name: str = user.split('!')[1]
            proxmox_api_user = user.split('!')[0]
        else:
            log.info("Using user/password authentication")
            if not password:
                raise ValueError("password must be set when not using token authentication")

            if token:
                raise ValueError("token must NOT be set when not using token authentication")

            log.debug(f"Proxmox password: {password[0:3]}***")
            token_name: str = None
            proxmox_api_user = user

        log.info(f"Proxmox host: {host}")
        log.info(f"Proxmox user: {proxmox_api_user}")
        log.info(f"Proxmox verify SSL: {verify_ssl}")

        log.info("Connecting to Proxmox API")

        return ProxmoxAPI(
            host=host,
            user=proxmox_api_user,
            password=password or None,
            token_name=token_name,
            token_value=token or None,
            verify_ssl=verify_ssl
        )

    def action(self) -> None:
        available_vms: list = self.client.cluster.resources.get(type='vm')

        denylist: list = self.configs.get('denylist') or []
        skip_tag: str = self.configs.get('skip_tag')
        filter_tag: str = self.configs.get('filter_tag')

        vms = list()
        for vm in available_vms:
            if filter_tag and ('tags' not in vm or filter_tag not in vm['tags'].split(';')):
                log.debug(f"VM {vm['name']} does not have filter_tag '{filter_tag}', skipping")
                continue
            if vm['status'] != "running":
                log.debug(f"VM {vm['name']} not running, skipping")
                continue
            if vm['name'] in denylist:
                log.debug(f"VM {vm['name']} in denylist, skipping")
                continue
            if skip_tag and 'tags' in vm and skip_tag in vm['tags'].split(';'):
                log.debug(f"VM {vm['name']} has skip_tag '{skip_tag}', skipping")
                continue
            vms.append(vm)

        if vms:
            vm: dict = random.choice(vms)
            log.info(f"Choose VM id={vm['vmid']}, name={vm['name']} on node={vm['node']}")
            log.debug(f"VM info: {vm}")

            min_uptime = self.configs.get('min_uptime')
            if min_uptime is not None:
                if vm['type'] == 'lxc':
                    current = self.client.nodes(vm['node']).lxc(vm['vmid']).status.current.get()
                else:
                    current = self.client.nodes(vm['node']).qemu(vm['vmid']).status.current.get()
                required_uptime = min_uptime * 60
                if current['uptime'] < required_uptime:
                    log.info(f"VM {vm['name']} required uptime lower then {min_uptime} min: {current['uptime'] / 60:.2f}, skipping")
                    log.info(f"done")
                    return

            if not self.dry_run:
                log.info(f"Stopping VM {vm['name']}")
                if vm['type'] == 'lxc':
                    self.client.nodes(vm['node']).lxc(vm['vmid']).status.shutdown.post(forceStop=1)
                else:
                    self.client.nodes(vm['node']).qemu(vm['vmid']).status.shutdown.post(forceStop=1)

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting VM {vm['name']}")
                if vm['type'] == 'lxc':
                    self.client.nodes(vm['node']).lxc(vm['vmid']).status.start.post()
                else:
                    self.client.nodes(vm['node']).qemu(vm['vmid']).status.start.post()

        else:
            log.info("No VMs found")

        log.info(f"done")
