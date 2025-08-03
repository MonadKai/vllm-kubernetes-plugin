from .common.logger_plugin import patch_all_loggers

__all__ = ["register"]


def register():
    patch_all_loggers()
