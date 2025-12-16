#!/usr/bin/env python3
"""
End-to-End Test: Diagnostic Pipeline

This test runs the complete UH2025Agent pipeline with patient data
using real LLM inference (Llama 3.2 3B, Qwen 2.5 14B, Qwen 2.5 32B).

HIPAA Compliance:
- All inference is local (llama-cpp-python)
- Default patient is SyntheticDemo (synthetic, included in repo)
- No cloud APIs used

Usage:
    python tests/test_patientx_e2e.py --use-stub  # Use stubs (fast, for CI)
    python tests/test_patientx_e2e.py             # Full LLM inference (slow)

    # Use specific patient (local testing):
    PATIENT_ID=PatientX python tests/test_patientx_e2e.py --use-stub

Author: Stanley Lab / RareResearch
Date: November 2025
"""

import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Default patient - SyntheticDemo is included in the repo
# Set PATIENT_ID=PatientX for local testing with real patient data
DEFAULT_PATIENT = os.environ.get("PATIENT_ID", "SyntheticDemo")


def load_patient_data(patient_id: str = None):
    """Load patient clinical and genomic data.

    Args:
        patient_id: Patient directory name (default: from PATIENT_ID env or SyntheticDemo)

    Returns:
        Tuple of (clinical_summary, genomic_data)
    """
    patient_id = patient_id or DEFAULT_PATIENT
    data_dir = PROJECT_ROOT / "Data" / patient_id

    # Load clinical summary (try both naming conventions)
    clinical_path = data_dir / "patient_clinical.md"
    if not clinical_path.exists():
        clinical_path = data_dir / f"{patient_id.lower()}_Clinical.md"
    if not clinical_path.exists():
        clinical_path = data_dir / f"patientX_Clinical.md"  # Legacy name

    with open(clinical_path, "r") as f:
        clinical_summary = f.read()

    # Load genomic data (try both naming conventions)
    genomic_path = data_dir / "patient_genomic.json"
    if not genomic_path.exists():
        genomic_path = data_dir / f"{patient_id.lower()}_Genomic.json"
    if not genomic_path.exists():
        genomic_path = data_dir / f"patientX_Genomic.json"  # Legacy name

    with open(genomic_path, "r") as f:
        genomic_data = json.load(f)

    return clinical_summary, genomic_data, patient_id


