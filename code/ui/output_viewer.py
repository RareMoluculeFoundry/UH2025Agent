"""
Output Viewer Module for UH2025Agent Topology

This module provides a tabbed interface for browsing pipeline outputs.
Displays regulatory analysis, pathogenicity scores, differential diagnosis, tool calls, and clinical reports.

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import pandas as pd
import ipywidgets as widgets
from IPython.display import display
import matplotlib.pyplot as plt
import seaborn as sns

# Import markdown with fallback
try:
    import markdown
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    print("Warning: markdown library not available, using plain text fallback")

# Import review interface
from .review_interface import DiagnosisReviewTable

class OutputTab:
    """Tab for displaying a single output type."""

    def __init__(self, tab_name: str, output_path: Path, display_type: str = 'json'):
        """
        Initialize output tab.

        Args:
            tab_name: Name of the tab
            output_path: Path to output file
            display_type: Type of display ('json', 'table', 'markdown', 'chart')
        """
        self.tab_name = tab_name
        self.output_path = output_path
        self.display_type = display_type
        self.container = None
        self._build_interface()

    def _build_interface(self):
        """Build the tab interface."""
        # Header
        header = widgets.HTML(
            value=f'<h3 style="margin-top: 0; color: #667eea;">{self.tab_name}</h3>'
        )

        # Status indicator
        self.status = widgets.HTML(value=self._get_status_html())

        # Refresh button
        self.refresh_button = widgets.Button(
            description='🔄 Refresh',
            button_style='info',
            layout=widgets.Layout(width='120px')
        )
        self.refresh_button.on_click(lambda b: self.refresh())

        # Download button
        self.download_button = widgets.Button(
            description='💾 Download',
            button_style='',
            layout=widgets.Layout(width='120px')
        )
        self.download_button.on_click(lambda b: self._download_output())

        # Button container
        button_box = widgets.HBox([
            self.refresh_button,
            self.download_button
        ], layout=widgets.Layout(padding='5px'))

        # Content area
        self.content = widgets.Output(
            layout=widgets.Layout(
                width='100%',
                height='500px',
                overflow_y='auto',
                border='1px solid #dee2e6',
                padding='10px'
            )
        )

        # Build container
        self.container = widgets.VBox([
            header,
            self.status,
            button_box,
            self.content
        ], layout=widgets.Layout(padding='20px'))

        # Initial load
        self.refresh()

    def _get_status_html(self) -> str:
        """Get status HTML based on file existence."""
        if self.output_path.exists():
            return '<p style="color: green;">✓ Output available</p>'
        else:
            return '<p style="color: gray;">⚠ No output yet - run pipeline to generate</p>'

    def refresh(self):
        """Refresh the output display."""
        self.status.value = self._get_status_html()

        with self.content:
            self.content.clear_output(wait=True)

            if not self.output_path.exists():
                print(f"⚠ Output file not found: {self.output_path.name}")
                print(f"Run the pipeline to generate this output.")
                return

            try:
                if self.display_type == 'json':
                    self._display_json()
                elif self.display_type == 'table':
                    self._display_table()
                elif self.display_type == 'markdown':
                    self._display_markdown()
                elif self.display_type == 'chart':
                    self._display_chart()
                else:
                    print(f"Unknown display type: {self.display_type}")
            except Exception as e:
                print(f"❌ Error loading output: {str(e)}")

    def _display_json(self):
        """Display JSON output as formatted text."""
        with open(self.output_path, 'r') as f:
            data = json.load(f)

        # Pretty print JSON
        print(json.dumps(data, indent=2))

    def _display_table(self):
        """Display JSON output as styled HTML table."""
        with open(self.output_path, 'r') as f:
            data = json.load(f)

        # Handle different data structures
        if 'differential_diagnosis' in data:
            self._display_differential_diagnosis(data)
        elif 'tool_calls' in data:
            self._display_tool_calls(data)
        elif 'regulatory_analysis' in data:
            self._display_regulatory_analysis(data)
        elif 'pathogenicity_scores' in data:
            self._display_pathogenicity_scores(data)
        else:
            # Generic table display
            df = pd.DataFrame(data)
            display(df)

    def _display_differential_diagnosis(self, data: Dict):
        """Display differential diagnosis with styling."""
        diagnoses = data['differential_diagnosis']

        # Create DataFrame
        df = pd.DataFrame(diagnoses)
        if 'confidence' in df.columns:
            df['confidence'] = df['confidence'].apply(lambda x: f"{x:.1%}")

        # Style and display
        html_table = df.to_html(
            index=False,
            classes='table',
            escape=False,
            columns=['disease', 'confidence', 'omim_id', 'genes', 'inheritance_pattern']
        )

        styled_html = f"""
        <style>
            .table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 1.05em;
                color: #212529;
                background-color: white;
            }}
            .table thead tr {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: left;
                font-weight: bold;
            }}
            .table th, .table td {{
                padding: 12px 16px;
                border: 1px solid #dee2e6;
            }}
            .table tbody tr:nth-of-type(even) {{
                background-color: #f8f9fa;
            }}
            .table tbody tr:hover {{
                background-color: #e3f2fd;
            }}
            .table tbody tr:first-of-type {{
                background-color: #bbdefb;
                font-weight: bold;
                border-left: 5px solid #1976d2;
            }}
        </style>
        {html_table}
        """

        display(widgets.HTML(value=styled_html))

    def _display_tool_calls(self, data: Dict):
        """Display tool calls with priority indicators."""
        tool_calls = data['tool_calls']

        html = '<div style="padding: 10px;">'
        for idx, call in enumerate(tool_calls, 1):
            priority = call.get('priority', 'medium').lower()
            color = {'high': '#d32f2f', 'medium': '#f57c00', 'low': '#388e3c'}.get(priority, '#757575')

            html += f"""
            <div style="margin-bottom: 15px; padding: 12px; border-left: 4px solid {color}; background-color: #f8f9fa;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 1.1em;">{idx}. {call.get('tool_name', 'Unknown')}</strong>
                    <span style="background-color: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.9em;">
                        {priority.upper()}
                    </span>
                </div>
                <div style="margin-top: 8px; color: #555;">
                    <strong>Parameters:</strong> {json.dumps(call.get('parameters', {}), indent=2)}
                </div>
                <div style="margin-top: 8px; color: #666; font-style: italic;">
                    {call.get('rationale', '')}
                </div>
            </div>
            """

        html += '</div>'
        display(widgets.HTML(value=html))

    def _display_regulatory_analysis(self, data: Dict):
        """Display regulatory analysis results."""
        analysis = data.get('regulatory_analysis', [])
        df = pd.DataFrame(analysis)

        if not df.empty and 'regulatory_impact_score' in df.columns:
            # Sort by impact score
            df = df.sort_values('regulatory_impact_score', ascending=False)

        display(df)

    def _display_pathogenicity_scores(self, data: Dict):
        """Display pathogenicity scores."""
        scores = data.get('pathogenicity_scores', [])
        df = pd.DataFrame(scores)

        if not df.empty:
            # Color code by classification
            display(df)

    def _display_markdown(self):
        """Display markdown content."""
        with open(self.output_path, 'r') as f:
            content = f.read()

        # Check if this is a clinical report - if so, use interactive display
        if 'clinical_report' in self.output_path.name.lower():
            self._display_clinical_report_interactive(content)
        else:
            display(widgets.HTML(value=f'<pre style="white-space: pre-wrap;">{content}</pre>'))

    def _parse_report_sections(self, content: str) -> List[Dict[str, str]]:
        """
        Parse markdown report into sections based on # headers.

        Returns:
            List of dictionaries with 'title' and 'content' keys
        """
        sections = []
        current_section = None
        current_content = []

        for line in content.split('\n'):
            # Check for top-level header (# Header)
            if line.startswith('# ') and not line.startswith('##'):
                # Save previous section if exists
                if current_section:
                    sections.append({
                        'title': current_section,
                        'content': '\n'.join(current_content).strip()
                    })

                # Start new section
                current_section = line[2:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections.append({
                'title': current_section,
                'content': '\n'.join(current_content).strip()
            })

        return sections

    def _display_clinical_report_interactive(self, content: str):
        """
        Display clinical report with interactive feedback UI.

        Each section has:
        - Collapsible content display
        - Feedback buttons (Accurate / Needs Revision / Incorrect)
        - Comment box
        - Border color based on feedback
        """
        from IPython.display import display
        import ipywidgets as widgets
        import markdown

        sections = self._parse_report_sections(content)
        section_widgets = []
        feedback_data = {}

        # Instructions header
        instructions = widgets.HTML(
            value='''
            <div style="background: #ffffff; padding: 16px; border-radius: 4px; margin-bottom: 16px;
                        border: 2px solid #1976d2; border-left: 6px solid #1976d2;">
                <div style="font-weight: bold; margin-bottom: 8px; color: #212121; font-size: 1.05em;">
                    📝 Clinician Feedback Interface
                </div>
                <div style="color: #212121; line-height: 1.6;">
                    Review each section of the AI-generated report and provide feedback to improve
                    future diagnostic reasoning. Your input will help refine the model's clinical judgment.
                </div>
            </div>
            '''
        )

        section_widgets.append(instructions)

        for idx, section in enumerate(sections):
            section_id = f"section_{idx}"

            # Feedback toggle buttons
            feedback_toggle = widgets.ToggleButtons(
                options=['✓ Accurate', '⚠ Needs Revision', '✗ Incorrect'],
                description='',
                disabled=False,
                button_style='',
                tooltips=['Clinically sound reasoning', 'Minor issues to address', 'Significant problems'],
                layout=widgets.Layout(width='400px')
            )

            # Comment box (initially hidden)
            comment_box = widgets.Textarea(
                value='',
                placeholder='Explain your feedback: What needs improvement? What was incorrect?',
                description='',
                layout=widgets.Layout(width='100%', height='80px', display='none'),
                style={'background': 'white', 'text_color': '#212121'}
            )

            # Section content display - convert markdown to HTML
            if MARKDOWN_AVAILABLE:
                try:
                    section_html = markdown.markdown(section["content"], extensions=['tables', 'fenced_code'])
                except Exception as e:
                    # Fallback to plain text if markdown conversion fails
                    section_html = section["content"].replace('\n', '<br>')
            else:
                # Fallback to plain text if markdown library not available
                section_html = section["content"].replace('\n', '<br>')

            section_content = widgets.HTML(
                value=f'<div style="background-color: #ffffff; padding: 12px; line-height: 1.6; color: #212121;">{section_html}</div>'
            )

            # Container for this section (will change border color based on feedback)
            section_container = widgets.VBox([
                widgets.HTML(
                    value=f'''
                    <div style="background-color: #ffffff; font-weight: bold; font-size: 1.2em; color: #212121; margin-bottom: 12px;">
                        {section['title']}
                    </div>
                    '''
                ),
                section_content,
                widgets.HTML(value='<div style="background-color: #ffffff; margin-top: 12px; margin-bottom: 8px; color: #5f6368; font-weight: 600;">Feedback:</div>'),
                feedback_toggle,
                comment_box
            ], layout=widgets.Layout(
                border='2px solid #dee2e6',
                padding='16px',
                margin='12px 0',
                border_radius='4px',
                background='#ffffff'
            ))

            # Feedback change handler
            def make_feedback_handler(container, comment, toggle_btn, sec_id):
                def on_feedback_change(change):
                    if change['new'] == '✓ Accurate':
                        container.layout.border = '2px solid #2e7d32'
                        comment.layout.display = 'none'
                    elif change['new'] == '⚠ Needs Revision':
                        container.layout.border = '2px solid #f57c00'
                        comment.layout.display = 'block'
                    elif change['new'] == '✗ Incorrect':
                        container.layout.border = '2px solid #c62828'
                        comment.layout.display = 'block'

                    # Store feedback
                    feedback_data[sec_id] = {
                        'rating': change['new'],
                        'comment': comment.value
                    }
                return on_feedback_change

            feedback_toggle.observe(
                make_feedback_handler(section_container, comment_box, feedback_toggle, section_id),
                names='value'
            )

            section_widgets.append(section_container)

        # Save feedback button
        save_button = widgets.Button(
            description='💾 Save All Feedback',
            button_style='success',
            layout=widgets.Layout(width='200px', height='40px')
        )

        save_status = widgets.HTML(value='')

        def on_save_feedback(button):
            # Save feedback to file
            feedback_file = self.output_path.parent / 'report_feedback.json'
            import json
            from datetime import datetime

            feedback_export = {
                'report_file': str(self.output_path),
                'feedback_date': datetime.now().isoformat(),
                'sections': feedback_data
            }

            with open(feedback_file, 'w') as f:
                json.dump(feedback_export, f, indent=2)

            save_status.value = f'''
            <div style="background-color: #ffffff; color: #2e7d32; font-weight: bold; margin-top: 12px; padding: 8px; border-radius: 4px;">
                ✓ Feedback saved to {feedback_file.name}
            </div>
            '''

        save_button.on_click(on_save_feedback)

        section_widgets.append(widgets.HBox([save_button, save_status], layout=widgets.Layout(margin='20px 0')))

        # Display all widgets
        display(widgets.VBox(section_widgets))

    def _display_chart(self):
        """Display confidence score chart."""
        with open(self.output_path, 'r') as f:
            data = json.load(f)

        if 'differential_diagnosis' not in data:
            print("No differential diagnosis data available for chart")
            return

        diagnoses = data['differential_diagnosis']
        diseases = [d['disease'] for d in diagnoses]
        confidences = [d['confidence'] for d in diagnoses]

        fig, ax = plt.subplots(figsize=(12, 6))
        colors = sns.color_palette("viridis", len(diseases))
        bars = ax.barh(diseases, confidences, color=colors, edgecolor='black', linewidth=1.5)

        ax.set_xlabel('Confidence Score', fontsize=12, fontweight='bold')
        ax.set_title('Differential Diagnosis Confidence Scores', fontsize=14, fontweight='bold', pad=15)
        ax.set_xlim(0, 1)
        ax.grid(axis='x', alpha=0.3)

        # Add confidence values
        for bar, conf in zip(bars, confidences):
            ax.text(conf + 0.02, bar.get_y() + bar.get_height()/2,
                   f'{conf:.1%}', va='center', fontsize=11, fontweight='bold')

        plt.tight_layout()
        plt.show()

    def _download_output(self):
        """Handle download button click."""
        if not self.output_path.exists():
            print("⚠ No output file to download")
            return

        print(f"💾 Output file location: {self.output_path}")
        print(f"Copy this file to download: {self.output_path.absolute()}")

    def get_widget(self) -> widgets.VBox:
        """Get the widget container."""
        return self.container


class OutputBrowser:
    """Main output browser interface for pipeline results."""

    def __init__(self, outputs_dir: Path):
        """
        Initialize output browser.

        Args:
            outputs_dir: Path to outputs directory
        """
        self.outputs_dir = Path(outputs_dir)
        self.output_tabs = {}
        self.tab_widget = None
        self._define_outputs()
        self._build_interface()

    def _define_outputs(self):
        """Define output tabs and their configurations."""
        # Reordered to prioritize clinical outputs first
        self.outputs = {
            'Clinical Report': {
                'path': self.outputs_dir / '05_report' / 'clinical_report.md',
                'display': 'markdown'
            },
            'Differential Diagnosis & Review': {
                'path': self.outputs_dir / '03_differential' / 'differential_diagnosis.json',
                'display': 'review'
            },
            'Pathogenicity Scores': {
                'path': self.outputs_dir / '02_pathogenicity' / 'pathogenicity_scores.json',
                'display': 'json'
            },
            'Regulatory Analysis': {
                'path': self.outputs_dir / '01_regulatory' / 'regulatory_analysis.json',
                'display': 'json'
            },
            'Tool Calls': {
                'path': self.outputs_dir / '04_toolcalls' / 'tool_calls.json',
                'display': 'table'
            },
            'Confidence Chart': {
                'path': self.outputs_dir / '03_differential' / 'differential_diagnosis.json',
                'display': 'chart'
            }
        }

    def _build_interface(self):
        """Build the tabbed output browser interface."""
        # Create tab for each output
        tab_children = []
        tab_titles = []

        for output_name, output_config in self.outputs.items():
            # Handle review tab specially
            if output_config['display'] == 'review':
                # Create review interface directly
                if output_config['path'].exists():
                    try:
                        # Load tool calls data for context
                        tool_calls_file = self.outputs_dir / '04_toolcalls' / 'tool_calls.json'
                        tool_calls_data = None
                        if tool_calls_file.exists():
                            with open(tool_calls_file, 'r') as f:
                                tool_calls_data = json.load(f)

                        # Create review table
                        review_table = DiagnosisReviewTable(output_config['path'])
                        self.output_tabs[output_name] = review_table

                        # Add tool calls summary if available
                        if tool_calls_data:
                            tool_calls_summary = self._create_tool_calls_summary(tool_calls_data)

                            # Combine review table + tool calls summary
                            combined_widget = widgets.VBox([
                                review_table.get_widget(),
                                widgets.HTML(value='<hr style="margin: 30px 0;">'),
                                tool_calls_summary
                            ])
                            tab_children.append(combined_widget)
                        else:
                            tab_children.append(review_table.get_widget())

                    except Exception as e:
                        # If review interface fails, show error
                        error_widget = widgets.VBox([
                            widgets.HTML(value=f'<h3>{output_name}</h3>'),
                            widgets.HTML(value=f'<p style="color: #c62828;">Error creating review interface: {str(e)}</p>')
                        ], layout=widgets.Layout(padding='20px'))
                        tab_children.append(error_widget)
                else:
                    # No data yet
                    no_data_widget = widgets.VBox([
                        widgets.HTML(value=f'<h3>{output_name}</h3>'),
                        widgets.HTML(value='<p style="color: #5f6368;">⚠ No differential diagnosis data available. Run pipeline to generate.</p>')
                    ], layout=widgets.Layout(padding='20px'))
                    tab_children.append(no_data_widget)
            else:
                # Standard output tab
                tab = OutputTab(
                    output_name,
                    output_config['path'],
                    output_config['display']
                )
                self.output_tabs[output_name] = tab
                tab_children.append(tab.get_widget())

            tab_titles.append(output_name)

        # Create Tab widget
        self.tab_widget = widgets.Tab(children=tab_children)
        for i, title in enumerate(tab_titles):
            self.tab_widget.set_title(i, title)

        # Refresh all button
        self.refresh_all_button = widgets.Button(
            description='🔄 Refresh All Outputs',
            button_style='success',
            layout=widgets.Layout(width='200px', height='40px')
        )
        self.refresh_all_button.on_click(lambda b: self.refresh_all())

        # Button container
        button_box = widgets.HBox([
            self.refresh_all_button
        ], layout=widgets.Layout(padding='10px', justify_content='center'))

        # Main container
        self.container = widgets.VBox([
            widgets.HTML(value='<h2 style="text-align: center;">📊 Pipeline Outputs</h2>'),
            button_box,
            self.tab_widget
        ])

    def _create_tool_calls_summary(self, tool_calls_data: Dict) -> widgets.Widget:
        """Create tool calls summary widget for differential diagnosis context."""

        tool_calls = tool_calls_data.get('tool_calls', [])

        summary_html = '''
        <div style="background: #ffffff; padding: 20px; border: 2px solid #1976d2; border-radius: 4px;">
            <h3 style="color: #212121; margin-top: 0;">🔬 Evidence Validation - Tool Calls Summary</h3>
            <p style="color: #5f6368; line-height: 1.6;">
                These database queries were generated to validate the differential diagnoses above.
                They represent evidence-gathering steps to confirm or refute each hypothesis.
            </p>
        '''

        # Group tool calls by priority
        high_priority = [tc for tc in tool_calls if tc.get('priority') == 'high']
        medium_priority = [tc for tc in tool_calls if tc.get('priority') == 'medium']
        low_priority = [tc for tc in tool_calls if tc.get('priority') == 'low']

        for priority_level, calls in [('HIGH', high_priority), ('MEDIUM', medium_priority), ('LOW', low_priority)]:
            if calls:
                color = {'HIGH': '#d32f2f', 'MEDIUM': '#f57c00', 'LOW': '#388e3c'}[priority_level]
                summary_html += f'''
                <div style="margin-top: 20px;">
                    <h4 style="color: {color};">{priority_level} Priority Calls ({len(calls)})</h4>
                '''

                for call in calls:
                    summary_html += f'''
                    <div style="background: #f8f9fa; padding: 12px; margin: 8px 0; border-left: 4px solid {color}; border-radius: 4px;">
                        <div style="display: flex; justify-content: space-between;">
                            <strong style="color: #212121;">{call.get('tool', 'Unknown')}</strong>
                            <span style="background: {color}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.85em;">
                                {priority_level}
                            </span>
                        </div>
                        <div style="color: #5f6368; margin-top: 8px; font-size: 0.95em;">
                            <strong>Query:</strong> {call.get('query', 'N/A')}
                        </div>
                        <div style="color: #5f6368; margin-top: 4px; font-size: 0.9em; font-style: italic;">
                            {call.get('rationale', '')}
                        </div>
                    </div>
                    '''

                summary_html += '</div>'

        summary_html += '''
            <div style="background: #e8f5e9; padding: 12px; border-radius: 4px; margin-top: 20px; border-left: 4px solid #2e7d32;">
                <strong style="color: #212121;">💡 Clinical Interpretation:</strong>
                <p style="color: #5f6368; margin-top: 8px; line-height: 1.6;">
                    High-priority calls validate core diagnostic hypotheses. Medium-priority provide supporting context.
                    Low-priority offer background information. Review these queries to understand the evidence base
                    supporting each differential diagnosis above.
                </p>
            </div>
        </div>
        '''

        return widgets.HTML(value=summary_html)

    def refresh_all(self):
        """Refresh all output tabs."""
        for tab in self.output_tabs.values():
            tab.refresh()

    def display(self):
        """Display the output browser interface."""
        display(self.container)

    def get_widget(self) -> widgets.VBox:
        """Get the widget container for embedding."""
        return self.container
