import importlib
import warnings

__all__ = [
    "get_package_version",
    "normalized_package_full_name",
    "get_package_scanned_info_module",
]


def get_package_version(package_name: str) -> str:
    """Get package version"""
    try:
        return importlib.metadata.version(package_name)
    except ImportError:
        print(f"Warning: {package_name} not found, using default version")
        return "unknown"


def normalized_version(version: str) -> str:
    """Normalize version string"""
    return version.replace(".", "_")


def normalized_package_full_name(package_name: str, package_version: str) -> str:
    return f"{package_name}__v{normalized_version(package_version)}"


def get_package_scanned_info_module(package_name: str) -> str:
    package_version = get_package_version(package_name)
    package_full_name = normalized_package_full_name(package_name, package_version)
    package_scanned_info_module = None
    try:
        package_scanned_info_module = importlib.import_module(
            f"vllm_kubernetes_plugin.package_scanned_info.{package_full_name}"
        )
    except Exception as e:
        warnings.warn(
            f"Failed to import module `vllm_kubernetes_plugin.package_scanned_info.{package_full_name}`: {e}"
        )
    return package_scanned_info_module
