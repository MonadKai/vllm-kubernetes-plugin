"""
vllm trace plugin for kubernetes deployment
"""

import functools
import importlib
import inspect
import logging
import os
import uuid
from typing import Awaitable, Callable, Optional

import vllm.envs as envs
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .config.vllm_scanned_info import SCANNED_INFO
from .common.logger_plugin import reset_logger_config

logger = logging.getLogger(__name__)
reset_logger_config(logger)


class XRequestIdMiddleware:
    """
    Middleware the set's the X-Request-Id header for each response
    to a random uuid4 (hex) value if the header isn't already
    present in the request, otherwise use the provided request id.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    def __call__(self, scope: Scope, receive: Receive, send: Send) -> Awaitable[None]:
        if scope["type"] not in ("http", "websocket"):
            return self.app(scope, receive, send)

        # Extract the request headers.
        request_headers = Headers(scope=scope)

        async def send_with_request_id(message: Message) -> None:
            """
            Custom send function to mutate the response headers
            and append X-Request-Id to it.
            """
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(raw=message["headers"])
                request_id = request_headers.get("X-Request-Id", uuid.uuid4().hex)
                response_headers.append("X-Request-Id", request_id)
            await send(message)

        return self.app(scope, receive, send_with_request_id)


def add_trace_env_vars() -> None:
    additional_env_vars = {
        "VLLM_TRACE_METHODS_WITH_REQUEST_ID": lambda: os.getenv(
            "VLLM_TRACE_METHODS_WITH_REQUEST_ID", "True"
        ).lower()
        in ("true", "1"),
    }
    envs.environment_variables.update(additional_env_vars)


def parse_method_name(method_full_name: str) -> tuple[str, str, str]:
    """
    Parse method name format: module_name.class_name:method_name
    Example:
        vllm.core.scheduler:abort_seq_group
        vllm.distributed.kv_transfer.kv_connector.v1.nixl_connector.NixlConnectorMetadata:add_new_req
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:allocate_new_blocks
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:free
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:get_blocks
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:get_num_blocks_to_allocate
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:get_num_common_prefix_blocks
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:remove_skipped_blocks
        vllm.v1.core.kv_cache_coordinator.HybridKVCacheCoordinator:save_new_computed_blocks
    Args:
        method_full_name: full method name

    Returns:
        (module_name, class_name, method_name) tuple

    Raises:
        ValueError: if format is incorrect
    """
    if ":" not in method_full_name:
        raise ValueError(
            f"Invalid method name format: `{method_full_name}`. Expected format: `module.class:method`"
        )

    module_class_part, method_name = method_full_name.rsplit(":", 1)

    if "." not in module_class_part:
        raise ValueError(
            f"Invalid method name format: `{method_full_name}`. Expected format: `module.class:method`"
        )

    module_name, class_name = module_class_part.rsplit(".", 1)

    return module_name, class_name, method_name


def import_method(module_name: str, class_name: str, method_name: str) -> tuple:
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        logger.warning(f"Failed to import module `{module_name}`: {e}!")
        return None, None, None

    if not hasattr(module, class_name):
        logger.warning(f"Class `{class_name}` not found in module `{module_name}`!")
        return None, None, None
    class_obj = getattr(module, class_name)
    if not hasattr(class_obj, method_name):
        logger.warning(
            f"Method `{method_name}` not found in class `{class_name}` of module `{module_name}`!"
        )
        return None, None, None
    return module, class_obj, getattr(class_obj, method_name)


def get_request_id_index_in_args(original_method: Callable) -> Optional[int]:
    sig = inspect.signature(original_method)
    param_names = list(sig.parameters.keys())
    for param_name in ["request_id", "req_id"]:
        if param_name in param_names:
            return param_names.index(param_name)
    return None


def _safe_get_request_id_index(method_full_name: str) -> Optional[int]:
    """Safely get request_id index, return None if method not found"""
    module_name, class_name, method_name = parse_method_name(method_full_name)
    module, class_obj, method = import_method(module_name, class_name, method_name)
    if module is None or class_obj is None or method is None:
        return None
    return get_request_id_index_in_args(method)


REQUEST_ID_INDEX_IN_ARGS = {
    method_full_name: index
    for method_full_name in SCANNED_INFO["methods_with_request_id"]
    if (index := _safe_get_request_id_index(method_full_name)) is not None
}


def create_traced_method(
    module: object,
    class_obj: object,
    method: Callable,
    request_id_index: int,
) -> Callable:
    module_name = module.__name__
    class_name = class_obj.__name__
    method_name = method.__name__
    method_full_name = f"{module_name}.{class_name}.{method_name}"

    curr_logger = logging.getLogger(module_name)

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        request_id = kwargs.get("request_id") or args[request_id_index]

        if request_id is None:
            logger.warning(
                f"`request_id` not found in method {method_full_name}, executing without tracing"
            )
            return method(*args, **kwargs)

        curr_logger.info(
            f"[request_id={request_id}] Start calling method `{method_full_name}`"
        )
        result = method(*args, **kwargs)
        curr_logger.info(
            f"[request_id={request_id}] End calling method `{method_full_name}`"
        )
        return result

    return wrapper


def patch_all_methods_with_request_id():
    """Patch all methods with request_id"""
    methods_with_request_id = SCANNED_INFO["methods_with_request_id"]

    for method_full_name in methods_with_request_id:
        if method_full_name not in REQUEST_ID_INDEX_IN_ARGS:
            logger.warning(
                f"Skipping patching for method without request_id parameter: {method_full_name}"
            )
            continue
        module_name, class_name, method_name = parse_method_name(method_full_name)
        module, class_obj, method = import_method(module_name, class_name, method_name)
        if module is None or class_obj is None or method is None:
            logger.warning(
                f"Skipping patching for non-existent method: {method_full_name}"
            )
            continue

        request_id_index = REQUEST_ID_INDEX_IN_ARGS[method_full_name]

        traced_method = create_traced_method(
            module, class_obj, method, request_id_index
        )

        try:
            setattr(class_obj, method_name, traced_method)
            logger.info(f"Successfully patched method: {method_full_name}")
        except Exception as e:
            logger.error(f"Failed to patch method {method_full_name}: {e}")
            continue


def register_trace_plugin():
    add_trace_env_vars()
    if envs.VLLM_TRACE_METHODS_WITH_REQUEST_ID:
        # TODO: add XRequestIdMiddleware to the app according to the vllm version
        patch_all_methods_with_request_id()
