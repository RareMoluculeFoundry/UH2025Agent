"""
Widgets Module for UH2025Agent Topology

Reusable widget components for the configurator and runtime interfaces.

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from pathlib import Path
from typing import List, Optional, Callable
from datetime import datetime
import json
import ipywidgets as widgets
from IPython.display import display


class PatientSelector:
    """Widget for selecting patient and viewing their data."""

    def __init__(self, data_dir: Path, on_change: Optional[Callable] = None):
        """
        Initialize patient selector.

        Args:
            data_dir: Path to Data directory containing patient folders
            on_change: Callback function when patient changes
        """
        self.data_dir = Path(data_dir)
        self.on_change_callback = on_change
        self.current_patient = None
        self._build_interface()

    def _get_patients(self) -> List[str]:
        """Get list of available patients."""
        if not self.data_dir.exists():
            return []
        return [
            d.name for d in self.data_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

    def _build_interface(self):
        """Build the patient selector interface with tabbed display."""
        patients = self._get_patients()

        # Patient dropdown
        self.selector = widgets.Dropdown(
            options=patients,
            value=patients[0] if patients else None,
            description='Patient:',
            style={'description_width': '100px'},
            layout=widgets.Layout(width='400px')
        )
        self.selector.observe(self._on_patient_change, names='value')

        # Status display
        self.status = widgets.HTML(
            value='<p style="color: #5f6368;">Select a patient to begin</p>'
        )

        # Create tabbed content viewers
        self._create_tab_widgets()

        # Container with header + tabs
        self.container = widgets.VBox([
            widgets.HTML(value='<h3 style="color: #212121;">📋 Patient Selection</h3>'),
            self.selector,
            self.status,
            widgets.HTML(value='<hr style="margin: 16px 0;">'),
            self.tab_widget
        ])

        # Load initial patient
        if patients:
            self._load_patient_data()

    def _create_tab_widgets(self):
        """Create tabbed content display for patient data."""

        # Tab 1: Clinical Summary (HTML with markdown rendering)
        self.clinical_viewer = widgets.HTML(
            value='<div style="background: #ffffff; color: #212121; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; line-height: 1.6;">No patient selected</div>',
            layout=widgets.Layout(width='100%')
        )

        clinical_tab = widgets.VBox([
            widgets.HTML(value='<h4 style="color: #212121; margin: 0 0 12px 0;">Clinical Summary</h4>'),
            self.clinical_viewer
        ])

        # Tab 2: Genomic Variants (formatted JSON)
        self.genomic_viewer = widgets.HTML(
            value='<div style="background: #ffffff; color: #212121; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; font-family: monospace; white-space: pre-wrap; font-size: 0.9em;">No patient selected</div>',
            layout=widgets.Layout(width='100%')
        )

        genomic_tab = widgets.VBox([
            widgets.HTML(value='<h4 style="color: #212121; margin: 0 0 12px 0;">Genomic Variants</h4>'),
            self.genomic_viewer
        ])

        # Tab 3: Patient Overview (combined summary)
        self.overview_viewer = widgets.HTML(
            value='<div style="background: #ffffff; color: #212121; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; line-height: 1.6;">No patient selected</div>',
            layout=widgets.Layout(width='100%')
        )

        overview_tab = widgets.VBox([
            widgets.HTML(value='<h4 style="color: #212121; margin: 0 0 12px 0;">Patient Overview</h4>'),
            self.overview_viewer
        ])

        # Create Tab widget
        self.tab_widget = widgets.Tab(
            children=[clinical_tab, genomic_tab, overview_tab]
        )
        self.tab_widget.set_title(0, '📄 Clinical Summary')
        self.tab_widget.set_title(1, '🧬 Genomic Data')
        self.tab_widget.set_title(2, '📊 Overview')

    def _on_patient_change(self, change):
        """Handle patient selection change."""
        self._load_patient_data()
        if self.on_change_callback:
            self.on_change_callback(self.selector.value)

    def _load_patient_data(self):
        """Load patient clinical and genomic data with rich formatting."""
        patient_id = self.selector.value
        if not patient_id:
            return

        self.current_patient = patient_id
        patient_dir = self.data_dir / patient_id

        # Load clinical summary
        clinical_file = patient_dir / f"{patient_id.lower()}_Clinical.md"
        clinical_content = ""
        if clinical_file.exists():
            with open(clinical_file, 'r') as f:
                clinical_content = f.read()

            # Tab 1: Clinical Summary with markdown rendering
            try:
                import markdown
                clinical_html = markdown.markdown(
                    clinical_content,
                    extensions=['tables', 'fenced_code', 'nl2br']
                )
            except:
                # Fallback to simple line breaks
                clinical_html = clinical_content.replace('\n', '<br>')

            self.clinical_viewer.value = f'<div style="background: #ffffff; color: #212121; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; line-height: 1.6;">{clinical_html}</div>'
            self.status.value = f'<p style="color: #2e7d32;">✓ Loaded data for {patient_id}</p>'
        else:
            self.clinical_viewer.value = '<div style="background: #ffffff; color: #c62828; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px;">Clinical summary not found.</div>'
            self.status.value = f'<p style="color: #f57c00;">⚠ Clinical data not found</p>'

        # Load genomic data
        genomic_file = patient_dir / f"{patient_id.lower()}_Genomic.json"
        genomic_data = {}
        if genomic_file.exists():
            with open(genomic_file, 'r') as f:
                genomic_data = json.load(f)

            # Tab 2: Genomic Variants with formatted JSON
            genomic_json = json.dumps(genomic_data, indent=2)
            self.genomic_viewer.value = f'<div style="background: #ffffff; color: #212121; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; font-family: monospace; white-space: pre-wrap; font-size: 0.9em;">{genomic_json}</div>'
        else:
            self.genomic_viewer.value = '<div style="background: #ffffff; color: #c62828; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; font-family: monospace;">Genomic data not found.</div>'

        # Tab 3: Patient Overview (summary statistics)
        num_variants = len(genomic_data.get('variants', []))
        clinical_preview = clinical_content[:300] if clinical_content else "No clinical data available"

        overview_html = f'''
        <div style="background: #ffffff; color: #212121; padding: 16px; border: 2px solid #dee2e6; border-radius: 4px; min-height: 300px; line-height: 1.8;">
            <h4 style="color: #1976d2; margin-top: 0;">Patient: {patient_id}</h4>

            <div style="background: #e3f2fd; padding: 12px; border-radius: 4px; margin: 12px 0; border-left: 4px solid #1976d2;">
                <strong style="color: #212121;">Quick Stats:</strong><br>
                <span style="color: #5f6368;">• Total Variants: <strong style="color: #212121;">{num_variants}</strong></span><br>
                <span style="color: #5f6368;">• Data Source: VCF + Clinical Records</span><br>
                <span style="color: #5f6368;">• Status: Ready for analysis</span>
            </div>

            <div style="margin-top: 16px;">
                <strong style="color: #212121;">Clinical Summary Preview:</strong><br>
                <div style="color: #5f6368; font-style: italic; margin-top: 8px; padding: 12px; background: #f8f9fa; border-radius: 4px;">
                    {clinical_preview}...
                </div>
            </div>
        </div>
        '''
        self.overview_viewer.value = overview_html

    def get_patient_id(self) -> Optional[str]:
        """Get currently selected patient ID."""
        return self.current_patient

    def get_widget(self) -> widgets.VBox:
        """Get the widget container."""
        return self.container


class ProgressTracker:
    """Widget for tracking pipeline execution progress."""

    def __init__(self, total_stages: int = 5):
        """
        Initialize progress tracker.

        Args:
            total_stages: Total number of pipeline stages
        """
        self.total_stages = total_stages
        self._build_interface()

    def _build_interface(self):
        """Build the progress tracker interface."""
        # Progress bar
        self.progress_bar = widgets.IntProgress(
            value=0,
            min=0,
            max=self.total_stages,
            description='Progress:',
            bar_style='info',
            layout=widgets.Layout(width='100%')
        )

        # Execution log - using HTML for explicit styling (works in light/dark themes)
        self.log = widgets.HTML(
            value='<div style="background: #ffffff; color: #212121; padding: 12px; height: 200px; overflow-y: auto; border: 2px solid #dee2e6; border-radius: 4px; font-family: monospace; white-space: pre-wrap; line-height: 1.4;"></div>',
            layout=widgets.Layout(width='100%')
        )
        self.log_messages = []  # Track log messages

        # Container
        self.container = widgets.VBox([
            self.progress_bar,
            widgets.HTML(value='<h4 style="color: #212121;">Execution Log</h4>'),
            self.log
        ])

    def update_progress(self, current: int, total: int, message: str):
        """
        Update progress bar.

        Args:
            current: Current stage number
            total: Total stages
            message: Progress message
        """
        self.progress_bar.value = current
        self.progress_bar.max = total

    def log_message(self, message: str):
        """
        Add a message to the execution log.

        Args:
            message: Log message
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")

        # Rebuild HTML with explicit styling for readability
        log_content = '<br>'.join(self.log_messages)
        self.log.value = f'<div style="background: #ffffff; color: #212121; padding: 12px; height: 200px; overflow-y: auto; border: 2px solid #dee2e6; border-radius: 4px; font-family: monospace; white-space: pre-wrap; line-height: 1.4;">{log_content}</div>'

    def reset(self):
        """Reset progress and clear log."""
        self.progress_bar.value = 0
        self.log_messages = []
        self.log.value = '<div style="background: #ffffff; color: #212121; padding: 12px; height: 200px; overflow-y: auto; border: 2px solid #dee2e6; border-radius: 4px; font-family: monospace; white-space: pre-wrap; line-height: 1.4;"></div>'

    def get_widget(self) -> widgets.VBox:
        """Get the widget container."""
        return self.container


