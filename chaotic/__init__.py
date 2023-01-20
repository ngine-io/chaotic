from chaotic.cloud.cloudscale_ch import CloudscaleChChaotic
from chaotic.cloud.cloudstack import CloudStackChaotic
from chaotic.cloud.digitalocean import DigitaloceanChaotic
from chaotic.cloud.exoscale import ExoscaleChaotic
from chaotic.cloud.hcloud import HcloudChaotic
from chaotic.cloud.nomad import NomadChaotic
from chaotic.cloud.proxmox_kvm import ProxmoxKvmChaotic
from chaotic.cloud.vultr import VultrChaotic
from chaotic.log import log


class ChaoticFactory:

    CLOUD_CLASSES: dict = {
        "cloudscale_ch": CloudscaleChChaotic,
        "cloudstack": CloudStackChaotic,
        "digitalocean": DigitaloceanChaotic,
        "exoscale": ExoscaleChaotic,
        "hcloud": HcloudChaotic,
        "nomad": NomadChaotic,
        "proxmox_kvm": ProxmoxKvmChaotic,
        "vultr": VultrChaotic,
    }

    def get_instance(self, name: str) -> object:
        log.info(f"Instantiate {name}")
        try:
            return self.CLOUD_CLASSES[name]()
        except KeyError as e:
            raise NotImplementedError(f"{e} not implemented")
