"""
Elyra integration tests for UH2025Agent topology.

Tests:
- Pipeline loading and validation
- DAG structure verification
- Individual node execution
- Full pipeline execution
- Module notebook execution

Usage:
    # Run all Elyra tests
    pytest tests/test_elyra_integration.py -v

    # Run only validation tests (fast)
    pytest tests/test_elyra_integration.py -k "validate" -v

    # Run notebook execution tests (slow)
    pytest tests/test_elyra_integration.py -k "execution" -v --run-slow
"""

import pytest
import json
from pathlib import Path
import sys

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))


class TestElyraRunnerValidation:
    """Test ElyraRunner loading and validation."""

    def test_pipeline_file_exists(self, elyra_pipeline_path):
        """Verify pipeline file exists."""
        assert elyra_pipeline_path.exists(), f"Pipeline not found: {elyra_pipeline_path}"

    def test_pipeline_loads(self, elyra_runner):
        """Verify pipeline JSON can be parsed."""
        assert elyra_runner is not None
        assert len(elyra_runner.nodes) > 0

    def test_pipeline_name(self, elyra_runner):
        """Verify pipeline has expected name."""
        assert elyra_runner.name == "UH2025Agent"

    def test_pipeline_version(self, elyra_runner):
        """Verify pipeline version is supported."""
        assert elyra_runner.version in ("3.0", "8")

    def test_pipeline_validates(self, elyra_runner):
        """Verify pipeline passes validation.

        Note: This test requires external module notebooks to exist.
        When running in standalone mode (without external modules),
        validation will fail due to missing notebook paths.
        """
        is_valid, errors = elyra_runner.validate()

        if not is_valid:
            # Check if errors are due to missing external modules
            missing_module_errors = [e for e in errors if "notebook not found" in e]
            if missing_module_errors and len(missing_module_errors) == len(errors):
                pytest.skip(
                    "Skipping: External module notebooks not available. "
                    "This is expected when running UH2025Agent standalone. "
                    "Use LangGraph execution mode instead of Elyra."
                )
            pytest.fail(f"Pipeline validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    def test_expected_node_count(self, elyra_runner):
        """Verify expected number of nodes."""
        # UH2025Agent has 5 nodes:
        # 01_regulatory, 02_pathogenicity, 03_differential, 04_toolcalls, 05_report
        assert len(elyra_runner.nodes) == 5

    def test_execution_order(self, elyra_runner):
        """Verify execution order is valid topological sort."""
        order = elyra_runner.execution_order
        assert len(order) == 5

        # Get node labels
        labels = [elyra_runner.nodes[node_id].label for node_id in order]

        # Verify parallel nodes come before their dependents
        regulatory_idx = next(i for i, l in enumerate(labels) if "regulatory" in l)
        pathogenicity_idx = next(i for i, l in enumerate(labels) if "pathogenicity" in l)
        differential_idx = next(i for i, l in enumerate(labels) if "differential" in l)

        # Both regulatory and pathogenicity must come before differential
        assert regulatory_idx < differential_idx
        assert pathogenicity_idx < differential_idx


class TestElyraDAGStructure:
    """Test DAG structure and dependencies."""

    def test_parallel_groups(self, elyra_runner):
        """Verify parallel execution groups are detected."""
        groups = elyra_runner.get_parallel_groups()

        # Should have at least 2 groups (parallel start + sequential chain)
        assert len(groups) >= 2

        # First group should have 2 parallel nodes (regulatory + pathogenicity)
        first_group_labels = [
            elyra_runner.nodes[node_id].label
            for node_id in groups[0]
        ]
        assert len(groups[0]) == 2, f"First group should have 2 parallel nodes, got: {first_group_labels}"

    def test_node_dependencies(self, elyra_runner):
        """Verify node dependencies are correctly parsed."""
        for node_id, node in elyra_runner.nodes.items():
            # All dependencies should reference valid nodes
            for dep_id in node.dependencies:
                assert dep_id in elyra_runner.nodes, \
                    f"Node '{node.label}' has invalid dependency: {dep_id}"

    def test_differential_depends_on_regulatory_and_pathogenicity(self, elyra_runner):
        """Verify 03_differential depends on both 01 and 02."""
        differential_node = None
        for node in elyra_runner.nodes.values():
            if "differential" in node.label:
                differential_node = node
                break

        assert differential_node is not None, "Could not find differential node"
        assert len(differential_node.dependencies) == 2, \
            f"Differential should have 2 dependencies, got: {differential_node.dependencies}"


class TestElyraNotebookPaths:
    """Test that notebook paths are correctly resolved."""

    def test_notebook_paths_exist(self, elyra_runner):
        """Verify all notebook paths exist."""
        for node_id, node in elyra_runner.nodes.items():
            notebook_path = Path(node.notebook_path)
            assert notebook_path.exists(), \
                f"Notebook for '{node.label}' not found: {notebook_path}"

    def test_notebook_paths_are_ipynb(self, elyra_runner):
        """Verify all notebook paths are .ipynb files."""
        for node in elyra_runner.nodes.values():
            assert node.notebook_path.endswith('.ipynb'), \
                f"Node '{node.label}' notebook is not .ipynb: {node.notebook_path}"


class TestElyraMetadata:
    """Test module Elyra metadata files."""

    def test_alphamissense_metadata_exists(self, modules_root):
        """Verify AlphaMissense has Elyra metadata."""
        metadata_path = modules_root / "AlphaMissense" / "notebooks" / "main.ipynb-meta.json"
        assert metadata_path.exists(), f"Metadata not found: {metadata_path}"

    def test_alphagenome_metadata_exists(self, modules_root):
        """Verify AlphaGenome has Elyra metadata."""
        metadata_path = modules_root / "AlphaGenome" / "notebooks" / "main.ipynb-meta.json"
        assert metadata_path.exists(), f"Metadata not found: {metadata_path}"

    def test_metadata_valid_json(self, modules_root):
        """Verify metadata files are valid JSON."""
        for module in ["AlphaMissense", "AlphaGenome"]:
            metadata_path = modules_root / module / "notebooks" / "main.ipynb-meta.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    data = json.load(f)

                # Check required fields
                assert "name" in data, f"{module} metadata missing 'name'"
                assert "description" in data, f"{module} metadata missing 'description'"
                assert "properties" in data, f"{module} metadata missing 'properties'"

    def test_metadata_papermill_compatible(self, modules_root):
        """Verify metadata indicates Papermill compatibility."""
        for module in ["AlphaMissense", "AlphaGenome"]:
            metadata_path = modules_root / module / "notebooks" / "main.ipynb-meta.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    data = json.load(f)

                module_meta = data.get("module_metadata", {})
                assert module_meta.get("papermill_compatible", False), \
                    f"{module} not marked as Papermill compatible"


@pytest.mark.notebook
@pytest.mark.slow
class TestElyraNodeExecution:
    """Test individual node execution via ElyraRunner."""

    def test_execute_regulatory_node(self, elyra_runner, tmp_output_dir):
        """Test executing regulatory analysis node."""
        result = elyra_runner.execute_node(
            node_label="01_regulatory_analysis",
            output_dir=str(tmp_output_dir / "regulatory"),
        )

        assert result.success, f"Node execution failed: {result.error}"
        assert result.output_notebook.exists()

    def test_execute_pathogenicity_node(self, elyra_runner, tmp_output_dir):
        """Test executing pathogenicity scoring node."""
        result = elyra_runner.execute_node(
            node_label="02_pathogenicity_scoring",
            output_dir=str(tmp_output_dir / "pathogenicity"),
        )

        assert result.success, f"Node execution failed: {result.error}"
        assert result.output_notebook.exists()

    def test_node_produces_output_notebook(self, elyra_runner, tmp_output_dir):
        """Test that node execution produces expected output notebook."""
        result = elyra_runner.execute_node(
            node_label="01_regulatory_analysis",
            output_dir=str(tmp_output_dir / "regulatory"),
        )

        assert result.success, f"Node execution failed: {result.error}"

        # Check that output notebook was created
        assert result.output_notebook.exists(), "Output notebook not found"

        # Check the output notebook contains executed cells
        import json
        with open(result.output_notebook) as f:
            nb = json.load(f)
        # Verify notebook has cells with outputs (execution completed)
        cells_with_outputs = [c for c in nb.get('cells', []) if c.get('outputs')]
        assert len(cells_with_outputs) > 0, "No cells with outputs in executed notebook"


@pytest.mark.notebook
@pytest.mark.slow
class TestElyraModuleNotebooks:
    """Test module notebooks execute correctly."""

    def test_alphamissense_notebook_executes(self, papermill_runner, module_notebook_paths, tmp_output_dir):
        """Test AlphaMissense notebook executes successfully."""
        notebook_path = module_notebook_paths["AlphaMissense"]

        result = papermill_runner.execute_notebook(
            notebook_path=notebook_path,
            output_dir=tmp_output_dir / "alphamissense",
            parameters={
                "patient_id": "TestPatient",
                "output_file": "test_output.json",
            }
        )

        assert result.success, f"AlphaMissense notebook failed: {result.error}"

    def test_alphagenome_notebook_executes(self, papermill_runner, module_notebook_paths, tmp_output_dir):
        """Test AlphaGenome notebook executes successfully."""
        notebook_path = module_notebook_paths["AlphaGenome"]

        result = papermill_runner.execute_notebook(
            notebook_path=notebook_path,
            output_dir=tmp_output_dir / "alphagenome",
            parameters={
                "patient_id": "TestPatient",
                "output_file": "test_output.json",
            }
        )

        assert result.success, f"AlphaGenome notebook failed: {result.error}"


@pytest.mark.notebook
@pytest.mark.slow
@pytest.mark.e2e
class TestElyraPipelineExecution:
    """Test full pipeline execution."""

    def test_pipeline_executes_local(self, elyra_runner, tmp_output_dir, assert_pipeline_success):
        """Test full local pipeline execution."""
        result = elyra_runner.execute_local(
            output_dir=str(tmp_output_dir / "pipeline_run"),
            parameters={
                "patient_id": "TestPatient",
            },
            node_filter=["01_regulatory_analysis", "02_pathogenicity_scoring"],  # Just test first two
        )

        assert_pipeline_success(result)
        assert result.total_duration_seconds > 0

    def test_pipeline_parallel_nodes_both_execute(self, elyra_runner, tmp_output_dir):
        """Test that both parallel nodes execute."""
        result = elyra_runner.execute_local(
            output_dir=str(tmp_output_dir / "parallel_test"),
            node_filter=["01_regulatory_analysis", "02_pathogenicity_scoring"],
        )

        # Both nodes should have results
        executed_labels = [
            elyra_runner.nodes[node_id].label
            for node_id in result.node_results.keys()
        ]

        assert any("regulatory" in label for label in executed_labels), \
            "Regulatory node not executed"
        assert any("pathogenicity" in label for label in executed_labels), \
            "Pathogenicity node not executed"


class TestElyraRunnerCLI:
    """Test ElyraRunner CLI interface."""

    def test_validate_only_cli(self, elyra_pipeline_path):
        """Test --validate-only CLI option.

        Note: This test requires external module notebooks to exist.
        """
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "code" / "elyra" / "runner.py"),
                str(elyra_pipeline_path),
                "--validate-only",
            ],
            capture_output=True,
            text=True,
        )

        # Check if failure is due to missing external modules
        if result.returncode != 0 and "notebook not found" in result.stdout:
            pytest.skip(
                "Skipping: External module notebooks not available. "
                "This is expected when running UH2025Agent standalone."
            )

        assert result.returncode == 0, f"Validation failed:\n{result.stderr}"
        assert "valid" in result.stdout.lower() or "nodes" in result.stdout.lower()
