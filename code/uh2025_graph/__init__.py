"""
UH2025 Graph Package: Stateful Agent Orchestration

This package provides LangGraph-based orchestration for the UH2025Agent
4-agent pipeline. It replaces the linear PipelineExecutor with a
stateful graph that supports:

- Conditional routing (Structuring → Executor loop)
- Human-in-the-loop checkpoints
- Parallel execution where possible
- State persistence for long-running analyses

Architecture:
    Ingestion → Structuring ⟷ Executor → Synthesis
                    ↑___________↓ (loop if more tools needed)

Note: This package is named 'uh2025_graph' to avoid conflicts with
the installed 'langgraph' library from LangChain.

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from .state import UH2025AgentState, create_initial_state, state_summary
from .graph import (
    create_uh2025_graph,
    UH2025GraphBuilder,
    run_pipeline,
)
from .nodes import (
    ingestion_node,
    structuring_node,
    executor_node,
    synthesis_node,
)
from .checkpoints import (
    HumanReviewCheckpoint,
    CheckpointManager,
)

__all__ = [
    # State
    "UH2025AgentState",
    "create_initial_state",
    "state_summary",
    # Graph
    "create_uh2025_graph",
    "UH2025GraphBuilder",
    "run_pipeline",
    # Nodes
    "ingestion_node",
    "structuring_node",
    "executor_node",
    "synthesis_node",
    # Checkpoints
    "HumanReviewCheckpoint",
    "CheckpointManager",
]
