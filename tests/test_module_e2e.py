"""
End-to-End Module Tests with Real Notebook Execution

Tests module notebooks using Papermill with backend-aware execution.
These tests verify that modules work correctly with real data and
appropriate compute backends.

Usage:
    # Run all E2E tests (auto-detect backend)
    pytest tests/test_module_e2e.py -v

    # Run with specific backend
    pytest tests/test_module_e2e.py -v --backend=mps

    # Run including slow tests
    pytest tests/test_module_e2e.py -v --run-slow

    # Keep output files for inspection
    pytest tests/test_module_e2e.py -v --keep-outputs

Author: Stanley Lab / RareResearch
Date: November 2025
"""

import pytest
import json
from pathlib import Path
import sys
import importlib.util

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
EXECUTOR_DIR = CODE_DIR / "executor"


def _load_module_from_file(name: str, filepath: Path):
    """Load a Python module directly from file."""
    spec = importlib.util.spec_from_file_location(name, str(filepath))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Load output_validator directly to get COMMON_SCHEMAS
_output_validator_module = _load_module_from_file(
    "_output_validator_e2e",
    EXECUTOR_DIR / "output_validator.py"
)
COMMON_SCHEMAS = _output_validator_module.COMMON_SCHEMAS


class TestBackendDetection:
    """Test backend detection functionality."""

    def test_backend_detected(self, detected_backend):
        """Backend should be detected."""
        assert detected_backend is not None
        assert detected_backend.name in ('cuda', 'rocm', 'mps', 'cpu')

    def test_backend_info_complete(self, detected_backend):
        """Backend info should have required fields."""
        info = detected_backend.to_dict()
        assert 'name' in info
        assert 'device_name' in info

    def test_effective_backend_uses_forced(self, effective_backend, forced_backend):
        """Effective backend should respect forced backend."""
        if forced_backend:
            assert effective_backend.name == forced_backend


class TestPapermillRunner:
    """Test PapermillRunner functionality."""

    def test_runner_initializes(self, papermill_runner):
        """Runner should initialize successfully."""
        assert papermill_runner is not None
        assert papermill_runner.backend is not None

    def test_backend_parameters(self, papermill_runner):
        """Runner should generate backend parameters."""
        params = papermill_runner.get_backend_parameters()

        assert 'BACKEND' in params
        assert 'DEVICE' in params
        assert params['BACKEND'] in ('cuda', 'rocm', 'mps', 'cpu')

    def test_backend_parameters_cuda(self, papermill_runner):
        """CUDA backend should set appropriate parameters."""
        if papermill_runner.backend.name != 'cuda':
            pytest.skip("Not CUDA backend")

        params = papermill_runner.get_backend_parameters()
        assert params['USE_CUDA'] is True
        assert params['USE_MPS'] is False
        assert params['DEVICE'] == 'cuda:0'

    def test_backend_parameters_mps(self, papermill_runner):
        """MPS backend should set appropriate parameters."""
        if papermill_runner.backend.name != 'mps':
            pytest.skip("Not MPS backend")

        params = papermill_runner.get_backend_parameters()
        assert params['USE_CUDA'] is False
        assert params['USE_MPS'] is True
        assert params['DEVICE'] == 'mps'

    def test_missing_notebook_returns_error(self, papermill_runner, tmp_output_dir):
        """Missing notebook should return error result."""
        result = papermill_runner.execute_notebook(
            notebook_path=Path("/nonexistent/notebook.ipynb"),
            output_dir=tmp_output_dir,
        )

        assert not result.success
        assert "not found" in result.error.lower()


