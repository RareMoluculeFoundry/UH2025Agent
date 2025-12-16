"""
AlphaMissense Variant Filtering

Functions for annotating and filtering variants based on pathogenicity predictions.
"""

from typing import Any
from ..data.loader import AlphaMissenseDB, PATHOGENIC_THRESHOLD, BENIGN_THRESHOLD


def annotate_variants(
    variants: list[dict],
    db: AlphaMissenseDB | None = None,
    include_ambiguous: bool = True,
) -> list[dict]:
    """
    Annotate variants with AlphaMissense pathogenicity scores.

    Args:
        variants: List of variant dictionaries with keys:
            - chrom or chromosome: Chromosome
            - pos or position: Position
            - ref: Reference allele
            - alt: Alternate allele
        db: AlphaMissenseDB instance (creates new if None)
        include_ambiguous: Include ambiguous variants in output

    Returns:
        List of variants with added AlphaMissense annotations:
            - am_pathogenicity: Pathogenicity score (0-1)
            - am_class: Classification
            - am_found: Whether variant was found in database
    """
    close_db = False
    if db is None:
        db = AlphaMissenseDB()
        close_db = True

    try:
        annotated = []

        for variant in variants:
            # Extract coordinates with flexible key names
            chrom = variant.get("chrom") or variant.get("chromosome", "")
            pos = variant.get("pos") or variant.get("position", 0)
            ref = variant.get("ref", "")
            alt = variant.get("alt", "")

            # Skip if missing required fields
            if not all([chrom, pos, ref, alt]):
                annotated_var = variant.copy()
                annotated_var.update({
                    "am_pathogenicity": None,
                    "am_class": None,
                    "am_found": False,
                })
                annotated.append(annotated_var)
                continue

            # Query database
            result = db.lookup_variant(str(chrom), int(pos), ref, alt)

            annotated_var = variant.copy()

            if result:
                annotated_var.update({
                    "am_pathogenicity": result.am_pathogenicity,
                    "am_class": result.am_class,
                    "am_found": True,
                    "uniprot_id": result.uniprot_id,
                    "protein_variant": result.protein_variant,
                })

                # Filter ambiguous if requested
                if not include_ambiguous and result.is_ambiguous:
                    continue
            else:
                annotated_var.update({
                    "am_pathogenicity": None,
                    "am_class": None,
                    "am_found": False,
                })

            annotated.append(annotated_var)

        return annotated

    finally:
        if close_db:
            db.close()


def filter_pathogenic(
    variants: list[dict],
    threshold: float = PATHOGENIC_THRESHOLD,
    require_annotation: bool = True,
) -> list[dict]:
    """
    Filter variants to keep only likely pathogenic ones.

    Args:
        variants: List of annotated variant dictionaries
        threshold: Pathogenicity threshold (default: 0.564 from paper)
        require_annotation: Only include variants with AlphaMissense annotation

    Returns:
        Filtered list of pathogenic variants
    """
    filtered = []

    for variant in variants:
        score = variant.get("am_pathogenicity")

        if score is None:
            if not require_annotation:
                filtered.append(variant)
            continue

        if score >= threshold:
            filtered.append(variant)

    return filtered


def filter_benign(
    variants: list[dict],
    threshold: float = BENIGN_THRESHOLD,
) -> list[dict]:
    """
    Filter variants to keep only likely benign ones.

    Args:
        variants: List of annotated variant dictionaries
        threshold: Benign threshold (default: 0.34 from paper)

    Returns:
        Filtered list of benign variants
    """
    return [
        v for v in variants
        if v.get("am_pathogenicity") is not None
        and v["am_pathogenicity"] < threshold
    ]


def classify_variants(
    variants: list[dict],
) -> dict[str, list[dict]]:
    """
    Classify variants into pathogenic, benign, and ambiguous categories.

    Args:
        variants: List of annotated variant dictionaries

    Returns:
        Dictionary with keys: 'pathogenic', 'benign', 'ambiguous', 'not_found'
    """
    classified = {
        "pathogenic": [],
        "benign": [],
        "ambiguous": [],
        "not_found": [],
    }

    for variant in variants:
        score = variant.get("am_pathogenicity")

        if score is None:
            classified["not_found"].append(variant)
        elif score > PATHOGENIC_THRESHOLD:
            classified["pathogenic"].append(variant)
        elif score < BENIGN_THRESHOLD:
            classified["benign"].append(variant)
        else:
            classified["ambiguous"].append(variant)

    return classified


def compute_summary_statistics(variants: list[dict]) -> dict:
    """
    Compute summary statistics for annotated variants.

    Args:
        variants: List of annotated variant dictionaries

    Returns:
        Dictionary with summary statistics
    """
    scores = [
        v["am_pathogenicity"]
        for v in variants
        if v.get("am_pathogenicity") is not None
    ]

    if not scores:
        return {
            "total": len(variants),
            "annotated": 0,
            "not_found": len(variants),
            "mean_score": None,
            "max_score": None,
            "min_score": None,
            "pathogenic_count": 0,
            "benign_count": 0,
            "ambiguous_count": 0,
        }

    classified = classify_variants(variants)

    return {
        "total": len(variants),
        "annotated": len(scores),
        "not_found": len(classified["not_found"]),
        "mean_score": sum(scores) / len(scores),
        "max_score": max(scores),
        "min_score": min(scores),
        "pathogenic_count": len(classified["pathogenic"]),
        "benign_count": len(classified["benign"]),
        "ambiguous_count": len(classified["ambiguous"]),
    }
