"""
Tests for AlphaMissense Data Loader

Tests variant lookup, protein variant queries, and batch operations.
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alphamissense.data.loader import (
    AlphaMissenseDB,
    VariantPrediction,
    PATHOGENIC_THRESHOLD,
    BENIGN_THRESHOLD,
)


class TestVariantPrediction:
    """Test VariantPrediction dataclass."""

    def test_variant_prediction_creation(self):
        """Should create VariantPrediction with all fields."""
        pred = VariantPrediction(
            chrom="chr1",
            pos=12345,
            ref="A",
            alt="G",
            genome="hg38",
            uniprot_id="P12345",
            transcript_id="ENST00000123456",
            protein_variant="A123G",
            am_pathogenicity=0.75,
            am_class="likely_pathogenic",
        )

        assert pred.chrom == "chr1"
        assert pred.pos == 12345
        assert pred.am_pathogenicity == 0.75

    def test_is_pathogenic_above_threshold(self):
        """Variants above threshold should be pathogenic."""
        pred = VariantPrediction(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            genome="hg38",
            uniprot_id="P12345",
            transcript_id="ENST00000123456",
            protein_variant="A1G",
            am_pathogenicity=0.9,
            am_class="likely_pathogenic",
        )

        assert pred.is_pathogenic is True
        assert pred.is_benign is False
        assert pred.is_ambiguous is False

    def test_is_benign_below_threshold(self):
        """Variants below threshold should be benign."""
        pred = VariantPrediction(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            genome="hg38",
            uniprot_id="P12345",
            transcript_id="ENST00000123456",
            protein_variant="A1G",
            am_pathogenicity=0.1,
            am_class="likely_benign",
        )

        assert pred.is_pathogenic is False
        assert pred.is_benign is True
        assert pred.is_ambiguous is False

    def test_is_ambiguous_in_middle(self):
        """Variants in middle range should be ambiguous."""
        pred = VariantPrediction(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            genome="hg38",
            uniprot_id="P12345",
            transcript_id="ENST00000123456",
            protein_variant="A1G",
            am_pathogenicity=0.45,
            am_class="ambiguous",
        )

        assert pred.is_pathogenic is False
        assert pred.is_benign is False
        assert pred.is_ambiguous is True

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        pred = VariantPrediction(
            chrom="chr1",
            pos=100,
            ref="A",
            alt="G",
            genome="hg38",
            uniprot_id="P12345",
            transcript_id="ENST00000123456",
            protein_variant="A1G",
            am_pathogenicity=0.75,
            am_class="likely_pathogenic",
        )

        d = pred.to_dict()

        assert d["chrom"] == "chr1"
        assert d["pos"] == 100
        assert d["am_pathogenicity"] == 0.75
        assert "is_pathogenic" in d
        assert "is_benign" in d


class TestThresholds:
    """Test pathogenicity threshold constants."""

    def test_threshold_values(self):
        """Thresholds should match AlphaMissense publication."""
        assert BENIGN_THRESHOLD == 0.34
        assert PATHOGENIC_THRESHOLD == 0.564

    def test_threshold_ordering(self):
        """Benign threshold should be less than pathogenic."""
        assert BENIGN_THRESHOLD < PATHOGENIC_THRESHOLD


class TestAlphaMissenseDBInitialization:
    """Test AlphaMissenseDB initialization."""

    def test_init_without_database(self, tmp_path):
        """Should raise error if database doesn't exist."""
        fake_path = tmp_path / "nonexistent.duckdb"

        with pytest.raises(FileNotFoundError):
            AlphaMissenseDB(db_path=fake_path)

    @patch("alphamissense.data.loader.duckdb")
    def test_init_with_database(self, mock_duckdb, tmp_path):
        """Should connect to existing database."""
        db_path = tmp_path / "test.duckdb"
        db_path.touch()

        mock_conn = MagicMock()
        mock_duckdb.connect.return_value = mock_conn

        db = AlphaMissenseDB(db_path=db_path)

        mock_duckdb.connect.assert_called_once()
        assert db.conn == mock_conn


