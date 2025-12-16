"""
LangGraph Node Functions for UH2025Agent

Each node wraps an agent and transforms the shared state.
Nodes are pure functions that take state and return state updates.

Node Functions:
- ingestion_node: Wraps IngestionAgent
- structuring_node: Wraps StructuringAgent
- executor_node: Wraps ExecutorAgent
- synthesis_node: Wraps SynthesisAgent

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from typing import Any, Dict
from datetime import datetime

from .state import UH2025AgentState, PipelineStage


def ingestion_node(state: UH2025AgentState) -> Dict[str, Any]:
    """
    Ingestion node: Parse clinical data and extract patient context.

    Wraps the IngestionAgent and transforms its outputs into
    state updates.

    Input state requirements:
        - clinical_summary: Raw clinical text
        - genomic_data: Optional variant data

    Output state updates:
        - patient_context: Normalized patient data
        - ingestion_confidence: Extraction confidence
        - ingestion_warnings: Extraction warnings
        - stage: Updated to STRUCTURING
    """
    from code.agents import IngestionAgent

    print(f"\n{'='*60}")
    print(f"[INGESTION NODE] Processing patient: {state.get('patient_id')}")
    print(f"{'='*60}")

    # Create and run ingestion agent
    agent = IngestionAgent()

    result = agent.run({
        "patient_id": state.get("patient_id"),
        "clinical_summary": state.get("clinical_summary"),
        "genomic_data": state.get("genomic_data", {}),
    })

    # Handle errors
    if result.status.value == "failed":
        return {
            "stage": PipelineStage.ERROR,
            "error": f"Ingestion failed: {result.error_message}",
        }

    # Extract outputs
    outputs = result.outputs
    patient_context = outputs.get("patient_context", {})

    print(f"[INGESTION NODE] Extraction complete")
    confidence = patient_context.get('metadata', {}).get('extraction_confidence')
    if confidence is None:
        confidence = 0.0
    warnings_list = patient_context.get('metadata', {}).get('extraction_warnings', [])
    if warnings_list is None:
        warnings_list = []
    print(f"  - Confidence: {confidence:.2f}")
    print(f"  - Warnings: {len(warnings_list)}")

    # Unload model to free memory
    agent.unload_model()

    return {
        "patient_context": patient_context,
        "ingestion_confidence": confidence,
        "ingestion_warnings": warnings_list,
        "stage": PipelineStage.STRUCTURING,
    }


def structuring_node(state: UH2025AgentState) -> Dict[str, Any]:
    """
    Structuring node: Generate diagnostic hypotheses and tool plan.

    Wraps the StructuringAgent and transforms its outputs into
    state updates. May request additional tool runs.

    Input state requirements:
        - patient_context: From ingestion
        - tool_results: From previous executor runs (if any)

    Output state updates:
        - diagnostic_hypotheses: Ranked diagnoses
        - tool_usage_plan: Tools to execute
        - variants_table: Parsed variants
        - needs_more_tools: Flag for executor loop
        - stage: Updated to EXECUTOR or SYNTHESIS
        - iteration: Incremented
    """
    from code.agents import StructuringAgent

    iteration = state.get("iteration", 0) + 1
    max_iterations = state.get("max_iterations", 3)

    print(f"\n{'='*60}")
    print(f"[STRUCTURING NODE] Iteration {iteration}/{max_iterations}")
    print(f"{'='*60}")

    # Create and run structuring agent
    agent = StructuringAgent()

    result = agent.run({
        "patient_context": state.get("patient_context", {}),
        "previous_tool_results": state.get("tool_results", []),
        "iteration": iteration,
    })

    # Handle errors
    if result.status.value == "failed":
        return {
            "stage": PipelineStage.ERROR,
            "error": f"Structuring failed: {result.error_message}",
            "iteration": iteration,
        }

    # Extract outputs
    outputs = result.outputs
    # Note: structuring agent returns "diagnostic_table" not "diagnostic_hypotheses"
    hypotheses = outputs.get("diagnostic_table", [])
    tool_plan = outputs.get("tool_usage_plan", [])
    variants = outputs.get("variants_table", [])

    print(f"[STRUCTURING NODE] Analysis complete")
    print(f"  - Hypotheses: {len(hypotheses)}")
    print(f"  - Tools to run: {len(tool_plan)}")

    # Determine if we need more tools or can proceed to synthesis
    needs_more = len(tool_plan) > 0 and iteration < max_iterations

    # Unload model to free memory
    agent.unload_model()

    return {
        "diagnostic_hypotheses": hypotheses,
        "tool_usage_plan": tool_plan,
        "variants_table": variants,
        "needs_more_tools": needs_more,
        "stage": PipelineStage.EXECUTOR if needs_more else PipelineStage.SYNTHESIS,
        "iteration": iteration,
    }


def executor_node(state: UH2025AgentState) -> Dict[str, Any]:
    """
    Executor node: Run bio-tools and collect results.

    Wraps the ExecutorAgent (no LLM, pure Python orchestration).
    Executes tools according to the plan from structuring.

    Input state requirements:
        - tool_usage_plan: From structuring
        - variants_table: From structuring

    Output state updates:
        - tool_results: Accumulated tool outputs
        - execution_id: Unique execution ID
        - tools_completed: Count of successful tools
        - tools_failed: Count of failed tools
        - stage: Updated to STRUCTURING (loop) or SYNTHESIS
    """
    from code.agents import ExecutorAgent

    print(f"\n{'='*60}")
    print(f"[EXECUTOR NODE] Running bio-tools")
    print(f"{'='*60}")

    tool_plan = state.get("tool_usage_plan", [])

    if not tool_plan:
        print("[EXECUTOR NODE] No tools to execute")
        return {
            "stage": PipelineStage.SYNTHESIS,
            "needs_more_tools": False,
        }

    # Create and run executor agent
    agent = ExecutorAgent()

    result = agent.run({
        "tool_usage_plan": tool_plan,
        "variants_table": state.get("variants_table", []),
    })

    # Handle errors (executor shouldn't fail, just report tool failures)
    if result.get("status") == "failed":
        return {
            "stage": PipelineStage.ERROR,
            "error": f"Executor failed: {result.get('error')}",
        }

    # Extract outputs
    executor_output = result.get("executor_output", {})
    new_results = result.get("tool_results", [])

    print(f"[EXECUTOR NODE] Execution complete")
    print(f"  - Completed: {executor_output.get('tools_completed', 0)}")
    print(f"  - Failed: {executor_output.get('tools_failed', 0)}")
    print(f"  - Duration: {executor_output.get('total_duration_seconds', 0):.2f}s")

    # Accumulate results (reducer will concat lists)
    return {
        "tool_results": new_results,  # Will be added to existing via operator.add
        "execution_id": result.get("execution_id", ""),
        "tools_completed": executor_output.get("tools_completed", 0),
        "tools_failed": executor_output.get("tools_failed", 0),
        "stage": PipelineStage.STRUCTURING,  # Loop back to structuring
        "needs_more_tools": False,  # Reset for next iteration
    }


def synthesis_node(state: UH2025AgentState) -> Dict[str, Any]:
    """
    Synthesis node: Generate final diagnostic report.

    Wraps the SynthesisAgent and produces the final clinical report
    with confidence scores and recommendations.

    Input state requirements:
        - patient_context: From ingestion
        - diagnostic_hypotheses: From structuring
        - tool_results: From executor

    Output state updates:
        - diagnostic_report: Final Markdown report
        - confidence_scores: Per-diagnosis confidence
        - recommendations: Clinical recommendations
        - stage: Updated to COMPLETE
        - end_time: Pipeline completion time
        - total_duration_seconds: Total execution time
    """
    from code.agents import SynthesisAgent

    print(f"\n{'='*60}")
    print(f"[SYNTHESIS NODE] Generating diagnostic report")
    print(f"{'='*60}")

    # Create and run synthesis agent
    agent = SynthesisAgent()

    result = agent.run({
        "patient_context": state.get("patient_context", {}),
        "diagnostic_hypotheses": state.get("diagnostic_hypotheses", []),
        "tool_results": state.get("tool_results", []),
        "patient_id": state.get("patient_id"),
    })

    # Handle errors
    if result.status.value == "failed":
        return {
            "stage": PipelineStage.ERROR,
            "error": f"Synthesis failed: {result.error_message}",
        }

    # Extract outputs
    outputs = result.outputs
    report = outputs.get("diagnostic_report", "")
    confidence = outputs.get("confidence_scores", {})
    recommendations = outputs.get("recommendations", [])

    print(f"[SYNTHESIS NODE] Report generated")
    print(f"  - Length: {len(report)} characters")
    print(f"  - Recommendations: {len(recommendations)}")

    # Calculate total duration
    end_time = datetime.now()
    start_time = state.get("start_time")
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        duration = (end_time - start_dt).total_seconds()
    else:
        duration = 0.0

    # Unload model
    agent.unload_model()

    return {
        "diagnostic_report": report,
        "confidence_scores": confidence,
        "recommendations": recommendations,
        "stage": PipelineStage.COMPLETE,
        "end_time": end_time.isoformat(),
        "total_duration_seconds": duration,
    }


def human_review_node(state: UH2025AgentState) -> Dict[str, Any]:
    """
    Human review checkpoint node.

    Pauses execution to await human feedback. The graph will
    resume when human_feedback is provided.

    This node doesn't perform any computation - it just sets
    the awaiting_human_review flag and preserves state.
    """
    review_stage = state.get("stage", PipelineStage.INIT).value

    print(f"\n{'='*60}")
    print(f"[HUMAN REVIEW] Checkpoint at stage: {review_stage}")
    print(f"{'='*60}")

    return {
        "awaiting_human_review": True,
        "review_stage": review_stage,
    }


def error_node(state: UH2025AgentState) -> Dict[str, Any]:
    """
    Error handling node.

    Called when any node fails. Records error details and
    terminates the pipeline gracefully.
    """
    error = state.get("error", "Unknown error")

    print(f"\n{'='*60}")
    print(f"[ERROR NODE] Pipeline failed")
    print(f"  Error: {error}")
    print(f"{'='*60}")

    end_time = datetime.now()
    start_time = state.get("start_time")
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        duration = (end_time - start_dt).total_seconds()
    else:
        duration = 0.0

    return {
        "stage": PipelineStage.ERROR,
        "end_time": end_time.isoformat(),
        "total_duration_seconds": duration,
    }