def run_stub_test():
    """Run pipeline with stub models (fast, for testing infrastructure)."""
    print("\n" + "=" * 60)
    print("UH2025Agent E2E Test - STUB MODE")
    print("=" * 60)

    clinical_summary, genomic_data, patient_id = load_patient_data()

    # Import pipeline components
    from uh2025_graph import run_pipeline, state_summary

    print(f"\nPatient ID: {patient_id}")
    print(f"Clinical Summary: {len(clinical_summary)} chars")
    print(f"Variants: {len(genomic_data.get('variants', []))}")
    print()

    # Run pipeline (stub mode)
    start = datetime.now()
    try:
        result = run_pipeline(
            patient_id=patient_id,
            clinical_summary=clinical_summary,
            genomic_data=genomic_data,
            with_human_review=False,
            max_iterations=2,
        )
        duration = (datetime.now() - start).total_seconds()

        print(state_summary(result))
        print(f"\nPipeline completed in {duration:.2f}s")

        # Check core outputs (relaxed for stub mode)
        assert result.get("patient_context"), "Missing patient_context"
        # Note: diagnostic_hypotheses may be empty if LLM output parsing failed
        # This is acceptable in stub mode; real LLM mode should produce hypotheses
        assert result.get("diagnostic_report") or result.get("tool_results"), "Missing both diagnostic_report and tool_results"

        # Print diagnostic report if available
        if result.get("diagnostic_report"):
            print("\n" + "=" * 60)
            print("DIAGNOSTIC REPORT (preview)")
            print("=" * 60)
            print(result["diagnostic_report"][:1000])
            if len(result["diagnostic_report"]) > 1000:
                print("... (truncated)")

        print("\n" + "=" * 60)
        print("STUB TEST PASSED")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\nSTUB TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_llm_test():
    """Run pipeline with real LLM inference (slow, full test)."""
    print("\n" + "=" * 60)
    print("UH2025Agent E2E Test - LIVE LLM MODE")
    print("=" * 60)

    # Check models exist
    models_dir = PROJECT_ROOT / "models"
    required_models = [
        "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        "Qwen2.5-32B-Instruct-Q4_K_M.gguf",
    ]

    print("\nChecking models...")
    for model in required_models:
        model_path = models_dir / model
        if model_path.exists():
            size_gb = model_path.stat().st_size / (1024**3)
            print(f"  [OK] {model} ({size_gb:.1f} GB)")
        else:
            print(f"  [MISSING] {model}")
            print(f"\nERROR: Model not found at {model_path}")
            print("Please download models first.")
            return False

    clinical_summary, genomic_data, patient_id = load_patient_data()

    print(f"\nPatient ID: {patient_id}")
    print(f"Clinical Summary: {len(clinical_summary)} chars")
    print(f"Variants: {len(genomic_data.get('variants', []))}")
    print()

    # Import pipeline components
    from uh2025_graph import run_pipeline, state_summary

    # Run pipeline (full LLM mode)
    print("Starting LLM inference pipeline...")
    print("(This may take several minutes)")
    print()

    start = datetime.now()
    try:
        result = run_pipeline(
            patient_id=patient_id,
            clinical_summary=clinical_summary,
            genomic_data=genomic_data,
            with_human_review=False,
            max_iterations=2,
        )
        duration = (datetime.now() - start).total_seconds()

        print(state_summary(result))

        # Print diagnostic report
        if result.get("diagnostic_report"):
            print("\n" + "=" * 60)
            print("DIAGNOSTIC REPORT")
            print("=" * 60)
            print(result["diagnostic_report"][:2000])
            if len(result["diagnostic_report"]) > 2000:
                print("... (truncated)")

        print(f"\nPipeline completed in {duration:.2f}s ({duration/60:.1f} min)")

        # Validate outputs
        assert result.get("patient_context"), "Missing patient_context"
        assert result.get("diagnostic_hypotheses"), "Missing diagnostic_hypotheses"

        print("\n" + "=" * 60)
        print("LIVE LLM TEST PASSED")
        print("=" * 60)

        # Save output
        output_path = PROJECT_ROOT / "outputs" / f"patientx_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.parent.mkdir(exist_ok=True)

        # Convert non-serializable types
        output_data = {}
        for key, value in result.items():
            if hasattr(value, 'value'):  # Enum
                output_data[key] = value.value
            else:
                output_data[key] = value

        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\nResults saved to: {output_path}")

        return True

    except Exception as e:
        print(f"\nLIVE LLM TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_import_test():
    """Test that all imports work correctly."""
    print("\n" + "=" * 60)
    print("IMPORT TEST")
    print("=" * 60)

    try:
        print("Testing imports...")

        # Core imports
        print("  [1/6] uh2025_graph.state...")
        from uh2025_graph import UH2025AgentState, create_initial_state
        print("        OK")

        print("  [2/6] uh2025_graph.graph...")
        from uh2025_graph import create_uh2025_graph, run_pipeline
        print("        OK")

        print("  [3/6] uh2025_graph.nodes...")
        from uh2025_graph import ingestion_node, structuring_node, executor_node, synthesis_node
        print("        OK")

        print("  [4/6] agents (ingestion)...")
        from agents.ingestion_agent import IngestionAgent
        print("        OK")

        print("  [5/6] agents (structuring)...")
        from agents.structuring_agent import StructuringAgent
        print("        OK")

        print("  [6/6] biotools...")
        from biotools import AlphaMissenseTool, AlphaGenomeTool, ClinVarTool
        print("        OK")

        print("\n" + "=" * 60)
        print("IMPORT TEST PASSED")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\nIMPORT TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="UH2025Agent End-to-End Test")
    parser.add_argument("--use-stub", action="store_true", help="Use stub models (fast)")
    parser.add_argument("--import-only", action="store_true", help="Only test imports")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("UH2025Agent End-to-End Test Suite")
    print("=" * 60)
    print(f"Project: {PROJECT_ROOT}")
    print(f"Time: {datetime.now().isoformat()}")

    # Always run import test first
    if not run_import_test():
        sys.exit(1)

    if args.import_only:
        sys.exit(0)

    # Run appropriate test
    if args.use_stub:
        success = run_stub_test()
    else:
        success = run_llm_test()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
