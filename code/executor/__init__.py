"""
Topology execution package.

Provides executors for different platforms:
- LocalExecutor: Local execution via Papermill
- PapermillRunner: Backend-aware Papermill wrapper
- ModuleTestRunner: Module-level test execution
- OutputValidator: JSON schema validation

Future:
- RayExecutor: Distributed execution on Ray clusters
- KubeflowCompiler: KFP pipeline generation
"""

from .local_executor import LocalExecutor
from .papermill_runner import (
    PapermillRunner,
    BackendDetector,
    BackendInfo,
    ExecutionResult,
)
from .module_test_runner import (
    ModuleTestRunner,
    ModuleTestResult,
    TestFixture,
)
from .output_validator import (
    OutputValidator,
    ValidationResult,
    ValidationError,
    COMMON_SCHEMAS,
    validate_with_schema,
)

__all__ = [
    # Core executors
    'LocalExecutor',
    'PapermillRunner',
    'ModuleTestRunner',

    # Backend detection
    'BackendDetector',
    'BackendInfo',

    # Results
    'ExecutionResult',
    'ModuleTestResult',
    'TestFixture',

    # Validation
    'OutputValidator',
    'ValidationResult',
    'ValidationError',
    'COMMON_SCHEMAS',
    'validate_with_schema',
]
