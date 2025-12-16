"""
AlphaMissenseTool: DeepMind pathogenicity predictions for missense variants.

AlphaMissense is a deep learning model from DeepMind that predicts
the pathogenicity of all possible single amino acid substitutions
in the human proteome (~71 million variants).

Reference:
Cheng et al. (2023). Accurate proteome-wide missense variant effect
prediction with AlphaMissense. Science, 381(6664).

Data Source: DeepMind AlphaMissense database
https://console.cloud.google.com/storage/browser/dm_alphamissense

Key Features:
- Pre-computed for entire human proteome
- Provides continuous pathogenicity score (0-1)
- Classifications: likely_benign, ambiguous, likely_pathogenic
- Based on evolutionary conservation and structural context
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os

from .base_tool import BaseTool, ToolResult, ToolStatus, Variant


class AlphaMissenseClass(Enum):
    """AlphaMissense pathogenicity classification."""
    LIKELY_BENIGN = "likely_benign"
    AMBIGUOUS = "ambiguous"
    LIKELY_PATHOGENIC = "likely_pathogenic"


@dataclass
class AlphaMissenseScore:
    """AlphaMissense prediction for a variant."""
    pathogenicity_score: float  # 0-1, higher = more pathogenic
    classification: AlphaMissenseClass

    # Metadata
    protein: Optional[str] = None
    amino_acid_position: Optional[int] = None
    reference_aa: Optional[str] = None
    alternate_aa: Optional[str] = None
    uniprot_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pathogenicity_score": self.pathogenicity_score,
            "classification": self.classification.value,
            "protein": self.protein,
            "amino_acid_position": self.amino_acid_position,
            "reference_aa": self.reference_aa,
            "alternate_aa": self.alternate_aa,
            "uniprot_id": self.uniprot_id,
        }


class AlphaMissenseTool(BaseTool):
    """
    Query AlphaMissense pathogenicity predictions for missense variants.

    AlphaMissense scores range from 0 to 1:
    - 0.0-0.34: Likely benign
    - 0.34-0.564: Ambiguous
    - 0.564-1.0: Likely pathogenic

    Note: AlphaMissense is ONLY applicable to missense variants
    (single amino acid substitutions).
    """

    name = "alphamissense"
    version = "1.0"
    description = "DeepMind pathogenicity predictions for missense variants"

    # Classification thresholds (from AlphaMissense paper)
    BENIGN_THRESHOLD = 0.34
    PATHOGENIC_THRESHOLD = 0.564

    # AlphaMissense is a static database - no rate limiting needed
    rate_limit_per_second = 100
    rate_limit_per_minute = 1000

    def __init__(self, database_path: Optional[str] = None):
        """
        Initialize AlphaMissense tool.

        Args:
            database_path: Path to AlphaMissense TSV or SQLite database.
        """
        super().__init__()
        self.database_path = database_path or os.environ.get("ALPHAMISSENSE_DB_PATH")
        self._db_connection = None

    def _validate_variant(self, variant: Variant) -> Optional[str]:
        """
        Validate variant for AlphaMissense query.

        AlphaMissense ONLY works for missense variants.
        Requires protein change information.
        """
        # Must have protein change
        if not variant.hgvs_p:
            return (
                "AlphaMissense requires protein change (hgvs_p). "
                "This tool only works for missense variants."
            )

        # Parse protein change
        hgvs_p = variant.hgvs_p
        if not hgvs_p.startswith("p."):
            return "Invalid protein change format. Expected p.Xxx123Yyy"

        # Check it's a missense (not nonsense, frameshift, etc.)
        # Simple check: should have 3-letter AA codes at start and end
        # e.g., p.Arg123Gly, p.R123G
        if "*" in hgvs_p or "fs" in hgvs_p or "del" in hgvs_p or "ins" in hgvs_p:
            return (
                "AlphaMissense only predicts missense variants. "
                "This appears to be a nonsense, frameshift, or indel variant."
            )

        return None

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        """
        Query AlphaMissense for a single missense variant.

        TODO: Implement actual database lookup.
        Currently returns stub data for development.
        """
        # Parse protein change
        protein_info = self._parse_protein_change(variant.hgvs_p)

        # Try database lookup
        if self.database_path and os.path.exists(self.database_path):
            return self._query_database(variant, protein_info)

        # Return stub data for development
        return self._stub_query(variant, protein_info)

    def _parse_protein_change(self, hgvs_p: str) -> Dict[str, Any]:
        """
        Parse HGVS protein notation.

        Examples:
        - p.Arg123Gly -> {ref: R, pos: 123, alt: G}
        - p.R123G -> {ref: R, pos: 123, alt: G}
        """
        import re

        # Three-letter AA codes
        aa_3to1 = {
            "Ala": "A", "Arg": "R", "Asn": "N", "Asp": "D", "Cys": "C",
            "Gln": "Q", "Glu": "E", "Gly": "G", "His": "H", "Ile": "I",
            "Leu": "L", "Lys": "K", "Met": "M", "Phe": "F", "Pro": "P",
            "Ser": "S", "Thr": "T", "Trp": "W", "Tyr": "Y", "Val": "V",
        }

        # Try three-letter format: p.Arg123Gly
        match = re.match(r"p\.([A-Z][a-z]{2})(\d+)([A-Z][a-z]{2})", hgvs_p)
        if match:
            ref_3, pos, alt_3 = match.groups()
            return {
                "ref": aa_3to1.get(ref_3, ref_3[0]),
                "pos": int(pos),
                "alt": aa_3to1.get(alt_3, alt_3[0]),
            }

        # Try single-letter format: p.R123G
        match = re.match(r"p\.([A-Z])(\d+)([A-Z])", hgvs_p)
        if match:
            ref, pos, alt = match.groups()
            return {"ref": ref, "pos": int(pos), "alt": alt}

        return {"ref": "?", "pos": 0, "alt": "?"}

    def _query_database(self, variant: Variant, protein_info: Dict) -> Dict[str, Any]:
        """
        Query local AlphaMissense database using DuckDB.

        Supports:
        - Local TSV/CSV files (compressed or uncompressed)
        - Remote files from Google Cloud Storage
        - DuckDB native files

        The AlphaMissense database contains columns:
        - CHROM, POS, REF, ALT (genomic coordinates)
        - genome (hg19 or hg38)
        - uniprot_id
        - transcript_id
        - protein_variant (e.g., "A123G")
        - am_pathogenicity (0-1 score)
        - am_class (likely_benign, ambiguous, likely_pathogenic)
        """
        import duckdb

        # Try to get connection
        if self._db_connection is None:
            self._db_connection = self._connect_database()

        if self._db_connection is None:
            # Fall back to stub if database not available
            return self._stub_query(variant, protein_info)

        try:
            # Build query based on available variant info
            query_result = None

            # Method 1: Query by protein change if gene is known
            if variant.gene and protein_info.get("pos"):
                ref_aa = protein_info.get("ref", "")
                pos = protein_info.get("pos", 0)
                alt_aa = protein_info.get("alt", "")

                # AlphaMissense uses single-letter format: R123G
                protein_variant = f"{ref_aa}{pos}{alt_aa}"

                # Try transcript-specific query first
                if variant.transcript:
                    query = """
                        SELECT am_pathogenicity, am_class, uniprot_id, transcript_id, protein_variant
                        FROM alphamissense
                        WHERE transcript_id = ? AND protein_variant = ?
                        LIMIT 1
                    """
                    query_result = self._db_connection.execute(
                        query, [variant.transcript, protein_variant]
                    ).fetchone()

                # Fall back to gene-based query
                if query_result is None:
                    query = """
                        SELECT am_pathogenicity, am_class, uniprot_id, transcript_id, protein_variant
                        FROM alphamissense
                        WHERE protein_variant = ?
                        LIMIT 1
                    """
                    query_result = self._db_connection.execute(
                        query, [protein_variant]
                    ).fetchone()

            # Method 2: Query by genomic coordinates
            if query_result is None and variant.chromosome and variant.position:
                chrom = variant.chromosome.replace("chr", "")
                query = """
                    SELECT am_pathogenicity, am_class, uniprot_id, transcript_id, protein_variant
                    FROM alphamissense
                    WHERE CHROM = ? AND POS = ? AND REF = ? AND ALT = ?
                    LIMIT 1
                """
                query_result = self._db_connection.execute(
                    query, [chrom, variant.position, variant.reference, variant.alternate]
                ).fetchone()

            if query_result is None:
                # Variant not found in database
                return {
                    "pathogenicity_score": None,
                    "classification": None,
                    "protein": variant.gene,
                    "amino_acid_position": protein_info.get("pos"),
                    "reference_aa": protein_info.get("ref"),
                    "alternate_aa": protein_info.get("alt"),
                    "uniprot_id": None,
                    "gene": variant.gene,
                    "transcript": variant.transcript,
                    "data_source": "AlphaMissense - Variant not found",
                }

            # Parse result
            am_score, am_class, uniprot_id, transcript_id, protein_var = query_result

            # Convert class string to enum
            classification = AlphaMissenseClass.AMBIGUOUS
            if am_class == "likely_benign":
                classification = AlphaMissenseClass.LIKELY_BENIGN
            elif am_class == "likely_pathogenic":
                classification = AlphaMissenseClass.LIKELY_PATHOGENIC

            am_score_obj = AlphaMissenseScore(
                pathogenicity_score=round(am_score, 4),
                classification=classification,
                protein=variant.gene,
                amino_acid_position=protein_info.get("pos"),
                reference_aa=protein_info.get("ref"),
                alternate_aa=protein_info.get("alt"),
                uniprot_id=uniprot_id,
            )

            return {
                **am_score_obj.to_dict(),
                "gene": variant.gene,
                "transcript": transcript_id or variant.transcript,
                "data_source": "AlphaMissense Database (LIVE)",
            }

        except Exception as e:
            # Log error and fall back to stub
            print(f"[AlphaMissense] Database query error: {e}")
            return self._stub_query(variant, protein_info)

    def _connect_database(self) -> Optional[Any]:
        """
        Connect to AlphaMissense database via DuckDB.

        Supports multiple data sources:
        1. Local parquet/duckdb file
        2. Local TSV file (compressed or not)
        3. Remote TSV from Google Cloud Storage
        """
        import duckdb

        try:
            conn = duckdb.connect(":memory:")

            # Check if database_path is a parquet or duckdb file
            if self.database_path and os.path.exists(self.database_path):
                ext = os.path.splitext(self.database_path)[1].lower()

                if ext in [".parquet", ".pq"]:
                    # Read parquet directly
                    conn.execute(f"""
                        CREATE TABLE alphamissense AS
                        SELECT * FROM read_parquet('{self.database_path}')
                    """)
                elif ext in [".tsv", ".csv", ".gz"]:
                    # Read TSV (possibly compressed)
                    conn.execute(f"""
                        CREATE TABLE alphamissense AS
                        SELECT * FROM read_csv('{self.database_path}',
                            delim='\t',
                            header=true,
                            auto_detect=true
                        )
                    """)
                elif ext in [".duckdb", ".db"]:
                    # Connect to existing DuckDB file
                    conn.close()
                    conn = duckdb.connect(self.database_path, read_only=True)
                else:
                    print(f"[AlphaMissense] Unknown file extension: {ext}")
                    return None

                # Create index for faster lookups
                try:
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_protein ON alphamissense(protein_variant)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_coords ON alphamissense(CHROM, POS)")
                except:
                    pass  # Index creation may fail on read-only DBs

                print(f"[AlphaMissense] Connected to database: {self.database_path}")
                return conn

            # Try Google Cloud Storage URL
            gcs_url = "gs://dm_alphamissense/AlphaMissense_hg38.tsv.gz"
            try:
                # DuckDB can read from GCS with httpfs extension
                conn.execute("INSTALL httpfs; LOAD httpfs;")
                conn.execute(f"""
                    CREATE TABLE alphamissense AS
                    SELECT * FROM read_csv('{gcs_url}',
                        delim='\t',
                        header=true,
                        auto_detect=true
                    )
                """)
                print(f"[AlphaMissense] Connected to GCS: {gcs_url}")
                return conn
            except Exception as e:
                print(f"[AlphaMissense] GCS connection failed: {e}")
                return None

        except Exception as e:
            print(f"[AlphaMissense] Database connection error: {e}")
            return None

    def _stub_query(self, variant: Variant, protein_info: Dict) -> Dict[str, Any]:
        """
        Return stub AlphaMissense scores for development/testing.
        """
        # Generate deterministic score based on variant
        seed = hash(variant.hgvs_p or "") % 1000
        score = min(1.0, seed / 1000)

        # Classify
        if score < self.BENIGN_THRESHOLD:
            classification = AlphaMissenseClass.LIKELY_BENIGN
        elif score < self.PATHOGENIC_THRESHOLD:
            classification = AlphaMissenseClass.AMBIGUOUS
        else:
            classification = AlphaMissenseClass.LIKELY_PATHOGENIC

        am_score = AlphaMissenseScore(
            pathogenicity_score=round(score, 4),
            classification=classification,
            protein=variant.gene,
            amino_acid_position=protein_info.get("pos"),
            reference_aa=protein_info.get("ref"),
            alternate_aa=protein_info.get("alt"),
            uniprot_id=f"[STUB] {variant.gene}_HUMAN" if variant.gene else None,
        )

        return {
            **am_score.to_dict(),
            "gene": variant.gene,
            "transcript": variant.transcript,
            "data_source": "STUB - Database not connected",
        }

    def _get_data_version(self) -> Optional[str]:
        """Get AlphaMissense data version."""
        return "AlphaMissense 2023 (STUB)"


# Utility functions for AlphaMissense interpretation

def interpret_score(score: float) -> str:
    """
    Interpret an AlphaMissense pathogenicity score.
    """
    if score < 0.34:
        return "Likely benign - low probability of pathogenicity"
    elif score < 0.564:
        return "Ambiguous - uncertain pathogenicity prediction"
    else:
        return "Likely pathogenic - high probability of pathogenicity"


def score_to_acmg_evidence(score: float) -> Optional[str]:
    """
    Convert AlphaMissense score to ACMG evidence code.

    Note: This is a simplification. ACMG guidelines recommend
    using multiple lines of computational evidence.
    """
    if score >= 0.8:
        return "PP3_strong"  # Strong supporting pathogenic
    elif score >= 0.564:
        return "PP3"  # Supporting pathogenic
    elif score < 0.1:
        return "BP4"  # Supporting benign
    else:
        return None  # Insufficient evidence
