"""
Pytest configuration and fixtures for UH2025Agent tests.

Provides:
- Backend detection and selection fixtures
- Papermill runner fixtures
- Module test runner fixtures
- Temporary directory management
- Test data loading utilities

Usage in tests:
    def test_notebook_execution(papermill_runner, tmp_output_dir):
        result = papermill_runner.execute_notebook(
            notebook_path=Path("notebooks/main.ipynb"),
            output_dir=tmp_output_dir,
        )
        assert result.success
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import sys
import importlib.util

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
EXECUTOR_DIR = CODE_DIR / "executor"

# Import modules directly via importlib to avoid conflicts with papermill's elyra entry point
# (papermill tries to load 'elyra.pipeline' which conflicts with our local 'elyra' package)

def _load_module_from_file(name: str, filepath: Path):
    """Load a Python module directly from file."""
    spec = importlib.util.spec_from_file_location(name, str(filepath))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load executor modules
_papermill_runner = _load_module_from_file("_papermill_runner", EXECUTOR_DIR / "papermill_runner.py")
_module_test_runner = _load_module_from_file("_module_test_runner", EXECUTOR_DIR / "module_test_runner.py")
_output_validator = _load_module_from_file("_output_validator", EXECUTOR_DIR / "output_validator.py")

# Extract classes
PapermillRunner = _papermill_runner.PapermillRunner
BackendDetector = _papermill_runner.BackendDetector
BackendInfo = _papermill_runner.BackendInfo
ModuleTestRunner = _module_test_runner.ModuleTestRunner
OutputValidator = _output_validator.OutputValidator


# =============================================================================
# Command-line options
# =============================================================================

def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--backend",
        action="store",
        default=None,
        choices=["cuda", "rocm", "mps", "cpu"],
        help="Force specific compute backend",
    )
    parser.addoption(
        "--use-stub",
        action="store_true",
        default=False,
        help="Use stub/mock mode for fast testing",
    )
    parser.addoption(
        "--keep-outputs",
        action="store_true",
        default=False,
        help="Keep test output files after completion",
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests (marked with @pytest.mark.slow)",
    )
    parser.addoption(
        "--run-gpu",
        action="store_true",
        default=False,
        help="Run GPU-requiring tests",
    )


def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow to run"
    )
    config.addinivalue_line(
        "markers", "gpu: mark test as requiring GPU"
    )
    config.addinivalue_line(
        "markers", "cuda: mark test as requiring CUDA"
    )
    config.addinivalue_line(
        "markers", "mps: mark test as requiring Apple MPS"
    )
    config.addinivalue_line(
        "markers", "notebook: mark test as notebook execution test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests based on markers and options."""
    run_slow = config.getoption("--run-slow")
    run_gpu = config.getoption("--run-gpu")
    backend = config.getoption("--backend")

    # Detect available backend
    detected_backend = BackendDetector.detect()

    for item in items:
        # Skip slow tests unless --run-slow
        if "slow" in item.keywords and not run_slow:
            item.add_marker(pytest.mark.skip(reason="Need --run-slow to run"))

        # Skip GPU tests unless --run-gpu
        if "gpu" in item.keywords and not run_gpu:
            item.add_marker(pytest.mark.skip(reason="Need --run-gpu to run"))

        # Skip CUDA tests if CUDA not available
        if "cuda" in item.keywords:
            if detected_backend.name != "cuda" and backend != "cuda":
                item.add_marker(pytest.mark.skip(reason="CUDA not available"))

        # Skip MPS tests if MPS not available
        if "mps" in item.keywords:
            if detected_backend.name != "mps" and backend != "mps":
                item.add_marker(pytest.mark.skip(reason="MPS not available"))


# =============================================================================
# Backend fixtures
# =============================================================================

@pytest.fixture(scope="session")
def detected_backend() -> BackendInfo:
    """
    Fixture providing detected compute backend.

    Returns:
        BackendInfo with detected backend details
    """
    return BackendDetector.detect()


@pytest.fixture(scope="session")
def forced_backend(request) -> Optional[str]:
    """
    Fixture providing command-line forced backend.

    Returns:
        Backend name if forced, None otherwise
    """
    return request.config.getoption("--backend")


@pytest.fixture(scope="session")
def effective_backend(detected_backend, forced_backend) -> BackendInfo:
    """
    Fixture providing effective backend (forced or detected).

    Returns:
        BackendInfo for the backend that will be used
    """
    if forced_backend:
        return BackendInfo(name=forced_backend)
    return detected_backend


@pytest.fixture
def is_gpu_available(detected_backend) -> bool:
    """Check if GPU backend is available."""
    return detected_backend.name in ("cuda", "rocm", "mps")


@pytest.fixture
def skip_if_no_gpu(is_gpu_available):
    """Skip test if no GPU available."""
    if not is_gpu_available:
        pytest.skip("No GPU backend available")


# =============================================================================
# Runner fixtures
# =============================================================================

