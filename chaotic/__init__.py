from chaotic.cloud import Chaotic
from chaotic.cloud.cloudscale_ch import CloudscaleChChaotic
from chaotic.cloud.cloudstack import CloudStackChaotic
from chaotic.cloud.digitalocean import DigitaloceanChaotic
from chaotic.cloud.hcloud import HcloudChaotic
from chaotic.cloud.nomad import NomadChaotic
from chaotic.cloud.proxmox import ProxmoxChaotic
from chaotic.cloud.vultr import VultrChaotic
from chaotic.log import log


class ChaoticFactory:

    CLOUD_CLASSES: dict = {
        "cloudscale_ch": CloudscaleChChaotic,
        "cloudstack": CloudStackChaotic,
        "digitalocean": DigitaloceanChaotic,
        "hcloud": HcloudChaotic,
        "nomad": NomadChaotic,
        "proxmox": ProxmoxChaotic,
        "vultr": VultrChaotic,
    }

    def get_instance(self, name: str) -> Chaotic:
        if name is None:
            raise ValueError("Cloud name must be provided")

        log.info(f"Instantiate {name}")
        try:
            return self.CLOUD_CLASSES[name]()
        except KeyError as e:
            raise NotImplementedError(f"{e} not implemented")
