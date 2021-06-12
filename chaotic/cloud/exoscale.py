import os
import random
import time
from cs import CloudStack

from chaotic.cloud.cloudstack import CloudStackChaotic
from chaotic.log import log

EXOSCALE_API_ENDPOINT: str = "https://api.exoscale.com/compute"
EXOSCALE_API_KEY: str = os.getenv('EXOSCALE_API_KEY')
EXOSCALE_API_SECRET: str = os.getenv('EXOSCALE_API_SECRET')


class ExoscaleChaotic(CloudStackChaotic):

    def __init__(self) -> None:
        self.cs = CloudStack(
            endpoint=EXOSCALE_API_ENDPOINT,
            key=EXOSCALE_API_KEY,
            secret=EXOSCALE_API_SECRET,
        )
