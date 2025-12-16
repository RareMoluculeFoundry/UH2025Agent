"""
AlphaMissense Database Loader

Provides the AlphaMissenseDB class for querying variant pathogenicity predictions.
Uses DuckDB for fast indexed lookups (~1ms per variant).

Classification Thresholds (from paper):
    - Likely Benign: am_pathogenicity < 0.34
    - Ambiguous: 0.34 <= am_pathogenicity <= 0.564
    - Likely Pathogenic: am_pathogenicity > 0.564
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    import duckdb
except ImportError:
    raise ImportError("DuckDB is required. Install with: pip install duckdb")


# Classification thresholds from AlphaMissense paper
BENIGN_THRESHOLD = 0.34
PATHOGENIC_THRESHOLD = 0.564

# Default data directory
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"


@dataclass
class VariantPrediction:
    """AlphaMissense prediction for a variant."""

    chrom: str | None
    pos: int | None
    ref: str | None
    alt: str | None
    uniprot_id: str
    protein_variant: str
    am_pathogenicity: float
    am_class: str

    @property
    def is_pathogenic(self) -> bool:
        """Check if variant is classified as likely pathogenic."""
        return self.am_pathogenicity > PATHOGENIC_THRESHOLD

    @property
    def is_benign(self) -> bool:
        """Check if variant is classified as likely benign."""
        return self.am_pathogenicity < BENIGN_THRESHOLD

    @property
    def is_ambiguous(self) -> bool:
        """Check if variant is of uncertain significance."""
        return BENIGN_THRESHOLD <= self.am_pathogenicity <= PATHOGENIC_THRESHOLD

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "chrom": self.chrom,
            "pos": self.pos,
            "ref": self.ref,
            "alt": self.alt,
            "uniprot_id": self.uniprot_id,
            "protein_variant": self.protein_variant,
            "am_pathogenicity": self.am_pathogenicity,
            "am_class": self.am_class,
            "is_pathogenic": self.is_pathogenic,
            "is_benign": self.is_benign,
            "is_ambiguous": self.is_ambiguous,
        }


class AlphaMissenseDB:
    """
    AlphaMissense database interface for variant pathogenicity queries.

    Provides fast lookups by genomic coordinates or protein variants using
    an indexed DuckDB database.

    Example:
        >>> db = AlphaMissenseDB()
        >>> result = db.lookup_variant("17", 62068646, "A", "G")
        >>> if result:
        ...     print(f"Score: {result.am_pathogenicity}")
        ...     print(f"Class: {result.am_class}")

        >>> # Protein-centric lookup
        >>> result = db.lookup_protein_variant("P35498", "K260E")
        >>> if result:
        ...     print(f"Pathogenic: {result.is_pathogenic}")

        >>> # Get all predictions for a protein
        >>> variants = db.get_protein_variants("P35498")
        >>> pathogenic = [v for v in variants if v.is_pathogenic]
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        target: Literal["hg38", "hg19", "aa_substitutions"] = "hg38",
    ):
        """
        Initialize AlphaMissense database connection.

        Args:
            db_path: Path to DuckDB database. If None, uses default location.
            target: Which database to use (for default path resolution).

        Raises:
            FileNotFoundError: If database doesn't exist (run indexer first).
        """
        if db_path is None:
            db_path = DEFAULT_DATA_DIR / f"AlphaMissense_{target}.duckdb"
        else:
            db_path = Path(db_path)

        if not db_path.exists():
            raise FileNotFoundError(
                f"AlphaMissense database not found: {db_path}\n"
                "Please download and index the data first:\n"
                "  from code.data import download_predictions, create_index\n"
                "  tsv_path = download_predictions('hg38')\n"
                "  create_index(tsv_path)"
            )

        self.db_path = db_path
        self.target = target
        self._conn = duckdb.connect(str(db_path), read_only=True)

    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def lookup_variant(
        self,
        chrom: str,
        pos: int,
        ref: str,
        alt: str,
    ) -> VariantPrediction | None:
        """
        Query by genomic coordinate.

        Args:
            chrom: Chromosome (1-22, X, Y, MT) - with or without 'chr' prefix
            pos: Position (1-based)
            ref: Reference allele
            alt: Alternate allele

        Returns:
            VariantPrediction if found, None otherwise
        """
        # Normalize chromosome (remove 'chr' prefix if present)
        chrom = chrom.replace("chr", "")

        query = """
            SELECT CHROM, POS, REF, ALT, uniprot_id, protein_variant,
                   am_pathogenicity, am_class
            FROM variants
            WHERE CHROM = ? AND POS = ? AND REF = ? AND ALT = ?
            LIMIT 1
        """

        result = self._conn.execute(query, [chrom, pos, ref, alt]).fetchone()

        if result is None:
            return None

        return VariantPrediction(
            chrom=result[0],
            pos=result[1],
            ref=result[2],
            alt=result[3],
            uniprot_id=result[4],
            protein_variant=result[5],
            am_pathogenicity=result[6],
            am_class=result[7],
        )

    def lookup_protein_variant(
        self,
        uniprot_id: str,
        protein_variant: str,
    ) -> VariantPrediction | None:
        """
        Query by protein variant.

        Args:
            uniprot_id: UniProt accession (e.g., "P35498")
            protein_variant: Amino acid change (e.g., "K260E" or "Lys260Glu")

        Returns:
            VariantPrediction if found, None otherwise
        """
        # Normalize protein variant format
        protein_variant = self._normalize_protein_variant(protein_variant)

        query = """
            SELECT CHROM, POS, REF, ALT, uniprot_id, protein_variant,
                   am_pathogenicity, am_class
            FROM variants
            WHERE uniprot_id = ? AND protein_variant = ?
            LIMIT 1
        """

        result = self._conn.execute(query, [uniprot_id, protein_variant]).fetchone()

        if result is None:
            return None

        return VariantPrediction(
            chrom=result[0] if len(result) > 0 else None,
            pos=result[1] if len(result) > 1 else None,
            ref=result[2] if len(result) > 2 else None,
            alt=result[3] if len(result) > 3 else None,
            uniprot_id=result[4],
            protein_variant=result[5],
            am_pathogenicity=result[6],
            am_class=result[7],
        )

    def get_protein_variants(
        self,
        uniprot_id: str,
        pathogenic_only: bool = False,
    ) -> list[VariantPrediction]:
        """
        Get all predicted variants for a protein.

        Args:
            uniprot_id: UniProt accession
            pathogenic_only: Only return likely pathogenic variants

        Returns:
            List of VariantPrediction objects
        """
        if pathogenic_only:
            query = """
                SELECT CHROM, POS, REF, ALT, uniprot_id, protein_variant,
                       am_pathogenicity, am_class
                FROM variants
                WHERE uniprot_id = ? AND am_class = 'likely_pathogenic'
                ORDER BY am_pathogenicity DESC
            """
        else:
            query = """
                SELECT CHROM, POS, REF, ALT, uniprot_id, protein_variant,
                       am_pathogenicity, am_class
                FROM variants
                WHERE uniprot_id = ?
                ORDER BY am_pathogenicity DESC
            """

        results = self._conn.execute(query, [uniprot_id]).fetchall()

        return [
            VariantPrediction(
                chrom=r[0],
                pos=r[1],
                ref=r[2],
                alt=r[3],
                uniprot_id=r[4],
                protein_variant=r[5],
                am_pathogenicity=r[6],
                am_class=r[7],
            )
            for r in results
        ]

    def batch_lookup(
        self,
        variants: list[tuple[str, int, str, str]],
    ) -> dict[tuple, VariantPrediction | None]:
        """
        Batch lookup of multiple variants by genomic coordinates.

        Args:
            variants: List of (chrom, pos, ref, alt) tuples

        Returns:
            Dictionary mapping (chrom, pos, ref, alt) -> VariantPrediction
        """
        results = {}

        for chrom, pos, ref, alt in variants:
            key = (chrom, pos, ref, alt)
            results[key] = self.lookup_variant(chrom, pos, ref, alt)

        return results

    def get_statistics(self) -> dict:
        """Get database statistics."""
        stats = {}

        # Total variants
        stats["total_variants"] = self._conn.execute(
            "SELECT COUNT(*) FROM variants"
        ).fetchone()[0]

        # Classification distribution
        class_dist = self._conn.execute("""
            SELECT am_class, COUNT(*) as count
            FROM variants
            GROUP BY am_class
        """).fetchall()
        stats["classification_distribution"] = dict(class_dist)

        # Score statistics
        score_stats = self._conn.execute("""
            SELECT
                AVG(am_pathogenicity) as mean,
                MIN(am_pathogenicity) as min,
                MAX(am_pathogenicity) as max
            FROM variants
        """).fetchone()
        stats["score_statistics"] = {
            "mean": score_stats[0],
            "min": score_stats[1],
            "max": score_stats[2],
        }

        return stats

    @staticmethod
    def _normalize_protein_variant(variant: str) -> str:
        """
        Normalize protein variant notation.

        Converts three-letter amino acid codes to single-letter:
            "Lys260Glu" -> "K260E"
            "p.K260E" -> "K260E"
        """
        # Remove common prefixes
        variant = variant.replace("p.", "")

        # Three-letter to single-letter amino acid mapping
        aa_map = {
            "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D",
            "Cys": "C", "Gln": "Q", "Glu": "E", "Gly": "G",
            "His": "H", "Ile": "I", "Leu": "L", "Lys": "K",
            "Met": "M", "Phe": "F", "Pro": "P", "Ser": "S",
            "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
        }

        # Convert three-letter codes
        for three, one in aa_map.items():
            variant = variant.replace(three, one)

        return variant
