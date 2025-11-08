import json
import os
import sys
import time
from argparse import ArgumentParser

import requests
import schedule
import truststore
import yaml
from requests.models import Response

from chaotic import ChaoticFactory
from chaotic.cloud import Chaotic
from chaotic.log import log
from chaotic.version import __version__

truststore.inject_into_ssl()

def app(config_source: str) -> None:
    print("")
    try:
        config: dict = dict()
        config_source: str = os.getenv('CHAOTIC_CONFIG', config_source)

        if config_source.startswith("http"):
            res: Response = requests.get(
                url=config_source,
            )
            res.raise_for_status()
            config = res.json()

        elif config_source.endswith(('.yaml', '.yml')):
            with open(config_source, "r") as infile:
                config = yaml.load(infile, Loader=yaml.FullLoader)
                infile.close()

        elif config_source.endswith('json'):
            with open(config_source, "r") as infile:
                config = json.load(infile)
                infile.close()

        if not config:
            raise Exception("Empty config file")

        if 'kind' not in config:
            raise Exception("No kind defined")

        chaos_factory: ChaoticFactory = ChaoticFactory()
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

def run_periodic(interval: int = 1, config_source: str = "config.yaml") -> None:
    log.info(f"Running periodic in intervals of {interval} minute")
    schedule.every(interval).minutes.do(app, config_source=config_source)
    time.sleep(1)
    schedule.run_all()
    while True:
        schedule.run_pending()
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(1)

def main() -> None:
    parser: ArgumentParser = ArgumentParser()
    parser.add_argument("--periodic", help="run periodic", action="store_true")
    parser.add_argument("--interval", help="set interval in minutes", type=int, default=1)
    parser.add_argument("--version", help="show version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--config", help="use config file", type=str, default="config.yaml")
    args = parser.parse_args()

    log.info(f"Starting version {__version__}")

    if args.periodic:
        try:
            run_periodic(interval=args.interval, config_source=args.config)
        except KeyboardInterrupt:
            print("")
            log.info(f"Stopping...")
            schedule.clear()
            log.info(f"done")
            pass
    else:
        app(config_source=args.config)

if __name__ == "__main__":
    main()
