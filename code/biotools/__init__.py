"""
UH2025-CDS-Agent: Bio-Tools Library

This module provides modular bio-informatics tool wrappers for the
Executor Agent. Each tool follows the BaseTool interface and can
be contributed by the community.

Available Tools:
- ClinVarTool: Query ClinVar for variant clinical significance
- SpliceAITool: Predict splice site impacts
- AlphaMissenseTool: DeepMind pathogenicity predictions for missense variants
- AlphaGenomeTool: DeepMind regulatory variant effect predictions
- REVELTool: Ensemble pathogenicity scores
- OMIMTool: Disease-gene relationships

Contributing New Tools:
See CONTRIBUTING.md in this directory for the simple interface.
We actively welcome contributions from the rare disease community!
"""

from .base_tool import BaseTool, ToolResult, Variant
from .clinvar import ClinVarTool
from .spliceai import SpliceAITool
from .alphamissense import AlphaMissenseTool
from .alphagenome import AlphaGenomeTool
from .revel import REVELTool
from .omim import OMIMTool
from .gnomad import GnomADTool

# Tool registry for dynamic loading
TOOL_REGISTRY = {
    "clinvar": ClinVarTool,
    "spliceai": SpliceAITool,
    "alphamissense": AlphaMissenseTool,
    "alphagenome": AlphaGenomeTool,
    "revel": REVELTool,
    "omim": OMIMTool,
    "gnomad": GnomADTool,
}

__all__ = [
    "BaseTool",
    "ToolResult",
    "Variant",
    "ClinVarTool",
    "SpliceAITool",
    "AlphaMissenseTool",
    "AlphaGenomeTool",
    "REVELTool",
    "OMIMTool",
    "GnomADTool",
    "TOOL_REGISTRY",
]

__version__ = "1.0.0"


def get_tool(tool_name: str) -> BaseTool:
    """
    Get a tool instance by name.

    Args:
        tool_name: Name of the tool (e.g., 'clinvar', 'spliceai')

    Returns:
        Instantiated tool

    Raises:
        KeyError: If tool not found in registry
    """
    if tool_name not in TOOL_REGISTRY:
        raise KeyError(
            f"Unknown tool: {tool_name}. "
            f"Available tools: {list(TOOL_REGISTRY.keys())}"
        )
    return TOOL_REGISTRY[tool_name]()


def list_tools() -> list:
    """List all available tools with their descriptions."""
    return [
        {
            "name": name,
            "class": cls.__name__,
            "description": cls.__doc__.split("\n")[0] if cls.__doc__ else "No description",
        }
        for name, cls in TOOL_REGISTRY.items()
    ]
