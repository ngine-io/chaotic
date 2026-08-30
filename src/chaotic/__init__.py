from chaotic.log import log
from chaotic.providers import (
    Chaotic,
    CloudscaleChChaotic,
    CloudStackChaotic,
    DigitaloceanChaotic,
    HcloudChaotic,
    NomadChaotic,
    ProxmoxChaotic,
    VultrChaotic,
)


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
