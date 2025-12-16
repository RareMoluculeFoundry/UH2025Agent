"""
AlphaGenome Splice Effect Prediction

Functions for predicting splicing effects of genetic variants.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class SpliceEffect:
    """Predicted splice effect of a variant."""

    variant_id: str
    effect_type: Literal["donor_loss", "acceptor_loss", "donor_gain", "acceptor_gain", "none"]
    delta_score: float  # Change in splice site strength
    confidence: float
    affected_exon: int | None
    transcript_id: str | None
    consequence: str  # Human-readable consequence

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "effect_type": self.effect_type,
            "delta_score": self.delta_score,
            "confidence": self.confidence,
            "affected_exon": self.affected_exon,
            "transcript_id": self.transcript_id,
            "consequence": self.consequence,
        }


# Splice site motif positions relative to exon boundary
DONOR_POSITIONS = range(-3, 9)  # 3 bp in exon, 6 bp in intron
ACCEPTOR_POSITIONS = range(-20, 4)  # 20 bp in intron, 3 bp in exon


def predict_splice_impact(
    variants: list[dict],
    transcript_id: str | None = None,
) -> list[SpliceEffect]:
    """
    Predict splice site impacts of variants.

    This is a simplified implementation that checks variant positions
    relative to canonical splice sites. In production, this would use
    deep learning models like SpliceAI or MMSplice.

    Args:
        variants: List of variant dicts with chrom, pos, ref, alt
        transcript_id: Transcript to analyze (optional)

    Returns:
        List of SpliceEffect predictions
    """
    effects = []

    for var in variants:
        chrom = var.get("chrom", var.get("chromosome", ""))
        pos = var.get("pos", var.get("position", 0))
        ref = var.get("ref", "")
        alt = var.get("alt", "")

        variant_id = f"{chrom}:{pos}:{ref}>{alt}"

        # Check for splice site disruption based on position
        # This is a simplified heuristic - real implementation uses ML models
        effect = _predict_splice_effect_mock(var)

        effects.append(SpliceEffect(
            variant_id=variant_id,
            effect_type=effect["type"],
            delta_score=effect["delta"],
            confidence=effect["confidence"],
            affected_exon=effect.get("exon"),
            transcript_id=transcript_id,
            consequence=effect["consequence"],
        ))

    return effects


def _predict_splice_effect_mock(variant: dict) -> dict:
    """
    Mock splice effect prediction.

    In production, this would call SpliceAI or similar model.
    """
    ref = variant.get("ref", "")
    alt = variant.get("alt", "")

    # Check for common splice-affecting patterns
    # GT at donor site, AG at acceptor site

    if ref == "G" and alt in ["A", "C"]:
        # Possible donor site disruption (GT -> AT/CT)
        return {
            "type": "donor_loss",
            "delta": -0.45,
            "confidence": 0.7,
            "consequence": "Potential loss of splice donor site",
        }
    elif ref == "A" and alt in ["G", "C", "T"]:
        # Possible acceptor site disruption (AG -> GG/CG/TG)
        return {
            "type": "acceptor_loss",
            "delta": -0.38,
            "confidence": 0.65,
            "consequence": "Potential loss of splice acceptor site",
        }
    elif len(ref) != len(alt):
        # Indel - may affect splicing
        return {
            "type": "none",
            "delta": -0.15,
            "confidence": 0.5,
            "consequence": "Indel may affect splicing (requires detailed analysis)",
        }
    else:
        return {
            "type": "none",
            "delta": 0.0,
            "confidence": 0.8,
            "consequence": "No predicted splice effect",
        }


def filter_splice_affecting(
    variants: list[dict],
    min_delta: float = 0.2,
) -> list[dict]:
    """
    Filter variants to those predicted to affect splicing.

    Args:
        variants: List of variant dictionaries
        min_delta: Minimum splice score change to consider significant

    Returns:
        Variants with predicted splice effects
    """
    effects = predict_splice_impact(variants)

    splice_affecting = []
    for var, effect in zip(variants, effects):
        if abs(effect.delta_score) >= min_delta:
            annotated = var.copy()
            annotated.update({
                "splice_effect": effect.effect_type,
                "splice_delta": effect.delta_score,
                "splice_consequence": effect.consequence,
            })
            splice_affecting.append(annotated)

    return splice_affecting