class StatusDisplay:
    """Simple status message display widget."""

    def __init__(self, initial_message: str = '', initial_color: str = 'gray'):
        """
        Initialize status display.

        Args:
            initial_message: Initial status message
            initial_color: Initial text color
        """
        self.widget = widgets.HTML(
            value=self._format_message(initial_message, initial_color)
        )

    def _format_message(self, message: str, color: str) -> str:
        """Format message with HTML styling."""
        return f'<p style="text-align: center; color: {color}; font-size: 1.1em; padding: 10px;">{message}</p>'

    def update(self, message: str, color: str = 'gray'):
        """
        Update status message.

        Args:
            message: New status message
            color: Text color (gray, green, red, orange, blue)
        """
        self.widget.value = self._format_message(message, color)

    def success(self, message: str):
        """Display success message."""
        self.update(message, 'green')

    def error(self, message: str):
        """Display error message."""
        self.update(message, 'red')

    def warning(self, message: str):
        """Display warning message."""
        self.update(message, 'orange')

    def info(self, message: str):
        """Display info message."""
        self.update(message, 'blue')

    def get_widget(self) -> widgets.HTML:
        """Get the widget."""
        return self.widget


class RunButton:
    """Styled run button for pipeline execution."""

    def __init__(
        self,
        description: str = '▶ Run Diagnostic Pipeline',
        on_click: Optional[Callable] = None
    ):
        """
        Initialize run button.

        Args:
            description: Button label
            on_click: Click handler function
        """
        self.button = widgets.Button(
            description=description,
            button_style='success',
            layout=widgets.Layout(width='300px', height='50px'),
            style={'font_weight': 'bold'}
        )

        if on_click:
            self.button.on_click(on_click)

        self.initial_description = description

    def set_running(self):
        """Set button to running state."""
        self.button.description = '⏸ Running...'
        self.button.button_style = 'warning'
        self.button.disabled = True

    def set_ready(self):
        """Set button to ready state."""
        self.button.description = self.initial_description
        self.button.button_style = 'success'
        self.button.disabled = False

    def set_complete(self):
        """Set button to complete state."""
        self.button.description = '✓ Complete'
        self.button.button_style = 'success'
        self.button.disabled = False

    def get_widget(self) -> widgets.Button:
        """Get the button widget."""
        return self.button