@pytest.fixture
def papermill_runner(forced_backend) -> PapermillRunner:
    """
    Fixture providing configured PapermillRunner.

    Returns:
        PapermillRunner instance
    """
    return PapermillRunner(
        backend=forced_backend,
        log_level="INFO",
    )


@pytest.fixture
def module_test_runner_factory(forced_backend, request):
    """
    Factory fixture for creating ModuleTestRunner instances.

    Usage:
        def test_module(module_test_runner_factory):
            runner = module_test_runner_factory("lab/obs/modules/AlphaMissense")
            result = runner.run_test(...)
    """
    runners = []
    keep_outputs = request.config.getoption("--keep-outputs")

    def factory(module_path: Path) -> ModuleTestRunner:
        runner = ModuleTestRunner(
            module_path=Path(module_path),
            backend=forced_backend,
            keep_outputs=keep_outputs,
        )
        runners.append(runner)
        return runner

    yield factory

    # Cleanup
    for runner in runners:
        runner.cleanup()


@pytest.fixture
def output_validator() -> OutputValidator:
    """
    Fixture providing OutputValidator instance.

    Returns:
        OutputValidator for validating test outputs
    """
    return OutputValidator()


# =============================================================================
# Directory fixtures
# =============================================================================

@pytest.fixture
def tmp_output_dir(request) -> Path:
    """
    Fixture providing temporary output directory.

    Automatically cleaned up unless --keep-outputs is set.

    Returns:
        Path to temporary directory
    """
    keep_outputs = request.config.getoption("--keep-outputs")
    tmp_dir = Path(tempfile.mkdtemp(prefix="pytest_output_"))

    yield tmp_dir

    if not keep_outputs:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Fixture providing project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def lab_root() -> Path:
    """Fixture providing lab root path."""
    return PROJECT_ROOT.parent.parent.parent  # lab/obs/topologies/UH2025Agent -> lab


@pytest.fixture(scope="session")
def modules_root(lab_root) -> Path:
    """Fixture providing modules root path."""
    return lab_root / "obs" / "modules"


# =============================================================================
# Test data fixtures
# =============================================================================

@pytest.fixture(scope="session")
def patient_x_data() -> Dict[str, Any]:
    """
    Fixture providing PatientX test data.

    Returns:
        Dictionary with clinical and genomic data
    """
    data_dir = PROJECT_ROOT / "Data" / "PatientX"

    # Load clinical summary
    clinical_path = data_dir / "patientX_Clinical.md"
    if clinical_path.exists():
        with open(clinical_path) as f:
            clinical_summary = f.read()
    else:
        clinical_summary = "Test patient clinical summary"

    # Load genomic data
    genomic_path = data_dir / "patientX_Genomic.json"
    if genomic_path.exists():
        with open(genomic_path) as f:
            genomic_data = json.load(f)
    else:
        genomic_data = {
            "variants": [
                {"chrom": "chr17", "pos": 41276044, "ref": "A", "alt": "G"},
            ]
        }

    return {
        "clinical_summary": clinical_summary,
        "genomic_data": genomic_data,
        "patient_id": "PatientX",
    }


@pytest.fixture
def sample_variants() -> list:
    """
    Fixture providing sample variant data for testing.

    Returns:
        List of variant dictionaries
    """
    return [
        {"chrom": "chr1", "pos": 12345, "ref": "A", "alt": "G"},
        {"chrom": "chr7", "pos": 55259515, "ref": "T", "alt": "G"},  # EGFR
        {"chrom": "chr17", "pos": 41276044, "ref": "A", "alt": "C"},  # BRCA1
    ]


@pytest.fixture
def sample_gene_list() -> list:
    """
    Fixture providing sample gene list for testing.

    Returns:
        List of gene symbols
    """
    return ["BRCA1", "BRCA2", "TP53", "EGFR", "SCN4A", "RYR1"]


# =============================================================================
# Mode fixtures
# =============================================================================

@pytest.fixture
def use_stub(request) -> bool:
    """
    Fixture indicating if stub mode is enabled.

    Returns:
        True if --use-stub flag was passed
    """
    return request.config.getoption("--use-stub")


@pytest.fixture
def skip_if_stub(use_stub):
    """Skip test if running in stub mode."""
    if use_stub:
        pytest.skip("Skipped in stub mode")


@pytest.fixture
def skip_if_not_stub(use_stub):
    """Skip test if NOT running in stub mode."""
    if not use_stub:
        pytest.skip("Only runs in stub mode")


# =============================================================================
# Utility fixtures
# =============================================================================

@pytest.fixture
def assert_valid_json():
    """
    Fixture providing JSON validation helper.

    Usage:
        def test_output(assert_valid_json, tmp_output_dir):
            # ... generate output ...
            assert_valid_json(tmp_output_dir / "output.json")
    """
    def _assert_valid_json(file_path: Path) -> Dict:
        assert file_path.exists(), f"File not found: {file_path}"
        with open(file_path) as f:
            data = json.load(f)
        return data

    return _assert_valid_json


