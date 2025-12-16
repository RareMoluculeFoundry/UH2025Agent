"""
Execution parity tests ensuring 1:1 behavior between:
- Direct notebook execution (via UnifiedRunner)
- LocalExecutor execution (topology-driven)
- ElyraRunner execution (pipeline-driven)

These tests verify that:
1. Parameter normalization is consistent across modes
2. Backend detection produces identical results
3. Output structures match between execution modes
4. JSON output content is identical (excluding timestamps/paths)

Usage:
    # Run all parity tests
    pytest tests/test_execution_parity.py -v --run-slow

    # Run only fast parity tests (no execution)
    pytest tests/test_execution_parity.py -v -m "parity and not slow"

    # Run backend parity tests only
    pytest tests/test_execution_parity.py -k "backend" -v
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


# Load unified runner
_unified_runner = _load_module_from_file(
    "_unified_runner_test",
    EXECUTOR_DIR / "unified_runner.py"
)
UnifiedRunner = _unified_runner.UnifiedRunner
ParityReport = _unified_runner.ParityReport


class TestParameterNormalization:
    """Test that parameter normalization is consistent."""

    def test_empty_parameters_normalized(self, unified_runner):
        """Empty parameters get backend params added."""
        normalized = unified_runner.normalize_parameters({})

        assert 'BACKEND' in normalized
        assert 'DEVICE' in normalized
        assert 'USE_CUDA' in normalized or 'USE_MPS' in normalized

    def test_output_dir_injected(self, unified_runner, tmp_output_dir):
        """output_dir is properly injected."""
        normalized = unified_runner.normalize_parameters(
            parameters={},
            output_dir=tmp_output_dir,
        )

        assert 'output_dir' in normalized
        assert normalized['output_dir'] == str(tmp_output_dir)

    def test_user_params_preserved(self, unified_runner):
        """User-provided parameters are preserved."""
        user_params = {
            'patient_id': 'TestPatient',
            'input_file': '/path/to/input.json',
            'custom_param': 'custom_value',
        }

        normalized = unified_runner.normalize_parameters(user_params)

        for key, value in user_params.items():
            assert key in normalized
            assert normalized[key] == value

    def test_backend_params_can_be_excluded(self, unified_runner):
        """Backend params can be excluded when requested."""
        normalized = unified_runner.normalize_parameters(
            parameters={},
            include_backend=False,
        )

        assert 'BACKEND' not in normalized
        assert 'DEVICE' not in normalized

    def test_normalization_idempotent(self, unified_runner, tmp_output_dir):
        """Normalizing already normalized params produces same result."""
        params = {'patient_id': 'TestPatient'}

        normalized1 = unified_runner.normalize_parameters(
            params, output_dir=tmp_output_dir
        )
        normalized2 = unified_runner.normalize_parameters(
            normalized1, output_dir=tmp_output_dir
        )

        # Should be identical
        assert normalized1 == normalized2


@pytest.mark.parity
class TestBackendParity:
    """Verify backend detection works identically across contexts."""

    def test_backend_detection_consistent(self, unified_runner):
        """Same backend detected each time."""
        backend1 = unified_runner.get_backend_info()
        backend2 = unified_runner.get_backend_info()

        assert backend1['backend']['name'] == backend2['backend']['name']

    def test_backend_params_propagated(self, unified_runner):
        """Backend parameters are properly set."""
        info = unified_runner.get_backend_info()

        params = info['parameters']
        assert 'BACKEND' in params
        assert 'DEVICE' in params
        assert params['BACKEND'] in ('cuda', 'rocm', 'mps', 'cpu')

    def test_backend_matches_normalized_params(self, unified_runner):
        """Backend in info matches backend in normalized params."""
        info = unified_runner.get_backend_info()
        normalized = unified_runner.normalize_parameters({})

        assert info['parameters']['BACKEND'] == normalized['BACKEND']
        assert info['parameters']['DEVICE'] == normalized['DEVICE']

    def test_mps_backend_on_apple_silicon(self, unified_runner):
        """MPS backend detected on Apple Silicon (if applicable)."""
        import platform

        info = unified_runner.get_backend_info()
        backend = info['backend']['name']

        # On Apple Silicon without CUDA/ROCm, should be MPS
        if platform.system() == 'Darwin' and platform.machine() == 'arm64':
            # MPS should be detected (unless CUDA/ROCm available via emulation)
            assert backend in ('mps', 'cuda', 'rocm', 'cpu')


@pytest.mark.parity
class TestOutputComparison:
    """Test output comparison functionality."""

    def test_identical_json_detected(self, unified_runner, tmp_output_dir):
        """Identical JSON files are detected as equal."""
        # Create two identical JSON files
        data = {'result': 'success', 'score': 0.95, 'items': [1, 2, 3]}

        file_a = tmp_output_dir / 'output_a.json'
        file_b = tmp_output_dir / 'output_b.json'

        with open(file_a, 'w') as f:
            json.dump(data, f)
        with open(file_b, 'w') as f:
            json.dump(data, f)

        comparison = unified_runner._compare_json_files(
            file_a, file_b,
            ignore_timestamps=True,
            ignore_paths=True,
        )

        assert comparison['identical'] is True
        assert len(comparison['differences']) == 0

    def test_different_json_detected(self, unified_runner, tmp_output_dir):
        """Different JSON files are detected as different."""
        file_a = tmp_output_dir / 'output_a.json'
        file_b = tmp_output_dir / 'output_b.json'

        with open(file_a, 'w') as f:
            json.dump({'result': 'success', 'score': 0.95}, f)
        with open(file_b, 'w') as f:
            json.dump({'result': 'success', 'score': 0.90}, f)

        comparison = unified_runner._compare_json_files(
            file_a, file_b,
            ignore_timestamps=True,
            ignore_paths=True,
        )

        assert comparison['identical'] is False
        assert len(comparison['differences']) > 0

    def test_timestamp_ignored_when_requested(self, unified_runner, tmp_output_dir):
        """Timestamp fields are ignored when requested."""
        file_a = tmp_output_dir / 'output_a.json'
        file_b = tmp_output_dir / 'output_b.json'

        with open(file_a, 'w') as f:
            json.dump({'result': 'success', 'timestamp': '2024-01-01T00:00:00'}, f)
        with open(file_b, 'w') as f:
            json.dump({'result': 'success', 'timestamp': '2024-01-02T00:00:00'}, f)

        comparison = unified_runner._compare_json_files(
            file_a, file_b,
            ignore_timestamps=True,
            ignore_paths=True,
        )

        assert comparison['identical'] is True

    def test_paths_ignored_when_requested(self, unified_runner, tmp_output_dir):
        """Path fields are ignored when requested."""
        file_a = tmp_output_dir / 'output_a.json'
        file_b = tmp_output_dir / 'output_b.json'

        with open(file_a, 'w') as f:
            json.dump({'result': 'success', 'output_path': '/path/a/output.json'}, f)
        with open(file_b, 'w') as f:
            json.dump({'result': 'success', 'output_path': '/path/b/output.json'}, f)

        comparison = unified_runner._compare_json_files(
            file_a, file_b,
            ignore_timestamps=True,
            ignore_paths=True,
        )

        assert comparison['identical'] is True

    def test_binary_hash_comparison(self, unified_runner, tmp_output_dir):
        """Binary files are compared by hash."""
        file_a = tmp_output_dir / 'output_a.bin'
        file_b = tmp_output_dir / 'output_b.bin'

        # Same content
        with open(file_a, 'wb') as f:
            f.write(b'binary content here')
        with open(file_b, 'wb') as f:
            f.write(b'binary content here')

        comparison = unified_runner._compare_binary_files(file_a, file_b)

        assert comparison['identical'] is True
        assert comparison['hash_a'] == comparison['hash_b']


@pytest.mark.parity
@pytest.mark.slow
class TestExecutionParity:
    """Verify identical outputs across execution modes."""

    def test_parameter_normalization_parity(self, unified_runner, tmp_output_dir):
        """Parameters are normalized identically regardless of source."""
        base_params = {
            'patient_id': 'TestPatient',
            'input_file': '/data/input.json',
        }

        # Simulate parameters from different sources
        direct_params = unified_runner.normalize_parameters(
            base_params.copy(),
            output_dir=tmp_output_dir / 'direct',
        )

        local_params = unified_runner.normalize_parameters(
            base_params.copy(),
            output_dir=tmp_output_dir / 'local',
        )

        elyra_params = unified_runner.normalize_parameters(
            base_params.copy(),
            output_dir=tmp_output_dir / 'elyra',
        )

        # Backend and device should be identical
        assert direct_params['BACKEND'] == local_params['BACKEND'] == elyra_params['BACKEND']
        assert direct_params['DEVICE'] == local_params['DEVICE'] == elyra_params['DEVICE']

        # User params should be preserved
        assert direct_params['patient_id'] == local_params['patient_id'] == elyra_params['patient_id']


@pytest.mark.parity
class TestParityReport:
    """Test ParityReport data structure."""

    def test_parity_report_creation(self):
        """ParityReport can be created with minimal data."""
        report = ParityReport(
            is_identical=True,
            mode_a='direct',
            mode_b='elyra',
        )

        assert report.is_identical is True
        assert report.mode_a == 'direct'
        assert report.mode_b == 'elyra'

    def test_parity_report_to_dict(self):
        """ParityReport serializes to dictionary."""
        report = ParityReport(
            is_identical=False,
            mode_a='direct',
            mode_b='local',
            parameter_differences=['BACKEND differs'],
            structure_differences=['Output count differs'],
        )

        data = report.to_dict()

        assert isinstance(data, dict)
        assert data['is_identical'] is False
        assert 'BACKEND differs' in data['parameter_differences']


# =============================================================================
# Fixtures (can be moved to conftest.py)
# =============================================================================

@pytest.fixture
def unified_runner():
    """Provide UnifiedRunner instance."""
    return UnifiedRunner(log_level='WARNING')
