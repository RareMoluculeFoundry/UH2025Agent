"""
AlphaMissense Data Downloader

Downloads pre-computed pathogenicity predictions from Google Cloud Storage.
Data is released under CC-BY-NC-SA 4.0 license.

Reference:
    Cheng et al. (2023). "Accurate proteome-wide missense variant effect prediction
    with AlphaMissense." Science, 381(6664), eadg7492.
    https://doi.org/10.1126/science.adg7492
"""

import os
import hashlib
from pathlib import Path
from typing import Callable, Literal
import urllib.request
import shutil

# Google Cloud Storage URLs for AlphaMissense data
ALPHAMISSENSE_URLS = {
    "hg38": "https://storage.googleapis.com/dm_alphamissense/AlphaMissense_hg38.tsv.gz",
    "hg19": "https://storage.googleapis.com/dm_alphamissense/AlphaMissense_hg19.tsv.gz",
    "aa_substitutions": "https://storage.googleapis.com/dm_alphamissense/AlphaMissense_aa_substitutions.tsv.gz",
}

# Expected file sizes (approximate, for validation)
EXPECTED_SIZES = {
    "hg38": 642_000_000,  # ~642 MB
    "hg19": 642_000_000,  # ~642 MB
    "aa_substitutions": 3_300_000_000,  # ~3.3 GB
}

# Default data directory
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def get_data_path(
    target: Literal["hg38", "hg19", "aa_substitutions"] = "hg38",
    data_dir: Path | str | None = None,
) -> Path:
    """
    Get the path where AlphaMissense data is/will be stored.

    Args:
        target: Which dataset to get path for
        data_dir: Custom data directory (default: module's data/ directory)

    Returns:
        Path to the data file
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR
    else:
        data_dir = Path(data_dir)

    return data_dir / f"AlphaMissense_{target}.tsv.gz"


def download_predictions(
    target: Literal["hg38", "hg19", "aa_substitutions"] = "hg38",
    data_dir: Path | str | None = None,
    force: bool = False,
    progress_callback: Callable | None = None,
) -> Path:
    """
    Download pre-computed AlphaMissense predictions from Google Cloud Storage.

    Args:
        target: Which dataset to download:
            - "hg38": Genomic coordinates (GRCh38), ~642 MB
            - "hg19": Genomic coordinates (GRCh37), ~642 MB
            - "aa_substitutions": Protein-centric, ~3.3 GB
        data_dir: Directory to save data (default: module's data/ directory)
        force: Re-download even if file exists
        progress_callback: Optional callback(bytes_downloaded, total_bytes)

    Returns:
        Path to downloaded file

    Raises:
        ValueError: If target is invalid
        ConnectionError: If download fails

    Example:
        >>> path = download_predictions("hg38")
        >>> print(f"Downloaded to: {path}")
    """
    if target not in ALPHAMISSENSE_URLS:
        raise ValueError(f"Invalid target: {target}. Must be one of: {list(ALPHAMISSENSE_URLS.keys())}")

    url = ALPHAMISSENSE_URLS[target]
    output_path = get_data_path(target, data_dir)

    # Check if already downloaded
    if output_path.exists() and not force:
        print(f"✓ AlphaMissense {target} data already exists: {output_path}")
        return output_path

    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading AlphaMissense {target} predictions...")
    print(f"  URL: {url}")
    print(f"  Destination: {output_path}")
    print(f"  Expected size: ~{EXPECTED_SIZES[target] / 1e6:.0f} MB")

    # Download with progress reporting
    temp_path = output_path.with_suffix(".tmp")

    try:
        def _report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if progress_callback:
                progress_callback(downloaded, total_size)
            elif total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                print(f"\r  Progress: {percent:.1f}% ({downloaded / 1e6:.1f} MB)", end="", flush=True)

        urllib.request.urlretrieve(url, temp_path, reporthook=_report_progress)
        print()  # newline after progress

        # Validate file size
        actual_size = temp_path.stat().st_size
        expected_min = EXPECTED_SIZES[target] * 0.9  # Allow 10% variance

        if actual_size < expected_min:
            raise ValueError(
                f"Downloaded file too small ({actual_size / 1e6:.1f} MB). "
                f"Expected at least {expected_min / 1e6:.1f} MB. "
                "Download may have been interrupted."
            )

        # Move to final location
        shutil.move(temp_path, output_path)
        print(f"✓ Downloaded successfully: {output_path}")
        print(f"  Size: {actual_size / 1e6:.1f} MB")

        return output_path

    except Exception as e:
        # Clean up temp file on failure
        if temp_path.exists():
            temp_path.unlink()
        raise ConnectionError(f"Failed to download AlphaMissense data: {e}") from e


def verify_download(
    target: Literal["hg38", "hg19", "aa_substitutions"] = "hg38",
    data_dir: Path | str | None = None,
) -> bool:
    """
    Verify that AlphaMissense data file exists and is valid.

    Args:
        target: Which dataset to verify
        data_dir: Data directory to check

    Returns:
        True if file exists and appears valid
    """
    path = get_data_path(target, data_dir)

    if not path.exists():
        return False

    # Check file size
    actual_size = path.stat().st_size
    expected_min = EXPECTED_SIZES[target] * 0.9

    return actual_size >= expected_min


if __name__ == "__main__":
    # CLI for downloading data
    import argparse

    parser = argparse.ArgumentParser(description="Download AlphaMissense predictions")
    parser.add_argument(
        "--target",
        choices=["hg38", "hg19", "aa_substitutions"],
        default="hg38",
        help="Which dataset to download (default: hg38)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        help="Directory to save data",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if file exists",
    )

    args = parser.parse_args()
    download_predictions(args.target, args.data_dir, args.force)
