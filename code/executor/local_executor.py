"""
Local executor - executes topology workflows locally using Papermill.

Supports:
- Sequential step execution
- Dependency resolution
- Parameter passing
- Output tracking
- Error handling and logging
- Privacy mode (HIPAA compliance)
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import sys

import papermill as pm

# Import local utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from validator.topology_validator import TopologyValidator
from utils.parameter_resolver import ParameterResolver
from utils.storage_manager import StorageManager
from utils.graph import TopologyGraph


class LocalExecutor:
    """Executes topology workflows locally using Papermill."""

    def __init__(
        self,
        topology_path: str,
        params_path: Optional[str] = None,
        output_dir: Optional[str] = None,
        privacy_mode: Optional[bool] = None,
        log_level: str = 'INFO'
    ):
        """
        Initialize local executor.

        Args:
            topology_path: Path to topology.yaml
            params_path: Path to runtime parameters YAML (optional)
            output_dir: Output directory (default: topology_dir/outputs/run_<timestamp>)
            privacy_mode: Enable privacy mode (default: from topology config)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.topology_path = Path(topology_path)
        self.topology_dir = self.topology_path.parent
        self.params_path = Path(params_path) if params_path else None

        # Load topology
        with open(self.topology_path, 'r') as f:
            self.topology_dict = yaml.safe_load(f)

        self.topology = self.topology_dict.get('topology', {})

        # Load runtime parameters
        self.runtime_params = None
        if self.params_path:
            with open(self.params_path, 'r') as f:
                self.runtime_params = yaml.safe_load(f)

        # Configure privacy mode
        execution_config = self.topology.get('execution', {})
        if privacy_mode is not None:
            self.privacy_mode = privacy_mode
        else:
            self.privacy_mode = execution_config.get('privacy_mode', False)

        # Initialize storage manager
        self.storage = StorageManager(
            topology_dir=self.topology_dir,
            output_base_dir=Path(output_dir) if output_dir else None,
            privacy_mode=self.privacy_mode
        )

        # Initialize parameter resolver
        self.resolver = ParameterResolver(
            topology_dict=self.topology_dict,
            topology_dir=self.topology_dir,
            runtime_params=self.runtime_params
        )

        # Configure logging
        self.log_level = getattr(logging, log_level.upper())
        self.logger = None  # Initialized in execute()
        self.log_entries = []

        # Execution state
        self.run_dir = None
        self.start_time = None
        self.end_time = None
        self.execution_status = 'pending'

    def _setup_logging(self):
        """Configure logging for execution."""
        self.logger = logging.getLogger('topology_executor')
        self.logger.setLevel(self.log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (added after run_dir is created)
        if self.run_dir:
            file_handler = logging.FileHandler(
                self.run_dir / 'topology_execution.log'
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(console_formatter)
            self.logger.addHandler(file_handler)

    def _log(self, level: str, message: str):
        """Log message and store in log entries."""
        if self.logger:
            getattr(self.logger, level.lower())(message)

        self.log_entries.append({
            'timestamp': datetime.now().isoformat(),
            'level': level.upper(),
            'message': message
        })

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate topology before execution.

        Returns:
            Tuple of (is_valid, errors)
        """
        validator = TopologyValidator(str(self.topology_path))
        return validator.validate()

    def execute(self) -> Dict[str, Any]:
        """
        Execute topology workflow.

        Returns:
            Execution summary dictionary

        Raises:
            ValueError: If validation fails
            RuntimeError: If execution fails
        """
        self.start_time = datetime.now()
        self.execution_status = 'running'

        # Create run directory
        topology_name = self.topology.get('name', 'unknown')
        run_id = self.start_time.strftime('%Y%m%d_%H%M%S')
        self.run_dir = self.storage.create_run_directory(
            run_id=run_id,
            topology_name=topology_name
        )

        # Setup logging
        self._setup_logging()

        self._log('INFO', f"Starting topology execution: {topology_name}")
        self._log('INFO', f"Run directory: {self.run_dir}")
        self._log('INFO', f"Privacy mode: {self.privacy_mode}")

        # Validate topology
        self._log('INFO', "Validating topology...")
        is_valid, errors = self.validate()
        if not is_valid:
            self._log('ERROR', f"Topology validation failed with {len(errors)} error(s):")
            for error in errors:
                self._log('ERROR', f"  - {error}")
            self.execution_status = 'failed'
            raise ValueError(f"Topology validation failed: {errors}")

        self._log('INFO', "✓ Topology validation passed")

        # Get execution order
        workflow = self.topology.get('workflow', [])
        graph = TopologyGraph.from_yaml(self.topology_dict)
        execution_order = graph.topological_sort()

        self._log('INFO', f"Execution plan: {' → '.join(execution_order)}")

        # Execute steps
        executed_steps = []
        try:
            for step_id in execution_order:
                # Find step definition
                step = next(s for s in workflow if s['step'] == step_id)

                # Check condition if present
                if 'condition' in step:
                    condition_result = self.resolver.evaluate_condition(
                        step['condition'],
                        step_id
                    )
                    if not condition_result:
                        self._log('INFO', f"Skipping step {step_id} (condition not met)")
                        continue

                # Execute step
                self._execute_step(step)
                executed_steps.append(step_id)

            self.execution_status = 'completed'
            self._log('INFO', f"✓ Topology execution completed successfully")

        except Exception as e:
            self.execution_status = 'failed'
            self._log('ERROR', f"Topology execution failed: {e}")
            raise RuntimeError(f"Execution failed at step {step_id}: {e}")

        finally:
            self.end_time = datetime.now()

            # Save execution metadata
            execution_summary = self._create_summary(executed_steps)
            self.storage.save_topology_metadata(
                run_dir=self.run_dir,
                topology_dict=self.topology_dict,
                resolved_params=self.resolver.get_resolved_parameters(),
                execution_info=execution_summary
            )

            # Save logs
            self.storage.save_execution_log(self.run_dir, self.log_entries)

        return execution_summary

    def _execute_step(self, step: Dict):
        """
        Execute a single workflow step.

        Args:
            step: Step dictionary from workflow

        Raises:
            RuntimeError: If step execution fails
        """
        step_id = step['step']
        module_id = step['module']

        self._log('INFO', f"Executing step: {step_id}")

        # Create step output directory
        step_dir = self.storage.create_step_directory(self.run_dir, step_id)

        # Get module information
        modules = {m['id']: m for m in self.topology.get('modules', [])}
        if module_id not in modules:
            raise ValueError(f"Module '{module_id}' not found")

        module = modules[module_id]
        module_path = self.topology_dir / module['path']
        notebook_path = module_path / module['notebook']

        if not notebook_path.exists():
            raise ValueError(f"Notebook not found: {notebook_path}")

        self._log('DEBUG', f"  Module: {module_id} ({module_path})")
        self._log('DEBUG', f"  Notebook: {notebook_path}")

        # Resolve step inputs
        resolved_inputs = self.resolver.resolve_step_inputs(step)
        self._log('DEBUG', f"  Inputs: {json.dumps(resolved_inputs, indent=2)}")

        # Execute notebook with Papermill
        output_notebook = step_dir / 'output.ipynb'
        step_log_file = step_dir / 'execution.log'

        try:
            # Configure Papermill execution
            pm_params = {
                **resolved_inputs,
                'output_dir': str(step_dir)  # Pass output directory to notebook
            }

            # Execute
            self._log('INFO', f"  Running notebook...")
            pm.execute_notebook(
                input_path=str(notebook_path),
                output_path=str(output_notebook),
                parameters=pm_params,
                log_output=True,
                progress_bar=False
            )

            self._log('INFO', f"  ✓ Step {step_id} completed successfully")

        except Exception as e:
            self._log('ERROR', f"  ✗ Step {step_id} failed: {e}")

            # Save error log
            with open(step_log_file, 'w') as f:
                f.write(f"Step execution failed: {e}\n")

            raise RuntimeError(f"Step {step_id} execution failed: {e}")

        # Register step outputs
        step_outputs = {}
        for output_name, output_pattern in step.get('outputs', {}).items():
            # Resolve output path (may contain {output_dir} placeholder)
            output_path = output_pattern.replace('{output_dir}', str(step_dir))
            output_path = Path(output_path)

            if output_path.exists():
                step_outputs[output_name] = str(output_path)
                self._log('DEBUG', f"  Output '{output_name}': {output_path}")
            else:
                self._log('WARNING', f"  Expected output not found: {output_path}")

        # Register outputs for future steps
        self.resolver.register_step_outputs(step_id, step_outputs)

    def _create_summary(self, executed_steps: List[str]) -> Dict[str, Any]:
        """
        Create execution summary.

        Args:
            executed_steps: List of executed step IDs

        Returns:
            Summary dictionary
        """
        duration = None
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        summary = {
            'status': self.execution_status,
            'topology_name': self.topology.get('name'),
            'topology_version': self.topology.get('version'),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'executed_steps': executed_steps,
            'total_steps': len(self.topology.get('workflow', [])),
            'output_directory': str(self.run_dir),
            'privacy_mode': self.privacy_mode,
            'storage_backend': self.storage.storage_backend,
            'platform': self.storage.platform
        }

        return summary


def main():
    """CLI interface for local topology execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Execute topology workflow locally using Papermill'
    )
    parser.add_argument(
        '--topology',
        default='topology.yaml',
        help='Path to topology.yaml (default: topology.yaml)'
    )
    parser.add_argument(
        '--params',
        help='Path to runtime parameters YAML (optional)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: topology_dir/outputs/run_<timestamp>)'
    )
    parser.add_argument(
        '--privacy-mode',
        action='store_true',
        help='Enable privacy mode (local storage only, no remote uploads)'
    )
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate topology, do not execute'
    )
    args = parser.parse_args()

    # Create executor
    executor = LocalExecutor(
        topology_path=args.topology,
        params_path=args.params,
        output_dir=args.output_dir,
        privacy_mode=args.privacy_mode,
        log_level=args.log_level
    )

    # Validate only mode
    if args.validate_only:
        print(f"Validating topology: {args.topology}")
        print("-" * 60)

        is_valid, errors = executor.validate()

        if is_valid:
            print("✓ Topology is valid!")
            return 0
        else:
            print(f"✗ Topology validation failed with {len(errors)} error(s):")
            for i, error in enumerate(errors, 1):
                print(f"{i}. {error}")
            return 1

    # Full execution
    print(f"Executing topology: {args.topology}")
    print("-" * 60)

    try:
        summary = executor.execute()

        print("\n" + "=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Status: {summary['status']}")
        print(f"Executed steps: {summary['executed_steps']}")
        print(f"Duration: {summary['duration_seconds']:.2f} seconds")
        print(f"Output directory: {summary['output_directory']}")
        print("=" * 60)

        return 0 if summary['status'] == 'completed' else 1

    except Exception as e:
        print(f"\n✗ Execution failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
