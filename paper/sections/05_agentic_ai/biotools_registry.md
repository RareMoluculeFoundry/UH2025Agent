# The Biotools Registry

## 5.4 Integrated Bio-Tool APIs

The UH2025-CDS-Agent integrates a curated set of bioinformatic tools that serve as the "sensor layer" for the Executor agent. Each tool provides domain-specific variant annotation, pathogenicity prediction, or gene-disease association data.

## Tool Overview

| Tool | Purpose | Implementation Status | Data Source |
|:-----|:--------|:---------------------|:------------|
| **AlphaMissense** | Missense pathogenicity | LIVE | DuckDB / GCS |
| **AlphaGenome** | Regulatory effect prediction | LIVE | API + Zarr cache |
| **ClinVar** | Clinical variant annotation | LIVE | NCBI E-Utils API |
| **OMIM** | Gene-disease relationships | CONDITIONAL | OMIM API (key required) |
| **SpliceAI** | Splice site prediction | STUB | Planned |
| **REVEL** | Ensemble pathogenicity | STUB | Planned |
| **Custom** | User-defined tools | Extensible | User-configured |

## Tool Implementations

### AlphaMissense

**Status**: LIVE

AlphaMissense, developed by Google DeepMind, uses protein language models derived from AlphaFold to predict missense variant pathogenicity.[33]

**Key Statistics**:
- 89% of 71 million possible missense variants classified
- Leap from 0.1% human expert confirmation to near-complete coverage
- Classes: `likely_pathogenic`, `likely_benign`, `ambiguous`

**Implementation**:
```python
# code/biotools/alphamissense.py
class AlphaMissenseTool(BaseTool):
    """Query AlphaMissense predictions via DuckDB."""

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        # Direct DuckDB query against local parquet/TSV
        # or Google Cloud Storage direct access
        result = self.db.execute("""
            SELECT am_pathogenicity, am_class
            FROM predictions
            WHERE uniprot_id = ? AND position = ?
        """, [uniprot_id, position])
        return {"pathogenicity": result.am_pathogenicity, ...}
```

**Code Location**: [code/biotools/alphamissense.py](../../code/biotools/alphamissense.py)

---

### AlphaGenome

**Status**: LIVE

AlphaGenome is DeepMind's "sequence-to-function" model that predicts gene regulation and expression directly from raw DNA sequences.[23]

**Capabilities**:
- Predicts regulatory effects of non-coding variants
- Functions as a "virtual lab" for variant effect prediction
- Tissue-specific predictions available

**Implementation**:
```python
# code/biotools/alphagenome.py
class AlphaGenomeTool(BaseTool):
    """Query AlphaGenome API with Zarr caching."""

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        cache_key = f"{variant.chrom}_{variant.pos}_{variant.ref}_{variant.alt}"
        if cached := self.cache.get(cache_key):
            return cached

        result = self.client.predict(
            chromosome=variant.chrom,
            position=variant.pos,
            reference=variant.ref,
            alternate=variant.alt
        )
        self.cache.set(cache_key, result)
        return result
```

**Code Location**: [code/biotools/alphagenome.py](../../code/biotools/alphagenome.py)

---

### ClinVar

**Status**: LIVE (v2.0.0)

ClinVar is NCBI's public archive of reports on relationships among human variations and phenotypes.[1]

**API Integration**:
- **esearch.fcgi**: Search ClinVar by variant, gene, or rsID
- **esummary.fcgi**: Fetch detailed variant annotations
- Rate limiting: 3 requests/second (10 with API key)

**Implementation**:
```python
# code/biotools/clinvar.py
class ClinVarTool(BaseTool):
    """Query ClinVar via NCBI E-utilities API."""

    def _search_clinvar(self, query: str) -> List[str]:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "clinvar", "term": query, "retmode": "json"}
        return response.json()["esearchresult"]["idlist"]

    def _fetch_summary(self, var_ids: List[str]) -> Dict:
        url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        params = {"db": "clinvar", "id": ",".join(var_ids), "retmode": "json"}
        return response.json()
```

**Output Fields**:
- `clinical_significance`: Pathogenic, Likely Pathogenic, VUS, etc.
- `review_status`: Number of stars (0-4)
- `conditions`: Associated phenotypes/diseases
- `last_evaluated`: Date of last review

