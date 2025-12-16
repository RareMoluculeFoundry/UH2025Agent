"""
Configurator Module for UH2025Agent Topology

This module provides a tabbed interface for configuring all pipeline parameters.
Generates configuration objects compatible with Kubeflow, Elyra, and local execution.

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from pathlib import Path
from typing import Dict, Any, Optional
import yaml
import ipywidgets as widgets
from IPython.display import display

class ModuleConfigTab:
    """Configuration tab for a single module in the pipeline."""

    def __init__(self, module_name: str, module_params: Dict[str, Any]):
        """
        Initialize module configuration tab.

        Args:
            module_name: Name of the module
            module_params: Dictionary of parameter definitions
        """
        self.module_name = module_name
        self.module_params = module_params
        self.widgets = {}
        self._build_widgets()

    def _build_widgets(self):
        """Build ipywidgets for each parameter."""
        widget_list = []

        # Module header
        header = widgets.HTML(
            value=f'<h3 style="margin-top: 0; color: #667eea;">{self.module_name}</h3>'
        )
        widget_list.append(header)

        # Create widget for each parameter
        for param_name, param_config in self.module_params.items():
            param_type = param_config.get('type', 'text')
            default = param_config.get('default', '')
            description = param_config.get('description', param_name)
            options = param_config.get('options', None)
            min_val = param_config.get('min', None)
            max_val = param_config.get('max', None)
            step = param_config.get('step', None)

            # Create appropriate widget based on type
            if param_type == 'float':
                widget = widgets.FloatSlider(
                    value=default,
                    min=min_val if min_val is not None else 0.0,
                    max=max_val if max_val is not None else 1.0,
                    step=step if step is not None else 0.01,
                    description=description,
                    style={'description_width': '200px'},
                    layout=widgets.Layout(width='600px')
                )
            elif param_type == 'int':
                widget = widgets.IntSlider(
                    value=default,
                    min=min_val if min_val is not None else 1,
                    max=max_val if max_val is not None else 100,
                    step=step if step is not None else 1,
                    description=description,
                    style={'description_width': '200px'},
                    layout=widgets.Layout(width='600px')
                )
            elif param_type == 'bool':
                widget = widgets.Checkbox(
                    value=default,
                    description=description,
                    style={'description_width': '200px'},
                    layout=widgets.Layout(width='600px')
                )
            elif param_type == 'dropdown' and options:
                widget = widgets.Dropdown(
                    options=options,
                    value=default,
                    description=description,
                    style={'description_width': '200px'},
                    layout=widgets.Layout(width='600px')
                )
            else:  # text
                widget = widgets.Text(
                    value=str(default),
                    description=description,
                    style={'description_width': '200px'},
                    layout=widgets.Layout(width='600px')
                )

            self.widgets[param_name] = widget
            widget_list.append(widget)

        # Create VBox container
        self.container = widgets.VBox(
            widget_list,
            layout=widgets.Layout(padding='20px')
        )

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration values."""
        config = {}
        for param_name, widget in self.widgets.items():
            config[param_name] = widget.value
        return config

    def get_widget(self) -> widgets.VBox:
        """Get the widget container."""
        return self.container


