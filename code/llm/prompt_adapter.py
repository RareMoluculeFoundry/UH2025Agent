"""
Prompt Adapter: Convert Agent Prompts to LangChain Format

This module adapts the existing YAML-based prompt templates
to LangChain's ChatPromptTemplate format, enabling seamless
integration with the LangChain/LangGraph orchestration layer.

Supports:
- YAML template loading
- Variable substitution
- Few-shot example injection
- Model-specific formatting (Llama 3, Qwen)

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)


@dataclass
class AgentPromptTemplate:
    """
    Parsed prompt template for an agent.

    Attributes:
        system: System message content
        user_template: User message template with {variables}
        examples: List of few-shot examples
        output_format: Expected output format (json, markdown, etc.)
        version: Template version
    """
    system: str
    user_template: str
    examples: List[Dict[str, str]] = field(default_factory=list)
    output_format: str = "json"
    version: str = "v1"
    variables: List[str] = field(default_factory=list)


class PromptAdapter:
    """
    Adapter to convert YAML prompt templates to LangChain format.

    This adapter bridges the existing prompt template system with
    LangChain's ChatPromptTemplate, enabling:
    - Consistent prompt management across the pipeline
    - Variable validation and substitution
    - Few-shot example injection
    - Model-specific formatting

    Usage:
        adapter = PromptAdapter(prompts_dir="/path/to/prompts")
        template = adapter.load("ingestion_v1.yaml")
        chain = template.to_langchain() | llm
        result = chain.invoke({"patient_data": "..."})
    """

    # Model-specific chat templates
    MODEL_TEMPLATES = {
        "llama": {
            "system_prefix": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n",
            "system_suffix": "<|eot_id|>",
            "user_prefix": "<|start_header_id|>user<|end_header_id|>\n\n",
            "user_suffix": "<|eot_id|>",
            "assistant_prefix": "<|start_header_id|>assistant<|end_header_id|>\n\n",
            "assistant_suffix": "<|eot_id|>",
        },
        "qwen": {
            "system_prefix": "<|im_start|>system\n",
            "system_suffix": "<|im_end|>\n",
            "user_prefix": "<|im_start|>user\n",
            "user_suffix": "<|im_end|>\n",
            "assistant_prefix": "<|im_start|>assistant\n",
            "assistant_suffix": "<|im_end|>\n",
        },
        "chatml": {  # Generic ChatML format
            "system_prefix": "<|im_start|>system\n",
            "system_suffix": "<|im_end|>\n",
            "user_prefix": "<|im_start|>user\n",
            "user_suffix": "<|im_end|>\n",
            "assistant_prefix": "<|im_start|>assistant\n",
            "assistant_suffix": "<|im_end|>\n",
        },
    }

    def __init__(
        self,
        prompts_dir: Optional[Union[str, Path]] = None,
        model_format: str = "chatml",
    ):
        """
        Initialize the prompt adapter.

        Args:
            prompts_dir: Directory containing YAML prompt templates.
                        Defaults to code/agents/prompts/
            model_format: Chat template format (llama, qwen, chatml)
        """
        if prompts_dir is None:
            # Default to code/agents/prompts/ relative to this file
            self.prompts_dir = Path(__file__).parent.parent / "agents" / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)

        if model_format not in self.MODEL_TEMPLATES:
            raise ValueError(
                f"Unknown model format: {model_format}. "
                f"Available: {list(self.MODEL_TEMPLATES.keys())}"
            )
        self.model_format = model_format
        self._template_cache: Dict[str, AgentPromptTemplate] = {}

    def load(self, template_name: str) -> AgentPromptTemplate:
        """
        Load a prompt template from YAML file.

        Args:
            template_name: Name of the template file (e.g., "ingestion_v1.yaml")

        Returns:
            Parsed AgentPromptTemplate
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        template_path = self.prompts_dir / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")

        with open(template_path) as f:
            data = yaml.safe_load(f)

        # Extract variables from user template
        user_template = data.get("user", "")
        variables = self._extract_variables(user_template)

        template = AgentPromptTemplate(
            system=data.get("system", ""),
            user_template=user_template,
            examples=data.get("examples", []),
            output_format=data.get("output_format", "json"),
            version=data.get("version", "v1"),
            variables=variables,
        )

        self._template_cache[template_name] = template
        return template

    def _extract_variables(self, template: str) -> List[str]:
        """Extract variable names from a template string."""
        import re
        # Match {variable_name} patterns
        return re.findall(r'\{(\w+)\}', template)

    def to_langchain(
        self,
        template: AgentPromptTemplate,
        include_examples: bool = True,
    ) -> ChatPromptTemplate:
        """
        Convert AgentPromptTemplate to LangChain ChatPromptTemplate.

        Args:
            template: The agent prompt template
            include_examples: Whether to include few-shot examples

        Returns:
            LangChain ChatPromptTemplate
        """
        messages = []

        # System message
        if template.system:
            messages.append(
                SystemMessagePromptTemplate.from_template(template.system)
            )

        # Few-shot examples
        if include_examples and template.examples:
            for example in template.examples:
                if "user" in example:
                    messages.append(HumanMessage(content=example["user"]))
                if "assistant" in example:
                    messages.append(AIMessage(content=example["assistant"]))

        # User message template
        messages.append(
            HumanMessagePromptTemplate.from_template(template.user_template)
        )

        return ChatPromptTemplate.from_messages(messages)

    def to_completion_prompt(
        self,
        template: AgentPromptTemplate,
        variables: Dict[str, Any],
        include_examples: bool = True,
    ) -> str:
        """
        Convert template to a raw completion prompt string.

        Useful for LlamaCpp which uses completion-style prompts
        rather than chat-style.

        Args:
            template: The agent prompt template
            variables: Variable values for substitution
            include_examples: Whether to include few-shot examples

        Returns:
            Formatted prompt string
        """
        fmt = self.MODEL_TEMPLATES[self.model_format]
        parts = []

        # System message
        if template.system:
            parts.append(
                f"{fmt['system_prefix']}{template.system}{fmt['system_suffix']}"
            )

        # Few-shot examples
        if include_examples and template.examples:
            for example in template.examples:
                if "user" in example:
                    parts.append(
                        f"{fmt['user_prefix']}{example['user']}{fmt['user_suffix']}"
                    )
                if "assistant" in example:
                    parts.append(
                        f"{fmt['assistant_prefix']}{example['assistant']}{fmt['assistant_suffix']}"
                    )

        # User message with variable substitution
        user_content = template.user_template
        for key, value in variables.items():
            user_content = user_content.replace(f"{{{key}}}", str(value))

        parts.append(f"{fmt['user_prefix']}{user_content}{fmt['user_suffix']}")

        # Start assistant response
        parts.append(fmt['assistant_prefix'])

        return "".join(parts)

    def format_output_instruction(
        self,
        template: AgentPromptTemplate,
    ) -> str:
        """
        Generate output format instruction based on template.

        Args:
            template: The agent prompt template

        Returns:
            Instruction string for output format
        """
        if template.output_format == "json":
            return (
                "Respond with valid JSON only. "
                "Do not include any text before or after the JSON object."
            )
        elif template.output_format == "markdown":
            return "Format your response using Markdown."
        elif template.output_format == "text":
            return "Respond with plain text."
        else:
            return f"Format your response as {template.output_format}."

    def validate_variables(
        self,
        template: AgentPromptTemplate,
        variables: Dict[str, Any],
    ) -> Optional[str]:
        """
        Validate that all required variables are provided.

        Args:
            template: The agent prompt template
            variables: Variable values to validate

        Returns:
            Error message if validation fails, None if valid
        """
        missing = [v for v in template.variables if v not in variables]
        if missing:
            return f"Missing required variables: {missing}"
        return None

    def create_chain_prompt(
        self,
        agent_type: str,
        version: str = "v1",
    ) -> ChatPromptTemplate:
        """
        Convenience method to create a LangChain prompt for an agent.

        Args:
            agent_type: Agent type (ingestion, structuring, synthesis)
            version: Prompt template version

        Returns:
            LangChain ChatPromptTemplate
        """
        template_name = f"{agent_type}_{version}.yaml"
        template = self.load(template_name)
        return self.to_langchain(template)

    def __repr__(self) -> str:
        return (
            f"PromptAdapter(prompts_dir={self.prompts_dir}, "
            f"format={self.model_format})"
        )


# Helper function for quick prompt creation
def create_prompt(
    agent_type: str,
    version: str = "v1",
    prompts_dir: Optional[Union[str, Path]] = None,
) -> ChatPromptTemplate:
    """
    Quick helper to create a LangChain prompt for an agent.

    Args:
        agent_type: Agent type (ingestion, structuring, synthesis)
        version: Prompt template version
        prompts_dir: Optional custom prompts directory

    Returns:
        LangChain ChatPromptTemplate
    """
    adapter = PromptAdapter(prompts_dir=prompts_dir)
    return adapter.create_chain_prompt(agent_type, version)
