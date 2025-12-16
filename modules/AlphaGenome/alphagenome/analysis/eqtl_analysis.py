"""
AlphaGenome eQTL Analysis

Functions for analyzing expression quantitative trait loci (eQTL) effects
of genetic variants across tissues.
"""

from dataclasses import dataclass
from typing import Literal

from ..api.client import AlphaGenomeClient, VariantEffect


@dataclass
class eQTLResult:
    """Result of eQTL analysis for a variant-gene pair."""

    variant_id: str
    gene: str
    best_tissue: str
    best_effect_size: float
    significant_tissues: list[str]
    tissue_effects: dict[str, float]
    overall_significance: Literal["high", "moderate", "low"]

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "gene": self.gene,
            "best_tissue": self.best_tissue,
            "best_effect_size": self.best_effect_size,
            "significant_tissues": self.significant_tissues,
            "tissue_effects": self.tissue_effects,
            "overall_significance": self.overall_significance,
        }


# Common tissues for eQTL analysis
GTEX_TISSUES = [
    "skeletal_muscle",
    "heart_left_ventricle",
    "brain_cortex",
    "liver",
    "adipose_subcutaneous",
    "whole_blood",
    "nerve_tibial",
    "skin_sun_exposed",
    "thyroid",
    "lung",
]


def analyze_eqtl_effects(
    variants: list[dict],
    gene: str,
    client: AlphaGenomeClient | None = None,
    tissues: list[str] | None = None,
    effect_threshold: float = 0.2,
) -> list[eQTLResult]:
    """
    Analyze eQTL effects of variants on a gene across tissues.

    Args:
        variants: List of variant dicts with chrom, pos, ref, alt
        gene: Target gene symbol
        client: AlphaGenome client (creates new if None)
        tissues: Tissues to analyze (default: common GTEx tissues)
        effect_threshold: Minimum effect size for significance

    Returns:
        List of eQTLResult for each variant
    """
    close_client = False
    if client is None:
        client = AlphaGenomeClient()
        close_client = True

    if tissues is None:
        tissues = GTEX_TISSUES[:5]  # Top 5 tissues

    try:
        results = []

        for var in variants:
            chrom = var.get("chrom", var.get("chromosome"))
            pos = var.get("pos", var.get("position"))
            ref = var.get("ref")
            alt = var.get("alt")

            if not all([chrom, pos, ref, alt]):
                continue

            # Get predictions across tissues
            tissue_effects = {}
            effects = []

            for tissue in tissues:
                effect = client.predict_variant(
                    chrom=chrom,
                    pos=pos,
                    ref=ref,
                    alt=alt,
                    gene=gene,
                    tissue=tissue,
                )
                tissue_effects[tissue] = effect.effect_size
                effects.append(effect)

            # Find significant tissues
            significant = [
                t for t, e in tissue_effects.items()
                if abs(e) >= effect_threshold
            ]

            # Determine best tissue
            best_tissue = max(tissue_effects, key=lambda t: abs(tissue_effects[t]))
            best_effect = tissue_effects[best_tissue]

            # Overall significance
            if abs(best_effect) >= 0.4:
                significance = "high"
            elif abs(best_effect) >= 0.2:
                significance = "moderate"
            else:
                significance = "low"

            result = eQTLResult(
                variant_id=f"{chrom}:{pos}:{ref}>{alt}",
                gene=gene,
                best_tissue=best_tissue,
                best_effect_size=best_effect,
                significant_tissues=significant,
                tissue_effects=tissue_effects,
                overall_significance=significance,
            )

            results.append(result)

        return results

    finally:
        if close_client:
            pass  # Client has no close method needed


def identify_regulatory_variants(
    variants: list[dict],
    gene: str,
    client: AlphaGenomeClient | None = None,
    min_effect: float = 0.3,
) -> list[dict]:
    """
    Identify variants with significant regulatory effects on a gene.

    Args:
        variants: List of variant dictionaries
        gene: Target gene
        client: AlphaGenome client
        min_effect: Minimum effect size to consider regulatory

    Returns:
        List of variants with regulatory effects, annotated with predictions
    """
    eqtl_results = analyze_eqtl_effects(
        variants, gene, client, effect_threshold=min_effect
    )

    regulatory = []

    for i, result in enumerate(eqtl_results):
        if result.overall_significance in ("high", "moderate"):
            var = variants[i].copy()
            var.update({
                "eqtl_gene": gene,
                "eqtl_effect_size": result.best_effect_size,
                "eqtl_tissue": result.best_tissue,
                "eqtl_significance": result.overall_significance,
                "is_regulatory": True,
            })
            regulatory.append(var)

    return regulatory


def compute_regulatory_burden(
    variants: list[dict],
    genes: list[str],
    client: AlphaGenomeClient | None = None,
) -> dict:
    """
    Compute regulatory burden across multiple genes.

    Args:
        variants: List of variants to analyze
        genes: List of gene symbols
        client: AlphaGenome client

    Returns:
        Dictionary with regulatory burden statistics
    """
    all_regulatory = []

    for gene in genes:
        regulatory = identify_regulatory_variants(variants, gene, client)
        all_regulatory.extend(regulatory)

    # Compute statistics
    if not all_regulatory:
        return {
            "total_variants": len(variants),
            "regulatory_variants": 0,
            "affected_genes": [],
            "burden_score": 0.0,
        }

    affected_genes = list(set(v["eqtl_gene"] for v in all_regulatory))
    effects = [v["eqtl_effect_size"] for v in all_regulatory]

    return {
        "total_variants": len(variants),
        "regulatory_variants": len(all_regulatory),
        "affected_genes": affected_genes,
        "burden_score": sum(abs(e) for e in effects) / len(variants),
        "max_effect": max(abs(e) for e in effects),
        "high_impact_count": sum(1 for v in all_regulatory if v["eqtl_significance"] == "high"),
    }
