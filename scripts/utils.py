import importlib
import inspect
import logging
import pkgutil
import warnings
from typing import List


def get_package_version(package_name: str) -> str:
    """Get package version"""
    try:
        import importlib.metadata

        return importlib.metadata.version(package_name)
    except ImportError:
        print(f"Warning: {package_name} not found, using default version")
        return "unknown"


def normalized_version(version: str) -> str:
    """Normalize version string"""
    return version.replace(".", "_").replace("-", "_").replace("+", "___")


def normalized_package_full_name(package_name: str, package_version: str) -> str:
    return f"{package_name}__v{normalized_version(package_version)}"


def find_logger_modules(root_module_name: str) -> List[str]:
    """Recursively find all modules containing a 'logger' variable of type logging.Logger.

    Args:
        root_module_name: The root module name to start traversing from

    Returns:
        List of module names containing logger variables
    """

    def _traverse_module(module_name: str, found_modules: List[str]) -> None:
        try:
            module = importlib.import_module(module_name)

            # Check for logger in current module's attributes
            for name, obj in inspect.getmembers(
                module, lambda x: isinstance(x, logging.Logger)
            ):
                if name == "logger":
                    found_modules.append(module_name)
                    break

            # Traverse submodules
            if hasattr(module, "__path__"):
                for _, name, is_pkg in pkgutil.iter_modules(module.__path__):
                    submodule_name = f"{module_name}.{name}"
                    _traverse_module(submodule_name, found_modules)

        except Exception as e:
            warnings.warn(f"Error traversing module {module_name}: {e}")

    modules_with_logger = []
    _traverse_module(root_module_name, modules_with_logger)
    return sorted(modules_with_logger)


def find_methods_with_request_id(
    root_module_name: str = "vllm", ignore_init: bool = True
) -> List[str]:
    """Recursively find all methods containing a 'request_id' or 'req_id' parameter.

    Args:
        root_module_name: root module name
        ignore_init: whether to ignore methods with __init__ name

    Returns:
        List of method names with 'request_id' or 'req_id' parameter
    """

    def _has_request_id_parameter(method) -> bool:
        """Check if the method contains 'request_id' or 'req_id' parameter"""
        try:
            signature = inspect.signature(method)
            parameter_names = list(signature.parameters.keys())
            return any(
                param_name in ["request_id", "req_id"] for param_name in parameter_names
            )
        except (ValueError, TypeError):
            return False

    def _traverse_module_for_methods(
        module_name: str, found_methods: List[str]
    ) -> None:
        try:
            module = importlib.import_module(module_name)

            # Check all classes in the current module
            for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
                # Only check classes defined in the current module (avoid imported classes)
                if class_obj.__module__ == module_name:
                    # Check all methods in the class using inspect.getmembers with a custom predicate
                    for method_name, method_obj in inspect.getmembers(class_obj):
                        # Check if it's a function, method, or other callable
                        if callable(method_obj) and _has_request_id_parameter(
                            method_obj
                        ):
                            # Skip __init__ if ignore_init is True
                            if ignore_init and method_name == "__init__":
                                continue

                            method_full_name = (
                                f"{module_name}.{class_name}:{method_name}"
                            )
                            if method_full_name not in found_methods:
                                found_methods.append(method_full_name)

            # Traverse submodules
            if hasattr(module, "__path__"):
                for _, submodule_name, is_pkg in pkgutil.iter_modules(module.__path__):
                    full_submodule_name = f"{module_name}.{submodule_name}"
                    _traverse_module_for_methods(full_submodule_name, found_methods)

        except Exception as e:
            warnings.warn(f"Error traversing module {module_name}: {e}")

    methods_with_request_id = []
    _traverse_module_for_methods(root_module_name, methods_with_request_id)
    return sorted(methods_with_request_id)
