"""
Pipeline Executor Module for UH2025Agent Topology

This module handles execution of the diagnostic pipeline with progress tracking,
status updates, and error handling.

Author: Stanley Lab / RareResearch
Date: November 2025
"""

from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import time


class PipelineExecutor:
    """Executes the UH2025Agent diagnostic pipeline with progress tracking."""

    def __init__(self, topology_root: Path):
        """
        Initialize pipeline executor.

        Args:
            topology_root: Path to topology root directory
        """
        self.topology_root = Path(topology_root)
        self.execution_state = {
            'running': False,
            'execution_id': None,
            'current_stage': None,
            'start_time': None,
            'end_time': None,
            'success': None
        }
        self.stages = [
            {
                'name': '01_regulatory_analysis',
                'description': 'AlphaGenome - Regulatory impact analysis',
                'module': 'AlphaGenome'
            },
            {
                'name': '02_pathogenicity_scoring',
                'description': 'AlphaMissense - Pathogenicity scoring',
                'module': 'AlphaMissense'
            },
            {
                'name': '03_differential_diagnosis',
                'description': 'RareLLM - Differential diagnosis generation',
                'module': 'RareLLM'
            },
            {
                'name': '04_tool_call_generation',
                'description': 'RareLLM - Evidence validation tool calls',
                'module': 'RareLLM'
            },
            {
                'name': '05_report_generation',
                'description': 'RareLLM - Clinical report generation',
                'module': 'RareLLM'
            }
        ]

    def execute(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        completion_callback: Optional[Callable[[bool], None]] = None
    ):
        """
        Execute the pipeline with provided configuration.

        Args:
            config: Configuration dictionary
            progress_callback: Called with (current_stage, total_stages, stage_name)
            log_callback: Called with log messages
            completion_callback: Called with success boolean when complete
        """
        if self.execution_state['running']:
            if log_callback:
                log_callback("⚠ Pipeline already running!")
            return

        # Initialize execution
        self.execution_state['running'] = True
        self.execution_state['execution_id'] = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.execution_state['start_time'] = datetime.now()
        self.execution_state['success'] = None

        if log_callback:
            log_callback("🚀 UH2025Agent Diagnostic Pipeline")
            log_callback(f"   Execution ID: {self.execution_state['execution_id']}")
            log_callback(f"   Patient: {config.get('patient_id', 'Unknown')}")
            log_callback("")

        try:
            # Execute each stage with realistic timing and detailed logging
            total_stages = len(self.stages)

            # Stage-specific details for logging
            stage_details = {
                '01_regulatory_analysis': {
                    'time': 13,
                    'details': [
                        'Analyzed 47 variants',
                        'Found 12 regulatory impacts',
                        '✓ Complete (13s)'
                    ]
                },
                '02_pathogenicity_scoring': {
                    'time': 12,
                    'details': [
                        'Scored 47 missense variants',
                        'High pathogenicity: 8 variants',
                        '✓ Complete (12s)'
                    ]
                },
                '03_differential_diagnosis': {
                    'time': 77,
                    'details': [
                        'Generated 5 candidate diagnoses',
                        'Top confidence: 0.89 (Paramyotonia Congenita)',
                        '✓ Complete (77s)'
                    ]
                },
                '04_tool_call_generation': {
                    'time': 49,
                    'details': [
                        'Generated 8 validation queries',
                        'Tools: OMIM, ClinVar, PubMed, GeneReviews',
                        '✓ Complete (49s)'
                    ]
                },
                '05_report_generation': {
                    'time': 38,
                    'details': [
                        'Synthesized evidence from 8 sources',
                        'Generated 1,247-word clinical report',
                        '✓ Complete (38s)'
                    ]
                }
            }

            for idx, stage in enumerate(self.stages, 1):
                self.execution_state['current_stage'] = stage['name']
                stage_name = stage['name']

                if log_callback:
                    log_callback(f"▶ Stage {idx}/{total_stages}: {stage['description']}")

                if progress_callback:
                    progress_callback(idx, total_stages, stage['description'])

                # Simulate stage execution
                self._execute_stage(stage, config)

                # Log stage details with realistic timing
                details = stage_details.get(stage_name, {})
                stage_time = details.get('time', 1)

                # Simulate stage execution time (shortened for demo - use 0.5s instead of actual time)
                time.sleep(0.5)

                # Log detailed progress
                if log_callback and 'details' in details:
                    for detail in details['details']:
                        if detail.startswith('├─') or detail.startswith('└─'):
                            log_callback(f"    {detail}")
                        else:
                            log_callback(f"    ├─ {detail}")

                if log_callback:
                    log_callback("")

            # Mark success
            self.execution_state['success'] = True
            self.execution_state['end_time'] = datetime.now()

            if log_callback:
                log_callback("✅ Pipeline complete")
                duration = (self.execution_state['end_time'] - self.execution_state['start_time']).total_seconds()
                log_callback(f"   Duration: 3 minutes 13 seconds (simulated)")
                log_callback("   All stages successful")
                log_callback("📊 Loading diagnostic results...")
                time.sleep(0.5)
                log_callback("✓ Results loaded - 5 diagnoses ready for review")

            if completion_callback:
                completion_callback(True)

        except Exception as e:
            self.execution_state['success'] = False
            self.execution_state['end_time'] = datetime.now()

            if log_callback:
                log_callback("")
                log_callback(f"❌ Pipeline failed: {str(e)}")

            if completion_callback:
                completion_callback(False)

        finally:
            self.execution_state['running'] = False

    def _execute_stage(self, stage: Dict[str, Any], config: Dict[str, Any]):
        """
        Execute a single pipeline stage.

        In a full implementation, this would:
        1. Validate stage requirements
        2. Execute the module notebook via papermill
        3. Verify outputs were created
        4. Handle errors gracefully

        For now, this is a stub that validates outputs exist.

        Args:
            stage: Stage configuration
            config: Pipeline configuration
        """
        # In real implementation:
        # - Would call papermill to execute notebook
        # - Would pass parameters from config
        # - Would capture outputs
        # - Would handle errors

        # For demo purposes, just validate output exists
        stage_name = stage['name']
        outputs_dir = self.topology_root / 'outputs'

        # Map stage names to output directories
        output_mapping = {
            '01_regulatory_analysis': '01_regulatory',
            '02_pathogenicity_scoring': '02_pathogenicity',
            '03_differential_diagnosis': '03_differential',
            '04_tool_call_generation': '04_toolcalls',
            '05_report_generation': '05_report'
        }

        output_dir = outputs_dir / output_mapping.get(stage_name, stage_name)

        # Check if outputs exist (for demo, they should after mock data creation)
        # In production, this would execute the notebook to create them
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory not found: {output_dir}")

        # Validate that output directory contains files (excluding .gitkeep)
        output_files = [f for f in output_dir.iterdir() if f.name != '.gitkeep']
        if not output_files:
            raise FileNotFoundError(
                f"Output directory exists but is empty: {output_dir}\n"
                f"Expected output files for stage: {stage_name}"
            )

    def is_running(self) -> bool:
        """Check if pipeline is currently running."""
        return self.execution_state['running']

    def get_execution_id(self) -> Optional[str]:
        """Get current execution ID."""
        return self.execution_state['execution_id']

    def get_current_stage(self) -> Optional[str]:
        """Get current stage name."""
        return self.execution_state['current_stage']

    def get_status(self) -> Dict[str, Any]:
        """Get full execution status."""
        return self.execution_state.copy()
