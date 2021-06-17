import os
import sys
import yaml
import time
import schedule
import argparse

from chaotic.log import log
from chaotic.version import __version__

from chaotic import ChaoticFactory

def app() -> None:
    print("")
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

def run_periodic(interval: int = 1) -> None:
    log.info(f"Running periodic in intervals of {interval} minute")
    schedule.every(interval).minutes.do(app)
    time.sleep(1)
    schedule.run_all()
    while True:
        schedule.run_pending()
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(1)

def main() -> None:
    log.info(f"Starting version {__version__}")

    parser = argparse.ArgumentParser()
    parser.add_argument("--periodic", help="Run periodic", action="store_true")
    parser.add_argument("--interval", help="Interval in minutes", type=int, default=1)
    args = parser.parse_args()

    if args.periodic:
        try:
            run_periodic(args.interval)
        except KeyboardInterrupt:
            log.info(f"Stopping...")
            schedule.clear()
            log.info(f"done")
            pass
    else:
        app()

if __name__ == "__main__":
    main()
