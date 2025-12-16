"""
UH2025Agent Code Package

Provides configurator, output viewer, and widget components for the
UH2025Agent diagnostic pipeline.

NOTE: The legacy PipelineExecutor has been archived to code/legacy/.
Use the new LangGraph-based pipeline via code.uh2025_graph.graph.run_pipeline()

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from .ui.configurator import TopologyConfigurator, ModuleConfigTab
from .ui.output_viewer import OutputBrowser, OutputTab
from .ui.widgets import PatientSelector, ProgressTracker, StatusDisplay, RunButton
from .ui.review_interface import DiagnosisReviewTable, DiagnosisReviewRow, create_review_interface

# Import the new LangGraph pipeline runner
from .uh2025_graph.graph import run_pipeline

__all__ = [
    'TopologyConfigurator',
    'ModuleConfigTab',
    'OutputBrowser',
    'OutputTab',
    'run_pipeline',  # New LangGraph-based pipeline
    'PatientSelector',
    'ProgressTracker',
    'StatusDisplay',
    'RunButton',
    'DiagnosisReviewTable',
    'DiagnosisReviewRow',
    'create_review_interface'
]
