"""
vllm logger plugin for kubernetes deployment
"""

import importlib
import logging
import logging.handlers
import os
import warnings

import vllm.envs as envs

_log_folder_created = False

DEFAULT_APP_NAME = "standalone"
DEFAULT_LOG_ROOT_MODULES = "vllm"
DEFAULT_LOG_FORMAT = "%(asctime)s.%(msecs)03d [{app_name}] [%(threadName)s] %(levelname)s [%(name)s.%(funcName)s] [-] %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_FILENAME = "api_server.log"
DEFAULT_LOG_FILE_MAX_BYTES = "8388608"
DEFAULT_LOG_FILE_BACKUP_COUNT = "5"


def add_logger_env_vars() -> None:
    """Setup additional environment variables for vLLM logger plugin"""
    additional_env_vars = {
        # kubernetes application name
        "APP_NAME": lambda: os.getenv("APP_NAME", DEFAULT_APP_NAME),
        # root module list for log module scanning
        "LOG_ROOT_MODULES": lambda: os.getenv(
            "LOG_ROOT_MODULES", DEFAULT_LOG_ROOT_MODULES
        ),
        "VLLM_LOG_FORMAT": lambda: os.getenv("VLLM_LOG_FORMAT", DEFAULT_LOG_FORMAT),
        "VLLM_LOG_DATE_FORMAT": lambda: os.getenv(
            "VLLM_LOG_DATE_FORMAT", DEFAULT_DATE_FORMAT
        ),
        "VLLM_LOG_FILENAME": lambda: os.getenv(
            "VLLM_LOG_FILENAME", DEFAULT_LOG_FILENAME
        ),
        "VLLM_LOG_FILE_MAX_BYTES": lambda: int(
            os.getenv("VLLM_LOG_FILE_MAX_BYTES", DEFAULT_LOG_FILE_MAX_BYTES)
        ),
        "VLLM_LOG_FILE_BACKUP_COUNT": lambda: int(
            os.getenv("VLLM_LOG_FILE_BACKUP_COUNT", DEFAULT_LOG_FILE_BACKUP_COUNT)
        ),
    }

    envs.environment_variables.update(additional_env_vars)


add_logger_env_vars()


def make_stream_handler() -> logging.StreamHandler:
    return logging.StreamHandler()


def default_log_folder() -> str:
    if os.path.exists("/workspace"):
        return "/workspace/logs"
    if os.path.exists("/vllm-workspace"):
        return "/vllm-workspace/logs"
    return "/tmp/logs"


def ensure_log_folder_exists() -> None:
    global _log_folder_created

    if not _log_folder_created:
        log_folder = default_log_folder()
        try:
            os.makedirs(log_folder, exist_ok=True)
            _log_folder_created = True
        except Exception as e:
            warnings.warn(f"Failed to create log folder {log_folder}: {e}")


def get_log_file_name() -> str:
    ensure_log_folder_exists()
    return f"{default_log_folder()}/{envs.VLLM_LOG_FILENAME}"


def make_file_handler() -> logging.handlers.RotatingFileHandler:
    return logging.handlers.RotatingFileHandler(
        filename=get_log_file_name(),
        maxBytes=envs.VLLM_LOG_FILE_MAX_BYTES,
        backupCount=envs.VLLM_LOG_FILE_BACKUP_COUNT,
        encoding="utf8",
    )


def make_kubernetes_formatter() -> logging.Formatter:
    fmt = envs.VLLM_LOG_FORMAT
    if "{app_name}" in fmt:
        fmt = fmt.format(app_name=envs.APP_NAME)
    datefmt = envs.VLLM_LOG_DATE_FORMAT
    return logging.Formatter(fmt=fmt, datefmt=datefmt)


def reset_logger_config(logger: logging.Logger) -> None:
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


def safe_import_logger(module_name: str) -> logging.Logger:
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "logger"):
            return module.logger
        else:
            return logging.getLogger(module_name)
    except Exception as e:
        warnings.warn(f"Failed to import logger module {module_name}: {e}")
        return logging.getLogger(module_name)


def patch_all_loggers():
    root_modules = envs.LOG_ROOT_MODULES
    root_modules = root_modules.split(",")
    for root_module in root_modules:
        if root_module == "vllm":
            from ..config.vllm_scanned_info import SCANNED_INFO

            logger_modules = SCANNED_INFO["modules_with_logger"]
            for logger_module in logger_modules:
                logger = safe_import_logger(logger_module)
                reset_logger_config(logger)
        else:
            warnings.warn(f"Unsupported root module: {root_module}")


def register_logger_plugin():
    if envs.VLLM_LOGGING_CONFIG_PATH or envs.VLLM_CONFIGURE_LOGGING == 1:
        warnings.warn(
            "logger plugin is not supported when `VLLM_LOGGING_CONFIG_PATH` is set or `VLLM_CONFIGURE_LOGGING` is 1, skipping k8s logger plugin"
        )
        return

    patch_all_loggers()
