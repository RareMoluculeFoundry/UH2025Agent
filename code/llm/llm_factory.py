"""
LLM Factory: HIPAA-Safe Local LLM Provider

This module provides a factory for creating LangChain LLM instances
using ONLY local execution backends. NO cloud APIs are permitted.

HIPAA Compliance:
- All inference runs locally via llama-cpp-python
- No data leaves the machine
- No cloud API keys required or accepted

Supported Backends:
- llama.cpp (via langchain_community.llms.LlamaCpp)

FORBIDDEN (will raise HIPAAViolationError):
- langchain_openai
- langchain_anthropic
- Any cloud-based LLM provider

Author: Stanley Lab / RareResearch
Date: November 2025
"""

import gc
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

from langchain_core.language_models.llms import BaseLLM


class HIPAAViolationError(Exception):
    """Raised when attempting to use a cloud-based LLM provider."""
    pass


class ModelSize(Enum):
    """Model size categories for memory management."""
    SMALL = "small"      # ~2GB  (Llama 3.2 3B Q4)
    MEDIUM = "medium"    # ~9GB  (Qwen 2.5 14B Q4)
    LARGE = "large"      # ~19GB (Qwen 2.5 32B Q4)


@dataclass
class ModelSpec:
    """Specification for a local GGUF model."""
    name: str
    filename: str
    size: ModelSize
    context_length: int
    memory_gb: float
    description: str


# Model registry - maps agent types to their default models
MODEL_REGISTRY: Dict[str, ModelSpec] = {
    "llama-3.2-3b-instruct": ModelSpec(
        name="llama-3.2-3b-instruct",
        filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        size=ModelSize.SMALL,
        context_length=8192,
        memory_gb=2.5,
        description="Llama 3.2 3B - Fast triage and ingestion",
    ),
    "qwen-2.5-14b-instruct": ModelSpec(
        name="qwen-2.5-14b-instruct",
        filename="Qwen2.5-14B-Instruct-Q4_K_M.gguf",
        size=ModelSize.MEDIUM,
        context_length=32768,
        memory_gb=9.5,
        description="Qwen 2.5 14B - Structuring and analysis",
    ),
    "qwen-2.5-32b-instruct": ModelSpec(
        name="qwen-2.5-32b-instruct",
        filename="Qwen2.5-32B-Instruct-Q4_K_M.gguf",
        size=ModelSize.LARGE,
        context_length=32768,
        memory_gb=19.5,
        description="Qwen 2.5 32B - Synthesis and report generation",
    ),
}

# Chat format by model family (for proper instruction following)
MODEL_CHAT_FORMATS: Dict[str, str] = {
    "llama-3.2-3b-instruct": "llama-3",
    "qwen-2.5-14b-instruct": "chatml",
    "qwen-2.5-32b-instruct": "chatml",
}

# Aliases for flexible model naming
MODEL_ALIASES: Dict[str, str] = {
    "qwen2.5-14b-instruct": "qwen-2.5-14b-instruct",
    "qwen2.5-32b-instruct": "qwen-2.5-32b-instruct",
    "llama3.2-3b-instruct": "llama-3.2-3b-instruct",
}

# Agent to model mapping (default assignments)
AGENT_MODEL_DEFAULTS: Dict[str, str] = {
    "ingestion": "llama-3.2-3b-instruct",
    "structuring": "qwen-2.5-14b-instruct",
    "synthesis": "qwen-2.5-32b-instruct",
}


