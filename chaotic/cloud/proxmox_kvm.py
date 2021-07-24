import os
import random
import time
from proxmoxer import ProxmoxAPI

from chaotic.cloud import Chaotic
from chaotic.log import log

PROXMOX_API_HOST = os.getenv('PROXMOX_API_HOST')
PROXMOX_API_USER = os.getenv('PROXMOX_API_USER', 'root@pam')
PROXMOX_API_PASSWORD = os.getenv('PROXMOX_API_PASSWORD')
PROXMOX_API_VERIFY_SSL = bool(os.getenv('PROXMOX_API_VERIFY_SSL', False))


class ProxmoxKvmChaotic(Chaotic):

    def __init__(self) -> None:
        super().__init__()
        log.info(f"Proxmox host: {PROXMOX_API_HOST}")
        log.info(f"Proxmox user: {PROXMOX_API_USER}")

        self.pve = ProxmoxAPI(
            host=PROXMOX_API_HOST,
            user=PROXMOX_API_USER,
            password=PROXMOX_API_PASSWORD,
            verify_ssl=PROXMOX_API_VERIFY_SSL
        )

    def action(self) -> None:
        vms = self.pve.cluster.resources.get(type='vm')

        denylist = self.configs.get('denylist') or []
        vms = [vm for vm in vms if vm['status'] == "running" and vm['name'] not in denylist]

        if vms:
            vm = random.choice(vms)
            log.info(f"Choose VM ID={vm['vmid']}, name={vm['name']} on node={vm['node']}")

            min_uptime = self.configs.get('min_uptime')
            if min_uptime is not None:
                current = self.pve.nodes(vm['node']).qemu(vm['vmid']).status.current.get()
                required_uptime = min_uptime * 60
                if current['uptime'] < required_uptime:
                    log.info(f"VM {vm['name']} required uptime lower then {min_uptime} min: {current['uptime'] / 60:.2f}, skipping")
                    log.info(f"done")
                    return

            if not self.dry_run:
                log.info(f"Stopping VM {vm['name']}")
                self.pve.nodes(vm['node']).qemu(vm['vmid']).status.shutdown.post(forceStop=1)

                wait_before_restart = int(self.configs.get('wait_before_restart', 60))
                log.info(f"Sleeping for {wait_before_restart} seconds")
                time.sleep(wait_before_restart)

                log.info(f"Starting VM {vm['name']}")
                self.pve.nodes(vm['node']).qemu(vm['vmid']).status.start.post()

        else:
            log.info("No VMs found")

        log.info(f"done")