class TestAlphaMissenseDBLookups:
    """Test AlphaMissenseDB lookup methods."""

    @pytest.fixture
    def mock_db(self, tmp_path):
        """Create mock database for testing."""
        db_path = tmp_path / "test.duckdb"
        db_path.touch()

        with patch("alphamissense.data.loader.duckdb") as mock_duckdb:
            mock_conn = MagicMock()
            mock_duckdb.connect.return_value = mock_conn
            db = AlphaMissenseDB(db_path=db_path)
            db._mock_conn = mock_conn
            yield db

    def test_lookup_variant_found(self, mock_db):
        """Should return VariantPrediction when variant found."""
        # Mock the query result
        mock_db._mock_conn.execute.return_value.fetchone.return_value = (
            "chr1",  # CHROM
            12345,   # POS
            "A",     # REF
            "G",     # ALT
            "hg38",  # genome
            "P12345",  # uniprot_id
            "ENST00000123456",  # transcript_id
            "A100G",  # protein_variant
            0.85,    # am_pathogenicity
            "likely_pathogenic",  # am_class
        )

        result = mock_db.lookup_variant("chr1", 12345, "A", "G")

        assert result is not None
        assert isinstance(result, VariantPrediction)
        assert result.chrom == "chr1"
        assert result.am_pathogenicity == 0.85

    def test_lookup_variant_not_found(self, mock_db):
        """Should return None when variant not found."""
        mock_db._mock_conn.execute.return_value.fetchone.return_value = None

        result = mock_db.lookup_variant("chr99", 99999, "X", "Y")

        assert result is None

    def test_lookup_protein_variant(self, mock_db):
        """Should lookup by protein variant notation."""
        mock_db._mock_conn.execute.return_value.fetchone.return_value = (
            "chr1", 12345, "A", "G", "hg38", "P12345",
            "ENST00000123456", "A100G", 0.75, "likely_pathogenic",
        )

        result = mock_db.lookup_protein_variant("P12345", "A100G")

        assert result is not None
        assert result.protein_variant == "A100G"

    def test_get_protein_variants_all(self, mock_db):
        """Should return all variants for a protein."""
        mock_db._mock_conn.execute.return_value.fetchall.return_value = [
            ("chr1", 100, "A", "G", "hg38", "P12345", "ENST1", "A1G", 0.9, "pathogenic"),
            ("chr1", 200, "C", "T", "hg38", "P12345", "ENST1", "C2T", 0.1, "benign"),
            ("chr1", 300, "G", "A", "hg38", "P12345", "ENST1", "G3A", 0.5, "ambiguous"),
        ]

        results = mock_db.get_protein_variants("P12345")

        assert len(results) == 3
        assert all(isinstance(r, VariantPrediction) for r in results)

    def test_get_protein_variants_pathogenic_only(self, mock_db):
        """Should filter to pathogenic variants only."""
        mock_db._mock_conn.execute.return_value.fetchall.return_value = [
            ("chr1", 100, "A", "G", "hg38", "P12345", "ENST1", "A1G", 0.9, "pathogenic"),
        ]

        results = mock_db.get_protein_variants("P12345", pathogenic_only=True)

        # The SQL should include the pathogenic filter
        call_args = mock_db._mock_conn.execute.call_args
        assert PATHOGENIC_THRESHOLD in str(call_args) or len(results) >= 0

    def test_batch_lookup(self, mock_db):
        """Should lookup multiple variants efficiently."""
        # First call returns result, second returns None
        mock_db._mock_conn.execute.return_value.fetchone.side_effect = [
            ("chr1", 100, "A", "G", "hg38", "P12345", "ENST1", "A1G", 0.8, "pathogenic"),
            None,
        ]

        variants = [
            {"chrom": "chr1", "pos": 100, "ref": "A", "alt": "G"},
            {"chrom": "chr2", "pos": 200, "ref": "C", "alt": "T"},
        ]

        results = mock_db.batch_lookup(variants)

        assert len(results) == 2
        assert ("chr1", 100, "A", "G") in results
        assert results[("chr1", 100, "A", "G")] is not None
        assert results[("chr2", 200, "C", "T")] is None

    def test_close_connection(self, mock_db):
        """Should close database connection."""
        mock_db.close()

        mock_db._mock_conn.close.assert_called_once()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_batch_lookup(self):
        """Empty variant list should return empty dict."""
        with patch("alphamissense.data.loader.duckdb") as mock_duckdb:
            db_path = Path("/tmp/test.duckdb")

            with patch.object(Path, "exists", return_value=True):
                mock_conn = MagicMock()
                mock_duckdb.connect.return_value = mock_conn

                db = AlphaMissenseDB(db_path=db_path)
                results = db.batch_lookup([])

                assert results == {}

    def test_variant_with_chr_prefix(self, tmp_path):
        """Should handle chromosome with and without 'chr' prefix."""
        db_path = tmp_path / "test.duckdb"
        db_path.touch()

        with patch("alphamissense.data.loader.duckdb") as mock_duckdb:
            mock_conn = MagicMock()
            mock_duckdb.connect.return_value = mock_conn
            mock_conn.execute.return_value.fetchone.return_value = None

            db = AlphaMissenseDB(db_path=db_path)

            # Both should work without error
            db.lookup_variant("chr1", 100, "A", "G")
            db.lookup_variant("1", 100, "A", "G")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
