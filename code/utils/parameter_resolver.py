"""
Parameter resolver - resolves parameter references in topology inputs.

Supports three reference types:
1. Dataset references: {dataset: "dataset-id"}
2. Parameter references: {param: "param-name"}
3. Step output references: {step: "step-id", output: "output-name"}
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import copy


class ParameterResolver:
    """Resolves parameter references in topology workflow."""

    def __init__(
        self,
        topology_dict: Dict,
        topology_dir: Path,
        runtime_params: Optional[Dict] = None,
        step_outputs: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize parameter resolver.

        Args:
            topology_dict: Parsed topology.yaml
            topology_dir: Directory containing topology.yaml
            runtime_params: Runtime parameter overrides (optional)
            step_outputs: Completed step outputs for reference resolution (optional)
        """
        self.topology_dict = topology_dict
        self.topology_dir = Path(topology_dir)
        self.topology = topology_dict.get('topology', {})

        # Global parameters with runtime overrides
        self.parameters = copy.deepcopy(self.topology.get('parameters', {}))
        if runtime_params:
            self.parameters.update(runtime_params)

        # Dataset references
        self.datasets = {
            d['id']: d for d in self.topology.get('datasets', [])
        }

        # Step outputs (populated during execution)
        self.step_outputs = step_outputs or {}

    def resolve_step_inputs(self, step: Dict) -> Dict[str, Any]:
        """
        Resolve all input references for a step.

        Args:
            step: Step dictionary from workflow

        Returns:
            Dictionary of resolved input values ready for notebook execution

        Raises:
            ValueError: If reference cannot be resolved
        """
        inputs = step.get('inputs', {})
        resolved = {}

        for input_name, input_value in inputs.items():
            resolved[input_name] = self.resolve_value(
                input_value,
                step_id=step['step']
            )

        return resolved

    def resolve_value(self, value: Any, step_id: str) -> Any:
        """
        Recursively resolve a single value.

        Args:
            value: Value to resolve (may contain references)
            step_id: Current step ID (for error messages)

        Returns:
            Resolved value

        Raises:
            ValueError: If reference cannot be resolved
        """
        # Handle dictionary references
        if isinstance(value, dict):
            # Dataset reference
            if 'dataset' in value:
                return self._resolve_dataset(value['dataset'], step_id)

            # Parameter reference
            elif 'param' in value:
                return self._resolve_parameter(value['param'], step_id)

            # Step output reference
            elif 'step' in value and 'output' in value:
                return self._resolve_step_output(
                    value['step'],
                    value['output'],
                    step_id
                )

            # Nested dictionary - resolve recursively
            else:
                return {
                    k: self.resolve_value(v, step_id)
                    for k, v in value.items()
                }

        # Handle list values
        elif isinstance(value, list):
            return [self.resolve_value(v, step_id) for v in value]

        # Literal value (string, number, boolean, etc.)
        else:
            return value

    def _resolve_dataset(self, dataset_id: str, step_id: str) -> str:
        """
        Resolve dataset reference to path.

        Args:
            dataset_id: Dataset identifier
            step_id: Current step ID (for error messages)

        Returns:
            Absolute path to dataset

        Raises:
            ValueError: If dataset not found
        """
        if dataset_id not in self.datasets:
            raise ValueError(
                f"Step '{step_id}' references undefined dataset '{dataset_id}'"
            )

        dataset = self.datasets[dataset_id]
        dataset_path = self.topology_dir / dataset['path']

        # If subset specified, return path to subset file
        if 'subset' in dataset:
            return str(dataset_path / dataset['subset'])

        # Otherwise return dataset directory
        return str(dataset_path)

    def _resolve_parameter(self, param_name: str, step_id: str) -> Any:
        """
        Resolve parameter reference to value.

        Args:
            param_name: Parameter name
            step_id: Current step ID (for error messages)

        Returns:
            Parameter value

        Raises:
            ValueError: If parameter not found
        """
        if param_name not in self.parameters:
            raise ValueError(
                f"Step '{step_id}' references undefined parameter '{param_name}'"
            )

        return self.parameters[param_name]

    def _resolve_step_output(
        self,
        ref_step_id: str,
        output_name: str,
        current_step_id: str
    ) -> str:
        """
        Resolve step output reference to path.

        Args:
            ref_step_id: Referenced step ID
            output_name: Output name from referenced step
            current_step_id: Current step ID (for error messages)

        Returns:
            Path to output file from referenced step

        Raises:
            ValueError: If step or output not found
        """
        # Check step exists
        if ref_step_id not in self.step_outputs:
            raise ValueError(
                f"Step '{current_step_id}' references output from "
                f"step '{ref_step_id}' which has not been executed yet"
            )

        step_outputs = self.step_outputs[ref_step_id]

        # Check output exists
        if output_name not in step_outputs:
            raise ValueError(
                f"Step '{current_step_id}' references undefined output "
                f"'{output_name}' from step '{ref_step_id}'"
            )

        return step_outputs[output_name]

    def register_step_outputs(self, step_id: str, outputs: Dict[str, str]):
        """
        Register outputs from a completed step.

        Args:
            step_id: Step ID
            outputs: Dictionary of output_name -> file_path
        """
        self.step_outputs[step_id] = outputs

    def get_resolved_parameters(self) -> Dict[str, Any]:
        """
        Get all parameters (defaults + runtime overrides).

        Returns:
            Dictionary of all parameters
        """
        return copy.deepcopy(self.parameters)

    def evaluate_condition(self, condition: str, step_id: str) -> bool:
        """
        Evaluate a conditional expression.

        Supports simple expressions like:
        - "confidence > 0.8"
        - "num_samples <= 1000"
        - "enable_parallel == true"

        Args:
            condition: Condition string
            step_id: Current step ID (for error messages)

        Returns:
            Boolean result of condition evaluation

        Raises:
            ValueError: If condition is invalid
        """
        try:
            # Replace parameter references in condition
            resolved_condition = condition
            for param_name, param_value in self.parameters.items():
                # Replace parameter names with their values
                if param_name in resolved_condition:
                    # Quote strings, leave numbers/booleans as-is
                    if isinstance(param_value, str):
                        param_repr = f"'{param_value}'"
                    else:
                        param_repr = str(param_value)
                    resolved_condition = resolved_condition.replace(
                        param_name, param_repr
                    )

            # Evaluate condition (safe eval with restricted namespace)
            # Only allow comparison operators and literals
            allowed_names = {'true': True, 'false': False, 'True': True, 'False': False}
            result = eval(resolved_condition, {"__builtins__": {}}, allowed_names)

            if not isinstance(result, bool):
                raise ValueError(
                    f"Condition must evaluate to boolean, got {type(result)}"
                )

            return result

        except Exception as e:
            raise ValueError(
                f"Step '{step_id}' has invalid condition '{condition}': {e}"
            )

    def resolve_parallel_config(self, parallel_config: Dict) -> Dict[str, Any]:
        """
        Resolve parallel execution configuration.

        Args:
            parallel_config: Parallel configuration from step

        Returns:
            Resolved parallel configuration

        Example:
            Input:
                {
                    "split_input": "data_chunks",
                    "num_workers": 4,
                    "merge_output": "processed_chunks"
                }

            Output:
                Same structure with any parameter references resolved
        """
        resolved = {}
        for key, value in parallel_config.items():
            # num_workers might reference a parameter
            if key == 'num_workers' and isinstance(value, dict):
                resolved[key] = self.resolve_value(value, step_id='parallel')
            else:
                resolved[key] = value

        return resolved


