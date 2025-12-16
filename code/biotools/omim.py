"""
[STUB] OMIMTool: Query OMIM for disease-gene relationships.

STATUS: STUB IMPLEMENTATION
- API structure defined, returns stub data without API key
- Real OMIM API integration exists but requires OMIM_API_KEY
- TODO: Test API integration with academic API key
- TODO: Add local OMIM dump fallback for offline use

OMIM (Online Mendelian Inheritance in Man) is the authoritative
database of human genes and genetic phenotypes. It provides:
- Disease-gene relationships
- Inheritance patterns
- Phenotypic features
- Allelic variants
- References to literature

Data Source: OMIM (https://www.omim.org/)
API: OMIM API (requires API key)

Note: OMIM API access requires registration and agreement to
terms of use. Academic use is generally approved.

Version 2.0.0: Real OMIM API implementation (conditional on API key)
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import os
import time
import logging

import requests

from .base_tool import BaseTool, ToolResult, ToolStatus, Variant

logger = logging.getLogger(__name__)


class InheritancePattern(Enum):
    """Mendelian inheritance patterns."""
    AUTOSOMAL_DOMINANT = "AD"
    AUTOSOMAL_RECESSIVE = "AR"
    X_LINKED_DOMINANT = "XLD"
    X_LINKED_RECESSIVE = "XLR"
    Y_LINKED = "YL"
    MITOCHONDRIAL = "MT"
    DIGENIC = "DG"
    SOMATIC = "SMu"
    UNKNOWN = "?"


@dataclass
class OMIMPhenotype:
    """A phenotype/disease from OMIM."""
    mim_number: str
    phenotype_name: str
    inheritance: Optional[InheritancePattern] = None
    phenotype_mapping_key: Optional[int] = None

    # Clinical details
    clinical_synopsis: Optional[str] = None
    clinical_features: List[str] = field(default_factory=list)

    # Related genes
    gene_symbols: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mim_number": self.mim_number,
            "phenotype_name": self.phenotype_name,
            "inheritance": self.inheritance.value if self.inheritance else None,
            "phenotype_mapping_key": self.phenotype_mapping_key,
            "clinical_synopsis": self.clinical_synopsis,
            "clinical_features": self.clinical_features,
            "gene_symbols": self.gene_symbols,
        }


@dataclass
class OMIMGene:
    """A gene entry from OMIM."""
    mim_number: str
    gene_symbol: str
    gene_name: str

    # Associated phenotypes
    phenotypes: List[OMIMPhenotype] = field(default_factory=list)

    # Allelic variants
    allelic_variants_count: int = 0

    # Chromosomal location
    cyto_location: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mim_number": self.mim_number,
            "gene_symbol": self.gene_symbol,
            "gene_name": self.gene_name,
            "phenotypes": [p.to_dict() for p in self.phenotypes],
            "allelic_variants_count": self.allelic_variants_count,
            "cyto_location": self.cyto_location,
        }


class OMIMTool(BaseTool):
    """
    Query OMIM for disease-gene relationships and phenotype information.

    Unlike other tools in the library, OMIM is primarily queried by
    GENE rather than by variant. It provides crucial context for
    understanding potential disease associations.

    Usage:
    - Query by gene symbol to get associated phenotypes
    - Query by MIM number for specific disease details
    - Query by phenotype name for differential diagnosis
    """

    name = "omim"
    version = "2.0.0"
    description = "Query OMIM for disease-gene relationships"

    # OMIM API base URL and endpoints
    API_BASE_URL = "https://api.omim.org/api"
    ENTRY_SEARCH_URL = f"{API_BASE_URL}/entry/search"
    ENTRY_URL = f"{API_BASE_URL}/entry"
    GENEINFO_URL = f"{API_BASE_URL}/geneMap/search"

    # OMIM API rate limits
    rate_limit_per_second = 4  # OMIM recommends max 4 requests/second
    rate_limit_per_minute = 240

    def __init__(self, api_key: Optional[str] = None, use_stub: bool = False):
        """
        Initialize OMIM tool.

        Args:
            api_key: OMIM API key. Required for full access.
                    Register at https://www.omim.org/api
            use_stub: If True, use stub data instead of real API (for testing)
        """
        super().__init__()
        self.api_key = api_key or os.environ.get("OMIM_API_KEY")
        self.use_stub = use_stub or os.environ.get("OMIM_USE_STUB", "").lower() == "true"
        self._last_request_time = 0.0

        if self.api_key:
            logger.info("OMIM initialized with API key")
        else:
            logger.warning("OMIM initialized without API key - will use stub data")

    def _validate_variant(self, variant: Variant) -> Optional[str]:
        """
        Validate variant for OMIM query.

        OMIM is primarily queried by gene, not by specific variants.
        """
        if not variant.gene:
            return (
                "OMIM queries require a gene symbol. "
                "Provide the gene associated with this variant."
            )
        return None

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        """
        Query OMIM for gene-disease relationships.

        Uses real OMIM API if API key is available, otherwise returns stub data.
        """
        gene = variant.gene

        # Use stub if configured or no API key
        if self.use_stub or not self.api_key:
            if not self.api_key:
                logger.debug(f"No OMIM API key - using stub for gene: {gene}")
            return self._stub_query(gene)

        try:
            return self._query_api(gene)
        except requests.RequestException as e:
            logger.error(f"OMIM API request failed: {e}")
            stub_result = self._stub_query(gene)
            stub_result["data_source"] = f"STUB - API error: {str(e)}"
            return stub_result
        except Exception as e:
            logger.error(f"Unexpected error querying OMIM: {e}")
            stub_result = self._stub_query(gene)
            stub_result["data_source"] = f"STUB - Error: {str(e)}"
            return stub_result

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        min_interval = 1.0 / self.rate_limit_per_second
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _query_api(self, gene: str) -> Dict[str, Any]:
        """
        Query OMIM API for gene information.

        Args:
            gene: Gene symbol to search

        Returns:
            Parsed OMIM data for the gene
        """
        self._rate_limit()

        # Search for gene in geneMap
        params = {
            "search": gene,
            "include": "geneMap",
            "format": "json",
            "apiKey": self.api_key,
        }

        response = requests.get(self.GENEINFO_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        gene_map_list = data.get("omim", {}).get("searchResponse", {}).get("geneMapList", [])

        if not gene_map_list:
            logger.info(f"No OMIM entries found for gene: {gene}")
            return self._not_found_result(gene)

        # Find the best match (exact gene symbol match preferred)
        best_match = None
        for entry in gene_map_list:
            gene_map = entry.get("geneMap", {})
            gene_symbols = gene_map.get("geneSymbols", "").split(", ")
            if gene.upper() in [s.upper() for s in gene_symbols]:
                best_match = gene_map
                break

        if not best_match and gene_map_list:
            best_match = gene_map_list[0].get("geneMap", {})

        if not best_match:
            return self._not_found_result(gene)

        return self._parse_gene_map(best_match)

    def _parse_gene_map(self, gene_map: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OMIM geneMap response into standardized format.

        Args:
            gene_map: Raw OMIM geneMap response

        Returns:
            Standardized gene annotation dict
        """
        # Extract gene info
        mim_number = str(gene_map.get("mimNumber", ""))
        gene_symbols = gene_map.get("geneSymbols", "").split(", ")
        gene_symbol = gene_symbols[0] if gene_symbols else ""
        gene_name = gene_map.get("geneName", "")
        cyto_location = gene_map.get("computedCytoLocation", "") or gene_map.get("cytoLocation", "")

        # Extract phenotypes
        phenotype_map_list = gene_map.get("phenotypeMapList", [])
        phenotypes = []
        inheritance_patterns = set()

        for phe_entry in phenotype_map_list:
            phe_map = phe_entry.get("phenotypeMap", {})

            # Parse inheritance
            inheritance_str = phe_map.get("phenotypeInheritance", "")
            inheritance = self._parse_inheritance_from_api(inheritance_str)
            if inheritance:
                inheritance_patterns.add(inheritance.value)

            phenotype = OMIMPhenotype(
                mim_number=str(phe_map.get("phenotypeMimNumber", "")),
                phenotype_name=phe_map.get("phenotype", ""),
                inheritance=inheritance,
                phenotype_mapping_key=phe_map.get("phenotypeMappingKey"),
                gene_symbols=gene_symbols,
            )
            phenotypes.append(phenotype)

        # Build gene entry
        gene_entry = OMIMGene(
            mim_number=mim_number,
            gene_symbol=gene_symbol,
            gene_name=gene_name,
            phenotypes=phenotypes,
            cyto_location=cyto_location,
        )

        return {
            "gene": gene_entry.to_dict(),
            "phenotypes": [p.to_dict() for p in phenotypes],
            "total_phenotypes": len(phenotypes),
            "inheritance_patterns": list(inheritance_patterns),
            "data_source": "OMIM API",
        }

    def _parse_inheritance_from_api(self, inheritance_str: str) -> Optional[InheritancePattern]:
        """Parse inheritance pattern string from OMIM API."""
        if not inheritance_str:
            return None

        inheritance_lower = inheritance_str.lower()

        # Check for multiple patterns (return first/dominant one)
        if "autosomal dominant" in inheritance_lower:
            return InheritancePattern.AUTOSOMAL_DOMINANT
        elif "autosomal recessive" in inheritance_lower:
            return InheritancePattern.AUTOSOMAL_RECESSIVE
        elif "x-linked dominant" in inheritance_lower:
            return InheritancePattern.X_LINKED_DOMINANT
        elif "x-linked recessive" in inheritance_lower:
            return InheritancePattern.X_LINKED_RECESSIVE
        elif "x-linked" in inheritance_lower:
            return InheritancePattern.X_LINKED_RECESSIVE
        elif "mitochondrial" in inheritance_lower:
            return InheritancePattern.MITOCHONDRIAL
        elif "digenic" in inheritance_lower:
            return InheritancePattern.DIGENIC
        elif "somatic" in inheritance_lower:
            return InheritancePattern.SOMATIC

        return InheritancePattern.UNKNOWN

    def _not_found_result(self, gene: str) -> Dict[str, Any]:
        """Return a standardized 'not found' result."""
        return {
            "gene": {
                "mim_number": None,
                "gene_symbol": gene,
                "gene_name": "",
                "phenotypes": [],
                "cyto_location": "",
            },
            "phenotypes": [],
            "total_phenotypes": 0,
            "inheritance_patterns": [],
            "data_source": "OMIM API - No entry found",
        }

    def _stub_query(self, gene: str) -> Dict[str, Any]:
        """
        Return stub OMIM data for development/testing.
        """
        # Generate deterministic MIM number
        mim_base = (hash(gene) % 100000) + 100000

        # Create stub phenotype
        phenotype = OMIMPhenotype(
            mim_number=str(mim_base),
            phenotype_name=f"[STUB] {gene}-related disorder",
            inheritance=InheritancePattern.AUTOSOMAL_DOMINANT,
            phenotype_mapping_key=3,  # 3 = gene with known phenotype
            clinical_features=[
                "[STUB] Progressive symptoms",
                "[STUB] Variable expressivity",
                "[STUB] Age-dependent penetrance",
            ],
            gene_symbols=[gene],
        )

        # Create stub gene entry
        gene_entry = OMIMGene(
            mim_number=str(mim_base + 1),
            gene_symbol=gene,
            gene_name=f"[STUB] {gene} gene",
            phenotypes=[phenotype],
            allelic_variants_count=25,
            cyto_location="[STUB] 1p36.33",
        )

        return {
            "gene": gene_entry.to_dict(),
            "phenotypes": [phenotype.to_dict()],
            "total_phenotypes": 1,
            "inheritance_patterns": ["AD"],
            "data_source": "STUB - API not connected",
        }

    def query_by_gene(self, gene_symbol: str) -> Dict[str, Any]:
        """
        Query OMIM by gene symbol.

        Args:
            gene_symbol: HGNC approved gene symbol (e.g., "SCN4A")

        Returns:
            Gene entry with associated phenotypes
        """
        dummy_variant = Variant(gene=gene_symbol)
        result = self.query(dummy_variant)
        return result.annotations if result.status == ToolStatus.SUCCESS else {}

    def query_by_mim(self, mim_number: str) -> Dict[str, Any]:
        """
        Query OMIM by MIM number.

        Args:
            mim_number: OMIM MIM number (e.g., "168300")

        Returns:
            Entry details for the MIM number
        """
        # TODO: Implement MIM number query
        return self._stub_query(f"MIM:{mim_number}")

    def search_phenotypes(self, search_term: str) -> List[OMIMPhenotype]:
        """
        Search OMIM phenotypes by keyword.

        Useful for differential diagnosis exploration.

        Args:
            search_term: Keyword to search (e.g., "myotonia")

        Returns:
            List of matching phenotypes
        """
        # TODO: Implement phenotype search
        return []

    def _get_data_version(self) -> Optional[str]:
        """Get OMIM data version."""
        if self.use_stub or not self.api_key:
            return "OMIM (STUB) - Real-time database"
        return "OMIM API - Real-time database"


