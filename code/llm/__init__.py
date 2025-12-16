"""
LLM Package: HIPAA-Safe Local Language Model Integration

This package provides LangChain-compatible LLM interfaces
using ONLY local execution backends (llama.cpp).

NO cloud APIs are permitted - all inference runs locally.

Components:
- LLMFactory: Factory for creating local LLM instances
- PromptAdapter: Convert prompts to LangChain templates
- HIPAAViolationError: Raised when cloud APIs are detected

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from .llm_factory import (
    LLMFactory,
    HIPAAViolationError,
    ModelSpec,
    ModelSize,
    MODEL_REGISTRY,
    AGENT_MODEL_DEFAULTS,
    get_llm,
)
from .prompt_adapter import (
    PromptAdapter,
    AgentPromptTemplate,
)
from .json_extractor import (
    extract_json,
    enforce_schema,
    JSONExtractionError,
    INGESTION_SCHEMA,
    STRUCTURING_SCHEMA,
    SYNTHESIS_SCHEMA,
)

__all__ = [
    # Factory
    "LLMFactory",
    "get_llm",
    # Error types
    "HIPAAViolationError",
    "JSONExtractionError",
    # Model specs
    "ModelSpec",
    "ModelSize",
    "MODEL_REGISTRY",
    "AGENT_MODEL_DEFAULTS",
    # Prompts
    "PromptAdapter",
    "AgentPromptTemplate",
    # JSON extraction
    "extract_json",
    "enforce_schema",
    "INGESTION_SCHEMA",
    "STRUCTURING_SCHEMA",
    "SYNTHESIS_SCHEMA",
]
