"""
BaseAgent: Abstract interface for all UH2025-CDS agents.

All agents in the 4-agent pipeline inherit from this base class,
ensuring consistent:
- Configuration management
- Model loading/unloading (via LangChain LlamaCpp)
- Prompt template handling
- RLHF feedback collection
- Result serialization

LangChain Integration (HIPAA-Safe):
- Uses llama-cpp-python backend via LLMFactory
- NO cloud APIs permitted (OpenAI, Anthropic, etc.)
- All inference runs locally on-device

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import json
import yaml

# LangChain imports (HIPAA-safe - local only)
if TYPE_CHECKING:
    from langchain_core.language_models.llms import BaseLLM


class AgentStatus(Enum):
    """Agent execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_REVIEW = "awaiting_review"


@dataclass
class ModelConfig:
    """
    Configuration for LLM model loading.

    Designed for llama.cpp backend with GGUF models.
    """
    name: str
    backend: str = "llama.cpp"
    quantization: str = "Q4_K_M"
    context_length: int = 8192
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1

    # Path to GGUF model file (resolved at runtime)
    model_path: Optional[str] = None

    # Memory estimate in GB
    memory_gb: float = 2.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "backend": self.backend,
            "quantization": self.quantization,
            "context_length": self.context_length,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repeat_penalty": self.repeat_penalty,
            "model_path": self.model_path,
            "memory_gb": self.memory_gb,
        }


@dataclass
class PromptConfig:
    """
    Configuration for prompt templates.

    Supports YAML-based templates with variable substitution.
    """
    template_path: str
    system_message: str = ""
    few_shot_examples: Optional[str] = None
    version: str = "v1"

    def load_template(self) -> Dict[str, Any]:
        """Load prompt template from YAML file."""
        path = Path(self.template_path)

        # Try relative path first
        if path.exists():
            with open(path) as f:
                return yaml.safe_load(f)

        # Try path relative to the agents directory
        agents_dir = Path(__file__).parent
        relative_path = agents_dir / self.template_path
        if relative_path.exists():
            with open(relative_path) as f:
                return yaml.safe_load(f)

        # Fallback to inline system message
        import logging
        logging.getLogger(__name__).warning(f"Prompt template not found: {self.template_path}")
        return {"system": self.system_message, "user": "", "examples": []}


@dataclass
class AgentConfig:
    """
    Full configuration for an agent.

    Combines model, prompt, and operational settings.
    """
    agent_id: str
    agent_type: str
    model: ModelConfig
    prompt: PromptConfig

    # Operational settings
    timeout_seconds: int = 300
    retry_count: int = 2
    collect_rlhf: bool = True

    # Context injection
    context_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "model": self.model.to_dict(),
            "prompt": {
                "template_path": self.prompt.template_path,
                "system_message": self.prompt.system_message[:100] + "...",
                "version": self.prompt.version,
            },
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "collect_rlhf": self.collect_rlhf,
        }


