"""
Diagnosis Review and Annotation Interface

This module provides an interactive interface for clinicians to review and annotate
AI-generated differential diagnoses. It supports flagging correct/incorrect diagnoses,
adjusting confidence scores, adding comments, and saving annotations for future
model improvement.

Author: Stanley Lab / RareResearch
Date: November 2025
License: CC-BY-4.0
Version: 2.0.0 - Added multi-turn feedback and reanalysis support
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

import ipywidgets as widgets
from IPython.display import display, HTML


class ReanalysisRequestType(Enum):
    """Types of reanalysis that can be requested."""
    FULL_RERUN = "full_rerun"  # Complete pipeline rerun
    DIFFERENTIAL_ONLY = "differential_only"  # Only redo differential diagnosis
    ADD_EVIDENCE = "add_evidence"  # Add new clinical evidence
    ADJUST_PRIORS = "adjust_priors"  # Adjust prior probabilities
    FOCUS_GENES = "focus_genes"  # Focus on specific genes


class DiagnosisReviewRow:
    """
    Interactive row widget for reviewing a single diagnosis.

    Provides:
    - Checkbox for marking diagnosis as correct/incorrect
    - Confidence adjustment slider
    - Text area for clinician comments
    - Visual indicators for review status
    """

    def __init__(
        self,
        diagnosis: Dict[str, Any],
        index: int,
        on_change: Optional[Callable] = None
    ):
        """
        Initialize a review row for a single diagnosis.

        Args:
            diagnosis: Dictionary containing diagnosis information
            index: Row index (0-based)
            on_change: Optional callback when review data changes
        """
        self.diagnosis = diagnosis
        self.index = index
        self.on_change = on_change

        # Extract diagnosis info
        self.disease_name = diagnosis.get('disease', 'Unknown')
        self.confidence = diagnosis.get('confidence', 0.0)
        self.omim_id = diagnosis.get('omim_id', 'N/A')
        self.genes = diagnosis.get('genes', [])
        self.rationale = diagnosis.get('rationale', '')

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create all interactive widgets for this row."""

        # Correct/Incorrect checkbox
        self.correct_checkbox = widgets.Checkbox(
            value=True,  # Default to correct
            description='',
            indent=False,
            layout=widgets.Layout(width='30px')
        )
        self.correct_checkbox.observe(self._on_widget_change, names='value')

        # Confidence adjustment slider
        self.confidence_slider = widgets.FloatSlider(
            value=self.confidence,
            min=0.0,
            max=1.0,
            step=0.01,
            description='',
            readout=True,
            readout_format='.0%',
            layout=widgets.Layout(width='200px')
        )
        self.confidence_slider.observe(self._on_widget_change, names='value')

        # Comments text area
        self.comments_textarea = widgets.Textarea(
            value='',
            placeholder='Add clinical notes or corrections...',
            description='',
            layout=widgets.Layout(width='300px', height='60px')
        )
        self.comments_textarea.observe(self._on_widget_change, names='value')

        # Disease name label (with OMIM link)
        omim_url = f"https://omim.org/entry/{self.omim_id}"
        self.disease_label = widgets.HTML(
            value=f'''
            <div style="font-weight: bold; margin-bottom: 4px; color: #212121;">
                {self.index + 1}. {self.disease_name}
            </div>
            <div style="font-size: 0.9em; color: #5f6368;">
                OMIM: <a href="{omim_url}" target="_blank" style="color: #1976d2;">{self.omim_id}</a> |
                Genes: {", ".join(self.genes) if self.genes else "N/A"}
            </div>
            '''
        )

        # Status indicator (updates based on checkbox)
        self.status_indicator = widgets.HTML(
            value=self._get_status_html(True)
        )

    def _on_widget_change(self, change):
        """Handle widget value changes."""
        # Update status indicator
        self.status_indicator.value = self._get_status_html(self.correct_checkbox.value)

        # Call parent callback
        if self.on_change:
            self.on_change()

    def _get_status_html(self, is_correct: bool) -> str:
        """Get HTML for status indicator."""
        if is_correct:
            return '''
            <div style="background: #4caf50; color: white; padding: 4px 12px;
                        border-radius: 12px; font-size: 0.85em; display: inline-block;">
                ✓ Correct
            </div>
            '''
        else:
            return '''
            <div style="background: #f44336; color: white; padding: 4px 12px;
                        border-radius: 12px; font-size: 0.85em; display: inline-block;">
                ✗ Incorrect
            </div>
            '''

    def get_widget(self) -> widgets.Widget:
        """Get the complete row widget."""
        # Layout: [Status] [Checkbox] [Disease Info] [Confidence Slider] [Comments]
        return widgets.HBox([
            widgets.VBox([
                self.status_indicator,
                widgets.HTML(value='<div style="font-size: 0.8em; color: #5f6368;">Mark as:</div>'),
                self.correct_checkbox
            ], layout=widgets.Layout(width='100px', align_items='center')),

            widgets.VBox([
                self.disease_label,
                widgets.HTML(value=f'<div style="font-size: 0.85em; color: #5f6368; margin-top: 4px;">{self.rationale[:150]}...</div>')
            ], layout=widgets.Layout(width='350px')),

            widgets.VBox([
                widgets.HTML(value='<div style="font-size: 0.85em; color: #212121; margin-bottom: 4px;">Adjusted Confidence:</div>'),
                self.confidence_slider,
                widgets.HTML(value=f'<div style="font-size: 0.8em; color: #5f6368;">Original: {self.confidence:.0%}</div>')
            ], layout=widgets.Layout(width='220px')),

            widgets.VBox([
                widgets.HTML(value='<div style="font-size: 0.85em; color: #212121; margin-bottom: 4px;">Clinical Notes:</div>'),
                self.comments_textarea
            ], layout=widgets.Layout(width='320px'))
        ], layout=widgets.Layout(
            border='2px solid #dee2e6',
            margin='8px 0',
            padding='12px',
            border_radius='4px',
            background='#ffffff'
        ))

    def get_annotation(self) -> Dict[str, Any]:
        """Get annotation data for this diagnosis."""
        return {
            'disease': self.disease_name,
            'omim_id': self.omim_id,
            'original_confidence': self.confidence,
            'adjusted_confidence': self.confidence_slider.value,
            'is_correct': self.correct_checkbox.value,
            'clinician_comments': self.comments_textarea.value,
            'genes': self.genes,
            'original_rationale': self.rationale
        }

    def set_annotation(self, annotation: Dict[str, Any]):
        """Load annotation data into this row."""
        if annotation.get('adjusted_confidence') is not None:
            self.confidence_slider.value = annotation['adjusted_confidence']
        if annotation.get('is_correct') is not None:
            self.correct_checkbox.value = annotation['is_correct']
        if annotation.get('clinician_comments'):
            self.comments_textarea.value = annotation['clinician_comments']


