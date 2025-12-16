"""
Synthetic Patient Generator for UH2025-CDS Diagnostic Arena.

This module generates realistic-but-fake patient cases for:
1. Testing the UH2025-CDS pipeline without real PHI
2. RLHF training data collection via the Diagnostic Arena
3. Algorithm validation and benchmarking
4. Educational demonstrations

Key Features:
- Disease seed prompts for various rare disease categories
- LLM-based clinical summary generation
- Synthetic VCF generation with known variants
- Configurable complexity levels
- Ground truth labels for evaluation

IMPORTANT: All generated patients are SYNTHETIC.
No real patient data is used in generation.
"""

from .generator import SyntheticPatientGenerator
from .prompts import load_disease_seed, list_disease_seeds

__all__ = [
    "SyntheticPatientGenerator",
    "load_disease_seed",
    "list_disease_seeds",
]

__version__ = "1.0.0"
