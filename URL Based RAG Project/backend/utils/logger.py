import logging
import os

from backend.utils.config import LOG_PATH, LOG_LEVEL

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

resolved_level = _LEVEL_MAP.get(LOG_LEVEL, logging.INFO)

_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

_file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
_file_handler.setLevel(resolved_level)
_file_handler.setFormatter(_formatter)

_console_handler = logging.StreamHandler()
_console_handler.setLevel(resolved_level)
_console_handler.setFormatter(_formatter)

_root_logger = logging.getLogger()

if not _root_logger.handlers:
    _root_logger.setLevel(resolved_level)
    _root_logger.addHandler(_file_handler)
    _root_logger.addHandler(_console_handler)
else:
    _root_logger.setLevel(resolved_level)


def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(resolved_level)
    return logger