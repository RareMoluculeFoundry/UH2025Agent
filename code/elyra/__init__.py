"""
Elyra integration package.

Provides:
- ElyraConverter: Convert topology.yaml to Elyra pipeline format
- ElyraRunner: Execute Elyra pipelines programmatically

Note: Imports are lazy to avoid conflicts with papermill's 'elyra' entry point.
"""

__all__ = [
    'ElyraConverter',
    'ElyraRunner',
    'PipelineNode',
    'PipelineExecutionResult',
]


def __getattr__(name):
    """Lazy imports to avoid circular import issues."""
    if name == 'ElyraConverter':
        from .convert import ElyraConverter
        return ElyraConverter
    elif name == 'ElyraRunner':
        from .runner import ElyraRunner
        return ElyraRunner
    elif name == 'PipelineNode':
        from .runner import PipelineNode
        return PipelineNode
    elif name == 'PipelineExecutionResult':
        from .runner import PipelineExecutionResult
        return PipelineExecutionResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
