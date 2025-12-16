"""
Module test runner - executes module notebooks with test fixtures.

Provides a higher-level interface for testing modules:
- Discovers and loads module test data
- Executes notebooks with appropriate fixtures
- Validates outputs against expected results
- Supports parallel execution across backends

Usage:
    runner = ModuleTestRunner(module_path="lab/obs/modules/AlphaMissense")
    result = runner.run_test(
        test_name="pathogenicity_lookup",
        test_data={"variants": [...]},
    )
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import tempfile
import shutil
import sys
import importlib.util

# Import papermill_runner - handle both package and direct import scenarios
try:
    from .papermill_runner import PapermillRunner, ExecutionResult, BackendInfo
except ImportError:
    # Direct import when loaded via importlib.util
    _pm_runner_path = Path(__file__).parent / "papermill_runner.py"
    if _pm_runner_path.exists() and "_papermill_runner" not in sys.modules:
        spec = importlib.util.spec_from_file_location("_papermill_runner", str(_pm_runner_path))
        _pm_module = importlib.util.module_from_spec(spec)
        sys.modules["_papermill_runner"] = _pm_module
        spec.loader.exec_module(_pm_module)
        PapermillRunner = _pm_module.PapermillRunner
        ExecutionResult = _pm_module.ExecutionResult
        BackendInfo = _pm_module.BackendInfo
    else:
        _pm_module = sys.modules.get("_papermill_runner")
        if _pm_module:
            PapermillRunner = _pm_module.PapermillRunner
            ExecutionResult = _pm_module.ExecutionResult
            BackendInfo = _pm_module.BackendInfo
        else:
            raise ImportError("Could not import papermill_runner")

logger = logging.getLogger(__name__)


@dataclass
class TestFixture:
    """Test fixture for module testing."""

    name: str
    input_data: Dict[str, Any]
    expected_outputs: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 600  # 10 minutes default
    skip_backends: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ModuleTestResult:
    """Result from module test execution."""

    test_name: str
    module_name: str
    success: bool
    execution_result: Optional[ExecutionResult] = None
    validation_passed: bool = False
    validation_errors: List[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'module_name': self.module_name,
            'success': self.success,
            'execution_result': self.execution_result.to_dict() if self.execution_result else None,
            'validation_passed': self.validation_passed,
            'validation_errors': self.validation_errors,
            'skipped': self.skipped,
            'skip_reason': self.skip_reason,
        }


class ModuleTestRunner:
    """
    Executes module notebooks with test fixtures.

    Provides standardized testing for DEFACT modules:
    - Automatic test fixture discovery
    - Backend-aware execution
    - Output validation
    - Result aggregation
    """

    def __init__(
        self,
        module_path: Path,
        backend: Optional[str] = None,
        temp_dir: Optional[Path] = None,
        keep_outputs: bool = False,
        log_level: str = 'INFO',
    ):
        """
        Initialize module test runner.

        Args:
            module_path: Path to module directory
            backend: Force specific backend (or auto-detect)
            temp_dir: Temporary directory for test outputs
            keep_outputs: Keep output files after tests
            log_level: Logging level
        """
        self.module_path = Path(module_path)
        self.keep_outputs = keep_outputs

        # Validate module path
        if not self.module_path.exists():
            raise ValueError(f"Module path does not exist: {self.module_path}")

        # Get module name
        self.module_name = self.module_path.name

        # Find notebooks directory
        self.notebooks_dir = self.module_path / 'notebooks'
        if not self.notebooks_dir.exists():
            # Try alternate location
            self.notebooks_dir = self.module_path

        # Setup temp directory
        if temp_dir:
            self.temp_dir = Path(temp_dir)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            self._temp_dir_created = False
        else:
            self.temp_dir = Path(tempfile.mkdtemp(prefix=f'module_test_{self.module_name}_'))
            self._temp_dir_created = True

        # Initialize Papermill runner
        self.runner = PapermillRunner(backend=backend, log_level=log_level)

        # Load module configuration
        self.config = self._load_module_config()

        logging.basicConfig(level=getattr(logging, log_level.upper()))

    def _load_module_config(self) -> Dict[str, Any]:
        """Load module configuration from module.yaml or similar."""
        config_paths = [
            self.module_path / 'module.yaml',
            self.module_path / 'config.yaml',
            self.module_path / 'module.json',
        ]

        for config_path in config_paths:
            if config_path.exists():
                import yaml
                with open(config_path) as f:
                    if config_path.suffix == '.json':
                        return json.load(f)
                    else:
                        return yaml.safe_load(f) or {}

        return {}

    def discover_notebooks(self) -> List[Path]:
        """
        Discover executable notebooks in module.

        Returns:
            List of notebook paths
        """
        notebooks = []

        # Look for main notebook
        main_notebook = self.notebooks_dir / 'main.ipynb'
        if main_notebook.exists():
            notebooks.append(main_notebook)

        # Look for other notebooks
        for nb in self.notebooks_dir.glob('*.ipynb'):
            if nb.name != 'main.ipynb' and not nb.name.startswith('_'):
                notebooks.append(nb)

        return notebooks

    def discover_test_fixtures(self) -> List[TestFixture]:
        """
        Discover test fixtures from module's test directory.

        Returns:
            List of test fixtures
        """
        fixtures = []

        # Look for test fixtures in tests/fixtures/
        fixtures_dir = self.module_path / 'tests' / 'fixtures'
        if fixtures_dir.exists():
            for fixture_file in fixtures_dir.glob('*.json'):
                try:
                    with open(fixture_file) as f:
                        data = json.load(f)

                    fixtures.append(TestFixture(
                        name=fixture_file.stem,
                        input_data=data.get('input', {}),
                        expected_outputs=data.get('expected_output'),
                        timeout_seconds=data.get('timeout', 600),
                        skip_backends=data.get('skip_backends', []),
                        tags=data.get('tags', []),
                    ))
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to load fixture {fixture_file}: {e}")

        # Look for test_data/ directory (alternative pattern)
        test_data_dir = self.module_path / 'test_data'
        if test_data_dir.exists():
            for data_file in test_data_dir.glob('*.json'):
                try:
                    with open(data_file) as f:
                        data = json.load(f)

                    fixtures.append(TestFixture(
                        name=f"data_{data_file.stem}",
                        input_data=data,
                    ))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to load test data {data_file}: {e}")

        return fixtures

    def run_test(
        self,
        notebook: Optional[Path] = None,
        test_fixture: Optional[TestFixture] = None,
        parameters: Optional[Dict[str, Any]] = None,
        validator: Optional[Callable[[Dict[str, Any]], List[str]]] = None,
    ) -> ModuleTestResult:
        """
        Run a single test against a module notebook.

        Args:
            notebook: Notebook path (default: main.ipynb)
            test_fixture: Test fixture with input data
            parameters: Additional parameters to inject
            validator: Custom validation function

        Returns:
            ModuleTestResult with execution details
        """
        # Default to main notebook
        if notebook is None:
            notebook = self.notebooks_dir / 'main.ipynb'

        if not notebook.exists():
            return ModuleTestResult(
                test_name=test_fixture.name if test_fixture else 'default',
                module_name=self.module_name,
                success=False,
                validation_errors=[f"Notebook not found: {notebook}"],
            )

        # Determine test name
        test_name = test_fixture.name if test_fixture else 'default'

        # Check if backend should be skipped
        if test_fixture and self.runner.backend.name in test_fixture.skip_backends:
            return ModuleTestResult(
                test_name=test_name,
                module_name=self.module_name,
                success=True,
                skipped=True,
                skip_reason=f"Backend {self.runner.backend.name} in skip list",
            )

        # Prepare parameters
        pm_params = {}
        if test_fixture:
            pm_params.update(test_fixture.input_data)
        if parameters:
            pm_params.update(parameters)

        # Setup output directory
        output_dir = self.temp_dir / f"test_{test_name}_{datetime.now().strftime('%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Running test '{test_name}' on module '{self.module_name}'")
        logger.info(f"Notebook: {notebook}")
        logger.info(f"Output directory: {output_dir}")

        # Execute notebook
        exec_result = self.runner.execute_notebook(
            notebook_path=notebook,
            parameters=pm_params,
            output_dir=output_dir,
            inject_backend=True,
        )

        # Validate outputs
        validation_errors = []
        if exec_result.success:
            # Custom validator
            if validator:
                validation_errors.extend(validator(exec_result.outputs))

            # Expected outputs validation
            if test_fixture and test_fixture.expected_outputs:
                validation_errors.extend(
                    self._validate_expected_outputs(
                        exec_result.outputs,
                        test_fixture.expected_outputs,
                        output_dir,
                    )
                )

        validation_passed = exec_result.success and len(validation_errors) == 0

        return ModuleTestResult(
            test_name=test_name,
            module_name=self.module_name,
            success=exec_result.success and validation_passed,
            execution_result=exec_result,
            validation_passed=validation_passed,
            validation_errors=validation_errors,
        )

    def _validate_expected_outputs(
        self,
        actual_outputs: Dict[str, Any],
        expected: Dict[str, Any],
        output_dir: Path,
    ) -> List[str]:
        """
        Validate actual outputs against expected outputs.

        Args:
            actual_outputs: Dictionary of output names to paths
            expected: Expected output specification
            output_dir: Directory containing output files

        Returns:
            List of validation errors
        """
        errors = []

        # Check required files exist
        for file_name, spec in expected.items():
            if file_name not in actual_outputs:
                # Try to find file directly
                possible_path = output_dir / file_name
                if not possible_path.exists():
                    errors.append(f"Missing expected output: {file_name}")
                    continue

            # Validate file content if spec provided
            if isinstance(spec, dict):
                output_path = Path(actual_outputs.get(file_name, output_dir / file_name))
                if output_path.exists() and output_path.suffix == '.json':
                    try:
                        with open(output_path) as f:
                            content = json.load(f)

                        # Check required fields
                        for field in spec.get('required_fields', []):
                            if field not in content:
                                errors.append(f"Missing required field '{field}' in {file_name}")

                        # Check value constraints
                        for field, constraint in spec.get('constraints', {}).items():
                            if field in content:
                                value = content[field]
                                if 'min' in constraint and value < constraint['min']:
                                    errors.append(f"Field '{field}' below minimum in {file_name}")
                                if 'max' in constraint and value > constraint['max']:
                                    errors.append(f"Field '{field}' above maximum in {file_name}")

                    except json.JSONDecodeError:
                        errors.append(f"Invalid JSON in {file_name}")

        return errors

    def run_all_tests(
        self,
        notebook: Optional[Path] = None,
        tags: Optional[List[str]] = None,
    ) -> List[ModuleTestResult]:
        """
        Run all discovered test fixtures.

        Args:
            notebook: Notebook to test (default: all notebooks)
            tags: Filter fixtures by tags

        Returns:
            List of test results
        """
        results = []

        # Discover fixtures
        fixtures = self.discover_test_fixtures()

        # Filter by tags
        if tags:
            fixtures = [f for f in fixtures if any(t in f.tags for t in tags)]

        # If no fixtures found, run with default parameters
        if not fixtures:
            logger.info("No test fixtures found, running with default parameters")
            fixtures = [TestFixture(name='default', input_data={})]

        # Determine notebooks to test
        if notebook:
            notebooks = [notebook]
        else:
            notebooks = self.discover_notebooks()

        if not notebooks:
            logger.error(f"No notebooks found in {self.notebooks_dir}")
            return results

        # Run tests
        for nb in notebooks:
            for fixture in fixtures:
                result = self.run_test(notebook=nb, test_fixture=fixture)
                results.append(result)

                # Log result
                status = "PASSED" if result.success else ("SKIPPED" if result.skipped else "FAILED")
                logger.info(f"  [{status}] {nb.name} / {fixture.name}")

        return results

    def cleanup(self):
        """Clean up temporary files."""
        if not self.keep_outputs and self._temp_dir_created:
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


def main():
    """CLI interface for module test runner."""
    import argparse

    parser = argparse.ArgumentParser(description='Run module tests')
    parser.add_argument('module_path', help='Path to module directory')
    parser.add_argument('--notebook', help='Specific notebook to test')
    parser.add_argument('--backend', choices=['cuda', 'rocm', 'mps', 'cpu'],
                        help='Force specific backend')
    parser.add_argument('--keep-outputs', action='store_true',
                        help='Keep output files after tests')
    parser.add_argument('--tags', nargs='+', help='Filter fixtures by tags')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    args = parser.parse_args()

    # Create runner
    with ModuleTestRunner(
        module_path=Path(args.module_path),
        backend=args.backend,
        keep_outputs=args.keep_outputs,
        log_level=args.log_level,
    ) as runner:

        # Run tests
        notebook = Path(args.notebook) if args.notebook else None
        results = runner.run_all_tests(notebook=notebook, tags=args.tags)

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)

        print(f"Total: {len(results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")

        if failed > 0:
            print("\nFailed tests:")
            for r in results:
                if not r.success and not r.skipped:
                    print(f"  - {r.test_name}")
                    for err in r.validation_errors:
                        print(f"      {err}")
                    if r.execution_result and r.execution_result.error:
                        print(f"      Error: {r.execution_result.error}")

        return 0 if failed == 0 else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
