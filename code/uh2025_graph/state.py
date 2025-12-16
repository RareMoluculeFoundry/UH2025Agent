"""
LangGraph State Definition for UH2025Agent

This module defines the TypedDict state that flows through the
LangGraph pipeline. The state is immutable and accumulates
outputs from each agent node.

State Flow:
1. Ingestion: raw_input → patient_context
2. Structuring: patient_context → diagnostic_hypotheses + tool_plan
3. Executor: tool_plan → tool_results
4. Synthesis: all outputs → diagnostic_report

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated
from enum import Enum
import operator


class PipelineStage(Enum):
    """Current stage of the pipeline."""
    INIT = "init"
    INGESTION = "ingestion"
    STRUCTURING = "structuring"
    EXECUTOR = "executor"
    SYNTHESIS = "synthesis"
    COMPLETE = "complete"
    ERROR = "error"
    AWAITING_REVIEW = "awaiting_review"


class UH2025AgentState(TypedDict, total=False):
    """
    State definition for the UH2025Agent LangGraph pipeline.

    This TypedDict flows through all nodes, accumulating outputs.
    Fields use Annotated types for reducer functions where needed.

    Attributes:
        # Pipeline Control
        stage: Current pipeline stage
        iteration: Number of Structuring↔Executor loops
        max_iterations: Maximum allowed loops
        error: Error message if pipeline failed

        # Raw Inputs
        patient_id: Patient identifier
        clinical_summary: Raw clinical text input
        genomic_data: VCF-style variant data

        # Ingestion Outputs
        patient_context: Normalized patient data
        ingestion_confidence: Extraction confidence score
        ingestion_warnings: Extraction warnings

        # Structuring Outputs
        diagnostic_hypotheses: Ranked list of diagnoses
        tool_usage_plan: Bio-tools to execute
        variants_table: Parsed variant information
        needs_more_tools: Flag if more tool runs needed

        # Executor Outputs
        tool_results: Results from each bio-tool
        execution_id: Unique execution identifier
        tools_completed: Count of successful tools
        tools_failed: Count of failed tools

        # Synthesis Outputs
        diagnostic_report: Final clinical report
        confidence_scores: Per-diagnosis confidence
        recommendations: Clinical recommendations

        # HITL Checkpoints
        awaiting_human_review: Flag for human checkpoint
        human_feedback: Collected human feedback
        review_stage: Which stage needs review
    """

    # Pipeline Control
    stage: PipelineStage
    iteration: int
    max_iterations: int
    error: Optional[str]

    # Raw Inputs
    patient_id: str
    clinical_summary: str
    genomic_data: Dict[str, Any]

    # Ingestion Outputs
    patient_context: Dict[str, Any]
    ingestion_confidence: float
    ingestion_warnings: Annotated[List[str], operator.add]

    # Structuring Outputs
    diagnostic_hypotheses: List[Dict[str, Any]]
    tool_usage_plan: List[Dict[str, Any]]
    variants_table: List[Dict[str, Any]]
    needs_more_tools: bool

    # Executor Outputs (accumulated across iterations)
    tool_results: Annotated[List[Dict[str, Any]], operator.add]
    execution_id: str
    tools_completed: int
    tools_failed: int

    # Synthesis Outputs
    diagnostic_report: str
    confidence_scores: Dict[str, float]
    recommendations: List[str]

    # HITL Checkpoints
    awaiting_human_review: bool
    human_feedback: Dict[str, Any]
    review_stage: Optional[str]

    # Metadata
    start_time: str
    end_time: Optional[str]
    total_duration_seconds: float


def create_initial_state(
    patient_id: str,
    clinical_summary: str,
    genomic_data: Optional[Dict[str, Any]] = None,
    max_iterations: int = 3,
) -> UH2025AgentState:
    """
    Create initial state for a new pipeline run.

    Args:
        patient_id: Unique patient identifier
        clinical_summary: Raw clinical text
        genomic_data: Optional VCF-style variant data
        max_iterations: Max Structuring↔Executor loops

    Returns:
        Initialized UH2025AgentState
    """
    from datetime import datetime

    return UH2025AgentState(
        # Pipeline Control
        stage=PipelineStage.INIT,
        iteration=0,
        max_iterations=max_iterations,
        error=None,

        # Raw Inputs
        patient_id=patient_id,
        clinical_summary=clinical_summary,
        genomic_data=genomic_data or {},

        # Ingestion Outputs (empty)
        patient_context={},
        ingestion_confidence=0.0,
        ingestion_warnings=[],

        # Structuring Outputs (empty)
        diagnostic_hypotheses=[],
        tool_usage_plan=[],
        variants_table=[],
        needs_more_tools=False,

        # Executor Outputs (empty)
        tool_results=[],
        execution_id="",
        tools_completed=0,
        tools_failed=0,

        # Synthesis Outputs (empty)
        diagnostic_report="",
        confidence_scores={},
        recommendations=[],

        # HITL Checkpoints
        awaiting_human_review=False,
        human_feedback={},
        review_stage=None,

        # Metadata
        start_time=datetime.now().isoformat(),
        end_time=None,
        total_duration_seconds=0.0,
    )


def state_summary(state: UH2025AgentState) -> str:
    """
    Generate a human-readable summary of the current state.

    Useful for debugging and logging.
    """
    return f"""
UH2025Agent State Summary
========================
Stage: {state.get('stage', 'unknown')}
Patient: {state.get('patient_id', 'unknown')}
Iteration: {state.get('iteration', 0)}/{state.get('max_iterations', 3)}

Ingestion:
  - Confidence: {state.get('ingestion_confidence', 0):.2f}
  - Warnings: {len(state.get('ingestion_warnings', []))}

Structuring:
  - Hypotheses: {len(state.get('diagnostic_hypotheses', []))}
  - Tools Planned: {len(state.get('tool_usage_plan', []))}
  - Needs More Tools: {state.get('needs_more_tools', False)}

Executor:
  - Tools Completed: {state.get('tools_completed', 0)}
  - Tools Failed: {state.get('tools_failed', 0)}
  - Total Results: {len(state.get('tool_results', []))}

Synthesis:
  - Report Generated: {bool(state.get('diagnostic_report'))}
  - Recommendations: {len(state.get('recommendations', []))}

HITL:
  - Awaiting Review: {state.get('awaiting_human_review', False)}
  - Review Stage: {state.get('review_stage', 'none')}

Error: {state.get('error', 'none')}
"""
