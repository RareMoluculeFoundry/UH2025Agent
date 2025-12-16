"""
Unified execution wrapper ensuring 1:1 parity between execution modes.

Ensures consistent behavior across:
- Direct notebook execution (per-module via PapermillRunner)
- LocalExecutor (topology-driven sequential execution)
- ElyraRunner (pipeline-driven DAG execution)

All execution modes ultimately go through PapermillRunner for consistent:
- Backend detection and parameter injection
- Output directory handling
- Parameter normalization
- Error handling and result structure

Usage:
    runner = UnifiedRunner()

    # Direct execution
    result = runner.execute_notebook(
        notebook_path="module/notebooks/main.ipynb",
        parameters={"input_data": "data.json"},
        output_dir="/tmp/output",
        mode="direct"
    )

    # Compare outputs
    report = runner.compare_outputs(result1, result2)
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
import importlib.util
import logging

logger = logging.getLogger(__name__)

# Load PapermillRunner via importlib to avoid conflicts
_executor_dir = Path(__file__).parent
_pm_runner_path = _executor_dir / "papermill_runner.py"

if _pm_runner_path.exists():
    spec = importlib.util.spec_from_file_location("_papermill_runner", str(_pm_runner_path))
    _pm_module = importlib.util.module_from_spec(spec)
    sys.modules["_papermill_runner_unified"] = _pm_module
    spec.loader.exec_module(_pm_module)
    PapermillRunner = _pm_module.PapermillRunner
    ExecutionResult = _pm_module.ExecutionResult
    BackendInfo = _pm_module.BackendInfo
    BackendDetector = _pm_module.BackendDetector
else:
    raise ImportError(f"PapermillRunner not found at {_pm_runner_path}")


@dataclass
class ParityReport:
    """Report comparing outputs between two execution modes."""

    is_identical: bool
    mode_a: str
    mode_b: str
    output_comparisons: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    parameter_differences: List[str] = field(default_factory=list)
    structure_differences: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_identical': self.is_identical,
            'mode_a': self.mode_a,
            'mode_b': self.mode_b,
            'output_comparisons': self.output_comparisons,
            'parameter_differences': self.parameter_differences,
            'structure_differences': self.structure_differences,
            'notes': self.notes,
        }


class UnifiedRunner:
    """
    Unified execution wrapper ensuring 1:1 parity between execution modes.

    All execution ultimately uses PapermillRunner to ensure:
    - Consistent backend detection
    - Consistent parameter normalization
    - Consistent output handling
    """

    # Standard parameter names that should be consistent across modes
    STANDARD_PARAMS = {
        'output_dir',      # Output directory for results
        'patient_id',      # Common identifier
        'input_file',      # Input data path
        'output_file',     # Output data path
        'privacy_mode',    # HIPAA compliance flag
    }

    # Backend parameters injected by PapermillRunner
    BACKEND_PARAMS = {
        'BACKEND',
        'DEVICE',
        'USE_CUDA',
        'USE_MPS',
        'CUDA_VISIBLE_DEVICES',
        'HIP_VISIBLE_DEVICES',
    }

    def __init__(
        self,
        backend: Optional[str] = None,
        log_level: str = 'INFO',
    ):
        """
        Initialize unified runner.

        Args:
            backend: Force specific backend ('cuda', 'rocm', 'mps', 'cpu')
                     If None, auto-detect best available
            log_level: Logging level
        """
        self.papermill_runner = PapermillRunner(
            backend=backend,
            log_level=log_level,
        )
        self.backend = self.papermill_runner.backend
        self.log_level = log_level

        logging.basicConfig(level=getattr(logging, log_level.upper()))

    def normalize_parameters(
        self,
        parameters: Dict[str, Any],
        output_dir: Optional[Path] = None,
        include_backend: bool = True,
    ) -> Dict[str, Any]:
        """
        Normalize parameters to standard format across all execution modes.

        Args:
            parameters: Input parameters
            output_dir: Output directory to inject
            include_backend: Whether to include backend parameters

        Returns:
            Normalized parameters dictionary
        """
        normalized = {}

        # Copy user parameters
        if parameters:
            normalized.update(parameters)

        # Add output_dir if provided and not already present
        if output_dir and 'output_dir' not in normalized:
            normalized['output_dir'] = str(output_dir)

        # Add backend parameters if requested
        if include_backend:
            backend_params = self.papermill_runner.get_backend_parameters()
            normalized.update(backend_params)

        return normalized

    def execute_notebook(
        self,
        notebook_path: Union[str, Path],
        parameters: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Union[str, Path]] = None,
        mode: str = "direct",
    ) -> ExecutionResult:
        """
        Execute notebook with unified parameter handling.

        Args:
            notebook_path: Path to notebook
            parameters: Parameters to inject
            output_dir: Output directory
            mode: Execution mode ("direct", "local", "elyra") - for tracking only

        Returns:
            ExecutionResult from PapermillRunner
        """
        notebook_path = Path(notebook_path)
        output_dir = Path(output_dir) if output_dir else None

        # Normalize parameters
        normalized_params = self.normalize_parameters(
            parameters=parameters or {},
            output_dir=output_dir,
            include_backend=True,
        )

        logger.info(f"Executing notebook: {notebook_path}")
        logger.info(f"Mode: {mode}")
        logger.debug(f"Normalized parameters: {json.dumps(normalized_params, indent=2, default=str)}")

        # Execute via PapermillRunner (same path for all modes)
        result = self.papermill_runner.execute_notebook(
            notebook_path=notebook_path,
            parameters=normalized_params,
            output_dir=output_dir,
            inject_backend=False,  # Already injected in normalized params
        )

        return result

    def compare_outputs(
        self,
        result_a: ExecutionResult,
        result_b: ExecutionResult,
        mode_a: str = "mode_a",
        mode_b: str = "mode_b",
        ignore_timestamps: bool = True,
        ignore_paths: bool = True,
    ) -> ParityReport:
        """
        Compare outputs between two execution results.

        Args:
            result_a: First execution result
            result_b: Second execution result
            mode_a: Name for first mode
            mode_b: Name for second mode
            ignore_timestamps: Ignore timestamp differences in outputs
            ignore_paths: Ignore absolute path differences

        Returns:
            ParityReport with comparison details
        """
        report = ParityReport(
            is_identical=True,
            mode_a=mode_a,
            mode_b=mode_b,
        )

        # Check success status
        if result_a.success != result_b.success:
            report.is_identical = False
            report.structure_differences.append(
                f"Success status differs: {mode_a}={result_a.success}, {mode_b}={result_b.success}"
            )

        # Check backend consistency
        if result_a.backend and result_b.backend:
            if result_a.backend.name != result_b.backend.name:
                report.is_identical = False
                report.parameter_differences.append(
                    f"Backend differs: {mode_a}={result_a.backend.name}, {mode_b}={result_b.backend.name}"
                )

        # Compare outputs
        outputs_a = result_a.outputs or {}
        outputs_b = result_b.outputs or {}

        # Check for missing outputs
        keys_a = set(outputs_a.keys())
        keys_b = set(outputs_b.keys())

        missing_in_b = keys_a - keys_b
        missing_in_a = keys_b - keys_a

        if missing_in_b:
            report.is_identical = False
            report.structure_differences.append(
                f"Outputs missing in {mode_b}: {missing_in_b}"
            )

        if missing_in_a:
            report.is_identical = False
            report.structure_differences.append(
                f"Outputs missing in {mode_a}: {missing_in_a}"
            )

        # Compare common outputs
        common_keys = keys_a & keys_b
        for key in common_keys:
            path_a = Path(outputs_a[key])
            path_b = Path(outputs_b[key])

            comparison = self._compare_output_files(
                path_a, path_b,
                ignore_timestamps=ignore_timestamps,
                ignore_paths=ignore_paths,
            )

            report.output_comparisons[key] = comparison

            if not comparison.get('identical', False):
                report.is_identical = False

        return report

    def _compare_output_files(
        self,
        path_a: Path,
        path_b: Path,
        ignore_timestamps: bool = True,
        ignore_paths: bool = True,
    ) -> Dict[str, Any]:
        """
        Compare two output files for content equality.

        Args:
            path_a: First file path
            path_b: Second file path
            ignore_timestamps: Ignore timestamp fields
            ignore_paths: Ignore path fields

        Returns:
            Comparison result dictionary
        """
        result = {
            'path_a': str(path_a),
            'path_b': str(path_b),
            'identical': False,
            'differences': [],
        }

        # Check existence
        if not path_a.exists():
            result['differences'].append(f"File A does not exist: {path_a}")
            return result

        if not path_b.exists():
            result['differences'].append(f"File B does not exist: {path_b}")
            return result

        # Compare by file type
        suffix = path_a.suffix.lower()

        if suffix == '.json':
            return self._compare_json_files(path_a, path_b, ignore_timestamps, ignore_paths)
        else:
            # Binary/hash comparison
            return self._compare_binary_files(path_a, path_b)

    def _compare_json_files(
        self,
        path_a: Path,
        path_b: Path,
        ignore_timestamps: bool,
        ignore_paths: bool,
    ) -> Dict[str, Any]:
        """Compare two JSON files."""
        result = {
            'path_a': str(path_a),
            'path_b': str(path_b),
            'identical': False,
            'differences': [],
        }

        try:
            with open(path_a) as f:
                data_a = json.load(f)
            with open(path_b) as f:
                data_b = json.load(f)
        except json.JSONDecodeError as e:
            result['differences'].append(f"JSON parse error: {e}")
            return result

        # Normalize for comparison
        normalized_a = self._normalize_json_for_comparison(
            data_a, ignore_timestamps, ignore_paths
        )
        normalized_b = self._normalize_json_for_comparison(
            data_b, ignore_timestamps, ignore_paths
        )

        if normalized_a == normalized_b:
            result['identical'] = True
        else:
            result['differences'] = self._find_json_differences(normalized_a, normalized_b)

        return result

    def _normalize_json_for_comparison(
        self,
        data: Any,
        ignore_timestamps: bool,
        ignore_paths: bool,
    ) -> Any:
        """Normalize JSON data for comparison."""
        if isinstance(data, dict):
            normalized = {}
            for k, v in data.items():
                # Skip timestamp fields
                if ignore_timestamps and any(ts in k.lower() for ts in ['timestamp', 'created_at', 'updated_at', 'time', 'date']):
                    continue
                # Skip path fields
                if ignore_paths and any(p in k.lower() for p in ['path', 'directory', 'dir', 'file']):
                    if isinstance(v, str) and ('/' in v or '\\' in v):
                        continue
                normalized[k] = self._normalize_json_for_comparison(v, ignore_timestamps, ignore_paths)
            return normalized
        elif isinstance(data, list):
            return [self._normalize_json_for_comparison(item, ignore_timestamps, ignore_paths) for item in data]
        else:
            return data

    def _find_json_differences(self, data_a: Any, data_b: Any, path: str = "") -> List[str]:
        """Find differences between two JSON structures."""
        differences = []

        if type(data_a) != type(data_b):
            differences.append(f"{path}: type differs ({type(data_a).__name__} vs {type(data_b).__name__})")
            return differences

        if isinstance(data_a, dict):
            keys_a = set(data_a.keys())
            keys_b = set(data_b.keys())

            for key in keys_a - keys_b:
                differences.append(f"{path}.{key}: missing in B")
            for key in keys_b - keys_a:
                differences.append(f"{path}.{key}: missing in A")

            for key in keys_a & keys_b:
                differences.extend(self._find_json_differences(
                    data_a[key], data_b[key], f"{path}.{key}"
                ))

        elif isinstance(data_a, list):
            if len(data_a) != len(data_b):
                differences.append(f"{path}: list length differs ({len(data_a)} vs {len(data_b)})")
            else:
                for i, (item_a, item_b) in enumerate(zip(data_a, data_b)):
                    differences.extend(self._find_json_differences(
                        item_a, item_b, f"{path}[{i}]"
                    ))

        elif data_a != data_b:
            differences.append(f"{path}: value differs ({data_a} vs {data_b})")

        return differences

    def _compare_binary_files(self, path_a: Path, path_b: Path) -> Dict[str, Any]:
        """Compare two binary files via hash."""
        result = {
            'path_a': str(path_a),
            'path_b': str(path_b),
            'identical': False,
            'differences': [],
        }

        hash_a = self._file_hash(path_a)
        hash_b = self._file_hash(path_b)

        result['hash_a'] = hash_a
        result['hash_b'] = hash_b

        if hash_a == hash_b:
            result['identical'] = True
        else:
            result['differences'].append(f"File hashes differ")

        return result

    def _file_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_backend_info(self) -> Dict[str, Any]:
        """Get current backend information."""
        return {
            'backend': self.backend.to_dict() if self.backend else None,
            'parameters': self.papermill_runner.get_backend_parameters(),
        }


def main():
    """CLI interface for UnifiedRunner."""
    import argparse

    parser = argparse.ArgumentParser(description='Unified notebook execution with parity checking')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Execute command
    exec_parser = subparsers.add_parser('execute', help='Execute a notebook')
    exec_parser.add_argument('notebook', help='Path to notebook')
    exec_parser.add_argument('--output-dir', help='Output directory')
    exec_parser.add_argument('--params', help='Parameters JSON file')
    exec_parser.add_argument('--backend', choices=['cuda', 'rocm', 'mps', 'cpu'],
                            help='Force specific backend')
    exec_parser.add_argument('--mode', default='direct',
                            choices=['direct', 'local', 'elyra'],
                            help='Execution mode (for tracking)')

    # Compare command
    cmp_parser = subparsers.add_parser('compare', help='Compare two output directories')
    cmp_parser.add_argument('dir_a', help='First output directory')
    cmp_parser.add_argument('dir_b', help='Second output directory')
    cmp_parser.add_argument('--mode-a', default='mode_a', help='Name for first mode')
    cmp_parser.add_argument('--mode-b', default='mode_b', help='Name for second mode')

    # Backend info command
    info_parser = subparsers.add_parser('info', help='Show backend information')

    args = parser.parse_args()

    if args.command == 'execute':
        # Load parameters if provided
        params = None
        if args.params:
            with open(args.params) as f:
                params = json.load(f)

        runner = UnifiedRunner(backend=args.backend)
        result = runner.execute_notebook(
            notebook_path=Path(args.notebook),
            parameters=params,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            mode=args.mode,
        )

        print("\nExecution Result:")
        print(json.dumps(result.to_dict(), indent=2, default=str))
        return 0 if result.success else 1

    elif args.command == 'compare':
        # This would need actual result objects - simplified for CLI
        print(f"Compare not yet implemented for CLI")
        return 1

    elif args.command == 'info':
        runner = UnifiedRunner()
        info = runner.get_backend_info()
        print("\nBackend Information:")
        print(json.dumps(info, indent=2, default=str))
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
