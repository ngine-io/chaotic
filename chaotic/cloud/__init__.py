from chaotic.log import log

class Chaotic():

    def configure(self, configs: dict, dry_run: bool) -> None:
        self.configs = configs
        self.dry_run = dry_run
        if self.dry_run:
            log.info(f"Running in dry-run")

    def action(self) -> None:
        raise NotImplementedError
