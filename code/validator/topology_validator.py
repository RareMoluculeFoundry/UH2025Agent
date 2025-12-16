"""
Topology validator - validates topology.yaml against schema and business rules.
"""

import json
import yaml
from pathlib import Path
from typing import Tuple, List, Dict
import jsonschema

from ..utils.graph import TopologyGraph


class TopologyValidator:
    """Validates topology definitions."""

    def __init__(self, topology_path: str):
        """
        Initialize validator.

        Args:
            topology_path: Path to topology.yaml file
        """
        self.topology_path = Path(topology_path)
        self.topology_dir = self.topology_path.parent
        self.topology_dict = None
        self.schema = None

    def load_topology(self) -> Tuple[bool, List[str]]:
        """
        Load and parse topology.yaml.

        Returns:
            Tuple of (success, errors)
        """
        errors = []

        if not self.topology_path.exists():
            errors.append(f"Topology file not found: {self.topology_path}")
            return False, errors

        try:
            with open(self.topology_path, 'r') as f:
                self.topology_dict = yaml.safe_load(f)
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {e}")
            return False, errors

        if not self.topology_dict or 'topology' not in self.topology_dict:
            errors.append("Missing 'topology' root key")
            return False, errors

        return True, []

    def load_schema(self) -> Tuple[bool, List[str]]:
        """
        Load JSON schema.

        Returns:
            Tuple of (success, errors)
        """
        errors = []
        schema_path = self.topology_dir / 'metadata' / 'schema.json'

        if not schema_path.exists():
            errors.append(f"Schema file not found: {schema_path}")
            return False, errors

        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON schema: {e}")
            return False, errors

        return True, []

    def validate_schema(self) -> Tuple[bool, List[str]]:
        """
        Validate topology against JSON schema.

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        if not self.schema:
            errors.append("Schema not loaded")
            return False, errors

        try:
            jsonschema.validate(self.topology_dict, self.schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message} at path: {'.'.join(str(p) for p in e.path)}")
            return False, errors
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid schema: {e}")
            return False, errors

        return True, []

    def validate_dag(self) -> Tuple[bool, List[str]]:
        """
        Validate DAG structure (no cycles, valid dependencies).

        Returns:
            Tuple of (is_valid, errors)
        """
        try:
            graph = TopologyGraph.from_yaml(self.topology_dict)
            return graph.validate()
        except Exception as e:
            return False, [f"DAG validation error: {e}"]

    def validate_module_references(self) -> Tuple[bool, List[str]]:
        """
        Validate module references exist.

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        topology = self.topology_dict.get('topology', {})
        modules = {m['id']: m for m in topology.get('modules', [])}
        workflow = topology.get('workflow', [])

        # Check each step references a valid module
        for step in workflow:
            module_id = step.get('module')
            if module_id not in modules:
                errors.append(f"Step '{step['step']}' references undefined module '{module_id}'")
                continue

            # Check module path exists
            module = modules[module_id]
            module_path = self.topology_dir / module['path']
            if not module_path.exists():
                errors.append(f"Module path does not exist: {module_path}")
            else:
                # Check notebook exists
                notebook_path = module_path / module['notebook']
                if not notebook_path.exists():
                    errors.append(f"Module notebook not found: {notebook_path}")

        return len(errors) == 0, errors

    def validate_dataset_references(self) -> Tuple[bool, List[str]]:
        """
        Validate dataset references exist.

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        topology = self.topology_dict.get('topology', {})
        datasets = {d['id']: d for d in topology.get('datasets', [])}

        # Check each dataset path exists
        for dataset_id, dataset in datasets.items():
            dataset_path = self.topology_dir / dataset['path']

            if not dataset_path.exists():
                if dataset.get('required', True):
                    errors.append(f"Required dataset path does not exist: {dataset_path}")
            else:
                # Check subset file exists if specified
                if 'subset' in dataset:
                    subset_path = dataset_path / dataset['subset']
                    if not subset_path.exists():
                        if dataset.get('required', True):
                            errors.append(f"Required dataset subset not found: {subset_path}")

        return len(errors) == 0, errors

    def validate_parameter_references(self) -> Tuple[bool, List[str]]:
        """
        Validate parameter references.

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        topology = self.topology_dict.get('topology', {})
        parameters = set(topology.get('parameters', {}).keys())
        workflow = topology.get('workflow', [])
        datasets = {d['id']: d for d in topology.get('datasets', [])}

        # Track outputs from each step
        step_outputs = {}
        for step in workflow:
            step_outputs[step['step']] = set(step.get('outputs', {}).keys())

        # Validate parameter references in inputs
        for step in workflow:
            inputs = step.get('inputs', {})
            for input_name, input_value in inputs.items():
                if isinstance(input_value, dict):
                    # Check parameter reference
                    if 'param' in input_value:
                        param_name = input_value['param']
                        if param_name not in parameters:
                            errors.append(f"Step '{step['step']}' references undefined parameter '{param_name}'")

                    # Check dataset reference
                    elif 'dataset' in input_value:
                        dataset_id = input_value['dataset']
                        if dataset_id not in datasets:
                            errors.append(f"Step '{step['step']}' references undefined dataset '{dataset_id}'")

                    # Check step output reference
                    elif 'step' in input_value and 'output' in input_value:
                        ref_step = input_value['step']
                        ref_output = input_value['output']

                        if ref_step not in step_outputs:
                            errors.append(f"Step '{step['step']}' references undefined step '{ref_step}'")
                        elif ref_output not in step_outputs[ref_step]:
                            errors.append(f"Step '{step['step']}' references undefined output '{ref_output}' from step '{ref_step}'")

        return len(errors) == 0, errors

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (is_valid, all_errors)
        """
        all_errors = []

        # Load topology
        success, errors = self.load_topology()
        if not success:
            return False, errors
        all_errors.extend(errors)

        # Load schema
        success, errors = self.load_schema()
        if not success:
            return False, all_errors + errors
        all_errors.extend(errors)

        # Schema validation
        success, errors = self.validate_schema()
        all_errors.extend(errors)

        # DAG validation
        success, errors = self.validate_dag()
        all_errors.extend(errors)

        # Module references
        success, errors = self.validate_module_references()
        all_errors.extend(errors)

        # Dataset references
        success, errors = self.validate_dataset_references()
        all_errors.extend(errors)

        # Parameter references
        success, errors = self.validate_parameter_references()
        all_errors.extend(errors)

        return len(all_errors) == 0, all_errors


def main():
    """CLI interface for topology validation."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Validate topology definition')
    parser.add_argument('--topology', default='topology.yaml',
                       help='Path to topology.yaml (default: topology.yaml)')
    args = parser.parse_args()

    print(f"Validating topology: {args.topology}")
    print("-" * 60)

    validator = TopologyValidator(args.topology)
    is_valid, errors = validator.validate()

    if is_valid:
        print("✓ Topology is valid!")
        print("\nValidation passed:")
        print("  - YAML syntax")
        print("  - Schema compliance")
        print("  - DAG structure (no cycles)")
        print("  - Module references")
        print("  - Dataset references")
        print("  - Parameter references")
        sys.exit(0)
    else:
        print("✗ Topology validation failed!")
        print(f"\nFound {len(errors)} error(s):\n")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
