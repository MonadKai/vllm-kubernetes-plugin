from .common.logger_plugin import register_logger_plugin
from .trace import register_trace_plugin

__all__ = ["register"]


def register():
    register_logger_plugin()
    register_trace_plugin()
