import os
import logging

from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(
    level=os.environ.get('CHAOTIC_LOG_LEVEL', 'INFO').upper(),
    format='%(asctime)s - %(name)s:%(levelname)s:%(message)s')

log = logging.getLogger('chatic')
log.debug('Init')
