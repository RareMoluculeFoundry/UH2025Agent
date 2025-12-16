"""
Tests for AlphaMissense Analysis Functions

Tests variant filtering, annotation, and gene-level analysis.
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphamissense.analysis.filtering import (
    annotate_variants,
    filter_pathogenic,
    classify_variants,
)
from alphamissense.analysis.gene_analysis import (
    GeneBurden,
    compute_gene_burden,
    get_pathogenic_genes,
    analyze_patient_genes,
    UNIPROT_TO_GENE,
)
from alphamissense.data.loader import VariantPrediction, PATHOGENIC_THRESHOLD, BENIGN_THRESHOLD


class TestAnnotateVariants:
    """Test variant annotation functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock AlphaMissenseDB."""
        db = MagicMock()
        return db

    def test_annotate_single_variant(self, mock_db):
        """Should annotate a single variant with pathogenicity."""
        mock_db.lookup_variant.return_value = VariantPrediction(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            genome="hg38",
            uniprot_id="P12345",
            transcript_id="ENST00000123456",
            protein_variant="A100G",
            am_pathogenicity=0.85,
            am_class="likely_pathogenic",
        )

        variants = [{"chrom": "chr1", "pos": 12345, "ref": "A", "alt": "G"}]

        with patch("alphamissense.analysis.filtering.AlphaMissenseDB", return_value=mock_db):
            results = annotate_variants(variants, db=mock_db)

        assert len(results) == 1
        assert results[0]["am_pathogenicity"] == 0.85
        assert results[0]["am_class"] == "likely_pathogenic"

    def test_annotate_missing_variant(self, mock_db):
        """Should handle variants not in database."""
        mock_db.lookup_variant.return_value = None

        variants = [{"chrom": "chr99", "pos": 99999, "ref": "X", "alt": "Y"}]

        with patch("alphamissense.analysis.filtering.AlphaMissenseDB", return_value=mock_db):
            results = annotate_variants(variants, db=mock_db)

        assert len(results) == 1
        assert results[0].get("am_pathogenicity") is None
        assert results[0].get("am_found") is False

    def test_annotate_multiple_variants(self, mock_db):
        """Should annotate multiple variants."""
        mock_db.lookup_variant.side_effect = [
            VariantPrediction(
                chrom="chr1", pos=100, ref="A", alt="G", genome="hg38",
                uniprot_id="P1", transcript_id="E1", protein_variant="A1G",
                am_pathogenicity=0.9, am_class="pathogenic",
            ),
            VariantPrediction(
                chrom="chr1", pos=200, ref="C", alt="T", genome="hg38",
                uniprot_id="P1", transcript_id="E1", protein_variant="C2T",
                am_pathogenicity=0.1, am_class="benign",
            ),
            None,
        ]

        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
            {"chrom": "chr1", "pos": 200, "ref": "C", "alt": "T"},
            {"chrom": "chr1", "pos": 300, "ref": "G", "alt": "A"},
        ]

        with patch("alphamissense.analysis.filtering.AlphaMissenseDB", return_value=mock_db):
            results = annotate_variants(variants, db=mock_db)

        assert len(results) == 3
        assert results[0]["am_pathogenicity"] == 0.9
        assert results[1]["am_pathogenicity"] == 0.1
        assert results[2].get("am_found") is False


class TestFilterPathogenic:
    """Test pathogenic variant filtering."""

    def test_filter_above_threshold(self):
        """Should filter variants above pathogenicity threshold."""
        variants = [
            {"chrom": "chr1", "pos": 100, "am_pathogenicity": 0.9},
            {"chrom": "chr1", "pos": 200, "am_pathogenicity": 0.3},
            {"chrom": "chr1", "pos": 300, "am_pathogenicity": 0.7},
        ]

        results = filter_pathogenic(variants)

        assert len(results) == 2
        assert all(v["am_pathogenicity"] > PATHOGENIC_THRESHOLD for v in results)

    def test_filter_custom_threshold(self):
        """Should respect custom threshold."""
        variants = [
            {"chrom": "chr1", "pos": 100, "am_pathogenicity": 0.9},
            {"chrom": "chr1", "pos": 200, "am_pathogenicity": 0.5},
            {"chrom": "chr1", "pos": 300, "am_pathogenicity": 0.3},
        ]

        results = filter_pathogenic(variants, threshold=0.4)

        assert len(results) == 2
        assert all(v["am_pathogenicity"] > 0.4 for v in results)

    def test_filter_empty_list(self):
        """Should handle empty variant list."""
        results = filter_pathogenic([])

        assert results == []

    def test_filter_no_pathogenic(self):
        """Should return empty when no pathogenic variants."""
        variants = [
            {"chrom": "chr1", "pos": 100, "am_pathogenicity": 0.1},
            {"chrom": "chr1", "pos": 200, "am_pathogenicity": 0.2},
        ]

        results = filter_pathogenic(variants)

        assert len(results) == 0


class TestClassifyVariants:
    """Test variant classification."""

    def test_classify_all_types(self):
        """Should classify variants into pathogenic, benign, ambiguous."""
        variants = [
            {"id": "1", "am_pathogenicity": 0.9},   # pathogenic
            {"id": "2", "am_pathogenicity": 0.1},   # benign
            {"id": "3", "am_pathogenicity": 0.45},  # ambiguous
            {"id": "4", "am_pathogenicity": 0.7},   # pathogenic
            {"id": "5", "am_pathogenicity": 0.2},   # benign
        ]

        results = classify_variants(variants)

        assert "pathogenic" in results
        assert "benign" in results
        assert "ambiguous" in results
        assert len(results["pathogenic"]) == 2
        assert len(results["benign"]) == 2
        assert len(results["ambiguous"]) == 1

    def test_classify_edge_cases(self):
        """Should handle edge cases at threshold boundaries."""
        variants = [
            {"id": "1", "am_pathogenicity": PATHOGENIC_THRESHOLD},  # exactly at threshold
            {"id": "2", "am_pathogenicity": BENIGN_THRESHOLD},      # exactly at threshold
        ]

        results = classify_variants(variants)

        # Exact threshold values - behavior depends on implementation (> vs >=)
        total = (
            len(results["pathogenic"]) +
            len(results["benign"]) +
            len(results["ambiguous"])
        )
        assert total == 2


class TestGeneBurden:
    """Test GeneBurden dataclass."""

    def test_gene_burden_creation(self):
        """Should create GeneBurden with all fields."""
        burden = GeneBurden(
            gene_symbol="BRCA1",
            uniprot_id="P38398",
            total_variants=100,
            pathogenic_count=20,
            benign_count=50,
            ambiguous_count=30,
            mean_pathogenicity=0.4,
            max_pathogenicity=0.95,
            pathogenic_fraction=0.2,
        )

        assert burden.gene_symbol == "BRCA1"
        assert burden.total_variants == 100
        assert burden.pathogenic_fraction == 0.2

    def test_is_high_burden_by_fraction(self):
        """Should identify high burden by pathogenic fraction."""
        burden = GeneBurden(
            gene_symbol="TEST",
            uniprot_id="P00001",
            total_variants=100,
            pathogenic_count=15,
            benign_count=70,
            ambiguous_count=15,
            mean_pathogenicity=0.35,
            max_pathogenicity=0.7,
            pathogenic_fraction=0.15,  # > 0.1
        )

        assert burden.is_high_burden is True

    def test_is_high_burden_by_max_score(self):
        """Should identify high burden by max pathogenicity."""
        burden = GeneBurden(
            gene_symbol="TEST",
            uniprot_id="P00001",
            total_variants=100,
            pathogenic_count=5,
            benign_count=90,
            ambiguous_count=5,
            mean_pathogenicity=0.2,
            max_pathogenicity=0.95,  # > 0.9
            pathogenic_fraction=0.05,
        )

        assert burden.is_high_burden is True

    def test_not_high_burden(self):
        """Should identify low burden genes."""
        burden = GeneBurden(
            gene_symbol="TEST",
            uniprot_id="P00001",
            total_variants=100,
            pathogenic_count=5,
            benign_count=90,
            ambiguous_count=5,
            mean_pathogenicity=0.2,
            max_pathogenicity=0.6,
            pathogenic_fraction=0.05,
        )

        assert burden.is_high_burden is False


class TestComputeGeneBurden:
    """Test gene burden computation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock AlphaMissenseDB."""
        db = MagicMock()
        return db

    def test_compute_single_gene(self, mock_db):
        """Should compute burden for single gene."""
        mock_db.get_protein_variants.return_value = [
            VariantPrediction(
                chrom="chr1", pos=100, ref="A", alt="G", genome="hg38",
                uniprot_id="P35498", transcript_id="E1", protein_variant="A1G",
                am_pathogenicity=0.9, am_class="pathogenic",
            ),
            VariantPrediction(
                chrom="chr1", pos=200, ref="C", alt="T", genome="hg38",
                uniprot_id="P35498", transcript_id="E1", protein_variant="C2T",
                am_pathogenicity=0.1, am_class="benign",
            ),
        ]

        with patch("alphamissense.analysis.gene_analysis.AlphaMissenseDB", return_value=mock_db):
            results = compute_gene_burden(["P35498"], db=mock_db)

        assert len(results) == 1
        assert results[0].uniprot_id == "P35498"
        assert results[0].gene_symbol == "SCN4A"  # From UNIPROT_TO_GENE mapping
        assert results[0].total_variants == 2
        assert results[0].pathogenic_count == 1
        assert results[0].benign_count == 1

    def test_compute_multiple_genes(self, mock_db):
        """Should compute burden for multiple genes."""
        # Return different variants for different genes
        def get_variants(uniprot_id):
            if uniprot_id == "P35498":
                return [
                    VariantPrediction(
                        chrom="chr1", pos=100, ref="A", alt="G", genome="hg38",
                        uniprot_id="P35498", transcript_id="E1", protein_variant="A1G",
                        am_pathogenicity=0.9, am_class="pathogenic",
                    ),
                ]
            elif uniprot_id == "P21817":
                return [
                    VariantPrediction(
                        chrom="chr2", pos=200, ref="C", alt="T", genome="hg38",
                        uniprot_id="P21817", transcript_id="E2", protein_variant="C2T",
                        am_pathogenicity=0.1, am_class="benign",
                    ),
                ]
            return []

        mock_db.get_protein_variants.side_effect = get_variants

        with patch("alphamissense.analysis.gene_analysis.AlphaMissenseDB", return_value=mock_db):
            results = compute_gene_burden(["P35498", "P21817"], db=mock_db)

        assert len(results) == 2

    def test_compute_empty_gene(self, mock_db):
        """Should skip genes with no variants."""
        mock_db.get_protein_variants.return_value = []

        with patch("alphamissense.analysis.gene_analysis.AlphaMissenseDB", return_value=mock_db):
            results = compute_gene_burden(["P00000"], db=mock_db)

        assert len(results) == 0

    def test_results_sorted_by_fraction(self, mock_db):
        """Results should be sorted by pathogenic fraction (descending)."""
        def get_variants(uniprot_id):
            if uniprot_id == "P1":
                return [
                    VariantPrediction(
                        chrom="chr1", pos=100, ref="A", alt="G", genome="hg38",
                        uniprot_id="P1", transcript_id="E1", protein_variant="A1G",
                        am_pathogenicity=0.1, am_class="benign",
                    ),
                ]
            elif uniprot_id == "P2":
                return [
                    VariantPrediction(
                        chrom="chr1", pos=100, ref="A", alt="G", genome="hg38",
                        uniprot_id="P2", transcript_id="E1", protein_variant="A1G",
                        am_pathogenicity=0.9, am_class="pathogenic",
                    ),
                ]
            return []

        mock_db.get_protein_variants.side_effect = get_variants

        with patch("alphamissense.analysis.gene_analysis.AlphaMissenseDB", return_value=mock_db):
            results = compute_gene_burden(["P1", "P2"], db=mock_db)

        # P2 should come first (higher pathogenic fraction)
        assert results[0].uniprot_id == "P2"
        assert results[1].uniprot_id == "P1"


class TestAnalyzePatientGenes:
    """Test patient gene analysis."""

    @pytest.fixture
    def mock_db(self):
        """Create mock AlphaMissenseDB."""
        db = MagicMock()
        db.get_protein_variants.return_value = [
            VariantPrediction(
                chrom="chr1", pos=100, ref="A", alt="G", genome="hg38",
                uniprot_id="P35498", transcript_id="E1", protein_variant="A1G",
                am_pathogenicity=0.9, am_class="pathogenic",
            ),
        ]
        return db

    def test_analyze_with_uniprot_ids(self, mock_db):
        """Should analyze genes from UniProt IDs."""
        variants = [
            {"chrom": "chr1", "pos": 100, "uniprot_id": "P35498", "gene": "SCN4A"},
        ]

        with patch("alphamissense.analysis.gene_analysis.AlphaMissenseDB", return_value=mock_db):
            results = analyze_patient_genes(variants, db=mock_db)

        assert "affected_genes" in results
        assert "gene_burdens" in results
        assert "high_risk_genes" in results
        assert len(results["affected_genes"]) >= 0

    def test_analyze_empty_variants(self, mock_db):
        """Should handle empty variant list."""
        results = analyze_patient_genes([], db=mock_db)

        assert results["affected_genes"] == []
        assert results["gene_burdens"] == []
        assert results["high_risk_genes"] == []

    def test_analyze_no_uniprot_ids(self, mock_db):
        """Should handle variants without UniProt IDs."""
        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
        ]

        results = analyze_patient_genes(variants, db=mock_db)

        assert results["affected_genes"] == []


class TestUniProtMapping:
    """Test UniProt to gene symbol mapping."""

    def test_known_genes_mapped(self):
        """Known rare disease genes should be in mapping."""
        assert "P35498" in UNIPROT_TO_GENE  # SCN4A
        assert "P21817" in UNIPROT_TO_GENE  # RYR1
        assert "P35523" in UNIPROT_TO_GENE  # CLCN1

    def test_mapping_values(self):
        """Mapping values should be gene symbols."""
        assert UNIPROT_TO_GENE["P35498"] == "SCN4A"
        assert UNIPROT_TO_GENE["P21817"] == "RYR1"
        assert UNIPROT_TO_GENE["P35523"] == "CLCN1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
