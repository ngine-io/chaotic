from chaotic.cloud.vultr import VultrChaotic
from chaotic.cloud.cloudscale_ch import CloudscaleChChaotic
from chaotic.cloud.digitalocean import DigitaloceanChaotic
from chaotic.cloud.hcloud import HcloudChaotic
from chaotic.cloud.nomad import NomadChaotic
from chaotic.log import log


class ChaoticFactory:

    CLOUD_CLASSES: dict = {
        'cloudscale_ch': CloudscaleChChaotic,
        'hcloud': HcloudChaotic,
        'nomad': NomadChaotic,
        'digitalocean': DigitaloceanChaotic,
        'vultr': VultrChaotic,
    }

    def get_instance(self, name: str) -> object:
        log.info(f"Instantiate {name}")
        try:
            obj_class = self.CLOUD_CLASSES[name]
            return obj_class()
        except KeyError as e:
            msg = f"{e} not implemented"
            raise NotImplementedError(msg)
