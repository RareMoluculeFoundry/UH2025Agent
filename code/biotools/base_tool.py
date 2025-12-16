"""
BaseTool: Abstract interface for all bio-informatics tools.

All tools in the UH2025-CDS bio-tools library inherit from this base class,
ensuring consistent:
- Input/output formats
- Error handling
- Rate limiting
- Caching
- Logging

This design makes it easy for the community to contribute new tools!
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json


class ToolStatus(Enum):
    """Execution status for a tool query."""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"


@dataclass
class Variant:
    """
    Standardized variant representation for tool queries.

    Supports multiple notation formats.
    """
    # Required: At least one of these must be provided
    chromosome: Optional[str] = None
    position: Optional[int] = None
    reference: Optional[str] = None
    alternate: Optional[str] = None

    # Alternative identifiers
    rsid: Optional[str] = None  # rs123456
    clinvar_id: Optional[str] = None  # ClinVar accession
    hgvs_c: Optional[str] = None  # c.123A>G
    hgvs_p: Optional[str] = None  # p.Arg41Gln
    hgvs_g: Optional[str] = None  # NC_000001.11:g.12345A>G

    # Gene context
    gene: Optional[str] = None
    transcript: Optional[str] = None

    # Additional metadata
    zygosity: Optional[str] = None
    quality: Optional[float] = None

    def to_vcf_string(self) -> str:
        """Convert to VCF-style string (chr:pos:ref>alt)."""
        if all([self.chromosome, self.position, self.reference, self.alternate]):
            return f"{self.chromosome}:{self.position}:{self.reference}>{self.alternate}"
        return self.hgvs_c or self.hgvs_g or self.rsid or "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chromosome": self.chromosome,
            "position": self.position,
            "reference": self.reference,
            "alternate": self.alternate,
            "rsid": self.rsid,
            "clinvar_id": self.clinvar_id,
            "hgvs_c": self.hgvs_c,
            "hgvs_p": self.hgvs_p,
            "gene": self.gene,
            "transcript": self.transcript,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Variant":
        """Create Variant from dictionary."""
        return cls(
            chromosome=data.get("chromosome") or data.get("chrom"),
            position=data.get("position") or data.get("pos"),
            reference=data.get("reference") or data.get("ref"),
            alternate=data.get("alternate") or data.get("alt"),
            rsid=data.get("rsid") or data.get("rs_id"),
            clinvar_id=data.get("clinvar_id"),
            hgvs_c=data.get("hgvs_c"),
            hgvs_p=data.get("hgvs_p") or data.get("protein_change"),
            gene=data.get("gene"),
            transcript=data.get("transcript"),
            zygosity=data.get("zygosity"),
            quality=data.get("quality") or data.get("qual"),
        )

    def cache_key(self) -> str:
        """Generate cache key for this variant."""
        key_data = self.to_vcf_string() + (self.gene or "")
        return hashlib.md5(key_data.encode()).hexdigest()


@dataclass
class ToolResult:
    """
    Standardized result from a tool query.

    All tools return results in this format for consistency.
    """
    tool_name: str
    variant: Variant
    status: ToolStatus

    # The actual annotation data (tool-specific)
    annotations: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    query_time: Optional[datetime] = None
    response_time_ms: float = 0.0
    cache_hit: bool = False

    # Error information
    error_message: Optional[str] = None

    # Source information
    data_version: Optional[str] = None
    data_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "variant": self.variant.to_dict(),
            "status": self.status.value,
            "annotations": self.annotations,
            "query_time": self.query_time.isoformat() if self.query_time else None,
            "response_time_ms": self.response_time_ms,
            "cache_hit": self.cache_hit,
            "error_message": self.error_message,
            "data_version": self.data_version,
        }


class BaseTool(ABC):
    """
    Abstract base class for all bio-informatics tools.

    Provides common functionality for:
    - Variant querying
    - Result caching
    - Rate limiting
    - Error handling

    Subclasses must implement:
    - _query_single(): Query a single variant
    - _validate_variant(): Check if variant is queryable by this tool

    Example implementation:
    ```python
    class MyNewTool(BaseTool):
        name = "my_tool"
        version = "1.0.0"
        description = "My awesome bio-tool"

        def _query_single(self, variant: Variant) -> Dict[str, Any]:
            # Call external API or database
            result = my_api.query(variant.rsid)
            return {"score": result.score, "prediction": result.pred}

        def _validate_variant(self, variant: Variant) -> Optional[str]:
            if not variant.rsid:
                return "This tool requires rsID"
            return None
    ```
    """

    # Class-level configuration (override in subclasses)
    name: str = "base_tool"
    version: str = "1.0.0"
    description: str = "Base bio-informatics tool"

    # Rate limiting
    rate_limit_per_second: int = 10
    rate_limit_per_minute: int = 100

    # Caching
    cache_enabled: bool = True
    cache_ttl_hours: int = 24

    # Timeout
    timeout_seconds: int = 30

    def __init__(self):
        """Initialize tool with optional configuration."""
        self._cache: Dict[str, ToolResult] = {}
        self._last_query_times: List[datetime] = []

    def query(self, variant: Variant) -> ToolResult:
        """
        Query the tool for a single variant.

        Handles caching, rate limiting, and error wrapping.

        Args:
            variant: Variant to query

        Returns:
            ToolResult with annotations or error information
        """
        start_time = datetime.now()

        # Check cache
        if self.cache_enabled:
            cache_key = f"{self.name}:{variant.cache_key()}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                cached.cache_hit = True
                return cached

        # Validate variant
        validation_error = self._validate_variant(variant)
        if validation_error:
            return ToolResult(
                tool_name=self.name,
                variant=variant,
                status=ToolStatus.ERROR,
                error_message=validation_error,
                query_time=start_time,
            )

        # Check rate limiting
        if not self._check_rate_limit():
            return ToolResult(
                tool_name=self.name,
                variant=variant,
                status=ToolStatus.RATE_LIMITED,
                error_message="Rate limit exceeded",
                query_time=start_time,
            )

        # Execute query
        try:
            annotations = self._query_single(variant)
            end_time = datetime.now()

            result = ToolResult(
                tool_name=self.name,
                variant=variant,
                status=ToolStatus.SUCCESS if annotations else ToolStatus.NOT_FOUND,
                annotations=annotations or {},
                query_time=start_time,
                response_time_ms=(end_time - start_time).total_seconds() * 1000,
                data_version=self._get_data_version(),
            )

            # Cache result
            if self.cache_enabled:
                self._cache[cache_key] = result

            return result

        except TimeoutError:
            return ToolResult(
                tool_name=self.name,
                variant=variant,
                status=ToolStatus.TIMEOUT,
                error_message=f"Query timed out after {self.timeout_seconds}s",
                query_time=start_time,
            )

        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                variant=variant,
                status=ToolStatus.ERROR,
                error_message=str(e),
                query_time=start_time,
            )

    def query_batch(self, variants: List[Variant]) -> List[ToolResult]:
        """
        Query multiple variants.

        Override in subclasses for batch-optimized queries.

        Args:
            variants: List of variants to query

        Returns:
            List of ToolResults
        """
        return [self.query(v) for v in variants]

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.now()

        # Clean old timestamps
        one_minute_ago = now.timestamp() - 60
        self._last_query_times = [
            t for t in self._last_query_times
            if t.timestamp() > one_minute_ago
        ]

        # Check minute limit
        if len(self._last_query_times) >= self.rate_limit_per_minute:
            return False

        # Check second limit (last N queries in last second)
        one_second_ago = now.timestamp() - 1
        recent = [t for t in self._last_query_times if t.timestamp() > one_second_ago]
        if len(recent) >= self.rate_limit_per_second:
            return False

        self._last_query_times.append(now)
        return True

    def _get_data_version(self) -> Optional[str]:
        """Get the version of the underlying data source."""
        return self.version

    @abstractmethod
    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        """
        Execute the actual query for a single variant.

        Must be implemented by subclasses.

        Args:
            variant: Validated variant to query

        Returns:
            Dictionary of annotations (empty dict if not found)
        """
        pass

    @abstractmethod
    def _validate_variant(self, variant: Variant) -> Optional[str]:
        """
        Validate that a variant can be queried by this tool.

        Must be implemented by subclasses.

        Args:
            variant: Variant to validate

        Returns:
            Error message if invalid, None if valid
        """
        pass

    def clear_cache(self):
        """Clear the result cache."""
        self._cache = {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, version={self.version})"
