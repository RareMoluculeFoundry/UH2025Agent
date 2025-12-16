"""
Pytest configuration for AlphaMissense tests.

Sets up proper import paths for the module code.
"""

import sys
from pathlib import Path

# Add the module root to the path so we can import from 'code'
module_root = Path(__file__).parent.parent
sys.path.insert(0, str(module_root))

# Also add as 'alphamissense' package alias
import importlib.util

def load_module_as(path: Path, name: str):
    """Load a module file under a given name."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    return None