class TopologyConfigurator:
    """Main configurator interface for the UH2025Agent topology."""

    def __init__(self, topology_root: Path):
        """
        Initialize topology configurator.

        Args:
            topology_root: Path to topology root directory
        """
        self.topology_root = Path(topology_root)
        self.module_tabs = {}
        self.tab_widget = None
        self._define_parameters()
        self._build_interface()

    def _define_parameters(self):
        """Define parameters for each module in the pipeline."""
        self.parameters = {
            'AlphaGenome': {
                'batch_size': {
                    'type': 'int',
                    'default': 32,
                    'min': 1,
                    'max': 128,
                    'description': 'Batch size for regulatory analysis'
                },
                'model_version': {
                    'type': 'dropdown',
                    'default': 'v1.0.0',
                    'options': ['v1.0.0-stub', 'v1.0.0', 'v2.0.0'],
                    'description': 'AlphaGenome model version'
                }
            },
            'AlphaMissense': {
                'pathogenicity_threshold': {
                    'type': 'float',
                    'default': 0.564,
                    'min': 0.0,
                    'max': 1.0,
                    'step': 0.001,
                    'description': 'Pathogenicity score threshold'
                },
                'database_path': {
                    'type': 'text',
                    'default': 'alphamissense_scores.db',
                    'description': 'Path to AlphaMissense database'
                }
            },
            'RareLLM - Differential': {
                'llm_temperature': {
                    'type': 'float',
                    'default': 0.3,
                    'min': 0.0,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'LLM temperature (creativity)'
                },
                'max_diagnoses': {
                    'type': 'int',
                    'default': 5,
                    'min': 1,
                    'max': 20,
                    'description': 'Max differential diagnoses'
                },
                'confidence_threshold': {
                    'type': 'float',
                    'default': 0.15,
                    'min': 0.0,
                    'max': 1.0,
                    'step': 0.05,
                    'description': 'Min confidence for inclusion'
                }
            },
            'RareLLM - Tool Calls': {
                'llm_temperature': {
                    'type': 'float',
                    'default': 0.2,
                    'min': 0.0,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'LLM temperature (creativity)'
                },
                'max_tool_calls': {
                    'type': 'int',
                    'default': 10,
                    'min': 1,
                    'max': 50,
                    'description': 'Max tool calls to generate'
                }
            },
            'RareLLM - Report': {
                'llm_temperature': {
                    'type': 'float',
                    'default': 0.4,
                    'min': 0.0,
                    'max': 2.0,
                    'step': 0.1,
                    'description': 'LLM temperature (creativity)'
                },
                'report_format': {
                    'type': 'dropdown',
                    'default': 'markdown',
                    'options': ['markdown', 'html', 'pdf'],
                    'description': 'Report output format'
                },
                'include_references': {
                    'type': 'bool',
                    'default': True,
                    'description': 'Include literature references'
                }
            },
            'Global Settings': {
                'patient_id': {
                    'type': 'text',
                    'default': 'PatientX',
                    'description': 'Patient identifier'
                },
                'privacy_mode': {
                    'type': 'bool',
                    'default': True,
                    'description': 'HIPAA compliance mode'
                },
                'enable_parallel': {
                    'type': 'bool',
                    'default': True,
                    'description': 'Parallel execution (Steps 01-02)'
                },
                'output_directory': {
                    'type': 'text',
                    'default': 'outputs',
                    'description': 'Output directory path'
                },
                'timeout_minutes': {
                    'type': 'int',
                    'default': 60,
                    'min': 5,
                    'max': 480,
                    'description': 'Execution timeout (minutes)'
                }
            }
        }

    def _build_interface(self):
        """Build the tabbed configurator interface."""
        # Create tab for each module
        tab_children = []
        tab_titles = []

        for module_name, module_params in self.parameters.items():
            tab = ModuleConfigTab(module_name, module_params)
            self.module_tabs[module_name] = tab
            tab_children.append(tab.get_widget())
            tab_titles.append(module_name)

        # Create Tab widget
        self.tab_widget = widgets.Tab(children=tab_children)
        for i, title in enumerate(tab_titles):
            self.tab_widget.set_title(i, title)

        # Create action buttons
        self.export_button = widgets.Button(
            description='💾 Export Config',
            button_style='info',
            layout=widgets.Layout(width='150px', height='40px')
        )
        self.load_button = widgets.Button(
            description='📂 Load Config',
            button_style='',
            layout=widgets.Layout(width='150px', height='40px')
        )
        self.reset_button = widgets.Button(
            description='🔄 Reset Defaults',
            button_style='warning',
            layout=widgets.Layout(width='150px', height='40px')
        )

        # Button handlers
        self.export_button.on_click(self._on_export)
        self.load_button.on_click(self._on_load)
        self.reset_button.on_click(self._on_reset)

        # Button container
        button_box = widgets.HBox([
            self.export_button,
            self.load_button,
            self.reset_button
        ], layout=widgets.Layout(padding='10px', justify_content='center'))

        # Status display
        self.status_display = widgets.HTML(
            value='<p style="text-align: center; color: gray;">Configure parameters above</p>'
        )

        # Main container
        self.container = widgets.VBox([
            widgets.HTML(value='<h2 style="text-align: center;">⚙️ Pipeline Configuration</h2>'),
            self.tab_widget,
            button_box,
            self.status_display
        ])

    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration from all tabs.

        Returns:
            Dictionary with all parameter values
        """
        config = {}
        for module_name, tab in self.module_tabs.items():
            module_config = tab.get_config()
            # Flatten global settings, nest module configs
            if module_name == 'Global Settings':
                config.update(module_config)
            else:
                # Convert module names to lowercase for consistency
                key = module_name.lower().replace(' ', '_').replace('-', '')
                config[key] = module_config
        return config

    def export_config(self, filepath: Optional[Path] = None) -> Path:
        """
        Export configuration to YAML file.

        Args:
            filepath: Optional custom path. Defaults to params.yaml

        Returns:
            Path to exported file
        """
        if filepath is None:
            filepath = self.topology_root / 'params.yaml'

        config = self.get_config()

        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        return filepath

    def load_config(self, filepath: Optional[Path] = None):
        """
        Load configuration from YAML file.

        Args:
            filepath: Optional custom path. Defaults to params.yaml
        """
        if filepath is None:
            filepath = self.topology_root / 'params.yaml'

        if not filepath.exists():
            self._update_status(f'⚠️ Config file not found: {filepath}', 'orange')
            return

        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)

        # Apply config to widgets
        for module_name, tab in self.module_tabs.items():
            if module_name == 'Global Settings':
                # Apply global settings
                for param_name, widget in tab.widgets.items():
                    if param_name in config:
                        widget.value = config[param_name]
            else:
                # Apply module settings
                key = module_name.lower().replace(' ', '_').replace('-', '')
                if key in config:
                    module_config = config[key]
                    for param_name, widget in tab.widgets.items():
                        if param_name in module_config:
                            widget.value = module_config[param_name]

        self._update_status(f'✅ Loaded config from {filepath.name}', 'green')

    def reset_to_defaults(self):
        """Reset all parameters to default values."""
        for module_name, module_params in self.parameters.items():
            tab = self.module_tabs[module_name]
            for param_name, param_config in module_params.items():
                if param_name in tab.widgets:
                    tab.widgets[param_name].value = param_config['default']

        self._update_status('🔄 Reset to default values', 'blue')

    def _on_export(self, button):
        """Handle export button click."""
        try:
            filepath = self.export_config()
            self._update_status(f'💾 Exported to {filepath.name}', 'green')
        except Exception as e:
            self._update_status(f'❌ Export failed: {str(e)}', 'red')

    def _on_load(self, button):
        """Handle load button click."""
        try:
            self.load_config()
        except Exception as e:
            self._update_status(f'❌ Load failed: {str(e)}', 'red')

    def _on_reset(self, button):
        """Handle reset button click."""
        self.reset_to_defaults()

    def _update_status(self, message: str, color: str = 'gray'):
        """Update status display."""
        self.status_display.value = f'<p style="text-align: center; color: {color};">{message}</p>'

    def display(self):
        """Display the configurator interface."""
        display(self.container)

    def get_widget(self) -> widgets.VBox:
        """Get the widget container for embedding."""
        return self.container