@dataclass
class AgentResult:
    """
    Standardized result from agent execution.

    Includes outputs, metadata, and RLHF feedback hooks.
    """
    agent_id: str
    agent_type: str
    status: AgentStatus

    # Outputs
    outputs: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)  # Paths to generated files

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Model info
    tokens_input: int = 0
    tokens_output: int = 0

    # Errors
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # RLHF
    awaiting_feedback: bool = False
    feedback_schema: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "outputs": self.outputs,
            "artifacts": self.artifacts,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "error_message": self.error_message,
            "awaiting_feedback": self.awaiting_feedback,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class BaseAgent(ABC):
    """
    Abstract base class for all UH2025-CDS agents.

    Provides common functionality for:
    - Configuration management
    - Model lifecycle (load/unload)
    - Prompt rendering
    - Result collection
    - RLHF feedback integration

    Subclasses must implement:
    - _execute(): Core agent logic
    - _validate_input(): Input validation
    - _get_feedback_schema(): RLHF schema for this agent's outputs
    """

    # Class-level defaults (override in subclasses)
    AGENT_TYPE: str = "base"
    DEFAULT_MODEL: str = "llama-3.2-3b-instruct"
    DEFAULT_QUANTIZATION: str = "Q4_K_M"
    DEFAULT_CONTEXT_LENGTH: int = 8192
    DEFAULT_TEMPERATURE: float = 0.3
    DEFAULT_MEMORY_GB: float = 2.0

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        Initialize agent with configuration.

        Args:
            config: Agent configuration. If None, uses defaults.
        """
        self.config = config or self._default_config()
        self._model: Optional["BaseLLM"] = None
        self._llm_factory = None
        self._is_loaded = False

    def _default_config(self) -> AgentConfig:
        """Create default configuration for this agent type."""
        return AgentConfig(
            agent_id=f"{self.AGENT_TYPE}_default",
            agent_type=self.AGENT_TYPE,
            model=ModelConfig(
                name=self.DEFAULT_MODEL,
                quantization=self.DEFAULT_QUANTIZATION,
                context_length=self.DEFAULT_CONTEXT_LENGTH,
                temperature=self.DEFAULT_TEMPERATURE,
                memory_gb=self.DEFAULT_MEMORY_GB,
            ),
            prompt=PromptConfig(
                template_path=f"prompts/{self.AGENT_TYPE}_v1.yaml",
                system_message=f"You are the {self.AGENT_TYPE} agent.",
            ),
        )

    def load_model(self) -> None:
        """
        Load the LLM model into memory via LangChain LlamaCpp.

        Uses the HIPAA-safe LLMFactory which enforces local-only
        execution (no cloud APIs permitted).
        """
        if self._is_loaded:
            return

        import logging
        logger = logging.getLogger(__name__)

        model_config = self.config.model
        logger.info(f"[{self.AGENT_TYPE}] Loading model: {model_config.name} ({model_config.quantization}, ~{model_config.memory_gb}GB)")

        # Import LLMFactory (lazy import to avoid circular dependencies)
        from code.llm import LLMFactory

        # Create factory and load model
        self._llm_factory = LLMFactory()

        # Map model name to LLMFactory model name
        model_name = self._map_model_name(model_config.name)

        self._model = self._llm_factory.create(
            model_name=model_name,
            temperature=model_config.temperature,
            top_p=model_config.top_p,
            top_k=model_config.top_k,
            repeat_penalty=model_config.repeat_penalty,
        )

        self._is_loaded = True
        logger.info(f"[{self.AGENT_TYPE}] Model loaded successfully")

    def _map_model_name(self, name: str) -> str:
        """
        Map agent model names to LLMFactory registry names.

        Handles variations in naming conventions.
        """
        # Normalize name
        name_lower = name.lower().replace("_", "-").replace(" ", "-")

        # Direct mapping
        mappings = {
            "llama-3.2-3b-instruct": "llama-3.2-3b-instruct",
            "llama-3-2-3b-instruct": "llama-3.2-3b-instruct",
            "qwen-2.5-14b-instruct": "qwen-2.5-14b-instruct",
            "qwen-2-5-14b-instruct": "qwen-2.5-14b-instruct",
            "qwen-2.5-32b-instruct": "qwen-2.5-32b-instruct",
            "qwen-2-5-32b-instruct": "qwen-2.5-32b-instruct",
        }

        if name_lower in mappings:
            return mappings[name_lower]

        # Return as-is if not found in mapping
        return name_lower

    def unload_model(self) -> None:
        """
        Unload model from memory.

        Important for sequential model loading on memory-constrained systems.
        Uses LLMFactory's unload method for proper cleanup.
        """
        if not self._is_loaded:
            return

        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[{self.AGENT_TYPE}] Unloading model: {self.config.model.name}")

        # Use LLMFactory's unload for proper cleanup
        if self._llm_factory is not None:
            self._llm_factory.unload()
            self._llm_factory = None

        self._model = None
        self._is_loaded = False
        logger.debug(f"[{self.AGENT_TYPE}] Model unloaded")

    def render_prompt(self, inputs: Dict[str, Any]) -> str:
        """
        Render the prompt template with input variables.

        Returns a simple concatenation of system + user message.
        The chat template formatting is handled by llama-cpp-python's
        chat_format parameter, which automatically wraps the text in
        the appropriate special tokens for each model family.

        Args:
            inputs: Dictionary of input variables for template substitution

        Returns:
            Rendered prompt string (system + user concatenated)
        """
        template = self.config.prompt.load_template()

        # Substitute variables in user template
        user_template = template.get("user", "")
        for key, value in inputs.items():
            user_template = user_template.replace(f"{{{key}}}", str(value))

        system_message = template.get("system", "")

        # Simple concatenation - let chat_format handle the special tokens
        # The llama-cpp-python library with chat_format will properly wrap this
        if system_message:
            return f"{system_message.strip()}\n\n{user_template.strip()}"
        return user_template.strip()

    def invoke_llm(self, prompt: str) -> str:
        """
        Invoke the loaded LLM with a prompt.

        This is a convenience method for subclasses to call the LLM.
        Handles both the LangChain interface and basic string I/O.

        Args:
            prompt: The formatted prompt string

        Returns:
            The LLM's response text

        Raises:
            RuntimeError: If model is not loaded
        """
        if not self._is_loaded or self._model is None:
            raise RuntimeError(
                f"Model not loaded. Call load_model() first or use run() method."
            )

        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Prompt length: {len(prompt)} chars")

        # LangChain LLM invoke
        response = self._model.invoke(prompt)

        # Handle different response types
        if isinstance(response, str):
            return response
        elif hasattr(response, 'content'):
            return response.content
        else:
            return str(response)

    def run(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent with given inputs.

        This is the main entry point for agent execution.
        Handles model loading, validation, execution, and result collection.

        Args:
            inputs: Dictionary of inputs for this agent

        Returns:
            AgentResult with outputs and metadata
        """
        result = AgentResult(
            agent_id=self.config.agent_id,
            agent_type=self.AGENT_TYPE,
            status=AgentStatus.PENDING,
            start_time=datetime.now(),
        )

        try:
            # Validate inputs
            validation_error = self._validate_input(inputs)
            if validation_error:
                result.status = AgentStatus.FAILED
                result.error_message = validation_error
                return result

            # Load model if needed
            result.status = AgentStatus.RUNNING
            self.load_model()

            # Execute agent logic
            outputs = self._execute(inputs)

            # Collect results
            result.outputs = outputs
            result.status = AgentStatus.COMPLETED

            # Set up RLHF feedback if enabled
            if self.config.collect_rlhf:
                result.awaiting_feedback = True
                result.feedback_schema = self._get_feedback_schema()
                result.status = AgentStatus.AWAITING_REVIEW

        except Exception as e:
            result.status = AgentStatus.FAILED
            result.error_message = str(e)
            import traceback
            result.error_traceback = traceback.format_exc()

        finally:
            result.end_time = datetime.now()
            if result.start_time:
                result.duration_seconds = (
                    result.end_time - result.start_time
                ).total_seconds()

        return result

    @abstractmethod
    def _execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core agent execution logic.

        Must be implemented by subclasses.

        Args:
            inputs: Validated input dictionary

        Returns:
            Dictionary of outputs
        """
        pass

    @abstractmethod
    def _validate_input(self, inputs: Dict[str, Any]) -> Optional[str]:
        """
        Validate input dictionary.

        Must be implemented by subclasses.

        Args:
            inputs: Input dictionary to validate

        Returns:
            Error message if validation fails, None if valid
        """
        pass

    @abstractmethod
    def _get_feedback_schema(self) -> Dict[str, Any]:
        """
        Get RLHF feedback schema for this agent's outputs.

        Must be implemented by subclasses.

        Returns:
            JSON Schema for feedback collection
        """
        pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self.config.agent_id}, "
            f"model={self.config.model.name}, "
            f"loaded={self._is_loaded})"
        )
