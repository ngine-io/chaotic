import os
import yaml
from chaotic.log import log

from chaotic import ChaoticFactory

def main() -> None:
    log.info(f"Starting")

    try:
        config_file = os.getenv('CHAOTIC_CONFIG', 'config.yaml')
        with open(config_file, "r") as infile:
            config = yaml.load(infile, Loader=yaml.FullLoader)

        chaos_factory = ChaoticFactory()
        chaos = chaos_factory.get_instance(config['kind'])
        chaos.configure(
            configs=config.get('configs') or dict(),
            dry_run=config.get('dry_run') or False
        )
        chaos.action()
    except Exception as ex:
        log.error(ex)

if __name__ == "__main__":
    main()
