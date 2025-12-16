"""
Elyra pipeline runner - executes .pipeline files programmatically.

Provides two execution modes:
1. Local execution via PapermillRunner (uses backend detection)
2. Elyra CLI execution (subprocess, requires elyra-pipeline CLI)

This enables testing Elyra pipelines from within Claude Code and pytest
without requiring the JupyterLab UI.

Usage:
    runner = ElyraRunner("elyra/UH2025Agent.pipeline")

    # Local execution (uses PapermillRunner)
    result = runner.execute_local(parameters={"patient_id": "test123"})

    # Elyra CLI execution (if available)
    result = runner.execute_elyra(runtime="local")
"""

import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import sys
import importlib.util

# Import papermill_runner directly from file to avoid sys.path conflicts
# (papermill has an 'elyra' entry point that conflicts with our module name)
_executor_dir = Path(__file__).parent.parent / "executor"
_pm_runner_path = _executor_dir / "papermill_runner.py"

if _pm_runner_path.exists():
    spec = importlib.util.spec_from_file_location("_papermill_runner", str(_pm_runner_path))
    _pm_module = importlib.util.module_from_spec(spec)
    sys.modules["_papermill_runner"] = _pm_module
    spec.loader.exec_module(_pm_module)

    PapermillRunner = _pm_module.PapermillRunner
    ExecutionResult = _pm_module.ExecutionResult
    BackendDetector = _pm_module.BackendDetector
else:
    # Fallback for when imported from different context
    from executor.papermill_runner import PapermillRunner, ExecutionResult, BackendDetector

logger = logging.getLogger(__name__)


@dataclass
class PipelineNode:
    """Represents a node in an Elyra pipeline."""

    id: str
    label: str
    notebook_path: str
    outputs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Node IDs this depends on
    env_vars: Dict[str, str] = field(default_factory=dict)
    cpu: Optional[int] = None
    memory: Optional[str] = None
    gpu: int = 0
    runtime_image: Optional[str] = None

    @classmethod
    def from_pipeline_node(cls, node_dict: Dict[str, Any], pipeline_dir: Path) -> 'PipelineNode':
        """
        Create PipelineNode from Elyra pipeline node dictionary.

        Args:
            node_dict: Node dictionary from .pipeline JSON
            pipeline_dir: Directory containing the .pipeline file

        Returns:
            PipelineNode instance
        """
        app_data = node_dict.get('app_data', {})
        component_params = app_data.get('component_parameters', {})

        # Get notebook path (relative to pipeline file)
        notebook_path = component_params.get('filename', '')
        if notebook_path:
            # Resolve relative path from pipeline directory
            notebook_path = str((pipeline_dir / notebook_path).resolve())

        # Extract dependencies from inputs
        dependencies = []
        for input_port in node_dict.get('inputs', []):
            for link in input_port.get('links', []):
                node_id_ref = link.get('node_id_ref')
                if node_id_ref:
                    dependencies.append(node_id_ref)

        # Parse env vars
        env_vars = {}
        for env_entry in component_params.get('env_vars', []):
            if 'env_var' in env_entry and 'value' in env_entry:
                env_vars[env_entry['env_var']] = env_entry['value']

        return cls(
            id=node_dict['id'],
            label=app_data.get('label', node_dict['id']),
            notebook_path=notebook_path,
            outputs=component_params.get('outputs', []),
            dependencies=dependencies,
            env_vars=env_vars,
            cpu=component_params.get('cpu'),
            memory=component_params.get('memory'),
            gpu=component_params.get('gpu', 0),
            runtime_image=component_params.get('runtime_image'),
        )


@dataclass
class PipelineExecutionResult:
    """Result from pipeline execution."""

    success: bool
    total_duration_seconds: float = 0.0
    node_results: Dict[str, ExecutionResult] = field(default_factory=dict)
    execution_order: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'total_duration_seconds': self.total_duration_seconds,
            'node_results': {
                node_id: result.to_dict()
                for node_id, result in self.node_results.items()
            },
            'execution_order': self.execution_order,
            'error': self.error,
        }


