from abc import ABC, abstractmethod
from datetime import datetime
from chaotic.log import log

class Chaotic(ABC):

    def configure(self, configs: dict, dry_run: bool, excludes: dict) -> None:
        self.configs = configs
        self.dry_run = dry_run
        self.excludes = excludes
        if self.dry_run:
            log.info(f"Running in dry-run")
        self._handle_excludes()

    def _handle_excludes(self) -> None:
        if 'days_of_year' in self.excludes:
            today = datetime.today().strftime('%b%d')
            if today in self.excludes['days_of_year']:
                log.info(f"Today '{today}' in days_of_year excludes, running dry-run")
                self.dry_run = True

        if 'weekdays' in self.excludes:
            today = datetime.today().strftime('%a')
            if today in self.excludes['weekdays']:
                log.info(f"Today '{today}' in weekday excludes, running dry-run")
                self.dry_run = True

        if 'times_of_day' in self.excludes:
            now = datetime.now().time()
            for time_range in self.excludes['times_of_day']:
                start, end = time_range.split('-')
                start_time = datetime.strptime(start, "%H:%M").time()
                end_time = datetime.strptime(end, "%H:%M").time()
                if start_time > end_time:
                    end_of_day = datetime.strptime("23:59", "%H:%M").time()
                    if start_time <= now <= end_of_day:
                        log.info(f"Exclude {start_time}-{end_time}")
                        log.info(f"{now} in time of day excludes, running dry-run")
                        self.dry_run = True

                    start_of_day = datetime.strptime("00:01", "%H:%M").time()
                    if start_of_day <= now <= end_time:
                        log.info(f"Exclude {start_time}-{end_time}")
                        log.info(f"{now} in time of day excludes, running dry-run")
                        self.dry_run = True
                else:
                    if start_time <= now <= end_time:
                        log.info(f"Exclude {start_time}-{end_time}")
                        log.info(f"{now} in time of day excludes, running dry-run")
                        self.dry_run = True

    @abstractmethod
    def action(self) -> None:
        pass
