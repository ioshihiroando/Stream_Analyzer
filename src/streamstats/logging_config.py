import logging
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def setup_logging() -> None:
    """ Функция для установки журнала логов. """
    log_path = ROOT / 'logs' / 'streamstats.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    formatter.converter = time.gmtime

    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )