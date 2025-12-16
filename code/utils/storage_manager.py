"""
Storage manager - handles platform-dependent storage for topology outputs.

Supports:
- L1 (Local): Local filesystem
- L2 (Academic cluster): S3-compatible storage
- L3 (Enterprise): GCS or S3

Automatically detects platform and configures storage accordingly.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


class StorageManager:
    """Manages storage for topology execution outputs."""

    # Platform detection markers
    L1_MARKERS = [
        '.delab_l1',
        os.path.expanduser('~/Projects/DeLab'),
    ]

    L2_MARKERS = [
        '/scratch',
        '/data/shared',
        '.delab_l2'
    ]

    L3_MARKERS = [
        '/mnt/enterprise',
        '.delab_l3'
    ]

    def __init__(
        self,
        topology_dir: Path,
        output_base_dir: Optional[Path] = None,
        privacy_mode: bool = False
    ):
        """
        Initialize storage manager.

        Args:
            topology_dir: Directory containing topology.yaml
            output_base_dir: Base directory for outputs (default: topology_dir/outputs)
            privacy_mode: If True, restrict to local storage only (HIPAA compliance)
        """
        self.topology_dir = Path(topology_dir)
        self.privacy_mode = privacy_mode

        # Detect platform
        self.platform = self._detect_platform()

        # Configure storage backend
        if privacy_mode:
            # Privacy mode: Force local storage regardless of platform
            self.storage_backend = 'local'
            self.output_base_dir = output_base_dir or (self.topology_dir / 'outputs')
        elif self.platform == 'L1':
            self.storage_backend = 'local'
            self.output_base_dir = output_base_dir or (self.topology_dir / 'outputs')
        elif self.platform == 'L2':
            self.storage_backend = 's3'
            self.output_base_dir = output_base_dir or Path('/scratch/delab/outputs')
            self.s3_bucket = os.environ.get('DELAB_S3_BUCKET', 'delab-l2-outputs')
            self.s3_prefix = os.environ.get('DELAB_S3_PREFIX', 'topologies')
        elif self.platform == 'L3':
            self.storage_backend = os.environ.get('DELAB_STORAGE_BACKEND', 'gcs')
            self.output_base_dir = output_base_dir or Path('/mnt/delab/outputs')

            if self.storage_backend == 'gcs':
                self.gcs_bucket = os.environ.get('DELAB_GCS_BUCKET', 'delab-l3-outputs')
                self.gcs_prefix = os.environ.get('DELAB_GCS_PREFIX', 'topologies')
            else:  # s3
                self.s3_bucket = os.environ.get('DELAB_S3_BUCKET', 'delab-l3-outputs')
                self.s3_prefix = os.environ.get('DELAB_S3_PREFIX', 'topologies')

        # Create base directory if it doesn't exist
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    def _detect_platform(self) -> str:
        """
        Auto-detect platform level (L1/L2/L3).

        Returns:
            'L1', 'L2', or 'L3'
        """
        # Check for L1 markers
        for marker in self.L1_MARKERS:
            marker_path = Path(marker)
            if marker_path.exists():
                return 'L1'

        # Check for L3 markers (check before L2 since L3 may have /data/shared)
        for marker in self.L3_MARKERS:
            if Path(marker).exists():
                return 'L3'

        # Check for L2 markers
        for marker in self.L2_MARKERS:
            if Path(marker).exists():
                return 'L2'

        # Default to L1 (local development)
        return 'L1'

    def create_run_directory(
        self,
        run_id: Optional[str] = None,
        topology_name: Optional[str] = None
    ) -> Path:
        """
        Create directory for topology run.

        Args:
            run_id: Run identifier (default: timestamp)
            topology_name: Topology name for directory structure

        Returns:
            Path to run directory
        """
        if run_id is None:
            run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

        if topology_name:
            run_dir = self.output_base_dir / topology_name / f"run_{run_id}"
        else:
            run_dir = self.output_base_dir / f"run_{run_id}"

        run_dir.mkdir(parents=True, exist_ok=True)

        # Create metadata file
        metadata = {
            'run_id': run_id,
            'topology_name': topology_name,
            'platform': self.platform,
            'storage_backend': self.storage_backend,
            'privacy_mode': self.privacy_mode,
            'start_time': datetime.now().isoformat(),
            'output_dir': str(run_dir)
        }

        with open(run_dir / 'run_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)

        return run_dir

    def create_step_directory(self, run_dir: Path, step_id: str) -> Path:
        """
        Create directory for step outputs.

        Args:
            run_dir: Run directory
            step_id: Step identifier

        Returns:
            Path to step directory
        """
        step_dir = run_dir / step_id
        step_dir.mkdir(parents=True, exist_ok=True)
        return step_dir

    def save_step_output(
        self,
        step_dir: Path,
        output_name: str,
        source_path: Path
    ) -> Path:
        """
        Save step output file.

        Args:
            step_dir: Step output directory
            output_name: Output identifier
            source_path: Source file path

        Returns:
            Path to saved output file
        """
        source_path = Path(source_path)
        dest_path = step_dir / source_path.name

        # Copy file to step directory
        if source_path.is_file():
            shutil.copy2(source_path, dest_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        else:
            raise ValueError(f"Source path does not exist: {source_path}")

        # Upload to remote storage if not L1 and not privacy mode
        if self.storage_backend != 'local' and not self.privacy_mode:
            self._upload_to_remote(dest_path, step_dir.parent.name, step_dir.name)

        return dest_path

    def _upload_to_remote(self, local_path: Path, run_id: str, step_id: str):
        """
        Upload file to remote storage (S3/GCS).

        Args:
            local_path: Local file path
            run_id: Run identifier
            step_id: Step identifier

        Note:
            This is a stub implementation. In production, would use
            boto3 (S3) or google-cloud-storage (GCS) libraries.
        """
        if self.privacy_mode:
            raise PermissionError(
                "Cannot upload to remote storage in privacy mode"
            )

        if self.storage_backend == 's3':
            # Stub for S3 upload
            remote_key = f"{self.s3_prefix}/{run_id}/{step_id}/{local_path.name}"
            print(f"[Storage] Would upload to s3://{self.s3_bucket}/{remote_key}")
            # TODO: Implement actual S3 upload
            # import boto3
            # s3 = boto3.client('s3')
            # s3.upload_file(str(local_path), self.s3_bucket, remote_key)

        elif self.storage_backend == 'gcs':
            # Stub for GCS upload
            remote_blob = f"{self.gcs_prefix}/{run_id}/{step_id}/{local_path.name}"
            print(f"[Storage] Would upload to gs://{self.gcs_bucket}/{remote_blob}")
            # TODO: Implement actual GCS upload
            # from google.cloud import storage
            # client = storage.Client()
            # bucket = client.bucket(self.gcs_bucket)
            # blob = bucket.blob(remote_blob)
            # blob.upload_from_filename(str(local_path))

    def save_topology_metadata(
        self,
        run_dir: Path,
        topology_dict: Dict,
        resolved_params: Dict,
        execution_info: Dict
    ):
        """
        Save topology metadata and provenance.

        Args:
            run_dir: Run directory
            topology_dict: Topology definition
            resolved_params: Resolved parameters
            execution_info: Execution metadata
        """
        metadata = {
            'topology': topology_dict,
            'parameters': resolved_params,
            'execution': execution_info,
            'platform': self.platform,
            'storage_backend': self.storage_backend,
            'privacy_mode': self.privacy_mode,
            'timestamp': datetime.now().isoformat()
        }

        metadata_path = run_dir / 'topology_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return metadata_path

    def save_execution_log(self, run_dir: Path, log_entries: List[Dict]):
        """
        Save execution log.

        Args:
            run_dir: Run directory
            log_entries: List of log entry dictionaries
        """
        log_path = run_dir / 'topology_execution.log'
        with open(log_path, 'w') as f:
            for entry in log_entries:
                timestamp = entry.get('timestamp', datetime.now().isoformat())
                level = entry.get('level', 'INFO')
                message = entry.get('message', '')
                f.write(f"[{timestamp}] {level}: {message}\n")

    def get_step_outputs(self, step_dir: Path) -> Dict[str, str]:
        """
        Get paths to all outputs in step directory.

        Args:
            step_dir: Step output directory

        Returns:
            Dictionary of output_name -> file_path
        """
        outputs = {}

        if not step_dir.exists():
            return outputs

        # List all files in step directory (excluding logs and metadata)
        for file_path in step_dir.iterdir():
            if file_path.is_file():
                # Skip execution logs and internal files
                if file_path.name in ['execution.log', 'output.ipynb']:
                    continue

                # Use filename without extension as output name
                output_name = file_path.stem
                outputs[output_name] = str(file_path)

        return outputs

    def cleanup_run(self, run_dir: Path, keep_outputs: bool = True):
        """
        Clean up run directory.

        Args:
            run_dir: Run directory
            keep_outputs: If True, keep output files, remove only notebooks
        """
        if not run_dir.exists():
            return

        if keep_outputs:
            # Remove only executed notebooks
            for step_dir in run_dir.iterdir():
                if step_dir.is_dir():
                    output_notebook = step_dir / 'output.ipynb'
                    if output_notebook.exists():
                        output_notebook.unlink()
        else:
            # Remove entire run directory
            shutil.rmtree(run_dir)

    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get storage configuration info.

        Returns:
            Dictionary with storage configuration
        """
        info = {
            'platform': self.platform,
            'storage_backend': self.storage_backend,
            'output_base_dir': str(self.output_base_dir),
            'privacy_mode': self.privacy_mode
        }

        if self.storage_backend == 's3':
            info['s3_bucket'] = self.s3_bucket
            info['s3_prefix'] = self.s3_prefix
        elif self.storage_backend == 'gcs':
            info['gcs_bucket'] = self.gcs_bucket
            info['gcs_prefix'] = self.gcs_prefix

        return info


def main():
    """CLI interface for storage manager testing."""
    import argparse

    parser = argparse.ArgumentParser(description='Test storage manager')
    parser.add_argument(
        '--topology-dir',
        default='.',
        help='Topology directory'
    )
    parser.add_argument(
        '--privacy-mode',
        action='store_true',
        help='Enable privacy mode (local only)'
    )
    args = parser.parse_args()

    # Create storage manager
    storage = StorageManager(
        topology_dir=Path(args.topology_dir),
        privacy_mode=args.privacy_mode
    )

    # Print configuration
    print("Storage Manager Configuration:")
    print("-" * 60)
    info = storage.get_storage_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test run directory creation
    print("\nTesting run directory creation...")
    run_dir = storage.create_run_directory(
        run_id='test_run',
        topology_name='example-topology'
    )
    print(f"  Created: {run_dir}")

    # Test step directory creation
    print("\nTesting step directory creation...")
    step_dir = storage.create_step_directory(run_dir, '01_preprocess')
    print(f"  Created: {step_dir}")

    print("\n✓ Storage manager test complete")


if __name__ == '__main__':
    main()
