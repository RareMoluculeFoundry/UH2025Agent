"""
UH2025-CDS-Agent: Agent Layer

This module provides the 4-agent architecture for rare disease diagnosis:

1. IngestionAgent - Parse and normalize clinical input data
2. StructuringAgent - Generate diagnostic hypotheses and tool execution plan
3. ExecutorAgent - Execute bio-tools in sandboxed environment
4. SynthesisAgent - Generate clinician-readable diagnostic report

Each agent follows the BaseAgent interface and supports:
- Configurable models (hot-swappable via llama.cpp)
- Version-controlled prompt templates
- RLHF feedback collection at each step
- Local-first execution (M4 Envelope)
"""

from .base_agent import BaseAgent, AgentConfig, AgentResult
from .ingestion_agent import IngestionAgent
from .structuring_agent import StructuringAgent
from .executor_agent import ExecutorAgent
from .synthesis_agent import SynthesisAgent

__all__ = [
    "BaseAgent",
    "AgentConfig",
    "AgentResult",
    "IngestionAgent",
    "StructuringAgent",
    "ExecutorAgent",
    "SynthesisAgent",
]

__version__ = "2.0.0"