class DiagnosisReviewTable:
    """
    Complete diagnosis review table with save/load functionality.

    Allows clinicians to:
    - Review all AI-generated diagnoses
    - Mark each as correct/incorrect
    - Adjust confidence scores
    - Add clinical notes
    - Save annotations for model improvement
    - Load previous annotations
    """

    def __init__(
        self,
        differential_diagnosis_file: Path,
        annotations_file: Optional[Path] = None
    ):
        """
        Initialize the review table.

        Args:
            differential_diagnosis_file: Path to differential_diagnosis.json
            annotations_file: Path to save/load annotations (default: same dir as diagnosis file)
        """
        self.diagnosis_file = Path(differential_diagnosis_file)

        if annotations_file is None:
            self.annotations_file = self.diagnosis_file.parent / 'annotations.json'
        else:
            self.annotations_file = Path(annotations_file)

        # Load diagnosis data
        self.diagnoses = []
        self.metadata = {}
        self._load_diagnoses()

        # Create review rows
        self.review_rows: List[DiagnosisReviewRow] = []
        self._create_review_rows()

        # Create control widgets
        self._create_controls()

        # Try to load existing annotations
        self._try_load_annotations()

    def _load_diagnoses(self):
        """Load differential diagnosis data from file."""
        if not self.diagnosis_file.exists():
            raise FileNotFoundError(f"Diagnosis file not found: {self.diagnosis_file}")

        with open(self.diagnosis_file, 'r') as f:
            data = json.load(f)

        self.diagnoses = data.get('differential_diagnosis', [])
        self.metadata = data.get('metadata', {})

    def _create_review_rows(self):
        """Create review row widgets for each diagnosis."""
        self.review_rows = [
            DiagnosisReviewRow(diagnosis, i, on_change=self._on_review_change)
            for i, diagnosis in enumerate(self.diagnoses)
        ]

    def _create_controls(self):
        """Create save/load/reset control widgets."""

        # Save button
        self.save_button = widgets.Button(
            description='💾 Save Annotations',
            button_style='success',
            tooltip='Save your review annotations',
            icon='save',
            layout=widgets.Layout(width='200px')
        )
        self.save_button.on_click(self._on_save_clicked)

        # Load button
        self.load_button = widgets.Button(
            description='📂 Load Annotations',
            button_style='info',
            tooltip='Load previously saved annotations',
            icon='folder-open',
            layout=widgets.Layout(width='200px')
        )
        self.load_button.on_click(self._on_load_clicked)

        # Reset button
        self.reset_button = widgets.Button(
            description='🔄 Reset to Default',
            button_style='warning',
            tooltip='Reset all annotations to default values',
            icon='refresh',
            layout=widgets.Layout(width='200px')
        )
        self.reset_button.on_click(self._on_reset_clicked)

        # Export button
        self.export_button = widgets.Button(
            description='📥 Export for Training',
            button_style='primary',
            tooltip='Export annotations as training data',
            icon='download',
            layout=widgets.Layout(width='200px')
        )
        self.export_button.on_click(self._on_export_clicked)

        # Status message
        self.status_message = widgets.HTML(
            value='<div style="color: #5f6368; font-style: italic;">Ready to review</div>'
        )

        # Summary statistics
        self.summary_widget = widgets.HTML(
            value=self._get_summary_html()
        )

    def _on_review_change(self):
        """Update summary when any review changes."""
        self.summary_widget.value = self._get_summary_html()

    def _get_summary_html(self) -> str:
        """Generate HTML summary of review status."""
        total = len(self.review_rows)
        correct = sum(1 for row in self.review_rows if row.correct_checkbox.value)
        incorrect = total - correct
        commented = sum(1 for row in self.review_rows if row.comments_textarea.value.strip())

        return f'''
        <div style="background: #ffffff; padding: 16px; border-radius: 4px; margin: 8px 0;
                    border: 2px solid #dee2e6;">
            <div style="font-weight: bold; margin-bottom: 8px; color: #212121; font-size: 1.1em;">
                Review Summary:
            </div>
            <div style="display: flex; gap: 20px; color: #212121;">
                <div>
                    <span style="color: #2e7d32; font-weight: bold; font-size: 1.2em;">{correct}</span>
                    <span style="color: #5f6368;"> Correct</span>
                </div>
                <div>
                    <span style="color: #c62828; font-weight: bold; font-size: 1.2em;">{incorrect}</span>
                    <span style="color: #5f6368;"> Incorrect</span>
                </div>
                <div>
                    <span style="color: #1565c0; font-weight: bold; font-size: 1.2em;">{commented}</span>
                    <span style="color: #5f6368;"> Commented</span>
                </div>
                <div style="color: #212121;">
                    Total: <span style="font-weight: bold;">{total}</span> diagnoses
                </div>
            </div>
        </div>
        '''

    def _on_save_clicked(self, button):
        """Save annotations to file."""
        try:
            self.save_annotations()
            self.status_message.value = f'''
            <div style="color: #4caf50; font-weight: bold;">
                ✓ Annotations saved to {self.annotations_file.name}
            </div>
            '''
        except Exception as e:
            self.status_message.value = f'''
            <div style="color: #f44336; font-weight: bold;">
                ✗ Error saving: {str(e)}
            </div>
            '''

    def _on_load_clicked(self, button):
        """Load annotations from file."""
        try:
            if self.load_annotations():
                self.status_message.value = f'''
                <div style="color: #4caf50; font-weight: bold;">
                    ✓ Annotations loaded from {self.annotations_file.name}
                </div>
                '''
            else:
                self.status_message.value = '''
                <div style="color: #ff9800; font-weight: bold;">
                    ⚠ No saved annotations found
                </div>
                '''
        except Exception as e:
            self.status_message.value = f'''
            <div style="color: #f44336; font-weight: bold;">
                ✗ Error loading: {str(e)}
            </div>
            '''

    def _on_reset_clicked(self, button):
        """Reset all annotations to default."""
        for row in self.review_rows:
            row.correct_checkbox.value = True
            row.confidence_slider.value = row.confidence
            row.comments_textarea.value = ''

        self.status_message.value = '''
        <div style="color: #ff9800; font-weight: bold;">
            ↻ Annotations reset to default
        </div>
        '''

    def _on_export_clicked(self, button):
        """Export annotations as training data."""
        try:
            export_path = self.annotations_file.parent / 'training_data.json'
            training_data = self._prepare_training_data()

            with open(export_path, 'w') as f:
                json.dump(training_data, f, indent=2)

            self.status_message.value = f'''
            <div style="color: #2196f3; font-weight: bold;">
                ✓ Training data exported to {export_path.name}
            </div>
            '''
        except Exception as e:
            self.status_message.value = f'''
            <div style="color: #f44336; font-weight: bold;">
                ✗ Error exporting: {str(e)}
            </div>
            '''

    def _prepare_training_data(self) -> Dict[str, Any]:
        """Prepare annotations in training data format."""
        return {
            'patient_id': self.metadata.get('patient_id', 'unknown'),
            'case_metadata': self.metadata,
            'annotated_diagnoses': [row.get_annotation() for row in self.review_rows],
            'annotation_metadata': {
                'annotated_at': datetime.now().isoformat(),
                'annotator': 'clinician',  # Could be made configurable
                'annotation_version': '1.0'
            },
            'feedback_summary': {
                'total_diagnoses': len(self.review_rows),
                'marked_correct': sum(1 for row in self.review_rows if row.correct_checkbox.value),
                'marked_incorrect': sum(1 for row in self.review_rows if not row.correct_checkbox.value),
                'confidence_adjustments': [
                    {
                        'disease': row.disease_name,
                        'original': row.confidence,
                        'adjusted': row.confidence_slider.value,
                        'delta': row.confidence_slider.value - row.confidence
                    }
                    for row in self.review_rows
                    if abs(row.confidence_slider.value - row.confidence) > 0.01
                ]
            }
        }

    def save_annotations(self):
        """Save current annotations to file."""
        annotations = {
            'diagnosis_file': str(self.diagnosis_file),
            'annotations': [row.get_annotation() for row in self.review_rows],
            'metadata': {
                'saved_at': datetime.now().isoformat(),
                'num_diagnoses': len(self.review_rows),
                'num_correct': sum(1 for row in self.review_rows if row.correct_checkbox.value),
                'num_incorrect': sum(1 for row in self.review_rows if not row.correct_checkbox.value),
                'num_commented': sum(1 for row in self.review_rows if row.comments_textarea.value.strip())
            }
        }

        with open(self.annotations_file, 'w') as f:
            json.dump(annotations, f, indent=2)

    def load_annotations(self) -> bool:
        """
        Load annotations from file.

        Returns:
            True if annotations were loaded, False if file doesn't exist
        """
        if not self.annotations_file.exists():
            return False

        with open(self.annotations_file, 'r') as f:
            data = json.load(f)

        annotations = data.get('annotations', [])

        # Match annotations to rows by disease name
        for annotation in annotations:
            disease_name = annotation.get('disease')
            for row in self.review_rows:
                if row.disease_name == disease_name:
                    row.set_annotation(annotation)
                    break

        # Update summary
        self._on_review_change()

        return True

    def _try_load_annotations(self):
        """Try to load annotations on initialization (silent)."""
        if self.annotations_file.exists():
            try:
                self.load_annotations()
            except:
                pass  # Silently fail if annotations can't be loaded

    def refresh(self):
        """Reload diagnosis data and refresh the interface."""
        try:
            # Reload diagnosis data from file
            self._load_diagnoses()

            # Recreate review rows with new data
            self._create_review_rows()

            # Try to restore existing annotations if any
            self._try_load_annotations()

            # Update summary widget
            self._on_review_change()

        except Exception as e:
            # Handle reload failure gracefully
            import traceback
            print(f"Warning: Could not refresh diagnosis data: {str(e)}")
            traceback.print_exc()

    def get_widget(self) -> widgets.Widget:
        """Get the complete review table widget."""

        # Header
        header = widgets.HTML(
            value='''
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white; padding: 16px; border-radius: 4px; margin-bottom: 16px;">
                <h2 style="margin: 0 0 8px 0;">🔍 Clinician Review & Annotation</h2>
                <p style="margin: 0; opacity: 0.9;">
                    Review AI-generated diagnoses, adjust confidence scores, and provide clinical feedback.
                    Your annotations will help improve future model performance.
                </p>
            </div>
            '''
        )

        # Instructions
        instructions = widgets.HTML(
            value='''
            <div style="background: #ffffff; padding: 16px; border-radius: 4px; margin-bottom: 16px;
                        border: 2px solid #1976d2; border-left: 6px solid #1976d2;">
                <div style="font-weight: bold; margin-bottom: 8px; color: #212121; font-size: 1.05em;">
                    📋 How to Review:
                </div>
                <ol style="margin: 4px 0; padding-left: 24px; color: #212121; line-height: 1.6;">
                    <li>Check/uncheck the box to mark each diagnosis as correct or incorrect</li>
                    <li>Adjust the confidence slider if you disagree with the AI's confidence level</li>
                    <li>Add clinical notes to explain your reasoning or suggest improvements</li>
                    <li>Click "💾 Save Annotations" to save your review</li>
                    <li>Click "📥 Export for Training" to prepare data for model fine-tuning</li>
                </ol>
            </div>
            '''
        )

        # Controls row
        controls_row = widgets.HBox([
            self.save_button,
            self.load_button,
            self.reset_button,
            self.export_button
        ], layout=widgets.Layout(gap='12px', margin='16px 0'))

        # All review rows
        review_rows_container = widgets.VBox([
            row.get_widget() for row in self.review_rows
        ])

        # Complete layout
        return widgets.VBox([
            header,
            instructions,
            self.summary_widget,
            controls_row,
            self.status_message,
            widgets.HTML(value='<hr style="margin: 20px 0;">'),
            review_rows_container
        ])


