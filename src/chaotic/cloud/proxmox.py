import os
import random
import time

from proxmoxer import ProxmoxAPI

from chaotic.cloud import Chaotic
from chaotic.log import log

PROXMOX_API_HOST: str = os.getenv("PROXMOX_API_HOST", "")
PROXMOX_API_USER: str = os.getenv("PROXMOX_API_USER", 'root@pam')
PROXMOX_API_TOKEN: str = os.getenv("PROXMOX_API_TOKEN", "")
PROXMOX_API_PASSWORD: str = os.getenv("PROXMOX_API_PASSWORD", "")
PROXMOX_API_VERIFY_SSL: bool = bool(os.getenv('PROXMOX_API_VERIFY_SSL', False))

class ProxmoxChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        if '!' in PROXMOX_API_USER:
            log.info("Using API token authentication")

            if not PROXMOX_API_TOKEN:
                raise ValueError("PROXMOX_API_TOKEN must be set when using token authentication")

            if PROXMOX_API_PASSWORD:
                raise ValueError("PROXMOX_API_PASSWORD must NOT be set when using token authentication")

            log.debug(f"Proxmox API token: {PROXMOX_API_TOKEN[0:3]}***")
            token_name: str = PROXMOX_API_USER.split('!')[1]
            proxmox_api_user = PROXMOX_API_USER.split('!')[0]
        else:
            log.info("Using user/password authentication")
            if not PROXMOX_API_PASSWORD:
                raise ValueError("PROXMOX_API_PASSWORD must be set when not using token authentication")

            if PROXMOX_API_TOKEN:
                raise ValueError("PROXMOX_API_TOKEN must NOT be set when not using token authentication")

            log.debug(f"Proxmox password: {PROXMOX_API_PASSWORD[0:3]}***")
            token_name: str = None
            proxmox_api_user = PROXMOX_API_USER

        log.info(f"Proxmox host: {PROXMOX_API_HOST}")
        log.info(f"Proxmox user: {proxmox_api_user}")
        log.info(f"Proxmox verify SSL: {PROXMOX_API_VERIFY_SSL}")

        log.info("Connecting to Proxmox API")

        self.pve = ProxmoxAPI(
            host=PROXMOX_API_HOST,
            user=proxmox_api_user,
            password=PROXMOX_API_PASSWORD or None,
            token_name=token_name,
            token_value=PROXMOX_API_TOKEN or None,
            verify_ssl=PROXMOX_API_VERIFY_SSL
        )

    def action(self) -> None:
        available_vms: list = self.pve.cluster.resources.get(type='vm')

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
                    current = self.pve.nodes(vm['node']).lxc(vm['vmid']).status.current.get()
                else:
                    current = self.pve.nodes(vm['node']).qemu(vm['vmid']).status.current.get()
                required_uptime = min_uptime * 60
                if current['uptime'] < required_uptime:
                    log.info(f"VM {vm['name']} required uptime lower then {min_uptime} min: {current['uptime'] / 60:.2f}, skipping")
                    log.info(f"done")
                    return

            if not self.dry_run:
                log.info(f"Stopping VM {vm['name']}")
                if vm['type'] == 'lxc':
                    self.pve.nodes(vm['node']).lxc(vm['vmid']).status.shutdown.post(forceStop=1)
                else:
                    self.pve.nodes(vm['node']).qemu(vm['vmid']).status.shutdown.post(forceStop=1)

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting VM {vm['name']}")
                if vm['type'] == 'lxc':
                    self.pve.nodes(vm['node']).lxc(vm['vmid']).status.start.post()
                else:
                    self.pve.nodes(vm['node']).qemu(vm['vmid']).status.start.post()

        else:
            log.info("No VMs found")

        log.info(f"done")