class LLMFactory:
    """
    Factory for creating HIPAA-compliant local LLM instances.

    This factory enforces local-only execution and provides
    sequential model loading to stay within memory budgets.

    Usage:
        factory = LLMFactory(models_dir="/path/to/models")
        llm = factory.create("ingestion")
        response = llm.invoke("Analyze this patient data...")
        factory.unload()  # Free memory before loading next model
    """

    # Forbidden modules - attempting to import these raises HIPAAViolationError
    FORBIDDEN_MODULES = [
        "langchain_openai",
        "langchain_anthropic",
        "openai",
        "anthropic",
        "google.generativeai",
        "cohere",
    ]

    def __init__(
        self,
        models_dir: Optional[Union[str, Path]] = None,
        n_gpu_layers: int = -1,  # -1 = all layers on GPU (Metal)
        n_batch: int = 512,
        verbose: bool = False,
    ):
        """
        Initialize the LLM factory.

        Args:
            models_dir: Directory containing GGUF model files.
                       Defaults to topology/models/
            n_gpu_layers: Number of layers to offload to GPU.
                         -1 means all layers (recommended for Metal)
            n_batch: Batch size for prompt processing
            verbose: Enable verbose llama.cpp output
        """
        self._enforce_hipaa_compliance()

        if models_dir is None:
            # Default to topology/models/ relative to this file
            self.models_dir = Path(__file__).parent.parent.parent / "models"
        else:
            self.models_dir = Path(models_dir)

        self.n_gpu_layers = n_gpu_layers
        self.n_batch = n_batch
        self.verbose = verbose

        self._current_model: Optional[BaseLLM] = None
        self._current_model_name: Optional[str] = None

    def _enforce_hipaa_compliance(self) -> None:
        """
        Verify no forbidden cloud API modules are installed/imported.

        Raises HIPAAViolationError if any cloud LLM packages are detected.
        """
        import sys

        for module in self.FORBIDDEN_MODULES:
            if module in sys.modules:
                raise HIPAAViolationError(
                    f"HIPAA VIOLATION: Cloud LLM module '{module}' is loaded. "
                    f"This system requires local-only LLM execution. "
                    f"Please uninstall {module} and use llama-cpp-python instead."
                )

    def _resolve_model_name(self, model_name: str) -> str:
        """Resolve model aliases to canonical names."""
        return MODEL_ALIASES.get(model_name, model_name)

    def _get_model_path(self, model_name: str) -> Path:
        """Get the full path to a model file."""
        # Resolve aliases first
        model_name = self._resolve_model_name(model_name)

        if model_name not in MODEL_REGISTRY:
            raise ValueError(
                f"Unknown model: {model_name}. "
                f"Available models: {list(MODEL_REGISTRY.keys())}"
            )

        spec = MODEL_REGISTRY[model_name]
        model_path = self.models_dir / spec.filename

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                f"Please download the model using:\n"
                f"  huggingface-cli download <repo> {spec.filename} --local-dir {self.models_dir}"
            )

        return model_path

    def create(
        self,
        agent_type: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        **kwargs: Any,
    ) -> BaseLLM:
        """
        Create a LangChain LLM instance for local inference.

        Args:
            agent_type: Agent type (ingestion, structuring, synthesis).
                       Uses default model for that agent type.
            model_name: Explicit model name (overrides agent_type default)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling probability
            top_k: Top-k sampling
            repeat_penalty: Penalty for repeated tokens
            **kwargs: Additional arguments passed to LlamaCpp

        Returns:
            LangChain BaseLLM instance (LlamaCpp)

        Raises:
            HIPAAViolationError: If cloud LLM modules are detected
            ValueError: If model not found in registry
            FileNotFoundError: If model file doesn't exist
        """
        # Determine which model to load
        if model_name is None:
            if agent_type is None:
                raise ValueError("Must specify either agent_type or model_name")
            model_name = AGENT_MODEL_DEFAULTS.get(agent_type)
            if model_name is None:
                raise ValueError(
                    f"Unknown agent type: {agent_type}. "
                    f"Available types: {list(AGENT_MODEL_DEFAULTS.keys())}"
                )

        # Resolve aliases to canonical names
        model_name = self._resolve_model_name(model_name)

        # Unload current model if different
        if self._current_model_name and self._current_model_name != model_name:
            self.unload()

        # Return cached model if same
        if self._current_model_name == model_name and self._current_model is not None:
            return self._current_model

        # Load new model
        model_path = self._get_model_path(model_name)
        spec = MODEL_REGISTRY[model_name]

        print(f"[LLMFactory] Loading model: {model_name}")
        print(f"  Path: {model_path}")
        print(f"  Context: {spec.context_length} tokens")
        print(f"  Memory: ~{spec.memory_gb} GB")

        # Import LlamaCpp from langchain_community
        from langchain_community.llms import LlamaCpp

        # Get chat format for this model
        chat_format = MODEL_CHAT_FORMATS.get(model_name, None)
        if chat_format:
            print(f"  Chat format: {chat_format}")

        self._current_model = LlamaCpp(
            model_path=str(model_path),
            n_ctx=spec.context_length,
            n_gpu_layers=self.n_gpu_layers,
            n_batch=self.n_batch,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            verbose=self.verbose,
            chat_format=chat_format,  # Enable proper chat template formatting
            **kwargs,
        )
        self._current_model_name = model_name

        print(f"[LLMFactory] Model loaded successfully")
        return self._current_model

    def create_for_agent(
        self,
        agent_type: str,
        **kwargs: Any,
    ) -> BaseLLM:
        """
        Convenience method to create LLM for a specific agent type.

        Uses the default model and temperature for that agent type.

        Args:
            agent_type: One of "ingestion", "structuring", "synthesis"
            **kwargs: Override default parameters

        Returns:
            LangChain BaseLLM instance
        """
        # Agent-specific default temperatures
        default_temps = {
            "ingestion": 0.1,      # Low temp for parsing accuracy
            "structuring": 0.3,   # Moderate for hypothesis generation
            "synthesis": 0.5,     # Higher for creative report writing
        }

        if "temperature" not in kwargs:
            kwargs["temperature"] = default_temps.get(agent_type, 0.3)

        return self.create(agent_type=agent_type, **kwargs)

    def unload(self) -> None:
        """
        Unload current model and free memory.

        Important for sequential model loading on memory-constrained systems.
        Call this before loading a different model size.
        """
        if self._current_model is not None:
            print(f"[LLMFactory] Unloading model: {self._current_model_name}")

            # Delete the model
            del self._current_model
            self._current_model = None
            self._current_model_name = None

            # Force garbage collection
            gc.collect()

            # If on macOS, try to release Metal memory
            try:
                import torch
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except (ImportError, AttributeError):
                pass  # torch not installed or MPS not available

            print("[LLMFactory] Memory released")

    def get_model_info(self, model_name: str) -> ModelSpec:
        """Get specification for a model."""
        if model_name not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_name}")
        return MODEL_REGISTRY[model_name]

    def list_models(self) -> Dict[str, ModelSpec]:
        """List all available models."""
        return MODEL_REGISTRY.copy()

    def estimate_memory(self, agent_types: list[str]) -> float:
        """
        Estimate peak memory usage for running multiple agents.

        Assumes sequential execution (only one model loaded at a time).

        Args:
            agent_types: List of agent types to run

        Returns:
            Peak memory estimate in GB
        """
        peak = 0.0
        for agent_type in agent_types:
            model_name = AGENT_MODEL_DEFAULTS.get(agent_type)
            if model_name:
                spec = MODEL_REGISTRY[model_name]
                peak = max(peak, spec.memory_gb)
        return peak

    @property
    def is_model_loaded(self) -> bool:
        """Check if a model is currently loaded."""
        return self._current_model is not None

    @property
    def current_model_name(self) -> Optional[str]:
        """Get the name of the currently loaded model."""
        return self._current_model_name

    def __enter__(self) -> "LLMFactory":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit - ensure model is unloaded."""
        self.unload()

    def __repr__(self) -> str:
        return (
            f"LLMFactory(models_dir={self.models_dir}, "
            f"loaded={self._current_model_name})"
        )


# Convenience function for quick access
def get_llm(
    agent_type: str,
    models_dir: Optional[Union[str, Path]] = None,
    **kwargs: Any,
) -> BaseLLM:
    """
    Quick helper to get an LLM instance for an agent type.

    Creates a new factory and loads the appropriate model.
    Remember to call factory.unload() when done.

    Args:
        agent_type: Agent type (ingestion, structuring, synthesis)
        models_dir: Optional custom models directory
        **kwargs: Additional arguments passed to LlamaCpp

    Returns:
        LangChain BaseLLM instance
    """
    factory = LLMFactory(models_dir=models_dir)
    return factory.create_for_agent(agent_type, **kwargs)
