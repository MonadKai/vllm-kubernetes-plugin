from .common.logger_plugin import register_logger_plugin
from .trace import register_trace_plugin
from .middleware import register_log_request_response_plugin

__all__ = ["register"]


def register():
    register_logger_plugin()
    register_trace_plugin()
    register_log_request_response_plugin()
