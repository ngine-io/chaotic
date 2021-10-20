import os
import sys
import logging
from logging.config import fileConfig
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

logging_config_file_path = os.environ.get('CHAOTIC_LOG_CONFIG', 'logging.ini')

logging_config = Path(logging_config_file_path)
if logging_config.is_file():
    fileConfig(logging_config_file_path)
else:
    logging.basicConfig(
        stream=sys.stdout,
        level=os.environ.get('CHAOTIC_LOG_LEVEL', 'INFO').upper(),
        format='%(asctime)s - %(name)s:%(levelname)s:%(message)s')

log = logging.getLogger('chaotic')
log.debug('Init')