class ElyraRunner:
    """
    Execute Elyra pipelines programmatically.

    Supports two execution modes:
    1. Local: Execute notebooks via PapermillRunner (recommended for testing)
    2. Elyra: Execute via elyra-pipeline CLI (requires Elyra installation)
    """

    def __init__(
        self,
        pipeline_path: str,
        base_output_dir: Optional[str] = None,
        log_level: str = 'INFO',
    ):
        """
        Initialize Elyra runner.

        Args:
            pipeline_path: Path to .pipeline file
            base_output_dir: Base directory for outputs (default: pipeline_dir/outputs)
            log_level: Logging level
        """
        self.pipeline_path = Path(pipeline_path).resolve()
        self.pipeline_dir = self.pipeline_path.parent

        if not self.pipeline_path.exists():
            raise FileNotFoundError(f"Pipeline not found: {self.pipeline_path}")

        # Load pipeline
        with open(self.pipeline_path) as f:
            self.pipeline_dict = json.load(f)

        # Configure logging
        self.log_level = getattr(logging, log_level.upper())
        logging.basicConfig(level=self.log_level)

        # Parse pipeline structure
        self.nodes = self._parse_nodes()
        self.execution_order = self._compute_execution_order()

        # Configure output directory
        if base_output_dir:
            self.base_output_dir = Path(base_output_dir)
        else:
            self.base_output_dir = self.pipeline_dir / 'outputs'

        logger.info(f"Loaded pipeline: {self.pipeline_path.name}")
        logger.info(f"Nodes: {len(self.nodes)}")
        logger.info(f"Execution order: {' → '.join(self.execution_order)}")

    @property
    def name(self) -> str:
        """Get pipeline name."""
        pipelines = self.pipeline_dict.get('pipelines', [])
        if pipelines:
            props = pipelines[0].get('app_data', {}).get('properties', {})
            return props.get('name', 'pipeline')
        return 'pipeline'

    @property
    def version(self) -> str:
        """Get pipeline schema version."""
        return self.pipeline_dict.get('version', 'unknown')

    def _parse_nodes(self) -> Dict[str, PipelineNode]:
        """Parse nodes from pipeline JSON."""
        nodes = {}

        pipelines = self.pipeline_dict.get('pipelines', [])
        if not pipelines:
            return nodes

        for node_dict in pipelines[0].get('nodes', []):
            node = PipelineNode.from_pipeline_node(node_dict, self.pipeline_dir)
            nodes[node.id] = node

        return nodes

    def _compute_execution_order(self) -> List[str]:
        """
        Compute execution order using topological sort.

        Returns:
            List of node IDs in execution order
        """
        # Build dependency graph
        in_degree = {node_id: 0 for node_id in self.nodes}
        dependents = {node_id: [] for node_id in self.nodes}

        for node_id, node in self.nodes.items():
            for dep_id in node.dependencies:
                if dep_id in self.nodes:
                    dependents[dep_id].append(node_id)
                    in_degree[node_id] += 1

        # Kahn's algorithm
        order = []
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]

        while queue:
            # Sort for deterministic order (by label)
            queue.sort(key=lambda x: self.nodes[x].label)
            node_id = queue.pop(0)
            order.append(node_id)

            for dependent_id in dependents[node_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)

        # Check for cycles
        if len(order) != len(self.nodes):
            remaining = set(self.nodes.keys()) - set(order)
            raise ValueError(f"Pipeline has cycles involving: {remaining}")

        return order

    def get_parallel_groups(self) -> List[List[str]]:
        """
        Get groups of nodes that can execute in parallel.

        Returns:
            List of groups, each containing node IDs that can run in parallel
        """
        groups = []
        processed = set()

        while len(processed) < len(self.nodes):
            # Find nodes whose dependencies are all processed
            parallel_group = []
            for node_id in self.execution_order:
                if node_id in processed:
                    continue

                node = self.nodes[node_id]
                if all(dep in processed for dep in node.dependencies):
                    parallel_group.append(node_id)

            if parallel_group:
                groups.append(parallel_group)
                processed.update(parallel_group)
            else:
                break

        return groups

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate pipeline structure.

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check version
        if self.version not in ('3.0', '8'):
            errors.append(f"Unsupported pipeline version: {self.version}")

        # Check nodes
        for node_id, node in self.nodes.items():
            # Check notebook exists
            if not node.notebook_path:
                errors.append(f"Node '{node.label}' has no notebook path")
            elif not Path(node.notebook_path).exists():
                errors.append(f"Node '{node.label}' notebook not found: {node.notebook_path}")

            # Check dependencies exist
            for dep_id in node.dependencies:
                if dep_id not in self.nodes:
                    errors.append(f"Node '{node.label}' depends on unknown node: {dep_id}")

        return len(errors) == 0, errors

    def execute_local(
        self,
        parameters: Optional[Dict[str, Any]] = None,
        backend: Optional[str] = None,
        output_dir: Optional[str] = None,
        stop_on_error: bool = True,
        node_filter: Optional[List[str]] = None,
    ) -> PipelineExecutionResult:
        """
        Execute pipeline locally using PapermillRunner.

        Args:
            parameters: Parameters to pass to all notebooks
            backend: Force specific backend (None for auto-detect)
            output_dir: Override output directory
            stop_on_error: Stop execution if a node fails
            node_filter: Only execute these node labels (None for all)

        Returns:
            PipelineExecutionResult with execution details
        """
        # Validate first
        is_valid, errors = self.validate()
        if not is_valid:
            return PipelineExecutionResult(
                success=False,
                error=f"Pipeline validation failed:\n" + "\n".join(f"  - {e}" for e in errors),
            )

        # Setup output directory
        if output_dir:
            run_output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            run_output_dir = self.base_output_dir / f'run_{timestamp}'

        run_output_dir.mkdir(parents=True, exist_ok=True)

        # Create runner
        runner = PapermillRunner(backend=backend)

        logger.info(f"Starting local pipeline execution")
        logger.info(f"Backend: {runner.backend.name}")
        logger.info(f"Output directory: {run_output_dir}")

        start_time = datetime.now()
        node_results = {}
        execution_order_actual = []
        overall_success = True

        # Execute nodes in order
        for node_id in self.execution_order:
            node = self.nodes[node_id]

            # Apply filter if specified
            if node_filter and node.label not in node_filter:
                logger.info(f"Skipping {node.label} (filtered)")
                continue

            logger.info(f"\n{'='*60}")
            logger.info(f"Executing: {node.label}")
            logger.info(f"Notebook: {node.notebook_path}")

            # Setup node output directory
            node_output_dir = run_output_dir / node.label
            node_output_dir.mkdir(parents=True, exist_ok=True)

            # Build parameters
            node_params = parameters.copy() if parameters else {}

            # Add outputs from previous nodes
            for dep_id in node.dependencies:
                if dep_id in node_results:
                    dep_result = node_results[dep_id]
                    dep_node = self.nodes[dep_id]
                    # Pass output paths from dependencies
                    node_params[f'{dep_node.label}_outputs'] = dep_result.outputs

            # Add node-specific env vars
            node_params.update(node.env_vars)

            # Execute
            result = runner.execute_notebook(
                notebook_path=Path(node.notebook_path),
                parameters=node_params,
                output_dir=node_output_dir,
            )

            node_results[node_id] = result
            execution_order_actual.append(node.label)

            if result.success:
                logger.info(f"✓ {node.label} completed in {result.duration_seconds:.2f}s")
            else:
                logger.error(f"✗ {node.label} failed: {result.error}")
                overall_success = False

                if stop_on_error:
                    logger.error("Stopping pipeline execution due to error")
                    break

        total_duration = (datetime.now() - start_time).total_seconds()

        return PipelineExecutionResult(
            success=overall_success,
            total_duration_seconds=total_duration,
            node_results=node_results,
            execution_order=execution_order_actual,
        )

    def execute_elyra(
        self,
        runtime: str = 'local',
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PipelineExecutionResult:
        """
        Execute pipeline via Elyra CLI (elyra-pipeline).

        Args:
            runtime: Runtime to use ('local' or configured runtime name)
            parameters: Parameters to pass (if supported)

        Returns:
            PipelineExecutionResult
        """
        # Check if elyra-pipeline CLI is available
        if not shutil.which('elyra-pipeline'):
            return PipelineExecutionResult(
                success=False,
                error="elyra-pipeline CLI not found. Install with: pip install elyra",
            )

        logger.info(f"Executing via Elyra CLI with runtime: {runtime}")

        start_time = datetime.now()

        try:
            # Build command
            cmd = [
                'elyra-pipeline',
                'submit',
                str(self.pipeline_path),
                '--runtime-config', runtime,
            ]

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )

            duration = (datetime.now() - start_time).total_seconds()

            if result.returncode == 0:
                logger.info(f"Elyra execution completed in {duration:.2f}s")
                return PipelineExecutionResult(
                    success=True,
                    total_duration_seconds=duration,
                )
            else:
                return PipelineExecutionResult(
                    success=False,
                    total_duration_seconds=duration,
                    error=f"Elyra CLI failed:\n{result.stderr}",
                )

        except subprocess.TimeoutExpired:
            return PipelineExecutionResult(
                success=False,
                error="Elyra execution timed out after 1 hour",
            )
        except Exception as e:
            return PipelineExecutionResult(
                success=False,
                error=f"Elyra execution failed: {str(e)}",
            )

    def execute_node(
        self,
        node_label: str,
        parameters: Optional[Dict[str, Any]] = None,
        backend: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute a single node by label.

        Useful for testing individual notebooks.

        Args:
            node_label: Label of node to execute
            parameters: Parameters to pass
            backend: Force specific backend
            output_dir: Override output directory

        Returns:
            ExecutionResult from notebook execution
        """
        # Find node by label
        node = None
        for n in self.nodes.values():
            if n.label == node_label:
                node = n
                break

        if not node:
            available = [n.label for n in self.nodes.values()]
            raise ValueError(
                f"Node '{node_label}' not found. Available: {available}"
            )

        # Setup output
        if output_dir:
            node_output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            node_output_dir = self.base_output_dir / f'{node.label}_{timestamp}'

        node_output_dir.mkdir(parents=True, exist_ok=True)

        # Create runner and execute
        runner = PapermillRunner(backend=backend)

        node_params = parameters.copy() if parameters else {}
        node_params.update(node.env_vars)

        return runner.execute_notebook(
            notebook_path=Path(node.notebook_path),
            parameters=node_params,
            output_dir=node_output_dir,
        )

    def __repr__(self) -> str:
        return f"ElyraRunner('{self.pipeline_path.name}', nodes={len(self.nodes)})"


def main():
    """CLI interface for ElyraRunner."""
    import argparse

    parser = argparse.ArgumentParser(description='Execute Elyra pipeline')
    parser.add_argument('pipeline', help='Path to .pipeline file')
    parser.add_argument('--backend', choices=['cuda', 'rocm', 'mps', 'cpu'],
                        help='Force specific backend')
    parser.add_argument('--output-dir', help='Output directory')
    parser.add_argument('--validate-only', action='store_true',
                        help='Only validate pipeline')
    parser.add_argument('--node', help='Execute single node by label')
    parser.add_argument('--elyra', action='store_true',
                        help='Use Elyra CLI instead of local execution')
    parser.add_argument('--runtime', default='local',
                        help='Elyra runtime config (default: local)')
    parser.add_argument('--params', help='Parameters JSON file')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])

    args = parser.parse_args()

    # Load parameters
    params = None
    if args.params:
        with open(args.params) as f:
            params = json.load(f)

    # Create runner
    runner = ElyraRunner(
        args.pipeline,
        base_output_dir=args.output_dir,
        log_level=args.log_level,
    )

    # Validate only
    if args.validate_only:
        is_valid, errors = runner.validate()
        if is_valid:
            print(f"✓ Pipeline is valid: {runner.name}")
            print(f"  Version: {runner.version}")
            print(f"  Nodes: {len(runner.nodes)}")
            print(f"  Execution order:")
            for i, node_id in enumerate(runner.execution_order, 1):
                node = runner.nodes[node_id]
                print(f"    {i}. {node.label}")
            return 0
        else:
            print(f"✗ Pipeline validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1

    # Execute single node
    if args.node:
        result = runner.execute_node(
            args.node,
            parameters=params,
            backend=args.backend,
        )
        print("\n" + "=" * 60)
        print("NODE EXECUTION RESULT")
        print("=" * 60)
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.success else 1

    # Execute pipeline
    if args.elyra:
        result = runner.execute_elyra(
            runtime=args.runtime,
            parameters=params,
        )
    else:
        result = runner.execute_local(
            parameters=params,
            backend=args.backend,
        )

    print("\n" + "=" * 60)
    print("PIPELINE EXECUTION RESULT")
    print("=" * 60)
    print(json.dumps(result.to_dict(), indent=2, default=str))

    return 0 if result.success else 1


if __name__ == '__main__':
    sys.exit(main())
