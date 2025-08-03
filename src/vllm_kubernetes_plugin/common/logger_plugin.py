import logging
import os
from logging import Logger

import vllm.envs as envs

from ..utils import find_logger_modules

logger = logging.getLogger(__name__)


def make_stream_handler() -> logging.StreamHandler:
    return logging.StreamHandler()


def get_log_file_name() -> str:
    if os.path.exists("/workspace"):
        log_folder = "/workspace/logs"
    if os.path.exists("/vllm-workspace"):
        log_folder = "/vllm-workspace/logs"
    try:
        logger.info(f"Create vllm workspace log folder: {log_folder}")
        os.makedirs(log_folder, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create vllm workspace log folder: {e}")
        raise e

    log_fn = os.getenv("VLLM_LOG_FILENAME", "server.log")
    return f"{log_folder}/{log_fn}"


def get_log_file_max_bytes() -> int:
    max_bytes = os.getenv("VLLM_LOG_FILE_MAX_BYTES", 8388608)
    return int(max_bytes)


def get_log_file_backup_count() -> int:
    backup_count = os.getenv("VLLM_LOG_FILE_BACKUP_COUNT", 5)
    return int(backup_count)


def make_file_handler() -> logging.handlers.RotatingFileHandler:
    return logging.handlers.RotatingFileHandler(
        filename=get_log_file_name(),
        maxBytes=get_log_file_max_bytes(),
        backupCount=get_log_file_backup_count(),
        encoding="utf8",
    )


def make_kubernetes_formatter() -> logging.Formatter:
    APP_NAME = os.getenv("APP_NAME", "standalone")
    _FORMAT = f"%(asctime)s.%(msecs)03d [{APP_NAME}] [%(threadName)s] %(levelname)s [%(name)s.%(funcName)s] [-] %(message)s"
    _DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    return logging.Formatter(fmt=_FORMAT, datefmt=_DATE_FORMAT)


def change_logger_config_to_kubernetes(logger: Logger) -> None:
    logger.handlers.clear()

    stream = make_stream_handler()
    file = make_file_handler()
    handlers = [stream, file]

    formatter = make_kubernetes_formatter()
    log_level = envs.VLLM_LOGGING_LEVEL

    for handler in handlers:
        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        logger.addHandler(handler)


def patch_all_loggers():
    root_modules = os.getenv("LOG_ROOT_MODULES", "vllm")
    root_modules = root_modules.split(",")
    for root_module in root_modules:
        logger_modules = find_logger_modules(root_module)
        for logger_module in logger_modules:
            logger = logging.getLogger(logger_module)
            change_logger_config_to_kubernetes(logger)
