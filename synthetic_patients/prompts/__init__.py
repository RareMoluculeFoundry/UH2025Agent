"""
Disease Seed Prompts for Synthetic Patient Generation.

This module provides disease seed configurations that guide the
generation of realistic synthetic patient cases.

Available Seeds:
- ion_channelopathy: Sodium/potassium channel disorders
- neuromuscular: Muscular dystrophies and myopathies
- metabolic: Inborn errors of metabolism
- connective_tissue: Ehlers-Danlos, Marfan, etc.
- neurodegeneration: Early-onset neurodegenerative disorders
"""

from pathlib import Path
from typing import Dict, Any, List
import yaml


SEED_DIRECTORY = Path(__file__).parent / "rare_disease_seeds"


def load_disease_seed(seed_name: str) -> Dict[str, Any]:
    """
    Load a disease seed configuration by name.

    Args:
        seed_name: Name of the seed (without .yaml extension)

    Returns:
        Dictionary containing seed configuration

    Raises:
        FileNotFoundError: If seed file doesn't exist
    """
    seed_path = SEED_DIRECTORY / f"{seed_name}.yaml"
    if not seed_path.exists():
        raise FileNotFoundError(
            f"Disease seed '{seed_name}' not found. "
            f"Available seeds: {list_disease_seeds()}"
        )

    with open(seed_path) as f:
        return yaml.safe_load(f)


def list_disease_seeds() -> List[str]:
    """
    List all available disease seeds.

    Returns:
        List of seed names (without .yaml extension)
    """
    if not SEED_DIRECTORY.exists():
        return []
    return [f.stem for f in SEED_DIRECTORY.glob("*.yaml")]


def get_seed_summary(seed_name: str) -> Dict[str, Any]:
    """
    Get a brief summary of a disease seed.

    Args:
        seed_name: Name of the seed

    Returns:
        Summary with category, conditions count, and genes
    """
    seed = load_disease_seed(seed_name)
    return {
        "name": seed_name,
        "category": seed.get("disease_category", "Unknown"),
        "conditions_count": len(seed.get("example_conditions", [])),
        "genes": seed.get("genes_of_interest", []),
        "phenotypes_count": len(seed.get("phenotype_features", [])),
    }


def list_all_seed_summaries() -> List[Dict[str, Any]]:
    """
    Get summaries of all available seeds.

    Returns:
        List of seed summaries
    """
    return [get_seed_summary(name) for name in list_disease_seeds()]
