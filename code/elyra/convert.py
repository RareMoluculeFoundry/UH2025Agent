"""
Elyra converter - converts topology.yaml to Elyra pipeline format (.pipeline).

Elyra pipelines are visual DAGs that can be executed in JupyterLab.
Supports local execution or submission to Kubeflow/Airflow runtimes.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
import sys

# Import validation utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from validator.topology_validator import TopologyValidator
from utils.graph import TopologyGraph


class ElyraConverter:
    """Converts topology definitions to Elyra pipeline format."""

    # Elyra pipeline schema version
    PIPELINE_VERSION = "3.0"
    PRIMARY_PIPELINE_VERSION = "3.0"

    # Node positioning
    NODE_WIDTH = 200
    NODE_HEIGHT = 100
    NODE_SPACING_X = 350
    NODE_SPACING_Y = 150

    def __init__(self, topology_path: str):
        """
        Initialize Elyra converter.

        Args:
            topology_path: Path to topology.yaml
        """
        self.topology_path = Path(topology_path)
        self.topology_dir = self.topology_path.parent

        # Load topology
        with open(self.topology_path, 'r') as f:
            self.topology_dict = yaml.safe_load(f)

        self.topology = self.topology_dict.get('topology', {})

        # Build module lookup
        self.modules = {
            m['id']: m for m in self.topology.get('modules', [])
        }

    def validate(self) -> bool:
        """
        Validate topology before conversion.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        validator = TopologyValidator(str(self.topology_path))
        is_valid, errors = validator.validate()

        if not is_valid:
            raise ValueError(
                f"Topology validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        return True

    def convert(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert topology to Elyra pipeline.

        Args:
            output_path: Output .pipeline file path (optional)

        Returns:
            Elyra pipeline dictionary
        """
        # Validate first
        self.validate()

        # Get workflow steps
        workflow = self.topology.get('workflow', [])

        # Build DAG for layout
        graph = TopologyGraph.from_yaml(self.topology_dict)
        execution_levels = graph.get_execution_levels()

        # Create pipeline structure
        pipeline = self._create_pipeline_skeleton()

        # Add nodes for each step
        nodes = []
        node_positions = self._calculate_node_positions(workflow, execution_levels)

        for step in workflow:
            node = self._create_node(step, node_positions[step['step']])
            nodes.append(node)

        # Add nodes to pipeline
        pipeline['pipelines'][0]['nodes'] = nodes

        # Add connections (edges) based on dependencies
        pipeline['pipelines'][0]['app_data']['ui_data']['comments'] = []

        # Save to file if output path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(pipeline, f, indent=2)

        return pipeline

    def _create_pipeline_skeleton(self) -> Dict[str, Any]:
        """Create basic Elyra pipeline structure."""
        pipeline_id = str(uuid.uuid4())

        return {
            "doc_type": "pipeline",
            "version": self.PIPELINE_VERSION,
            "json_schema": "http://api.dataplatform.ibm.com/schemas/common-pipeline/pipeline-flow/pipeline-flow-v3-schema.json",
            "id": pipeline_id,
            "primary_pipeline": pipeline_id,
            "pipelines": [
                {
                    "id": pipeline_id,
                    "nodes": [],  # Will be populated
                    "app_data": {
                        "ui_data": {
                            "comments": []
                        },
                        "version": self.PRIMARY_PIPELINE_VERSION,
                        "runtime_type": "KUBEFLOW_PIPELINES",
                        "properties": {
                            "name": self.topology.get('name', 'topology'),
                            "runtime": "Kubeflow Pipelines",
                            "description": self.topology.get('description', '')
                        }
                    },
                    "runtime_ref": ""
                }
            ],
            "schemas": []
        }

    def _calculate_node_positions(
        self,
        workflow: List[Dict],
        execution_levels: Dict[str, int]
    ) -> Dict[str, tuple]:
        """
        Calculate visual positions for nodes based on execution levels.

        Args:
            workflow: Workflow steps
            execution_levels: Step execution levels from TopologyGraph

        Returns:
            Dictionary mapping step_id -> (x, y) position
        """
        positions = {}

        # Group steps by level
        levels = {}
        for step in workflow:
            step_id = step['step']
            level = execution_levels.get(step_id, 0)

            if level not in levels:
                levels[level] = []
            levels[level].append(step_id)

        # Calculate positions
        for level, step_ids in sorted(levels.items()):
            num_steps = len(step_ids)
            x = level * self.NODE_SPACING_X + 50

            # Center steps vertically within level
            for i, step_id in enumerate(step_ids):
                y = i * self.NODE_SPACING_Y + 50
                positions[step_id] = (x, y)

        return positions

    def _create_node(self, step: Dict, position: tuple) -> Dict[str, Any]:
        """
        Create Elyra node for a workflow step.

        Args:
            step: Step dictionary from workflow
            position: (x, y) position tuple

        Returns:
            Elyra node dictionary
        """
        step_id = step['step']
        module_id = step['module']
        module = self.modules[module_id]

        # Get notebook path relative to topology directory
        notebook_path = Path(module['path']) / module['notebook']

        # Create node
        node_id = str(uuid.uuid4())

        node = {
            "id": node_id,
            "type": "execution_node",
            "op": "execute-notebook-node",
            "app_data": {
                "label": step_id,
                "component_parameters": {
                    "filename": str(notebook_path),
                    "runtime_image": self._get_runtime_image(step),
                    "dependencies": self._get_dependencies(module),
                    "include_subdirectories": False,
                    "outputs": self._format_outputs(step),
                    "env_vars": self._format_env_vars(step),
                    "kubernetes_secrets": [],
                    "kubernetes_tolerations": [],
                    "kubernetes_pod_annotations": [],
                    "mounted_volumes": [],
                    "cpu": self._get_cpu_request(step),
                    "memory": self._get_memory_request(step),
                    "gpu": self._get_gpu_request(step)
                },
                "ui_data": {
                    "label": step_id,
                    "image": "/static/elyra/notebook.svg",
                    "x_pos": position[0],
                    "y_pos": position[1],
                    "description": step.get('description', '')
                }
            },
            "inputs": [
                {
                    "id": f"inPort-{node_id}",
                    "app_data": {
                        "ui_data": {
                            "cardinality": {"min": 0, "max": -1},
                            "label": "Input Port"
                        }
                    }
                }
            ],
            "outputs": [
                {
                    "id": f"outPort-{node_id}",
                    "app_data": {
                        "ui_data": {
                            "cardinality": {"min": 0, "max": -1},
                            "label": "Output Port"
                        }
                    }
                }
            ]
        }

        return node

    def _get_runtime_image(self, step: Dict) -> str:
        """
        Get Docker runtime image for step.

        Args:
            step: Step dictionary

        Returns:
            Docker image name
        """
        # Default to standard JupyterLab image
        # In production, would reference module-specific Docker images
        return "elyra/kf-notebook:latest"

    def _get_dependencies(self, module: Dict) -> List[str]:
        """
        Get file dependencies for module.

        Args:
            module: Module dictionary

        Returns:
            List of file patterns to include
        """
        # Include entire module directory
        return [f"{module['path']}/*"]

    def _format_outputs(self, step: Dict) -> List[str]:
        """
        Format output file patterns for Elyra.

        Args:
            step: Step dictionary

        Returns:
            List of output file patterns
        """
        outputs = []
        for output_name, output_path in step.get('outputs', {}).items():
            # Extract filename from path
            if '/' in output_path:
                filename = Path(output_path).name
                outputs.append(filename)
            else:
                outputs.append(output_path)

        return outputs

    def _format_env_vars(self, step: Dict) -> List[Dict[str, str]]:
        """
        Format environment variables for Elyra.

        Args:
            step: Step dictionary

        Returns:
            List of {env_var, value} dictionaries
        """
        env_vars = []

        # Add step-specific environment variables if present
        if 'env' in step:
            for key, value in step['env'].items():
                env_vars.append({
                    "env_var": key,
                    "value": str(value)
                })

        # Add privacy mode if enabled
        execution_config = self.topology.get('execution', {})
        if execution_config.get('privacy_mode'):
            env_vars.append({
                "env_var": "DELAB_PRIVACY_MODE",
                "value": "true"
            })

        return env_vars

    def _get_cpu_request(self, step: Dict) -> Optional[int]:
        """Get CPU resource request."""
        resources = step.get('resources', {})
        return resources.get('cpu')

    def _get_memory_request(self, step: Dict) -> Optional[int]:
        """Get memory resource request (in GB)."""
        resources = step.get('resources', {})
        memory_str = resources.get('memory')

        if not memory_str:
            return None

        # Parse memory string (e.g., "16Gi" -> 16)
        if isinstance(memory_str, str):
            if memory_str.endswith('Gi'):
                return int(memory_str[:-2])
            elif memory_str.endswith('G'):
                return int(memory_str[:-1])
            elif memory_str.endswith('Mi'):
                return int(memory_str[:-2]) // 1024
            elif memory_str.endswith('M'):
                return int(memory_str[:-1]) // 1024

        return None

    def _get_gpu_request(self, step: Dict) -> Optional[int]:
        """Get GPU resource request."""
        resources = step.get('resources', {})
        return resources.get('gpu', 0)


def main():
    """CLI interface for Elyra conversion."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert topology.yaml to Elyra pipeline format'
    )
    parser.add_argument(
        '--topology',
        default='topology.yaml',
        help='Path to topology.yaml (default: topology.yaml)'
    )
    parser.add_argument(
        '--output',
        help='Output .pipeline file path (default: <topology-name>.pipeline)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate topology, do not convert'
    )
    args = parser.parse_args()

    # Create converter
    converter = ElyraConverter(args.topology)

    # Validate only mode
    if args.validate_only:
        print(f"Validating topology: {args.topology}")
        print("-" * 60)

        try:
            converter.validate()
            print("✓ Topology is valid for Elyra conversion!")
            return 0
        except ValueError as e:
            print(f"✗ Validation failed:\n{e}")
            return 1

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        topology_name = converter.topology.get('name', 'topology')
        output_path = f"{topology_name}.pipeline"

    # Convert
    print(f"Converting topology: {args.topology}")
    print(f"Output pipeline: {output_path}")
    print("-" * 60)

    try:
        pipeline = converter.convert(output_path)

        num_nodes = len(pipeline['pipelines'][0]['nodes'])
        print(f"\n✓ Conversion successful!")
        print(f"  - {num_nodes} nodes created")
        print(f"  - Pipeline saved to: {output_path}")
        print(f"\nTo open in JupyterLab:")
        print(f"  jupyter lab {output_path}")

        return 0

    except Exception as e:
        print(f"\n✗ Conversion failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
