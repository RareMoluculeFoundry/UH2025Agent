"""
AlphaGenome API Client

Provides a cached client for the AlphaGenome API, which predicts the effects
of genetic variants on chromatin accessibility and gene expression.

Reference:
    AlphaGenome predicts regulatory effects across the human genome.
    https://deepmind.google/discover/blog/alphagenome/
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .cache import PredictionCache


# Default cache directory
DEFAULT_CACHE_DIR = Path(__file__).parent.parent.parent / "cache"


@dataclass
class GenomicInterval:
    """Genomic interval specification."""

    chrom: str
    start: int
    end: int

    def __str__(self):
        return f"{self.chrom}:{self.start}-{self.end}"

    @classmethod
    def from_variant(cls, chrom: str, pos: int, context_size: int = 10000):
        """Create interval centered on a variant position."""
        return cls(
            chrom=chrom,
            start=max(0, pos - context_size // 2),
            end=pos + context_size // 2,
        )


@dataclass
class VariantEffect:
    """Predicted effect of a variant."""

    variant_id: str
    chrom: str
    pos: int
    ref: str
    alt: str
    effect_size: float
    effect_direction: Literal["increase", "decrease", "neutral"]
    confidence: float
    tissue: str | None
    gene: str | None
    regulatory_element: str | None
    p_value: float | None

    def to_dict(self) -> dict:
        return {
            "variant_id": self.variant_id,
            "chrom": self.chrom,
            "pos": self.pos,
            "ref": self.ref,
            "alt": self.alt,
            "effect_size": self.effect_size,
            "effect_direction": self.effect_direction,
            "confidence": self.confidence,
            "tissue": self.tissue,
            "gene": self.gene,
            "regulatory_element": self.regulatory_element,
            "p_value": self.p_value,
        }


class AlphaGenomeClient:
    """
    Client for AlphaGenome API with caching.

    The AlphaGenome API predicts the effects of genetic variants on:
    - Chromatin accessibility
    - Gene expression
    - Regulatory element activity

    Example:
        >>> client = AlphaGenomeClient(api_key="your-key")
        >>> effect = client.predict_variant(
        ...     chrom="chr17",
        ...     pos=62068646,
        ...     ref="A",
        ...     alt="G",
        ...     gene="SCN4A"
        ... )
        >>> print(f"Effect: {effect.effect_size}")
    """

    def __init__(
        self,
        api_key: str | None = None,
        cache_dir: Path | str | None = None,
        use_cache: bool = True,
    ):
        """
        Initialize AlphaGenome client.

        Args:
            api_key: AlphaGenome API key (or set ALPHAGENOME_API_KEY env var)
            cache_dir: Directory for caching predictions
            use_cache: Whether to cache API responses
        """
        import os

        self.api_key = api_key or os.environ.get("ALPHAGENOME_API_KEY")

        if cache_dir is None:
            cache_dir = DEFAULT_CACHE_DIR
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.use_cache = use_cache
        self._cache = PredictionCache(self.cache_dir) if use_cache else None

        # API base URL (placeholder - actual API uses gRPC)
        self._api_url = "https://api.alphagenome.deepmind.com/v1"

    def predict_variant(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        gene: str | None = None,
        tissue: str | None = None,
        context_size: int = 10000,
    ) -> VariantEffect:
        """
        Predict the regulatory effect of a variant.

        Args:
            chrom: Chromosome (with or without 'chr' prefix)
            pos: Position (1-based)
            ref: Reference allele
            alt: Alternate allele
            gene: Target gene (optional, for eQTL analysis)
            tissue: Specific tissue (optional)
            context_size: Genomic context window size

        Returns:
            VariantEffect with predicted regulatory impact
        """
        # Normalize chromosome
        chrom = chrom if chrom.startswith("chr") else f"chr{chrom}"

        # Generate cache key
        cache_key = self._make_cache_key(chrom, pos, ref, alt, gene, tissue)

        # Check cache
        if self._cache:
            cached = self._cache.get(cache_key)
            if cached:
                return self._deserialize_effect(cached)

        # Make API call (or mock for now)
        effect = self._call_api(chrom, pos, ref, alt, gene, tissue, context_size)

        # Cache result
        if self._cache:
            self._cache.set(cache_key, self._serialize_effect(effect))

        return effect

    def predict_eqtl(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        gene: str,
        tissues: list[str] | None = None,
    ) -> list[VariantEffect]:
        """
        Predict eQTL effects across tissues.

        Args:
            chrom: Chromosome
            pos: Position
            ref: Reference allele
            alt: Alternate allele
            gene: Target gene symbol
            tissues: List of tissues (default: common tissues)

        Returns:
            List of VariantEffect for each tissue
        """
        if tissues is None:
            tissues = [
                "skeletal_muscle",
                "heart",
                "brain",
                "liver",
                "adipose",
            ]

        effects = []
        for tissue in tissues:
            effect = self.predict_variant(
                chrom, pos, ref, alt, gene=gene, tissue=tissue
            )
            effects.append(effect)

        return effects

    def batch_predict(
        self,
        variants: list[dict],
        gene: str | None = None,
    ) -> list[VariantEffect]:
        """
        Predict effects for multiple variants.

        Args:
            variants: List of variant dicts with chrom, pos, ref, alt
            gene: Target gene (applied to all variants)

        Returns:
            List of VariantEffect predictions
        """
        effects = []

        for var in variants:
            effect = self.predict_variant(
                chrom=var.get("chrom", var.get("chromosome")),
                pos=var.get("pos", var.get("position")),
                ref=var["ref"],
                alt=var["alt"],
                gene=gene or var.get("gene"),
            )
            effects.append(effect)

        return effects

    def _call_api(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        gene: str | None,
        tissue: str | None,
        context_size: int,
    ) -> VariantEffect:
        """
        Make API call (mock implementation).

        In production, this would use the actual AlphaGenome gRPC API.
        For now, returns a mock prediction based on variant characteristics.
        """
        # Mock implementation - generate realistic predictions
        # In production, this calls the actual API

        variant_id = f"{chrom}:{pos}:{ref}>{alt}"

        # Mock effect calculation based on variant type
        # Real API uses deep learning on genomic context
        if gene and gene in ["SCN4A", "SCN1A", "CACNA1S"]:
            # Ion channel genes - higher regulatory impact
            effect_size = 0.45
            effect_dir = "decrease"
            confidence = 0.85
        elif tissue == "skeletal_muscle":
            effect_size = 0.32
            effect_dir = "decrease"
            confidence = 0.78
        else:
            effect_size = 0.15
            effect_dir = "neutral"
            confidence = 0.65

        return VariantEffect(
            variant_id=variant_id,
            chrom=chrom,
            pos=pos,
            ref=ref,
            alt=alt,
            effect_size=effect_size,
            effect_direction=effect_dir,
            confidence=confidence,
            tissue=tissue,
            gene=gene,
            regulatory_element="enhancer" if effect_size > 0.3 else None,
            p_value=0.001 if confidence > 0.8 else 0.05,
        )

    def _make_cache_key(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
        gene: str | None,
        tissue: str | None,
    ) -> str:
        """Generate cache key for a query."""
        key_data = f"{chrom}:{pos}:{ref}:{alt}:{gene}:{tissue}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _serialize_effect(self, effect: VariantEffect) -> dict:
        """Serialize effect for caching."""
        return effect.to_dict()

    def _deserialize_effect(self, data: dict) -> VariantEffect:
        """Deserialize effect from cache."""
        return VariantEffect(**data)


def create_cached_client(
    api_key: str | None = None,
    cache_dir: Path | str | None = None,
) -> AlphaGenomeClient:
    """
    Create an AlphaGenome client with caching enabled.

    Args:
        api_key: API key (or set ALPHAGENOME_API_KEY env var)
        cache_dir: Cache directory path

    Returns:
        Configured AlphaGenomeClient
    """
    return AlphaGenomeClient(
        api_key=api_key,
        cache_dir=cache_dir,
        use_cache=True,
    )
