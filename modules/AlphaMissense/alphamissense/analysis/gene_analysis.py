"""
AlphaMissense Gene-Level Analysis

Functions for computing gene-level pathogenicity burden and identifying
high-risk genes based on variant predictions.
"""

from dataclasses import dataclass
from typing import Literal

from ..data.loader import AlphaMissenseDB, PATHOGENIC_THRESHOLD


@dataclass
class GeneBurden:
    """Gene-level pathogenicity burden statistics."""

    gene_symbol: str
    uniprot_id: str
    total_variants: int
    pathogenic_count: int
    benign_count: int
    ambiguous_count: int
    mean_pathogenicity: float
    max_pathogenicity: float
    pathogenic_fraction: float

    @property
    def is_high_burden(self) -> bool:
        """Check if gene has high pathogenic burden."""
        return self.pathogenic_fraction > 0.1 or self.max_pathogenicity > 0.9


# UniProt ID to gene symbol mapping (common rare disease genes)
# In production, this would use UniProt API or local mapping file
UNIPROT_TO_GENE = {
    "P35498": "SCN4A",  # Sodium channel (myotonia, periodic paralysis)
    "P35499": "SCN1A",  # Sodium channel (epilepsy)
    "P21817": "RYR1",   # Ryanodine receptor (malignant hyperthermia)
    "Q13698": "CACNA1S", # Calcium channel (periodic paralysis)
    "P35523": "CLCN1",  # Chloride channel (myotonia)
    "Q9UQD0": "SCN8A",  # Sodium channel (epilepsy)
    "O43526": "KCNQ2",  # Potassium channel (epilepsy)
    "P51787": "KCNQ1",  # Potassium channel (Long QT)
    "Q12809": "KCNH2",  # Potassium channel (Long QT)
    "P08684": "CYP3A4", # Cytochrome P450
}


def compute_gene_burden(
    uniprot_ids: list[str],
    db: AlphaMissenseDB | None = None,
    metric: Literal["mean", "max", "weighted"] = "mean",
) -> list[GeneBurden]:
    """
    Compute pathogenicity burden for a list of genes.

    Args:
        uniprot_ids: List of UniProt accessions
        db: AlphaMissenseDB instance (creates new if None)
        metric: Burden metric to compute:
            - "mean": Average pathogenicity across all variants
            - "max": Maximum pathogenicity
            - "weighted": Weighted by variant frequency (not implemented)

    Returns:
        List of GeneBurden objects sorted by pathogenic_fraction
    """
    close_db = False
    if db is None:
        db = AlphaMissenseDB()
        close_db = True

    try:
        burdens = []

        for uniprot_id in uniprot_ids:
            variants = db.get_protein_variants(uniprot_id)

            if not variants:
                continue

            # Count by classification
            pathogenic = [v for v in variants if v.is_pathogenic]
            benign = [v for v in variants if v.is_benign]
            ambiguous = [v for v in variants if v.is_ambiguous]

            # Compute scores
            scores = [v.am_pathogenicity for v in variants]
            mean_score = sum(scores) / len(scores) if scores else 0.0
            max_score = max(scores) if scores else 0.0

            # Get gene symbol
            gene_symbol = UNIPROT_TO_GENE.get(uniprot_id, uniprot_id)

            burden = GeneBurden(
                gene_symbol=gene_symbol,
                uniprot_id=uniprot_id,
                total_variants=len(variants),
                pathogenic_count=len(pathogenic),
                benign_count=len(benign),
                ambiguous_count=len(ambiguous),
                mean_pathogenicity=mean_score,
                max_pathogenicity=max_score,
                pathogenic_fraction=len(pathogenic) / len(variants) if variants else 0.0,
            )

            burdens.append(burden)

        # Sort by pathogenic fraction (descending)
        burdens.sort(key=lambda x: x.pathogenic_fraction, reverse=True)

        return burdens

    finally:
        if close_db:
            db.close()


def get_pathogenic_genes(
    db: AlphaMissenseDB | None = None,
    min_pathogenic_fraction: float = 0.1,
    min_variants: int = 10,
) -> list[GeneBurden]:
    """
    Find genes with high pathogenic burden across all variants.

    Args:
        db: AlphaMissenseDB instance
        min_pathogenic_fraction: Minimum fraction of pathogenic variants
        min_variants: Minimum total variants to consider

    Returns:
        List of high-burden genes
    """
    # This would require a full database scan in production
    # For now, analyze common rare disease genes
    common_genes = list(UNIPROT_TO_GENE.keys())

    burdens = compute_gene_burden(common_genes, db)

    return [
        b for b in burdens
        if b.total_variants >= min_variants
        and b.pathogenic_fraction >= min_pathogenic_fraction
    ]


def analyze_patient_genes(
    variants: list[dict],
    db: AlphaMissenseDB | None = None,
) -> dict:
    """
    Analyze genes affected by patient variants.

    Args:
        variants: List of annotated variants with 'gene' or 'uniprot_id' key
        db: AlphaMissenseDB instance

    Returns:
        Dictionary with gene-level analysis:
            - affected_genes: List of genes with variants
            - gene_burdens: GeneBurden for each affected gene
            - high_risk_genes: Genes with high pathogenic burden
    """
    # Extract unique genes/proteins
    uniprot_ids = set()
    gene_to_uniprot = {}

    for var in variants:
        uniprot = var.get("uniprot_id")
        gene = var.get("gene")

        if uniprot:
            uniprot_ids.add(uniprot)
            if gene:
                gene_to_uniprot[gene] = uniprot

    if not uniprot_ids:
        return {
            "affected_genes": [],
            "gene_burdens": [],
            "high_risk_genes": [],
        }

    # Compute burden for affected genes
    burdens = compute_gene_burden(list(uniprot_ids), db)

    # Identify high-risk
    high_risk = [b for b in burdens if b.is_high_burden]

    return {
        "affected_genes": [b.gene_symbol for b in burdens],
        "gene_burdens": burdens,
        "high_risk_genes": high_risk,
    }
