"""
LangGraph Graph Definition for UH2025Agent

This module defines the StateGraph that orchestrates the
4-agent pipeline with conditional routing and checkpoints.

Graph Structure:
    START → ingestion → structuring → [conditional]
                            ↓              ↓
                        executor ←────┘    synthesis → END
                            ↓
                        structuring (loop)

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from typing import Any, Dict, Optional, Callable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from .state import UH2025AgentState, PipelineStage, create_initial_state
from .nodes import (
    ingestion_node,
    structuring_node,
    executor_node,
    synthesis_node,
    human_review_node,
    error_node,
)


def should_continue_to_executor(state: UH2025AgentState) -> str:
    """
    Routing function: Determine if we should run executor or synthesis.

    Returns:
        "executor" if more tools need to run
        "synthesis" if ready for final report
        "error" if pipeline failed
    """
    if state.get("stage") == PipelineStage.ERROR:
        return "error"

    if state.get("needs_more_tools", False):
        return "executor"

    return "synthesis"


def should_loop_or_finish(state: UH2025AgentState) -> str:
    """
    Routing function: Determine if we should loop back to structuring.

    After executor runs, we can either:
    - Loop back to structuring if more analysis needed
    - Go to synthesis if we have enough data
    - Go to error if something failed

    Returns:
        "structuring" to loop
        "synthesis" to finish
        "error" if failed
    """
    if state.get("stage") == PipelineStage.ERROR:
        return "error"

    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 3)

    # Check if we've exhausted iterations
    if iteration >= max_iterations:
        return "synthesis"

    # Check if more tools are requested
    if state.get("needs_more_tools", False):
        return "structuring"

    return "synthesis"


class UH2025GraphBuilder:
    """
    Builder class for constructing the UH2025Agent LangGraph.

    Provides a fluent interface for customizing the graph with:
    - Custom node functions
    - Checkpoint configuration
    - Human review checkpoints

    Usage:
        builder = UH2025GraphBuilder()
        builder.with_human_review(after=["ingestion"])
        graph = builder.build()
        result = graph.invoke(initial_state)
    """

    def __init__(self):
        """Initialize the graph builder."""
        self._human_review_after: set[str] = set()
        self._custom_nodes: Dict[str, Callable] = {}
        self._checkpointer: Optional[Any] = None

    def with_human_review(self, after: list[str]) -> "UH2025GraphBuilder":
        """
        Add human review checkpoints after specified nodes.

        Args:
            after: List of node names after which to pause for review
                  Valid values: "ingestion", "structuring", "executor"

        Returns:
            Self for chaining
        """
        valid_nodes = {"ingestion", "structuring", "executor"}
        for node in after:
            if node not in valid_nodes:
                raise ValueError(f"Invalid node for review: {node}. Must be one of {valid_nodes}")
            self._human_review_after.add(node)
        return self

    def with_custom_node(self, name: str, fn: Callable) -> "UH2025GraphBuilder":
        """
        Replace a node function with a custom implementation.

        Args:
            name: Node name to replace
            fn: Custom node function

        Returns:
            Self for chaining
        """
        self._custom_nodes[name] = fn
        return self

    def with_checkpointer(self, checkpointer: Any) -> "UH2025GraphBuilder":
        """
        Add a checkpointer for state persistence.

        Args:
            checkpointer: LangGraph checkpointer instance

        Returns:
            Self for chaining
        """
        self._checkpointer = checkpointer
        return self

    def build(self) -> StateGraph:
        """
        Build and return the configured StateGraph.

        Returns:
            Compiled StateGraph ready for invocation
        """
        # Create graph with state schema
        graph = StateGraph(UH2025AgentState)

        # Get node functions (custom or default)
        ingestion_fn = self._custom_nodes.get("ingestion", ingestion_node)
        structuring_fn = self._custom_nodes.get("structuring", structuring_node)
        executor_fn = self._custom_nodes.get("executor", executor_node)
        synthesis_fn = self._custom_nodes.get("synthesis", synthesis_node)

        # Add nodes
        graph.add_node("ingestion", ingestion_fn)
        graph.add_node("structuring", structuring_fn)
        graph.add_node("executor", executor_fn)
        graph.add_node("synthesis", synthesis_fn)
        graph.add_node("error", error_node)

        # Add human review nodes if configured
        if "ingestion" in self._human_review_after:
            graph.add_node("review_ingestion", human_review_node)
        if "structuring" in self._human_review_after:
            graph.add_node("review_structuring", human_review_node)
        if "executor" in self._human_review_after:
            graph.add_node("review_executor", human_review_node)

        # Add edges
        graph.add_edge(START, "ingestion")

        # Ingestion → (review?) → structuring
        if "ingestion" in self._human_review_after:
            graph.add_edge("ingestion", "review_ingestion")
            graph.add_edge("review_ingestion", "structuring")
        else:
            graph.add_edge("ingestion", "structuring")

        # Structuring → conditional (executor or synthesis)
        if "structuring" in self._human_review_after:
            graph.add_edge("structuring", "review_structuring")
            graph.add_conditional_edges(
                "review_structuring",
                should_continue_to_executor,
                {
                    "executor": "executor",
                    "synthesis": "synthesis",
                    "error": "error",
                }
            )
        else:
            graph.add_conditional_edges(
                "structuring",
                should_continue_to_executor,
                {
                    "executor": "executor",
                    "synthesis": "synthesis",
                    "error": "error",
                }
            )

        # Executor → conditional (loop or finish)
        if "executor" in self._human_review_after:
            graph.add_edge("executor", "review_executor")
            graph.add_conditional_edges(
                "review_executor",
                should_loop_or_finish,
                {
                    "structuring": "structuring",
                    "synthesis": "synthesis",
                    "error": "error",
                }
            )
        else:
            graph.add_conditional_edges(
                "executor",
                should_loop_or_finish,
                {
                    "structuring": "structuring",
                    "synthesis": "synthesis",
                    "error": "error",
                }
            )

        # Synthesis and Error → END
        graph.add_edge("synthesis", END)
        graph.add_edge("error", END)

        # Compile with checkpointer if provided
        if self._checkpointer:
            return graph.compile(checkpointer=self._checkpointer)
        else:
            return graph.compile()


def create_uh2025_graph(
    with_human_review: bool = False,
    review_after: Optional[list[str]] = None,
    persist: bool = False,
) -> StateGraph:
    """
    Convenience function to create a UH2025Agent graph.

    Args:
        with_human_review: Enable human review checkpoints
        review_after: Specific nodes to add review after
                     Defaults to ["structuring"] if with_human_review=True
        persist: Enable memory-based state persistence

    Returns:
        Compiled StateGraph

    Example:
        # Simple pipeline (no review)
        graph = create_uh2025_graph()

        # With human review after structuring
        graph = create_uh2025_graph(with_human_review=True)

        # Custom review points
        graph = create_uh2025_graph(
            with_human_review=True,
            review_after=["ingestion", "structuring"]
        )
    """
    builder = UH2025GraphBuilder()

    if with_human_review:
        review_nodes = review_after or ["structuring"]
        builder.with_human_review(after=review_nodes)

    if persist:
        builder.with_checkpointer(MemorySaver())

    return builder.build()


def run_pipeline(
    patient_id: str,
    clinical_summary: str,
    genomic_data: Optional[Dict[str, Any]] = None,
    with_human_review: bool = False,
    max_iterations: int = 3,
) -> UH2025AgentState:
    """
    Convenience function to run the full pipeline.

    Args:
        patient_id: Patient identifier
        clinical_summary: Raw clinical text
        genomic_data: Optional variant data
        with_human_review: Enable HITL checkpoints
        max_iterations: Max structuring↔executor loops

    Returns:
        Final pipeline state with all outputs

    Example:
        result = run_pipeline(
            patient_id="PAT-001",
            clinical_summary="45 year old female with...",
            genomic_data={"variants": [...]},
        )
        print(result["diagnostic_report"])
    """
    # Create initial state
    initial_state = create_initial_state(
        patient_id=patient_id,
        clinical_summary=clinical_summary,
        genomic_data=genomic_data,
        max_iterations=max_iterations,
    )

    # Create and run graph
    graph = create_uh2025_graph(with_human_review=with_human_review)
    final_state = graph.invoke(initial_state)

    return final_state
