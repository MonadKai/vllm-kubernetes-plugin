import pkgutil
import importlib
import inspect
import logging
from typing import List


logger = logging.getLogger(__name__)


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
            for name, obj in inspect.getmembers(module, lambda x: isinstance(x, logging.Logger)):
                if name == "logger":
                    found_modules.append(module_name)
                    break
            
            # Traverse submodules
            if hasattr(module, "__path__"):
                for _, name, is_pkg in pkgutil.iter_modules(module.__path__):
                    submodule_name = f"{module_name}.{name}"
                    _traverse_module(submodule_name, found_modules)
                    
        except Exception as e:
            logger.warning(f"Error traversing module {module_name}: {e}")
    
    modules_contain_logger = []
    _traverse_module(root_module_name, modules_contain_logger)
    return sorted(modules_contain_logger)
