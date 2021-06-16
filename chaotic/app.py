import os
import sys
import yaml
from chaotic.log import log

from chaotic import ChaoticFactory

def main() -> None:
    log.info(f"Starting")

    try:
        config_file = os.getenv('CHAOTIC_CONFIG', 'config.yaml')
        with open(config_file, "r") as infile:
            config = yaml.load(infile, Loader=yaml.FullLoader)

        if not config:
            raise Exception("Empty config file")

        if 'kind' not in config:
            raise Exception("No kind defined")

        chaos_factory = ChaoticFactory()
        chaos = chaos_factory.get_instance(config['kind'])
        chaos.configure(
            configs=config.get('configs') or dict(),
            dry_run=config.get('dry_run') or False,
            excludes=config.get('excludes') or dict(),
        )
        chaos.action()
    except Exception as ex:
        log.error(ex)
        sys.exit(1)

if __name__ == "__main__":
    main()
