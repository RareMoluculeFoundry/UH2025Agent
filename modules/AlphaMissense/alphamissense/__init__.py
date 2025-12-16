# AlphaMissense Module - Variant Pathogenicity Prediction
#
# This module provides lookup and analysis of AlphaMissense pathogenicity predictions
# for missense variants across the human proteome.

from .data.loader import AlphaMissenseDB
from .data.downloader import download_predictions, get_data_path
from .data.indexer import create_index, index_exists

__version__ = "1.0.0"
__all__ = [
    "AlphaMissenseDB",
    "download_predictions",
    "get_data_path",
    "create_index",
    "index_exists",
]