# Utility functions for OMIM data interpretation

def parse_inheritance(pattern_string: str) -> InheritancePattern:
    """
    Parse inheritance pattern string to enum.

    Examples:
    - "Autosomal dominant" -> AD
    - "Autosomal recessive" -> AR
    - "X-linked recessive" -> XLR
    """
    pattern_lower = pattern_string.lower()

    if "autosomal dominant" in pattern_lower or pattern_string == "AD":
        return InheritancePattern.AUTOSOMAL_DOMINANT
    elif "autosomal recessive" in pattern_lower or pattern_string == "AR":
        return InheritancePattern.AUTOSOMAL_RECESSIVE
    elif "x-linked dominant" in pattern_lower:
        return InheritancePattern.X_LINKED_DOMINANT
    elif "x-linked recessive" in pattern_lower or "x-linked" in pattern_lower:
        return InheritancePattern.X_LINKED_RECESSIVE
    elif "mitochondrial" in pattern_lower:
        return InheritancePattern.MITOCHONDRIAL
    elif "digenic" in pattern_lower:
        return InheritancePattern.DIGENIC
    else:
        return InheritancePattern.UNKNOWN


def phenotype_mapping_key_description(key: int) -> str:
    """
    Describe OMIM phenotype mapping key.

    1 = Gene with known sequence and target disorder
    2 = Gene with known sequence but no disorder association
    3 = Gene with known sequence and phenotypic association
    4 = Gene with no known sequence but with disease association
    """
    descriptions = {
        1: "Gene with known sequence and target disorder",
        2: "Gene with known sequence, uncertain disorder relationship",
        3: "Gene with known sequence and phenotype association",
        4: "Gene with uncertain sequence but disease association",
    }
    return descriptions.get(key, "Unknown mapping")