**Code Location**: [code/biotools/clinvar.py](../../code/biotools/clinvar.py)

---

### OMIM

**Status**: CONDITIONAL (requires API key)

The Online Mendelian Inheritance in Man (OMIM) database provides authoritative gene-disease relationships.[1]

**Features**:
- Gene-to-phenotype mapping
- Inheritance pattern classification
- MIM number cross-references

**Implementation**:
```python
# code/biotools/omim.py
class OMIMTool(BaseTool):
    """Query OMIM API for gene-disease associations."""

    def _query_api(self, gene: str) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("OMIM_API_KEY not set, using stub")
            return self._stub_query(gene)

        url = f"{self.base_url}/geneMap/search"
        params = {
            "search": f"approved_gene_symbol:{gene}",
            "include": "geneMap",
            "apiKey": self.api_key
        }
        return self._parse_response(response.json())
```

**Registration**: https://www.omim.org/api

**Code Location**: [code/biotools/omim.py](../../code/biotools/omim.py)

---

### SpliceAI

**Status**: STUB (Planned)

SpliceAI predicts the likelihood that a variant will affect RNA splicing.

**Planned Features**:
- Delta score prediction for donor/acceptor gain/loss
- Pre-computed lookup table integration
- API fallback for novel variants

**Code Location**: [code/biotools/spliceai.py](../../code/biotools/spliceai.py)

---

### REVEL

**Status**: STUB (Planned)

REVEL (Rare Exome Variant Ensemble Learner) provides ensemble pathogenicity scores.

**Planned Features**:
- Pre-computed score lookup
- Integration with dbNSFP database
- Score interpretation guidance

**Code Location**: [code/biotools/revel.py](../../code/biotools/revel.py)

---

## Tool Integration Architecture

### Base Tool Interface

All bio-tools inherit from `BaseTool`, providing a consistent interface:

```python
# code/biotools/base_tool.py
class BaseTool(ABC):
    @abstractmethod
    def query(self, variants: List[Variant]) -> List[ToolResult]:
        """Query the tool for a list of variants."""
        pass

    def _query_batch(self, variants: List[Variant]) -> List[ToolResult]:
        """Batch query with rate limiting."""
        pass
```

### Executor Integration

The Executor agent selects tools based on the Structuring agent's `tool_usage_plan`:

```python
# Tool selection flow
tool_usage_plan = [
    {"variant": "chr17:62023005:G:A", "tool": "clinvar", "rationale": "..."},
    {"variant": "chr17:62023005:G:A", "tool": "alphamissense", "rationale": "..."},
]

for plan_item in tool_usage_plan:
    tool = tool_registry[plan_item["tool"]]
    result = tool.query([plan_item["variant"]])
```

### Result Aggregation

Tool results are aggregated into a unified structure for the Synthesis agent:

```json
{
  "variant": "chr17:62023005:G:A",
  "tool_results": {
    "clinvar": {"clinical_significance": "Pathogenic", ...},
    "alphamissense": {"pathogenicity": 0.89, "class": "likely_pathogenic"},
    "omim": {"phenotypes": [{"name": "Paramyotonia Congenita", "mim": "168300"}]}
  },
  "consensus_pathogenicity": "likely_pathogenic"
}
```

## Adding Custom Tools

The biotools registry is extensible. To add a custom tool:

1. **Create tool class** inheriting from `BaseTool`:
   ```python
   # code/biotools/my_tool.py
   class MyTool(BaseTool):
       name = "my_tool"
       version = "1.0.0"

       def _query_single(self, variant: Variant) -> Dict[str, Any]:
           # Implementation
           pass
   ```

2. **Register in tool registry**:
   ```python
   # code/biotools/__init__.py
   from .my_tool import MyTool
   TOOL_REGISTRY["my_tool"] = MyTool
   ```

3. **Add to params.yaml** (optional):
   ```yaml
   biotools:
     my_tool:
       enabled: true
       api_key: ${MY_TOOL_API_KEY}
   ```

See [CONTRIBUTING.md](../../code/biotools/CONTRIBUTING.md) for detailed guidelines.

## References

- [1] ARPA-H - Rare Disease Statistics
- [23] CO/AI - AlphaGenome & Pushmeet Kohli
- [33] DeepMind Blog - AlphaMissense details