def main():
    """CLI interface for testing parameter resolution."""
    import argparse
    import yaml
    import json

    parser = argparse.ArgumentParser(
        description='Test parameter resolution for topology'
    )
    parser.add_argument(
        '--topology',
        default='topology.yaml',
        help='Path to topology.yaml'
    )
    parser.add_argument(
        '--params',
        help='Path to runtime parameters YAML (optional)'
    )
    parser.add_argument(
        '--step',
        required=True,
        help='Step ID to resolve inputs for'
    )
    args = parser.parse_args()

    # Load topology
    with open(args.topology, 'r') as f:
        topology_dict = yaml.safe_load(f)

    # Load runtime parameters
    runtime_params = None
    if args.params:
        with open(args.params, 'r') as f:
            runtime_params = yaml.safe_load(f)

    # Create resolver
    topology_dir = Path(args.topology).parent
    resolver = ParameterResolver(
        topology_dict=topology_dict,
        topology_dir=topology_dir,
        runtime_params=runtime_params
    )

    # Find step
    workflow = topology_dict.get('topology', {}).get('workflow', [])
    target_step = None
    for step in workflow:
        if step['step'] == args.step:
            target_step = step
            break

    if not target_step:
        print(f"Error: Step '{args.step}' not found in workflow")
        return 1

    # Resolve inputs
    try:
        resolved_inputs = resolver.resolve_step_inputs(target_step)
        print(f"Resolved inputs for step '{args.step}':")
        print(json.dumps(resolved_inputs, indent=2))
        return 0
    except ValueError as e:
        print(f"Error resolving inputs: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
