"""
[STUB] ClinVarTool: Query NCBI ClinVar for variant clinical significance.

STATUS: STUB IMPLEMENTATION
- API structure is defined but returns mock data when use_stub=True
- Real NCBI E-utilities integration exists but is not fully tested
- TODO: Complete E-Utils API testing and validation
- TODO: Add local VCF dump fallback for offline use

ClinVar is a public archive of reports on relationships between
human genetic variants and phenotypes, with supporting evidence.

Data Source: NCBI ClinVar (https://www.ncbi.nlm.nih.gov/clinvar/)
API: NCBI E-utilities (esearch.fcgi, esummary.fcgi)

Key Annotations:
- Clinical significance (pathogenic, likely pathogenic, VUS, etc.)
- Review status (criteria provided, reviewed by expert panel, etc.)
- Associated conditions
- Submission history

Version 2.0.0: Real NCBI E-utilities API implementation
"""

from typing import Any, Dict, List, Optional
import os
import time
import logging

import requests

from .base_tool import BaseTool, ToolResult, ToolStatus, Variant

logger = logging.getLogger(__name__)


class ClinVarTool(BaseTool):
    """
    Query ClinVar for variant clinical significance annotations.

    ClinVar provides expertly curated clinical interpretations of
    genetic variants, essential for rare disease diagnosis.
    """

    name = "clinvar"
    version = "2.0.0"
    description = "Query ClinVar for variant clinical significance"

    # NCBI E-utilities base URLs
    EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    ESEARCH_URL = f"{EUTILS_BASE}/esearch.fcgi"
    ESUMMARY_URL = f"{EUTILS_BASE}/esummary.fcgi"

    # ClinVar-specific configuration
    rate_limit_per_second = 3  # NCBI recommends max 3 requests/second without API key
    rate_limit_per_minute = 100

    # Clinical significance levels
    SIGNIFICANCE_LEVELS = [
        "pathogenic",
        "likely_pathogenic",
        "uncertain_significance",
        "likely_benign",
        "benign",
        "conflicting_interpretations",
        "not_provided",
    ]

    # Review status levels (quality indicator)
    REVIEW_STATUS = {
        "practice_guideline": 4,
        "reviewed_by_expert_panel": 3,
        "criteria_provided_multiple_submitters_no_conflicts": 2,
        "criteria_provided_single_submitter": 1,
        "no_assertion_criteria_provided": 0,
    }

    def __init__(self, api_key: Optional[str] = None, use_stub: bool = False):
        """
        Initialize ClinVar tool.

        Args:
            api_key: NCBI API key (optional but recommended for higher rate limits)
            use_stub: If True, use stub data instead of real API (for testing)
        """
        super().__init__()
        self.api_key = api_key or os.environ.get("NCBI_API_KEY")
        self.use_stub = use_stub or os.environ.get("CLINVAR_USE_STUB", "").lower() == "true"
        self._last_request_time = 0.0

        if self.api_key:
            # Higher rate limits with API key
            self.rate_limit_per_second = 10
            self.rate_limit_per_minute = 300
            logger.info("ClinVar initialized with API key (higher rate limits)")
        else:
            logger.info("ClinVar initialized without API key (limited to 3 req/sec)")

    def _validate_variant(self, variant: Variant) -> Optional[str]:
        """
        Validate variant for ClinVar query.

        ClinVar can be queried by:
        - rsID
        - ClinVar accession
        - Genomic coordinates (chr:pos:ref>alt)
        - HGVS notation
        """
        has_identifier = any([
            variant.rsid,
            variant.clinvar_id,
            all([variant.chromosome, variant.position, variant.reference, variant.alternate]),
            variant.hgvs_c,
            variant.hgvs_g,
        ])

        if not has_identifier:
            return (
                "ClinVar requires at least one of: rsID, ClinVar ID, "
                "genomic coordinates (chr:pos:ref>alt), or HGVS notation"
            )

        return None

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        """
        Query ClinVar for a single variant using NCBI E-utilities.

        Uses esearch to find ClinVar IDs, then esummary to fetch details.
        Falls back to stub data if API fails or use_stub is True.
        """
        # Use stub data if configured
        if self.use_stub:
            logger.debug("Using stub data (use_stub=True)")
            return self._stub_query(variant)

        # Build query string
        query = self._build_query(variant)
        logger.debug(f"ClinVar query: {query}")

        try:
            # Step 1: Search for ClinVar IDs (esearch)
            clinvar_ids = self._esearch(query)

            if not clinvar_ids:
                logger.info(f"No ClinVar entries found for query: {query}")
                return self._not_found_result(variant)

            # Step 2: Fetch variant details (esummary)
            # Use the first (most relevant) ID
            clinvar_id = clinvar_ids[0]
            result = self._esummary(clinvar_id)

            if result:
                result["data_source"] = "NCBI ClinVar E-Utils API"
                result["query_used"] = query
                return result
            else:
                logger.warning(f"esummary returned no data for ID: {clinvar_id}")
                return self._not_found_result(variant)

        except requests.RequestException as e:
            logger.error(f"ClinVar API request failed: {e}")
            # Fall back to stub on network errors
            logger.info("Falling back to stub data due to API error")
            stub_result = self._stub_query(variant)
            stub_result["data_source"] = f"STUB - API error: {str(e)}"
            return stub_result

        except Exception as e:
            logger.error(f"Unexpected error querying ClinVar: {e}")
            stub_result = self._stub_query(variant)
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

    def _esearch(self, query: str) -> List[str]:
        """
        Search ClinVar for variant IDs using esearch.

        Args:
            query: ClinVar search query string

        Returns:
            List of ClinVar variant IDs (UIDs)
        """
        self._rate_limit()

        params = {
            "db": "clinvar",
            "term": query,
            "retmode": "json",
            "retmax": 5,  # Get top 5 matches
        }
        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.get(self.ESEARCH_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        esearch_result = data.get("esearchresult", {})

        # Check for errors
        if "ERROR" in esearch_result:
            logger.error(f"esearch error: {esearch_result['ERROR']}")
            return []

        id_list = esearch_result.get("idlist", [])
        logger.debug(f"esearch found {len(id_list)} IDs: {id_list}")
        return id_list

    def _esummary(self, clinvar_uid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ClinVar variant summary using esummary.

        Args:
            clinvar_uid: ClinVar UID from esearch

        Returns:
            Parsed variant data or None if not found
        """
        self._rate_limit()

        params = {
            "db": "clinvar",
            "id": clinvar_uid,
            "retmode": "json",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        response = requests.get(self.ESUMMARY_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        result = data.get("result", {})

        # Get the document summary
        if clinvar_uid not in result:
            logger.warning(f"UID {clinvar_uid} not in esummary result")
            return None

        doc = result[clinvar_uid]
        return self._parse_esummary(doc, clinvar_uid)

    def _parse_esummary(self, doc: Dict[str, Any], uid: str) -> Dict[str, Any]:
        """
        Parse esummary document into standardized format.

        Args:
            doc: Raw esummary document
            uid: ClinVar UID

        Returns:
            Standardized variant annotation dict
        """
        # Extract clinical significance
        clinical_sig = doc.get("clinical_significance", {})
        description = clinical_sig.get("description", "not_provided")

        # Normalize significance string
        significance_normalized = description.lower().replace(" ", "_")

        # Extract review status
        review_status = clinical_sig.get("review_status", "no_assertion_criteria_provided")
        review_stars = self._review_status_to_stars(review_status)

        # Extract gene information
        genes = doc.get("genes", [])
        gene_symbol = genes[0].get("symbol", "") if genes else ""

        # Extract conditions/traits
        trait_set = doc.get("trait_set", [])
        conditions = []
        for trait in trait_set:
            trait_names = trait.get("trait_name", [])
            for t in trait_names:
                conditions.append({
                    "name": t.get("value", ""),
                    "medgen_id": trait.get("trait_xrefs", {}).get("medgen", ""),
                    "omim_id": trait.get("trait_xrefs", {}).get("omim", ""),
                })

        # Extract accession
        accession = doc.get("accession", f"VCV{uid}")

        # Extract variation details
        variation_set = doc.get("variation_set", [{}])[0] if doc.get("variation_set") else {}
        hgvs_list = variation_set.get("canonical_spdi", "")

        return {
            "clinvar_accession": accession,
            "clinvar_uid": uid,
            "clinical_significance": significance_normalized,
            "clinical_significance_description": description,
            "review_status": review_status,
            "review_stars": review_stars,
            "conditions": conditions if conditions else [{"name": "Not specified", "medgen_id": "", "omim_id": ""}],
            "gene_symbol": gene_symbol,
            "molecular_consequence": variation_set.get("variant_type", ""),
            "hgvs_expressions": {
                "canonical_spdi": hgvs_list,
            },
            "title": doc.get("title", ""),
            "last_evaluated": clinical_sig.get("last_evaluated", ""),
            "supporting_submissions": {
                "scv_count": doc.get("supporting_submissions", {}).get("scv", 0),
            },
        }

    def _review_status_to_stars(self, review_status: str) -> int:
        """Convert review status string to star rating (0-4)."""
        status_lower = review_status.lower()
        for status_pattern, stars in self.REVIEW_STATUS.items():
            if status_pattern in status_lower:
                return stars
        return 0

    def _not_found_result(self, variant: Variant) -> Dict[str, Any]:
        """Return a standardized 'not found' result."""
        return {
            "clinvar_accession": None,
            "clinical_significance": "not_found",
            "review_status": "no_data",
            "review_stars": 0,
            "conditions": [],
            "gene_symbol": variant.gene or "",
            "data_source": "NCBI ClinVar E-Utils API - No entry found",
        }

    def _build_query(self, variant: Variant) -> str:
        """Build ClinVar query string from variant."""
        if variant.clinvar_id:
            return variant.clinvar_id

        if variant.rsid:
            return variant.rsid

        if variant.hgvs_c and variant.gene:
            return f"{variant.gene}[gene] AND {variant.hgvs_c}"

        if all([variant.chromosome, variant.position]):
            chrom = variant.chromosome.replace("chr", "")
            return f"{chrom}[chr] AND {variant.position}[chrpos]"

        return variant.to_vcf_string()

    def _stub_query(self, variant: Variant) -> Dict[str, Any]:
        """
        Return stub ClinVar data for development/testing.

        This will be replaced with actual API calls.
        """
        # Simulated response based on variant
        gene = variant.gene or "UNKNOWN"

        return {
            "clinvar_accession": f"VCV{hash(variant.to_vcf_string()) % 1000000:06d}",
            "clinical_significance": "uncertain_significance",
            "clinical_significance_ordered": [
                "uncertain_significance"
            ],
            "review_status": "criteria_provided_single_submitter",
            "review_stars": 1,
            "conditions": [
                {
                    "name": f"[STUB] {gene}-related disorder",
                    "medgen_id": "C0000000",
                    "omim_id": None,
                }
            ],
            "gene_symbol": gene,
            "molecular_consequence": "missense_variant",
            "hgvs_expressions": {
                "genomic": variant.hgvs_g,
                "coding": variant.hgvs_c,
                "protein": variant.hgvs_p,
            },
            "submissions": [
                {
                    "submitter": "[STUB] Clinical Lab",
                    "significance": "uncertain_significance",
                    "date": "2024-01-01",
                    "method": "clinical_testing",
                }
            ],
            "last_evaluated": "2024-06-01",
            "data_source": "STUB - API not connected",
        }

    def query_batch(self, variants: List[Variant]) -> List[ToolResult]:
        """
        Query multiple variants using ClinVar batch API.

        ClinVar supports batch queries via E-utilities for efficiency.
        """
        # TODO: Implement batch query using efetch
        # For now, fall back to sequential queries
        return super().query_batch(variants)

    def get_submission_history(self, clinvar_id: str) -> List[Dict[str, Any]]:
        """
        Get full submission history for a ClinVar accession.

        Useful for understanding how interpretations have changed over time.
        """
        # TODO: Implement submission history lookup
        return []

    def _get_data_version(self) -> Optional[str]:
        """Get ClinVar data version from einfo."""
        if self.use_stub:
            return "2024-06 (STUB)"

        try:
            self._rate_limit()
            einfo_url = f"{self.EUTILS_BASE}/einfo.fcgi"
            params = {"db": "clinvar", "retmode": "json"}
            if self.api_key:
                params["api_key"] = self.api_key

            response = requests.get(einfo_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            dbinfo = data.get("einforesult", {}).get("dbinfo", [{}])[0]
            last_update = dbinfo.get("lastupdate", "unknown")
            return f"ClinVar {last_update}"
        except Exception as e:
            logger.warning(f"Could not get ClinVar version: {e}")
            return "ClinVar (version unknown)"


# Utility functions for ClinVar data interpretation

def parse_significance(significance: str) -> int:
    """
    Convert clinical significance to numeric score.

    Higher scores = more pathogenic.
    """
    scores = {
        "pathogenic": 5,
        "likely_pathogenic": 4,
        "uncertain_significance": 3,
        "likely_benign": 2,
        "benign": 1,
        "conflicting_interpretations": 3,
    }
    return scores.get(significance.lower(), 3)


def parse_review_status(status: str) -> int:
    """
    Convert review status to star rating (0-4).

    Higher = more reliable.
    """
    status_map = {
        "practice guideline": 4,
        "reviewed by expert panel": 3,
        "criteria provided, multiple submitters, no conflicts": 2,
        "criteria provided, single submitter": 1,
        "no assertion criteria provided": 0,
        "no assertion provided": 0,
    }
    return status_map.get(status.lower(), 0)