@pytest.fixture
def assert_notebook_success():
    """
    Fixture providing notebook execution assertion helper.

    Usage:
        def test_notebook(papermill_runner, assert_notebook_success):
            result = papermill_runner.execute_notebook(...)
            assert_notebook_success(result)
    """
    def _assert_success(result):
        from executor.papermill_runner import ExecutionResult

        assert isinstance(result, ExecutionResult), "Result must be ExecutionResult"
        if not result.success:
            error_msg = result.error or "Unknown error"
            pytest.fail(f"Notebook execution failed: {error_msg}")

    return _assert_success


# =============================================================================
# Elyra fixtures
# =============================================================================

@pytest.fixture(scope="session")
def elyra_pipeline_path(project_root) -> Path:
    """
    Fixture providing path to UH2025Agent Elyra pipeline.

    Returns:
        Path to the .pipeline file
    """
    return project_root / "elyra" / "UH2025Agent.pipeline"


@pytest.fixture(scope="session")
def elyra_runner(elyra_pipeline_path, forced_backend):
    """
    Fixture providing ElyraRunner instance.

    Returns:
        ElyraRunner configured for the UH2025Agent pipeline
    """
    # Load ElyraRunner directly via importlib to avoid conflicts
    _elyra_runner_module = _load_module_from_file(
        "_elyra_runner",
        CODE_DIR / "elyra" / "runner.py"
    )
    ElyraRunner = _elyra_runner_module.ElyraRunner

    return ElyraRunner(
        pipeline_path=str(elyra_pipeline_path),
        log_level="INFO",
    )


@pytest.fixture
def elyra_node_runner(elyra_runner, forced_backend, tmp_output_dir):
    """
    Factory fixture for running individual Elyra nodes.

    Usage:
        def test_node(elyra_node_runner):
            result = elyra_node_runner("01_regulatory_analysis")
            assert result.success
    """
    def _run_node(node_label: str, parameters: dict = None):
        return elyra_runner.execute_node(
            node_label=node_label,
            parameters=parameters,
            output_dir=str(tmp_output_dir / node_label),
        )

    return _run_node


@pytest.fixture
def module_notebook_paths(modules_root) -> dict:
    """
    Fixture providing paths to module notebooks.

    Returns:
        Dictionary mapping module name to notebook path
    """
    return {
        "AlphaMissense": modules_root / "AlphaMissense" / "notebooks" / "main.ipynb",
        "AlphaGenome": modules_root / "AlphaGenome" / "notebooks" / "main.ipynb",
    }


@pytest.fixture
def assert_pipeline_success():
    """
    Fixture providing pipeline execution assertion helper.

    Usage:
        def test_pipeline(elyra_runner, assert_pipeline_success):
            result = elyra_runner.execute_local(...)
            assert_pipeline_success(result)
    """
    def _assert_success(result):
        # Use duck typing instead of isinstance to avoid type identity issues
        # from loading modules multiple times via importlib
        assert hasattr(result, 'success'), "Result must have 'success' attribute"
        assert hasattr(result, 'node_results'), "Result must have 'node_results' attribute"
        if not result.success:
            # Build detailed error message
            errors = []
            for node_id, node_result in result.node_results.items():
                if not node_result.success:
                    errors.append(f"  - {node_id}: {node_result.error}")

            error_msg = result.error or "Unknown error"
            if errors:
                error_msg += "\n" + "\n".join(errors)

            pytest.fail(f"Pipeline execution failed: {error_msg}")

    return _assert_success


# =============================================================================
# Unified Runner fixtures
# =============================================================================

@pytest.fixture
def unified_runner(forced_backend):
    """
    Fixture providing UnifiedRunner instance.

    Returns:
        UnifiedRunner for execution parity testing
    """
    # Load UnifiedRunner via importlib to avoid conflicts
    _unified_runner = _load_module_from_file(
        "_unified_runner_conftest",
        EXECUTOR_DIR / "unified_runner.py"
    )
    UnifiedRunner = _unified_runner.UnifiedRunner

    return UnifiedRunner(
        backend=forced_backend,
        log_level="WARNING",
    )


@pytest.fixture
def local_executor_factory(project_root, forced_backend, request):
    """
    Factory fixture for creating LocalExecutor instances.

    Usage:
        def test_local(local_executor_factory):
            executor = local_executor_factory()
            result = executor.execute()
    """
    executors = []
    keep_outputs = request.config.getoption("--keep-outputs")

    def factory(output_dir=None):
        # Load LocalExecutor via importlib
        _local_executor = _load_module_from_file(
            "_local_executor_conftest",
            EXECUTOR_DIR / "local_executor.py"
        )
        LocalExecutor = _local_executor.LocalExecutor

        topology_path = project_root / "topology.yaml"
        executor = LocalExecutor(
            topology_path=str(topology_path),
            output_dir=output_dir,
            log_level="WARNING",
        )
        executors.append(executor)
        return executor

    yield factory

    # Cleanup if needed
    if not keep_outputs:
        for executor in executors:
            if hasattr(executor, 'run_dir') and executor.run_dir:
                import shutil
                shutil.rmtree(executor.run_dir, ignore_errors=True)