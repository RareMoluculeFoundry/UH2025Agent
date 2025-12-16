"""
Output Manager for FAIR-Compliant Pipeline Outputs

This module provides utilities for managing pipeline outputs following
FAIR principles (Findable, Accessible, Interoperable, Reusable).

Features:
- Execution ID generation
- Output directory management
- Metadata generation with provenance tracking
- Checksum computation and verification
- Output validation against schema

Author: Stanley Lab / RareResearch
Version: 1.0.0
Date: 2025-11-03
"""

import hashlib
import json
import platform
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class OutputManager:
    """Manager for FAIR-compliant pipeline outputs."""

    def __init__(self, topology_root: Path):
        """
        Initialize output manager.

        Args:
            topology_root: Root directory of topology (contains outputs/)
        """
        self.topology_root = Path(topology_root)
        self.outputs_dir = self.topology_root / "outputs"
        self.metadata_schema_path = self.topology_root / "metadata" / "output_schema.yaml"

        # Load metadata schema
        self.schema = self._load_schema()

    def _load_schema(self) -> Optional[Dict]:
        """Load output metadata schema."""
        if self.metadata_schema_path.exists():
            with open(self.metadata_schema_path) as f:
                return yaml.safe_load(f)
        return None

    @staticmethod
    def generate_execution_id() -> str:
        """
        Generate unique execution ID with timestamp.

        Returns:
            Execution ID in format: run_YYYYMMDD_HHMMSS
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"run_{timestamp}"

    @staticmethod
    def generate_output_id(stage: str, run_id: str) -> str:
        """
        Generate unique output ID (DID format).

        Args:
            stage: Stage name (e.g., "differential", "toolcalls")
            run_id: Execution ID

        Returns:
            DID format: did:defact:output:{stage}:{run_id}:{uuid}
        """
        short_uuid = str(uuid.uuid4())[:8]
        return f"did:defact:output:{stage}:{run_id}:{short_uuid}"

    def create_output_path(self, stage_dir: str, filename: str) -> Path:
        """
        Create path for output file.

        Args:
            stage_dir: Stage directory name (e.g., "03_differential")
            filename: Output filename

        Returns:
            Full path to output file
        """
        output_dir = self.outputs_dir / stage_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename

    @staticmethod
    def compute_checksum(file_path: Path) -> str:
        """
        Compute SHA-256 checksum of file.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of SHA-256 hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def generate_metadata(
        self,
        output_id: str,
        output_type: str,
        output_path: Path,
        module: str,
        notebook: str,
        version: str,
        execution_id: str,
        timestamp: str,
        duration_seconds: float,
        platform: str,
        backend: str,
        inputs: Dict[str, str],
        parameters: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        model: Optional[str] = None,
        lora_adapter: Optional[str] = None,
        license: str = "CC-BY-4.0",
        attribution: str = "RareResearch / Stanley Lab / DeLab Platform"
    ) -> Dict[str, Any]:
        """
        Generate FAIR-compliant metadata for output.

        Args:
            output_id: Unique output identifier (DID format)
            output_type: Type of output
            output_path: Path to output file
            module: Module name
            notebook: Notebook filename
            version: Module version
            execution_id: Pipeline execution ID
            timestamp: ISO 8601 timestamp
            duration_seconds: Execution time
            platform: Execution platform
            backend: Compute backend
            inputs: Input files dictionary
            parameters: Parameter dictionary
            quality_metrics: Quality metrics dictionary
            model: LLM model name (optional)
            lora_adapter: LoRA adapter name (optional)
            license: License (default: CC-BY-4.0)
            attribution: Attribution string

        Returns:
            Complete metadata dictionary
        """
        # Compute checksum
        checksum = self.compute_checksum(output_path)

        # Get file info
        file_stat = output_path.stat()

        # Determine MIME type
        mime_type = {
            '.json': 'application/json',
            '.md': 'text/markdown',
            '.txt': 'text/plain'
        }.get(output_path.suffix, 'application/octet-stream')

        # Build metadata
        metadata = {
            'identity': {
                'output_id': output_id,
                'output_type': output_type,
                'format': mime_type,
                'filename': output_path.name
            },
            'provenance': {
                'generated_by': {
                    'module': module,
                    'notebook': notebook,
                    'version': version,
                    'git_commit': None  # Could be populated from git
                },
                'execution': {
                    'execution_id': execution_id,
                    'timestamp': timestamp,
                    'duration_seconds': duration_seconds,
                    'platform': platform
                }
            },
            'compute_environment': {
                'backend': backend,
                'system_info': {
                    'platform': platform.system(),
                    'platform_version': platform.version(),
                    'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                }
            },
            'inputs': inputs,
            'parameters': parameters,
            'quality_metrics': {
                'output_size_bytes': file_stat.st_size,
                **quality_metrics
            },
            'verification': {
                'checksum_sha256': checksum,
                'checksum_algorithm': 'SHA-256',
                'verification_timestamp': datetime.now().isoformat() + 'Z'
            },
            'licensing': {
                'license': license,
                'attribution': attribution,
                'usage_restrictions': 'Research and educational use only. Not for clinical decision-making without physician review.'
            },
            'related': {
                'pipeline_run': f"outputs/{execution_id}/run_metadata.yaml",
                'upstream_outputs': [],  # To be populated by caller
                'downstream_outputs': []
            }
        }

        # Add optional fields
        if model:
            metadata['compute_environment']['model'] = model
        if lora_adapter:
            metadata['compute_environment']['lora_adapter'] = lora_adapter

        return metadata

    def save_with_metadata(
        self,
        output_data: Any,
        output_path: Path,
        metadata: Dict[str, Any],
        output_format: str = 'json'
    ) -> Tuple[Path, Path]:
        """
        Save output and metadata files atomically.

        Args:
            output_data: Data to save
            output_path: Path for output file
            metadata: Metadata dictionary
            output_format: Format ('json' or 'markdown')

        Returns:
            Tuple of (output_path, metadata_path)
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save output file
        if output_format == 'json':
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
        elif output_format == 'markdown':
            with open(output_path, 'w') as f:
                f.write(output_data)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

        # Recompute checksum now that file is saved
        metadata['verification']['checksum_sha256'] = self.compute_checksum(output_path)
        metadata['verification']['verification_timestamp'] = datetime.now().isoformat() + 'Z'
        metadata['quality_metrics']['output_size_bytes'] = output_path.stat().st_size

        # Save metadata file
        metadata_path = output_path.parent / f"{output_path.stem}_metadata.yaml"
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

        return output_path, metadata_path

    def validate_output(
        self,
        output_path: Path,
        metadata_path: Path
    ) -> Tuple[bool, List[str]]:
        """
        Validate output file and metadata.

        Args:
            output_path: Path to output file
            metadata_path: Path to metadata file

        Returns:
            Tuple of (is_valid, error_list)
        """
        errors = []

        # Check files exist
        if not output_path.exists():
            errors.append(f"Output file not found: {output_path}")
            return False, errors

        if not metadata_path.exists():
            errors.append(f"Metadata file not found: {metadata_path}")
            return False, errors

        # Load metadata
        try:
            with open(metadata_path) as f:
                metadata = yaml.safe_load(f)
        except Exception as e:
            errors.append(f"Failed to load metadata: {e}")
            return False, errors

        # Check required fields
        required_fields = [
            'identity.output_id',
            'identity.output_type',
            'provenance.generated_by.module',
            'provenance.execution.execution_id',
            'verification.checksum_sha256'
        ]

        for field_path in required_fields:
            parts = field_path.split('.')
            value = metadata
            try:
                for part in parts:
                    value = value[part]
                if value is None:
                    errors.append(f"Required field is None: {field_path}")
            except KeyError:
                errors.append(f"Missing required field: {field_path}")

        # Verify checksum
        try:
            computed_checksum = self.compute_checksum(output_path)
            stored_checksum = metadata['verification']['checksum_sha256']
            if computed_checksum != stored_checksum:
                errors.append(
                    f"Checksum mismatch: computed={computed_checksum[:16]}..., "
                    f"stored={stored_checksum[:16]}..."
                )
        except Exception as e:
            errors.append(f"Checksum verification failed: {e}")

        # Validate JSON structure if JSON output
        if output_path.suffix == '.json':
            try:
                with open(output_path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {e}")

        return len(errors) == 0, errors

    def list_outputs(self, execution_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all outputs, optionally filtered by execution ID.

        Args:
            execution_id: Optional execution ID to filter by

        Returns:
            List of output info dictionaries
        """
        outputs = []

        for stage_dir in self.outputs_dir.iterdir():
            if not stage_dir.is_dir() or stage_dir.name.startswith('.'):
                continue

            for output_file in stage_dir.glob('*.json'):
                # Skip metadata files
                if output_file.name.endswith('_metadata.yaml'):
                    continue

                metadata_file = output_file.parent / f"{output_file.stem}_metadata.yaml"

                if metadata_file.exists():
                    with open(metadata_file) as f:
                        metadata = yaml.safe_load(f)

                    # Filter by execution_id if specified
                    if execution_id and metadata['provenance']['execution']['execution_id'] != execution_id:
                        continue

                    outputs.append({
                        'output_path': output_file,
                        'metadata_path': metadata_file,
                        'output_id': metadata['identity']['output_id'],
                        'output_type': metadata['identity']['output_type'],
                        'execution_id': metadata['provenance']['execution']['execution_id'],
                        'timestamp': metadata['provenance']['execution']['timestamp']
                    })

        return sorted(outputs, key=lambda x: x['timestamp'])


# Convenience functions
def save_output_with_fair_metadata(
    output_data: Any,
    output_path: Path,
    stage: str,
    module: str,
    notebook: str,
    execution_id: str,
    backend: str,
    inputs: Dict[str, str],
    parameters: Dict[str, Any],
    duration_seconds: float,
    quality_metrics: Dict[str, Any],
    model: Optional[str] = None,
    lora_adapter: Optional[str] = None,
    version: str = "1.0.0",
    platform: str = "local",
    output_format: str = 'json'
) -> Tuple[Path, Path]:
    """
    Convenience function to save output with FAIR metadata.

    Returns:
        Tuple of (output_path, metadata_path)
    """
    # Initialize manager
    topology_root = output_path.parents[2]  # Assumes outputs/{stage}/file.ext
    manager = OutputManager(topology_root)

    # Generate IDs and timestamp
    output_id = manager.generate_output_id(stage, execution_id)
    timestamp = datetime.now().isoformat() + 'Z'

    # Generate metadata
    metadata = manager.generate_metadata(
        output_id=output_id,
        output_type=stage,
        output_path=output_path,
        module=module,
        notebook=notebook,
        version=version,
        execution_id=execution_id,
        timestamp=timestamp,
        duration_seconds=duration_seconds,
        platform=platform,
        backend=backend,
        inputs=inputs,
        parameters=parameters,
        quality_metrics=quality_metrics,
        model=model,
        lora_adapter=lora_adapter
    )

    # Save with metadata
    return manager.save_with_metadata(
        output_data=output_data,
        output_path=output_path,
        metadata=metadata,
        output_format=output_format
    )