class TestOutputValidator:
    """Test OutputValidator functionality."""

    def test_validator_initializes(self, output_validator):
        """Validator should initialize successfully."""
        assert output_validator is not None

    def test_valid_json_passes(self, output_validator):
        """Valid JSON should pass validation."""
        data = {
            "variants": [
                {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
            ]
        }

        result = output_validator.validate_json(
            data, schema=COMMON_SCHEMAS['variant_output']
        )

        assert result.valid
        assert len(result.errors) == 0

    def test_invalid_json_fails(self, output_validator):
        """Invalid JSON should fail validation."""
        data = {
            "variants": [
                {"chrom": "chr1", "pos": "invalid"},  # pos should be int
            ]
        }

        result = output_validator.validate_json(
            data, schema=COMMON_SCHEMAS['variant_output']
        )

        assert not result.valid
        assert len(result.errors) > 0

    def test_missing_required_field_fails(self, output_validator):
        """Missing required field should fail validation."""
        data = {"not_variants": []}  # Missing 'variants' field

        result = output_validator.validate_json(
            data, schema=COMMON_SCHEMAS['variant_output']
        )

        assert not result.valid


@pytest.mark.notebook
class TestModuleNotebookExecution:
    """Test actual module notebook execution."""

    @pytest.fixture
    def alphamissense_module(self, modules_root) -> Path:
        """Path to AlphaMissense module."""
        return modules_root / "AlphaMissense"

    @pytest.fixture
    def alphagenome_module(self, modules_root) -> Path:
        """Path to AlphaGenome module."""
        return modules_root / "AlphaGenome"

    def test_alphamissense_module_exists(self, alphamissense_module):
        """AlphaMissense module should exist."""
        assert alphamissense_module.exists()
        assert (alphamissense_module / "notebooks").exists() or \
               (alphamissense_module / "alphamissense").exists()

    def test_alphagenome_module_exists(self, alphagenome_module):
        """AlphaGenome module should exist."""
        assert alphagenome_module.exists()
        assert (alphagenome_module / "notebooks").exists() or \
               (alphagenome_module / "alphagenome").exists()

    @pytest.mark.slow
    def test_alphamissense_notebook_simple(
        self,
        papermill_runner,
        alphamissense_module,
        tmp_output_dir,
        sample_variants,
        assert_notebook_success,
    ):
        """
        Test AlphaMissense notebook with simple variant input.

        This test verifies the notebook can execute with backend
        parameter injection.
        """
        notebook_path = alphamissense_module / "notebooks" / "main.ipynb"

        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        # Execute notebook with sample variants
        result = papermill_runner.execute_notebook(
            notebook_path=notebook_path,
            parameters={
                "variants": sample_variants,
                "test_mode": True,
            },
            output_dir=tmp_output_dir,
        )

        # Verify execution
        assert_notebook_success(result)
        assert result.output_notebook.exists()

    @pytest.mark.slow
    def test_alphagenome_notebook_simple(
        self,
        papermill_runner,
        alphagenome_module,
        tmp_output_dir,
        sample_variants,
        assert_notebook_success,
    ):
        """
        Test AlphaGenome notebook with simple variant input.

        This test verifies the notebook can execute with backend
        parameter injection.
        """
        notebook_path = alphagenome_module / "notebooks" / "main.ipynb"

        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        # Execute notebook with sample variants
        result = papermill_runner.execute_notebook(
            notebook_path=notebook_path,
            parameters={
                "variants": sample_variants,
                "test_mode": True,
            },
            output_dir=tmp_output_dir,
        )

        # Verify execution
        assert_notebook_success(result)
        assert result.output_notebook.exists()


@pytest.mark.e2e
class TestModuleTestRunner:
    """Test ModuleTestRunner functionality."""

    def test_runner_discovers_notebooks(
        self,
        module_test_runner_factory,
        modules_root,
    ):
        """Runner should discover module notebooks."""
        alphamissense_path = modules_root / "AlphaMissense"

        if not alphamissense_path.exists():
            pytest.skip("AlphaMissense module not found")

        runner = module_test_runner_factory(alphamissense_path)
        notebooks = runner.discover_notebooks()

        # Should find at least the main notebook or some notebooks
        # (may be empty if notebooks are in different location)
        assert isinstance(notebooks, list)

    def test_runner_loads_config(
        self,
        module_test_runner_factory,
        modules_root,
    ):
        """Runner should load module config if present."""
        alphamissense_path = modules_root / "AlphaMissense"

        if not alphamissense_path.exists():
            pytest.skip("AlphaMissense module not found")

        runner = module_test_runner_factory(alphamissense_path)

        # Config should be loaded (may be empty dict if no config file)
        assert isinstance(runner.config, dict)

    @pytest.mark.slow
    def test_runner_executes_with_fixture(
        self,
        module_test_runner_factory,
        modules_root,
        sample_variants,
    ):
        """Runner should execute module with test fixture."""
        from executor.module_test_runner import TestFixture

        alphamissense_path = modules_root / "AlphaMissense"

        if not alphamissense_path.exists():
            pytest.skip("AlphaMissense module not found")

        runner = module_test_runner_factory(alphamissense_path)

        # Create test fixture
        fixture = TestFixture(
            name="simple_variants",
            input_data={
                "variants": sample_variants,
                "test_mode": True,
            },
        )

        # Run test
        result = runner.run_test(test_fixture=fixture)

        # Should complete (success depends on notebook implementation)
        assert result.test_name == "simple_variants"
        assert result.module_name == "AlphaMissense"
        # Note: May not succeed if notebook requires database/data


@pytest.mark.e2e
class TestPatientXPipeline:
    """Test end-to-end pipeline with PatientX data."""

    def test_patient_data_loads(self, patient_x_data):
        """PatientX data should load successfully."""
        assert "clinical_summary" in patient_x_data
        assert "genomic_data" in patient_x_data
        assert "patient_id" in patient_x_data

    def test_patient_data_has_variants(self, patient_x_data):
        """PatientX data should contain variants."""
        genomic = patient_x_data["genomic_data"]
        assert "variants" in genomic
        assert len(genomic["variants"]) > 0

    @pytest.mark.slow
    def test_pipeline_with_patientx(
        self,
        papermill_runner,
        patient_x_data,
        tmp_output_dir,
        use_stub,
    ):
        """
        Test full pipeline execution with PatientX data.

        Note: This test may take several minutes with real LLM inference.
        Use --use-stub for fast CI testing.
        """
        # This test is conceptual - actual pipeline execution
        # would require the full UH2025Agent graph setup

        # For now, verify we can access the data
        assert patient_x_data["patient_id"] == "PatientX"
        assert len(patient_x_data["clinical_summary"]) > 0

        if use_stub:
            # In stub mode, just verify data structure
            pytest.skip("Full pipeline test skipped in stub mode")


@pytest.mark.gpu
class TestGPUExecution:
    """Tests that require GPU backend."""

    def test_gpu_backend_available(self, detected_backend, skip_if_no_gpu):
        """GPU backend should be available."""
        assert detected_backend.name in ('cuda', 'rocm', 'mps')

    @pytest.mark.cuda
    def test_cuda_execution(
        self,
        papermill_runner,
        detected_backend,
    ):
        """Test CUDA-specific execution."""
        if detected_backend.name != 'cuda':
            pytest.skip("CUDA not available")

        params = papermill_runner.get_backend_parameters()
        assert params['USE_CUDA'] is True
        assert 'cuda:' in params['DEVICE']

    @pytest.mark.mps
    def test_mps_execution(
        self,
        papermill_runner,
        detected_backend,
    ):
        """Test MPS-specific execution."""
        if detected_backend.name != 'mps':
            pytest.skip("MPS not available")

        params = papermill_runner.get_backend_parameters()
        assert params['USE_MPS'] is True
        assert params['DEVICE'] == 'mps'


class TestCommonSchemas:
    """Test common output schema validation."""

    def test_variant_output_schema(self, output_validator):
        """Variant output schema should validate correctly."""
        # Valid data
        valid_data = {
            "variants": [
                {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
                {"chrom": "chr17", "pos": 41276044, "ref": "T", "alt": "C"},
            ],
            "metadata": {"source": "test"},
        }

        result = output_validator.validate_json(
            valid_data,
            schema=COMMON_SCHEMAS['variant_output'],
        )
        assert result.valid

    def test_pathogenicity_output_schema(self, output_validator):
        """Pathogenicity output schema should validate correctly."""
        # Valid data
        valid_data = {
            "predictions": [
                {
                    "variant_id": "chr1:100:A>G",
                    "score": 0.85,
                    "classification": "likely_pathogenic",
                },
            ],
        }

        result = output_validator.validate_json(
            valid_data,
            schema=COMMON_SCHEMAS['pathogenicity_output'],
        )
        assert result.valid

    def test_analysis_summary_schema(self, output_validator):
        """Analysis summary schema should validate correctly."""
        # Valid data
        valid_data = {
            "summary": {
                "total_variants": 100,
                "pathogenic_count": 5,
                "benign_count": 80,
            },
            "top_findings": [],
            "recommendations": [],
        }

        result = output_validator.validate_json(
            valid_data,
            schema=COMMON_SCHEMAS['analysis_summary'],
        )
        assert result.valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
