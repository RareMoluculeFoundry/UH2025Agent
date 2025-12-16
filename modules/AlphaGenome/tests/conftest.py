"""
Pytest configuration for AlphaGenome tests.

Sets up proper import paths for the module code.
"""

import sys
from pathlib import Path

# Add the module root to the path so we can import from 'code'
module_root = Path(__file__).parent.parent
sys.path.insert(0, str(module_root))
