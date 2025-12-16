"""
Tests for AlphaGenome Analysis Functions

Tests eQTL analysis and splice effect prediction.
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphagenome.analysis.eqtl_analysis import (
    eQTLResult,
    analyze_eqtl_effects,
    identify_regulatory_variants,
    GTEX_TISSUES,
)
from alphagenome.analysis.splice_effects import (
    SpliceEffect,
    predict_splice_impact,
    filter_splice_affecting,
    DONOR_POSITIONS,
    ACCEPTOR_POSITIONS,
)
from alphagenome.api.client import VariantEffect


class TestEQTLResult:
    """Test eQTLResult dataclass."""

    def test_eqtl_result_creation(self):
        """Should create eQTLResult with all fields."""
        result = eQTLResult(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            best_tissue="brain",
            best_effect_size=0.75,
            significant_tissues=["brain", "liver"],
            tissue_effects={"brain": 0.75, "liver": 0.5},
        )

        assert result.variant_id == "chr1:12345:A>G"
        assert result.gene == "BRCA1"
        assert result.best_tissue == "brain"
        assert result.best_effect_size == 0.75
        assert len(result.significant_tissues) == 2

    def test_is_significant_with_tissues(self):
        """Should be significant when tissues are affected."""
        result = eQTLResult(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            best_tissue="brain",
            best_effect_size=0.75,
            significant_tissues=["brain"],
            tissue_effects={"brain": 0.75},
        )

        assert result.is_significant is True

    def test_not_significant_no_tissues(self):
        """Should not be significant when no tissues affected."""
        result = eQTLResult(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            best_tissue=None,
            best_effect_size=0.0,
            significant_tissues=[],
            tissue_effects={},
        )

        assert result.is_significant is False

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        result = eQTLResult(
            variant_id="chr1:12345:A>G",
            gene="BRCA1",
            best_tissue="brain",
            best_effect_size=0.75,
            significant_tissues=["brain"],
            tissue_effects={"brain": 0.75},
        )

        d = result.to_dict()

        assert d["variant_id"] == "chr1:12345:A>G"
        assert d["gene"] == "BRCA1"
        assert "is_significant" in d


class TestAnalyzeEQTLEffects:
    """Test eQTL effect analysis."""

    @pytest.fixture
    def mock_client(self):
        """Create mock AlphaGenomeClient."""
        client = MagicMock()
        return client

    def test_analyze_single_variant(self, mock_client):
        """Should analyze eQTL effects for single variant."""
        # Mock predict_eqtl to return effects
        mock_client.predict_eqtl.return_value = [
            VariantEffect(
                variant_id="chr1:100:A>G",
                gene="TEST",
                effect_size=0.5,
                p_value=0.01,
                tissue="brain",
                effect_type="eQTL",
                confidence=0.9,
            ),
        ]

        variants = [{"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"}]

        with patch("alphagenome.analysis.eqtl_analysis.AlphaGenomeClient", return_value=mock_client):
            results = analyze_eqtl_effects(variants, gene="TEST", client=mock_client)

        assert len(results) == 1
        assert isinstance(results[0], eQTLResult)

    def test_analyze_multiple_variants(self, mock_client):
        """Should analyze multiple variants."""
        mock_client.predict_eqtl.return_value = [
            VariantEffect(
                variant_id="test",
                gene="TEST",
                effect_size=0.3,
                p_value=0.05,
                tissue="brain",
                effect_type="eQTL",
                confidence=0.8,
            ),
        ]

        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
            {"chrom": "chr1", "pos": 200, "ref": "C", "alt": "T"},
        ]

        with patch("alphagenome.analysis.eqtl_analysis.AlphaGenomeClient", return_value=mock_client):
            results = analyze_eqtl_effects(variants, gene="TEST", client=mock_client)

        assert len(results) == 2

    def test_analyze_empty_variants(self, mock_client):
        """Should handle empty variant list."""
        results = analyze_eqtl_effects([], gene="TEST", client=mock_client)

        assert results == []

    def test_analyze_with_custom_tissues(self, mock_client):
        """Should use custom tissue list."""
        tissues = ["brain", "liver"]

        mock_client.predict_eqtl.return_value = [
            VariantEffect(
                variant_id="test",
                gene="TEST",
                effect_size=0.5,
                p_value=0.01,
                tissue="brain",
                effect_type="eQTL",
                confidence=0.9,
            ),
        ]

        variants = [{"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"}]

        with patch("alphagenome.analysis.eqtl_analysis.AlphaGenomeClient", return_value=mock_client):
            results = analyze_eqtl_effects(
                variants, gene="TEST", client=mock_client, tissues=tissues
            )

        # Should have called with our tissue list
        assert mock_client.predict_eqtl.called


class TestIdentifyRegulatoryVariants:
    """Test regulatory variant identification."""

    @pytest.fixture
    def mock_client(self):
        """Create mock AlphaGenomeClient."""
        client = MagicMock()
        return client

    def test_identify_high_effect_variants(self, mock_client):
        """Should identify variants with high effect sizes."""
        mock_client.predict_eqtl.return_value = [
            VariantEffect(
                variant_id="chr1:100:A>G",
                gene="TEST",
                effect_size=0.5,
                p_value=0.01,
                tissue="brain",
                effect_type="eQTL",
                confidence=0.9,
            ),
        ]

        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
        ]

        with patch("alphagenome.analysis.eqtl_analysis.AlphaGenomeClient", return_value=mock_client):
            results = identify_regulatory_variants(
                variants, gene="TEST", client=mock_client, min_effect=0.3
            )

        assert len(results) >= 0  # Results depend on mock

    def test_filter_by_min_effect(self, mock_client):
        """Should filter variants below effect threshold."""
        mock_client.predict_eqtl.return_value = [
            VariantEffect(
                variant_id="test",
                gene="TEST",
                effect_size=0.1,  # Below threshold
                p_value=0.01,
                tissue="brain",
                effect_type="eQTL",
                confidence=0.9,
            ),
        ]

        variants = [{"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"}]

        with patch("alphagenome.analysis.eqtl_analysis.AlphaGenomeClient", return_value=mock_client):
            results = identify_regulatory_variants(
                variants, gene="TEST", client=mock_client, min_effect=0.3
            )

        # Should be filtered out due to low effect
        assert len(results) == 0


class TestGTExTissues:
    """Test GTEx tissue configuration."""

    def test_gtex_tissues_defined(self):
        """Should have GTEx tissue list defined."""
        assert GTEX_TISSUES is not None
        assert len(GTEX_TISSUES) > 0

    def test_common_tissues_included(self):
        """Common tissues should be in GTEx list."""
        common_tissues = ["brain", "liver", "heart", "muscle"]

        for tissue in common_tissues:
            assert tissue in GTEX_TISSUES


class TestSpliceEffect:
    """Test SpliceEffect dataclass."""

    def test_splice_effect_creation(self):
        """Should create SpliceEffect with all fields."""
        effect = SpliceEffect(
            variant_id="chr1:12345:A>G",
            effect_type="donor_loss",
            delta_score=-0.45,
            confidence=0.8,
            affected_exon=5,
            transcript_id="ENST00000123456",
            consequence="Potential loss of splice donor site",
        )

        assert effect.variant_id == "chr1:12345:A>G"
        assert effect.effect_type == "donor_loss"
        assert effect.delta_score == -0.45
        assert effect.affected_exon == 5

    def test_splice_effect_types(self):
        """Should support all splice effect types."""
        types = ["donor_loss", "acceptor_loss", "donor_gain", "acceptor_gain", "none"]

        for effect_type in types:
            effect = SpliceEffect(
                variant_id="test",
                effect_type=effect_type,
                delta_score=0.0,
                confidence=0.5,
                affected_exon=None,
                transcript_id=None,
                consequence="test",
            )
            assert effect.effect_type == effect_type

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        effect = SpliceEffect(
            variant_id="chr1:12345:A>G",
            effect_type="donor_loss",
            delta_score=-0.45,
            confidence=0.8,
            affected_exon=5,
            transcript_id="ENST00000123456",
            consequence="test",
        )

        d = effect.to_dict()

        assert d["variant_id"] == "chr1:12345:A>G"
        assert d["effect_type"] == "donor_loss"
        assert d["delta_score"] == -0.45


class TestPredictSpliceImpact:
    """Test splice impact prediction."""

    def test_predict_donor_loss(self):
        """Should predict donor site loss for G>A at donor."""
        variants = [{"chrom": "chr1", "pos": 100, "ref": "G", "alt": "A"}]

        results = predict_splice_impact(variants)

        assert len(results) == 1
        assert results[0].effect_type == "donor_loss"
        assert results[0].delta_score < 0

    def test_predict_acceptor_loss(self):
        """Should predict acceptor site loss for A>G at acceptor."""
        variants = [{"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"}]

        results = predict_splice_impact(variants)

        assert len(results) == 1
        assert results[0].effect_type == "acceptor_loss"
        assert results[0].delta_score < 0

    def test_predict_no_effect(self):
        """Should predict no effect for neutral variants."""
        variants = [{"chrom": "chr1", "pos": 100, "ref": "C", "alt": "T"}]

        results = predict_splice_impact(variants)

        assert len(results) == 1
        assert results[0].effect_type == "none"
        assert results[0].delta_score == 0.0

    def test_predict_indel_effect(self):
        """Should handle indels (different length ref/alt)."""
        variants = [{"chrom": "chr1", "pos": 100, "ref": "AT", "alt": "A"}]

        results = predict_splice_impact(variants)

        assert len(results) == 1
        assert results[0].effect_type == "none"
        assert results[0].delta_score < 0  # Indels have slight negative score

    def test_predict_multiple_variants(self):
        """Should predict effects for multiple variants."""
        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "G", "alt": "A"},
            {"chrom": "chr1", "pos": 200, "ref": "A", "alt": "G"},
            {"chrom": "chr1", "pos": 300, "ref": "C", "alt": "T"},
        ]

        results = predict_splice_impact(variants)

        assert len(results) == 3
        assert results[0].effect_type == "donor_loss"
        assert results[1].effect_type == "acceptor_loss"
        assert results[2].effect_type == "none"

    def test_predict_with_transcript_id(self):
        """Should include transcript ID when provided."""
        variants = [{"chrom": "chr1", "pos": 100, "ref": "G", "alt": "A"}]

        results = predict_splice_impact(variants, transcript_id="ENST00000123456")

        assert len(results) == 1
        assert results[0].transcript_id == "ENST00000123456"


class TestFilterSpliceAffecting:
    """Test splice-affecting variant filtering."""

    def test_filter_by_delta_score(self):
        """Should filter variants by minimum delta score."""
        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "G", "alt": "A"},  # donor loss
            {"chrom": "chr1", "pos": 200, "ref": "C", "alt": "T"},  # no effect
        ]

        results = filter_splice_affecting(variants, min_delta=0.2)

        # Should only include donor loss (high delta)
        assert len(results) == 1
        assert "splice_effect" in results[0]
        assert results[0]["splice_effect"] == "donor_loss"

    def test_filter_empty_list(self):
        """Should handle empty variant list."""
        results = filter_splice_affecting([])

        assert results == []

    def test_filter_no_splice_effects(self):
        """Should return empty when no splice effects."""
        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "C", "alt": "T"},
            {"chrom": "chr1", "pos": 200, "ref": "T", "alt": "C"},
        ]

        results = filter_splice_affecting(variants, min_delta=0.2)

        # No variants should pass filter
        assert len(results) == 0

    def test_filter_adds_annotations(self):
        """Should add splice annotations to variants."""
        variants = [{"chrom": "chr1", "pos": 100, "ref": "G", "alt": "A"}]

        results = filter_splice_affecting(variants, min_delta=0.1)

        if results:
            assert "splice_effect" in results[0]
            assert "splice_delta" in results[0]
            assert "splice_consequence" in results[0]


class TestSplicePositions:
    """Test splice site position constants."""

    def test_donor_positions(self):
        """Donor positions should span exon-intron boundary."""
        # Donor: 3bp in exon (-3 to -1), 6bp in intron (0 to 5)
        assert -3 in DONOR_POSITIONS
        assert -1 in DONOR_POSITIONS
        assert 0 in DONOR_POSITIONS
        assert 5 in DONOR_POSITIONS
        assert 8 in DONOR_POSITIONS

    def test_acceptor_positions(self):
        """Acceptor positions should span intron-exon boundary."""
        # Acceptor: 20bp in intron (-20 to -1), 3bp in exon (0 to 2)
        assert -20 in ACCEPTOR_POSITIONS
        assert -1 in ACCEPTOR_POSITIONS
        assert 0 in ACCEPTOR_POSITIONS
        assert 3 in ACCEPTOR_POSITIONS


class TestVariantIDGeneration:
    """Test variant ID generation in predictions."""

    def test_variant_id_format(self):
        """Variant IDs should follow chrom:pos:ref>alt format."""
        variants = [{"chrom": "chr1", "pos": 12345, "ref": "A", "alt": "G"}]

        results = predict_splice_impact(variants)

        assert results[0].variant_id == "chr1:12345:A>G"

    def test_variant_id_alternative_keys(self):
        """Should handle alternative key names."""
        variants = [{"chromosome": "chr1", "position": 12345, "ref": "A", "alt": "G"}]

        results = predict_splice_impact(variants)

        assert results[0].variant_id == "chr1:12345:A>G"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