def inheritance_supports_variant(
    inheritance: InheritancePattern,
    zygosity: str,
    sex: Optional[str] = None,
) -> bool:
    """
    Check if inheritance pattern is consistent with variant zygosity.

    Args:
        inheritance: OMIM inheritance pattern
        zygosity: Variant zygosity (heterozygous, homozygous, hemizygous)
        sex: Patient sex (male, female) - needed for X-linked

    Returns:
        True if inheritance pattern supports the observed zygosity
    """
    zygosity = zygosity.lower()

    if inheritance == InheritancePattern.AUTOSOMAL_DOMINANT:
        # AD: heterozygous sufficient
        return zygosity in ["heterozygous", "homozygous"]

    elif inheritance == InheritancePattern.AUTOSOMAL_RECESSIVE:
        # AR: typically requires homozygous or compound het
        return zygosity in ["homozygous", "compound_het", "compound_heterozygous"]

    elif inheritance == InheritancePattern.X_LINKED_RECESSIVE:
        # XLR: hemizygous in males, homozygous in females
        if sex == "male":
            return zygosity in ["hemizygous", "homozygous"]
        else:
            return zygosity == "homozygous"

    elif inheritance == InheritancePattern.X_LINKED_DOMINANT:
        # XLD: heterozygous in females, hemizygous in males
        return True  # Any X-linked variant could cause XLD

    return True  # Default to not filtering
