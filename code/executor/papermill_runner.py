"""
Backend-aware Papermill runner for notebook execution.

Extends LocalExecutor with:
- Automatic backend detection (MPS, CUDA, ROCm, CPU)
- Backend parameter injection
- Pytest integration support
- Enhanced output capture

Usage:
    runner = PapermillRunner()
    result = runner.execute_notebook(
        notebook_path="module/notebooks/main.ipynb",
        parameters={"input_data": "/path/to/data.json"},
        output_dir="/tmp/output"
    )
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging

import papermill as pm

logger = logging.getLogger(__name__)


@dataclass
class BackendInfo:
    """Information about detected compute backend."""

    name: str  # 'mps', 'cuda', 'rocm', 'cpu'
    device_name: Optional[str] = None
    memory_gb: Optional[float] = None
    compute_capability: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'device_name': self.device_name,
            'memory_gb': self.memory_gb,
            'compute_capability': self.compute_capability,
        }


@dataclass
class ExecutionResult:
    """Result from notebook execution."""

    success: bool
    output_notebook: Optional[Path] = None
    duration_seconds: float = 0.0
    backend: Optional[BackendInfo] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    log_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'output_notebook': str(self.output_notebook) if self.output_notebook else None,
            'duration_seconds': self.duration_seconds,
            'backend': self.backend.to_dict() if self.backend else None,
            'outputs': self.outputs,
            'error': self.error,
            'log_path': str(self.log_path) if self.log_path else None,
        }


class BackendDetector:
    """Detects available compute backends."""

    # Backend priority chain
    PRIORITY = ['cuda', 'rocm', 'mps', 'cpu']

    @classmethod
    def detect(cls) -> BackendInfo:
        """
        Auto-detect best available backend.

        Priority: CUDA (NVIDIA) → ROCm (AMD) → MPS (Apple) → CPU

        Returns:
            BackendInfo with detected backend details
        """
        # Check CUDA first
        cuda_info = cls._check_cuda()
        if cuda_info:
            return cuda_info

        # Check ROCm
        rocm_info = cls._check_rocm()
        if rocm_info:
            return rocm_info

        # Check MPS (Apple Silicon)
        mps_info = cls._check_mps()
        if mps_info:
            return mps_info

        # Fallback to CPU
        return BackendInfo(
            name='cpu',
            device_name=platform.processor() or 'Unknown CPU',
        )

    @classmethod
    def _check_cuda(cls) -> Optional[BackendInfo]:
        """Check for NVIDIA CUDA support."""
        try:
            # Try nvidia-smi
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(', ')
                    device_name = parts[0] if parts else 'NVIDIA GPU'
                    memory_mb = float(parts[1]) if len(parts) > 1 else None
                    return BackendInfo(
                        name='cuda',
                        device_name=device_name,
                        memory_gb=memory_mb / 1024 if memory_mb else None,
                    )
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        # Try PyTorch
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                memory_bytes = torch.cuda.get_device_properties(0).total_memory
                return BackendInfo(
                    name='cuda',
                    device_name=device_name,
                    memory_gb=memory_bytes / (1024**3),
                    compute_capability=f"{torch.cuda.get_device_capability(0)[0]}.{torch.cuda.get_device_capability(0)[1]}",
                )
        except ImportError:
            pass

        return None

    @classmethod
    def _check_rocm(cls) -> Optional[BackendInfo]:
        """Check for AMD ROCm support."""
        try:
            # Try rocminfo
            result = subprocess.run(
                ['rocminfo'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and 'GPU' in result.stdout:
                # Parse device name from rocminfo output
                for line in result.stdout.split('\n'):
                    if 'Marketing Name' in line:
                        device_name = line.split(':')[-1].strip()
                        return BackendInfo(
                            name='rocm',
                            device_name=device_name,
                        )
                return BackendInfo(name='rocm', device_name='AMD GPU')
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return None

    @classmethod
    def _check_mps(cls) -> Optional[BackendInfo]:
        """Check for Apple MPS (Metal Performance Shaders) support."""
        if platform.system() != 'Darwin':
            return None

        if platform.machine() != 'arm64':
            return None

        # Check PyTorch MPS availability
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # Get chip info via sysctl
                try:
                    result = subprocess.run(
                        ['sysctl', '-n', 'machdep.cpu.brand_string'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    device_name = result.stdout.strip() if result.returncode == 0 else 'Apple Silicon'
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    device_name = 'Apple Silicon'

                return BackendInfo(
                    name='mps',
                    device_name=device_name,
                )
        except ImportError:
            # No PyTorch, but still might be Apple Silicon
            pass

        # Even without PyTorch, return MPS if on Apple Silicon
        # (notebooks may use MLX or other frameworks)
        return BackendInfo(
            name='mps',
            device_name='Apple Silicon',
        )


class PapermillRunner:
    """
    Backend-aware Papermill runner for notebook execution.

    Wraps pm.execute_notebook with:
    - Automatic backend detection
    - Backend parameter injection
    - Enhanced logging
    - Output capture
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        log_level: str = 'INFO',
        default_timeout: int = 3600,  # 1 hour default
    ):
        """
        Initialize Papermill runner.

        Args:
            backend: Force specific backend ('cuda', 'rocm', 'mps', 'cpu')
                     If None, auto-detect best available
            log_level: Logging level
            default_timeout: Default execution timeout in seconds
        """
        # Configure logging
        self.log_level = getattr(logging, log_level.upper())
        logging.basicConfig(level=self.log_level)

        # Detect or use specified backend
        if backend:
            self.backend = BackendInfo(name=backend)
            logger.info(f"Using specified backend: {backend}")
        else:
            self.backend = BackendDetector.detect()
            logger.info(f"Auto-detected backend: {self.backend.name}")
            if self.backend.device_name:
                logger.info(f"Device: {self.backend.device_name}")

        self.default_timeout = default_timeout

    def get_backend_parameters(self) -> Dict[str, Any]:
        """
        Get parameters to inject for backend configuration.

        Returns:
            Dictionary of backend-related parameters for notebook injection
        """
        params = {
            'BACKEND': self.backend.name,
            'DEVICE': self._get_device_string(),
        }

        # Backend-specific parameters
        if self.backend.name == 'cuda':
            params['USE_CUDA'] = True
            params['USE_MPS'] = False
            params['CUDA_VISIBLE_DEVICES'] = os.environ.get('CUDA_VISIBLE_DEVICES', '0')

        elif self.backend.name == 'rocm':
            params['USE_CUDA'] = False  # ROCm uses HIP, not CUDA
            params['USE_MPS'] = False
            params['HIP_VISIBLE_DEVICES'] = os.environ.get('HIP_VISIBLE_DEVICES', '0')

        elif self.backend.name == 'mps':
            params['USE_CUDA'] = False
            params['USE_MPS'] = True

        else:  # CPU
            params['USE_CUDA'] = False
            params['USE_MPS'] = False

        return params

    def _get_device_string(self) -> str:
        """Get device string for PyTorch/etc."""
        if self.backend.name == 'cuda':
            return 'cuda:0'
        elif self.backend.name == 'mps':
            return 'mps'
        else:
            return 'cpu'

    def execute_notebook(
        self,
        notebook_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        output_dir: Optional[Path] = None,
        output_notebook: Optional[Path] = None,
        inject_backend: bool = True,
        timeout: Optional[int] = None,
        kernel_name: Optional[str] = None,
        progress_bar: bool = False,
        log_output: bool = True,
    ) -> ExecutionResult:
        """
        Execute a notebook with Papermill.

        Args:
            notebook_path: Path to input notebook
            parameters: Parameters to inject (tagged 'parameters' cell)
            output_dir: Directory for output files (also passed to notebook)
            output_notebook: Path for executed notebook (default: output_dir/output.ipynb)
            inject_backend: Whether to inject backend parameters
            timeout: Execution timeout in seconds
            kernel_name: Jupyter kernel to use
            progress_bar: Show Papermill progress bar
            log_output: Log notebook output

        Returns:
            ExecutionResult with execution details
        """
        notebook_path = Path(notebook_path)
        if not notebook_path.exists():
            return ExecutionResult(
                success=False,
                error=f"Notebook not found: {notebook_path}",
                backend=self.backend,
            )

        # Setup output directory
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = notebook_path.parent / 'outputs' / datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir.mkdir(parents=True, exist_ok=True)

        # Output notebook path
        if output_notebook:
            output_notebook = Path(output_notebook)
        else:
            output_notebook = output_dir / 'output.ipynb'

        # Build parameters
        pm_params = parameters.copy() if parameters else {}

        # Inject backend parameters
        if inject_backend:
            pm_params.update(self.get_backend_parameters())

        # Always pass output directory
        pm_params['output_dir'] = str(output_dir)

        # Log execution details
        logger.info(f"Executing notebook: {notebook_path}")
        logger.info(f"Backend: {self.backend.name}")
        logger.info(f"Output directory: {output_dir}")
        logger.debug(f"Parameters: {json.dumps(pm_params, indent=2, default=str)}")

        # Setup log file
        log_path = output_dir / 'execution.log'

        start_time = datetime.now()

        try:
            # Execute with Papermill
            pm.execute_notebook(
                input_path=str(notebook_path),
                output_path=str(output_notebook),
                parameters=pm_params,
                kernel_name=kernel_name,
                progress_bar=progress_bar,
                log_output=log_output,
                request_save_on_cell_execute=True,
            )

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"Notebook executed successfully in {duration:.2f}s")

            # Collect outputs
            outputs = self._collect_outputs(output_dir)

            return ExecutionResult(
                success=True,
                output_notebook=output_notebook,
                duration_seconds=duration,
                backend=self.backend,
                outputs=outputs,
                log_path=log_path,
            )

        except pm.PapermillExecutionError as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Notebook execution failed at cell {e.cell_index}: {e.ename}: {e.evalue}"
            logger.error(error_msg)

            # Save error details to log
            with open(log_path, 'w') as f:
                f.write(f"Execution failed after {duration:.2f}s\n")
                f.write(f"Error: {error_msg}\n")
                f.write(f"Traceback:\n{e.traceback}\n")

            return ExecutionResult(
                success=False,
                output_notebook=output_notebook if output_notebook.exists() else None,
                duration_seconds=duration,
                backend=self.backend,
                error=error_msg,
                log_path=log_path,
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.error(error_msg)

            return ExecutionResult(
                success=False,
                duration_seconds=duration,
                backend=self.backend,
                error=error_msg,
            )

    def _collect_outputs(self, output_dir: Path) -> Dict[str, Any]:
        """
        Collect output files from execution directory.

        Args:
            output_dir: Directory containing outputs

        Returns:
            Dictionary mapping output names to file paths
        """
        outputs = {}

        # Look for common output patterns
        output_patterns = [
            ('json', '*.json'),
            ('csv', '*.csv'),
            ('parquet', '*.parquet'),
            ('png', '*.png'),
            ('html', '*.html'),
            ('md', '*.md'),
        ]

        for output_type, pattern in output_patterns:
            files = list(output_dir.glob(pattern))
            for f in files:
                # Skip the output notebook
                if f.suffix == '.ipynb':
                    continue
                outputs[f.stem] = str(f)

        return outputs


def main():
    """CLI interface for testing PapermillRunner."""
    import argparse

    parser = argparse.ArgumentParser(description='Execute notebook with backend detection')
    parser.add_argument('notebook', help='Path to notebook')
    parser.add_argument('--backend', choices=['cuda', 'rocm', 'mps', 'cpu'],
                        help='Force specific backend')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--params', help='Parameters JSON file')
    parser.add_argument('--no-inject-backend', action='store_true',
                        help='Do not inject backend parameters')
    parser.add_argument('--progress', action='store_true',
                        help='Show progress bar')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    args = parser.parse_args()

    # Load parameters if provided
    params = None
    if args.params:
        with open(args.params) as f:
            params = json.load(f)

    # Create runner
    runner = PapermillRunner(
        backend=args.backend,
        log_level=args.log_level,
    )

    # Execute
    result = runner.execute_notebook(
        notebook_path=Path(args.notebook),
        parameters=params,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        inject_backend=not args.no_inject_backend,
        progress_bar=args.progress,
    )

    # Print result
    print("\n" + "=" * 60)
    print("EXECUTION RESULT")
    print("=" * 60)
    print(json.dumps(result.to_dict(), indent=2))

    return 0 if result.success else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