# Convenience function for easy initialization
def create_review_interface(outputs_dir: Path) -> DiagnosisReviewTable:
    """
    Create a diagnosis review interface for the differential diagnosis output.

    Args:
        outputs_dir: Path to the outputs directory

    Returns:
        DiagnosisReviewTable widget

    Example:
        >>> from code.ui.review_interface import create_review_interface
        >>> review_table = create_review_interface(Path('outputs'))
        >>> display(review_table.get_widget())
    """
    diagnosis_file = outputs_dir / '03_differential' / 'differential_diagnosis.json'
    return DiagnosisReviewTable(diagnosis_file)


class ReanalysisRequest:
    """
    Container for a reanalysis request based on clinician feedback.

    Used to communicate what changes the clinician wants the AI to consider
    when re-running the diagnostic pipeline.
    """

    def __init__(
        self,
        request_type: ReanalysisRequestType,
        feedback_summary: Dict[str, Any],
        clinician_guidance: str = "",
        focus_genes: Optional[List[str]] = None,
        additional_evidence: Optional[Dict[str, Any]] = None,
        confidence_adjustments: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize a reanalysis request.

        Args:
            request_type: Type of reanalysis requested
            feedback_summary: Summary of clinician feedback from review
            clinician_guidance: Free-text guidance from clinician
            focus_genes: List of genes to prioritize in reanalysis
            additional_evidence: New clinical evidence to incorporate
            confidence_adjustments: Adjusted prior probabilities for conditions
        """
        self.request_type = request_type
        self.feedback_summary = feedback_summary
        self.clinician_guidance = clinician_guidance
        self.focus_genes = focus_genes or []
        self.additional_evidence = additional_evidence or {}
        self.confidence_adjustments = confidence_adjustments or {}
        self.created_at = datetime.now().isoformat()
        self.iteration = 1  # Track which iteration this is

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "request_type": self.request_type.value,
            "feedback_summary": self.feedback_summary,
            "clinician_guidance": self.clinician_guidance,
            "focus_genes": self.focus_genes,
            "additional_evidence": self.additional_evidence,
            "confidence_adjustments": self.confidence_adjustments,
            "created_at": self.created_at,
            "iteration": self.iteration,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReanalysisRequest":
        """Create from dictionary."""
        req = cls(
            request_type=ReanalysisRequestType(data["request_type"]),
            feedback_summary=data.get("feedback_summary", {}),
            clinician_guidance=data.get("clinician_guidance", ""),
            focus_genes=data.get("focus_genes"),
            additional_evidence=data.get("additional_evidence"),
            confidence_adjustments=data.get("confidence_adjustments"),
        )
        req.created_at = data.get("created_at", req.created_at)
        req.iteration = data.get("iteration", 1)
        return req


class MultiTurnReviewInterface:
    """
    Extended review interface with multi-turn feedback and reanalysis support.

    This interface allows clinicians to:
    - Review AI-generated diagnoses (like DiagnosisReviewTable)
    - Request reanalysis with specific guidance
    - Add new clinical evidence for the next iteration
    - Track multiple rounds of feedback and improvement
    - Export complete feedback history for RLHF training
    """

    def __init__(
        self,
        outputs_dir: Path,
        reanalysis_callback: Optional[Callable[[ReanalysisRequest], None]] = None,
    ):
        """
        Initialize the multi-turn review interface.

        Args:
            outputs_dir: Path to the pipeline outputs directory
            reanalysis_callback: Optional callback function to trigger reanalysis
                                 Will be called with ReanalysisRequest when "Reanalyze" is clicked
        """
        self.outputs_dir = Path(outputs_dir)
        self.reanalysis_callback = reanalysis_callback

        # Track feedback history across iterations
        self.feedback_history: List[Dict[str, Any]] = []
        self.current_iteration = 1

        # Load diagnosis review table
        self.review_table = create_review_interface(outputs_dir)

        # Create multi-turn specific widgets
        self._create_multiturn_widgets()

        # Load history if exists
        self._load_history()

    def _create_multiturn_widgets(self):
        """Create widgets for multi-turn feedback."""

        # Reanalysis type selector
        self.reanalysis_type_dropdown = widgets.Dropdown(
            options=[
                ("Full Pipeline Rerun", ReanalysisRequestType.FULL_RERUN.value),
                ("Differential Diagnosis Only", ReanalysisRequestType.DIFFERENTIAL_ONLY.value),
                ("Add New Evidence", ReanalysisRequestType.ADD_EVIDENCE.value),
                ("Adjust Prior Probabilities", ReanalysisRequestType.ADJUST_PRIORS.value),
                ("Focus on Specific Genes", ReanalysisRequestType.FOCUS_GENES.value),
            ],
            value=ReanalysisRequestType.DIFFERENTIAL_ONLY.value,
            description="",
            layout=widgets.Layout(width="250px"),
        )

        # Clinician guidance text area
        self.guidance_textarea = widgets.Textarea(
            value="",
            placeholder="Provide specific guidance for the reanalysis (e.g., 'Consider autosomal recessive inheritance' or 'Focus on cardiac phenotypes')...",
            description="",
            layout=widgets.Layout(width="100%", height="100px"),
        )

        # Focus genes input
        self.focus_genes_input = widgets.Text(
            value="",
            placeholder="Comma-separated gene symbols (e.g., SCN4A, CLCN1, DMD)",
            description="",
            layout=widgets.Layout(width="100%"),
        )

        # Additional evidence text area
        self.additional_evidence_textarea = widgets.Textarea(
            value="",
            placeholder="Add new clinical findings or test results (e.g., 'EMG shows myotonic discharges', 'Muscle biopsy shows ragged red fibers')...",
            description="",
            layout=widgets.Layout(width="100%", height="80px"),
        )

        # Reanalysis button
        self.reanalysis_button = widgets.Button(
            description="🔄 Request Reanalysis",
            button_style="danger",
            tooltip="Request AI to reanalyze with your feedback",
            icon="refresh",
            layout=widgets.Layout(width="200px"),
        )
        self.reanalysis_button.on_click(self._on_reanalysis_clicked)

        # History viewer
        self.history_output = widgets.Output()

        # Iteration indicator
        self.iteration_indicator = widgets.HTML(
            value=self._get_iteration_html()
        )

        # Multi-turn status message
        self.multiturn_status = widgets.HTML(
            value='<div style="color: #5f6368; font-style: italic;">Ready for feedback</div>'
        )

    def _get_iteration_html(self) -> str:
        """Get HTML for iteration indicator."""
        return f'''
        <div style="background: #e3f2fd; padding: 8px 16px; border-radius: 4px;
                    border-left: 4px solid #1976d2; margin: 8px 0;">
            <span style="font-weight: bold; color: #1565c0;">
                Iteration {self.current_iteration}
            </span>
            <span style="color: #5f6368; margin-left: 12px;">
                {len(self.feedback_history)} previous feedback cycle(s)
            </span>
        </div>
        '''

    def _on_reanalysis_clicked(self, button):
        """Handle reanalysis button click."""
        try:
            # Build feedback summary from review table
            feedback_summary = self._build_feedback_summary()

            # Parse focus genes
            focus_genes = []
            if self.focus_genes_input.value.strip():
                focus_genes = [g.strip().upper() for g in self.focus_genes_input.value.split(",")]

            # Parse additional evidence
            additional_evidence = {}
            if self.additional_evidence_textarea.value.strip():
                additional_evidence = {
                    "clinical_notes": self.additional_evidence_textarea.value,
                    "added_at": datetime.now().isoformat(),
                }

            # Build confidence adjustments from review
            confidence_adjustments = {}
            for row in self.review_table.review_rows:
                if abs(row.confidence_slider.value - row.confidence) > 0.01:
                    confidence_adjustments[row.disease_name] = row.confidence_slider.value

            # Create reanalysis request
            request = ReanalysisRequest(
                request_type=ReanalysisRequestType(self.reanalysis_type_dropdown.value),
                feedback_summary=feedback_summary,
                clinician_guidance=self.guidance_textarea.value,
                focus_genes=focus_genes,
                additional_evidence=additional_evidence,
                confidence_adjustments=confidence_adjustments,
            )
            request.iteration = self.current_iteration

            # Save feedback to history
            self._save_feedback_to_history(request)

            # Save request to file
            request_file = self._save_reanalysis_request(request)

            # Update status
            self.multiturn_status.value = f'''
            <div style="color: #ff9800; font-weight: bold;">
                🔄 Reanalysis requested (saved to {request_file.name})
            </div>
            '''

            # Call callback if provided
            if self.reanalysis_callback:
                self.reanalysis_callback(request)
                self.multiturn_status.value = f'''
                <div style="color: #4caf50; font-weight: bold;">
                    ✓ Reanalysis triggered - waiting for results...
                </div>
                '''

            # Increment iteration
            self.current_iteration += 1
            self.iteration_indicator.value = self._get_iteration_html()

            # Update history display
            self._update_history_display()

        except Exception as e:
            self.multiturn_status.value = f'''
            <div style="color: #f44336; font-weight: bold;">
                ✗ Error creating request: {str(e)}
            </div>
            '''

    def _build_feedback_summary(self) -> Dict[str, Any]:
        """Build summary of current feedback state."""
        summary = {
            "iteration": self.current_iteration,
            "timestamp": datetime.now().isoformat(),
            "diagnoses_reviewed": len(self.review_table.review_rows),
            "marked_correct": [],
            "marked_incorrect": [],
            "confidence_adjustments": [],
            "clinical_notes": [],
        }

        for row in self.review_table.review_rows:
            diagnosis_info = {
                "disease": row.disease_name,
                "omim_id": row.omim_id,
                "original_confidence": row.confidence,
                "adjusted_confidence": row.confidence_slider.value,
            }

            if row.correct_checkbox.value:
                summary["marked_correct"].append(diagnosis_info)
            else:
                summary["marked_incorrect"].append(diagnosis_info)

            if abs(row.confidence_slider.value - row.confidence) > 0.01:
                summary["confidence_adjustments"].append({
                    **diagnosis_info,
                    "delta": row.confidence_slider.value - row.confidence,
                })

            if row.comments_textarea.value.strip():
                summary["clinical_notes"].append({
                    "disease": row.disease_name,
                    "note": row.comments_textarea.value,
                })

        return summary

    def _save_feedback_to_history(self, request: ReanalysisRequest):
        """Save current feedback to history."""
        history_entry = {
            "iteration": self.current_iteration,
            "timestamp": datetime.now().isoformat(),
            "request": request.to_dict(),
            "annotations": [row.get_annotation() for row in self.review_table.review_rows],
        }
        self.feedback_history.append(history_entry)
        self._save_history()

    def _save_reanalysis_request(self, request: ReanalysisRequest) -> Path:
        """Save reanalysis request to file."""
        request_dir = self.outputs_dir / "feedback" / "reanalysis_requests"
        request_dir.mkdir(parents=True, exist_ok=True)

        request_file = request_dir / f"reanalysis_request_iter{self.current_iteration}.json"
        with open(request_file, "w") as f:
            json.dump(request.to_dict(), f, indent=2)

        return request_file

    def _save_history(self):
        """Save feedback history to file."""
        history_dir = self.outputs_dir / "feedback"
        history_dir.mkdir(parents=True, exist_ok=True)

        history_file = history_dir / "feedback_history.json"
        with open(history_file, "w") as f:
            json.dump({
                "current_iteration": self.current_iteration,
                "history": self.feedback_history,
            }, f, indent=2)

    def _load_history(self):
        """Load feedback history if it exists."""
        history_file = self.outputs_dir / "feedback" / "feedback_history.json"
        if history_file.exists():
            with open(history_file, "r") as f:
                data = json.load(f)
                self.current_iteration = data.get("current_iteration", 1)
                self.feedback_history = data.get("history", [])
                self.iteration_indicator.value = self._get_iteration_html()

    def _update_history_display(self):
        """Update the history display widget."""
        self.history_output.clear_output()
        with self.history_output:
            if not self.feedback_history:
                display(HTML('<div style="color: #5f6368;">No feedback history yet.</div>'))
                return

            html = '<div style="max-height: 300px; overflow-y: auto;">'
            for entry in reversed(self.feedback_history[-5:]):  # Show last 5
                iter_num = entry.get("iteration", "?")
                timestamp = entry.get("timestamp", "")[:19]
                req_type = entry.get("request", {}).get("request_type", "unknown")
                correct = len(entry.get("request", {}).get("feedback_summary", {}).get("marked_correct", []))
                incorrect = len(entry.get("request", {}).get("feedback_summary", {}).get("marked_incorrect", []))

                html += f'''
                <div style="background: #f5f5f5; padding: 8px; margin: 4px 0;
                            border-radius: 4px; border-left: 3px solid #1976d2;">
                    <div style="font-weight: bold; color: #212121;">
                        Iteration {iter_num}
                    </div>
                    <div style="font-size: 0.9em; color: #5f6368;">
                        {timestamp} | Type: {req_type}<br>
                        Correct: {correct} | Incorrect: {incorrect}
                    </div>
                </div>
                '''
            html += '</div>'
            display(HTML(html))

    def refresh_after_reanalysis(self):
        """Refresh the interface after reanalysis completes."""
        # Reload the diagnosis data
        self.review_table.refresh()

        # Clear guidance inputs
        self.guidance_textarea.value = ""
        self.focus_genes_input.value = ""
        self.additional_evidence_textarea.value = ""

        # Update status
        self.multiturn_status.value = '''
        <div style="color: #4caf50; font-weight: bold;">
            ✓ Reanalysis complete - review updated diagnoses below
        </div>
        '''

        # Update history
        self._update_history_display()

    def get_widget(self) -> widgets.Widget:
        """Get the complete multi-turn review widget."""

        # Header for multi-turn section
        multiturn_header = widgets.HTML(
            value='''
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
                        color: white; padding: 12px; border-radius: 4px; margin: 16px 0 8px 0;">
                <h3 style="margin: 0 0 4px 0;">🔄 Multi-Turn Feedback & Reanalysis</h3>
                <p style="margin: 0; opacity: 0.9; font-size: 0.95em;">
                    Request the AI to reanalyze with your corrections and guidance.
                    Your feedback will improve the diagnostic accuracy.
                </p>
            </div>
            '''
        )

        # Reanalysis options panel
        reanalysis_panel = widgets.VBox([
            self.iteration_indicator,

            widgets.HTML(value='<div style="font-weight: bold; margin: 12px 0 4px 0; color: #212121;">Reanalysis Type:</div>'),
            self.reanalysis_type_dropdown,

            widgets.HTML(value='<div style="font-weight: bold; margin: 12px 0 4px 0; color: #212121;">Clinical Guidance for AI:</div>'),
            self.guidance_textarea,

            widgets.HTML(value='<div style="font-weight: bold; margin: 12px 0 4px 0; color: #212121;">Focus on Genes (optional):</div>'),
            self.focus_genes_input,

            widgets.HTML(value='<div style="font-weight: bold; margin: 12px 0 4px 0; color: #212121;">Additional Evidence (optional):</div>'),
            self.additional_evidence_textarea,

            widgets.HBox([
                self.reanalysis_button,
                self.multiturn_status,
            ], layout=widgets.Layout(gap="16px", margin="12px 0", align_items="center")),
        ], layout=widgets.Layout(
            background="#fff",
            padding="16px",
            border="2px solid #ff6b6b",
            border_radius="4px",
            margin="8px 0",
        ))

        # History panel
        history_panel = widgets.VBox([
            widgets.HTML(value='<div style="font-weight: bold; margin-bottom: 8px; color: #212121;">📜 Feedback History:</div>'),
            self.history_output,
        ], layout=widgets.Layout(
            background="#fafafa",
            padding="12px",
            border="1px solid #dee2e6",
            border_radius="4px",
            margin="8px 0",
        ))

        # Initialize history display
        self._update_history_display()

        # Combine with base review table
        return widgets.VBox([
            self.review_table.get_widget(),
            widgets.HTML(value='<hr style="margin: 24px 0; border-color: #dee2e6;">'),
            multiturn_header,
            reanalysis_panel,
            history_panel,
        ])


def create_multiturn_review_interface(
    outputs_dir: Path,
    reanalysis_callback: Optional[Callable[[ReanalysisRequest], None]] = None,
) -> MultiTurnReviewInterface:
    """
    Create a multi-turn diagnosis review interface with reanalysis support.

    Args:
        outputs_dir: Path to the pipeline outputs directory
        reanalysis_callback: Optional callback to trigger reanalysis

    Returns:
        MultiTurnReviewInterface widget

    Example:
        >>> from code.ui.review_interface import create_multiturn_review_interface
        >>>
        >>> def on_reanalysis(request):
        ...     print(f"Reanalysis requested: {request.request_type}")
        ...     # Trigger pipeline rerun here
        ...
        >>> review = create_multiturn_review_interface(
        ...     Path('outputs'),
        ...     reanalysis_callback=on_reanalysis
        ... )
        >>> display(review.get_widget())
    """
    return MultiTurnReviewInterface(outputs_dir, reanalysis_callback)
