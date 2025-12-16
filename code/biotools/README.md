# UH2025Agent Bio-Tools Library

The Executor Agent orchestrates a library of bioinformatics tools for variant annotation and evidence gathering.

## Bio-Tool Status

| Tool | Status | Implementation | Data Source | Notes |
|------|--------|----------------|-------------|-------|
| **AlphaMissense** | ✅ LIVE | DuckDB queries | DeepMind 71M variants | Requires data download (~2GB) |
| **ClinVar** | ⚠️ STUB | Returns placeholder | NCBI ClinVar API | E-Utils API planned |
| **OMIM** | ⚠️ STUB | Returns placeholder | OMIM API | Requires API key |
| **SpliceAI** | ⚠️ STUB | Returns placeholder | Illumina pre-computed | API integration planned |
| **REVEL** | ⚠️ STUB | Returns placeholder | dbNSFP | Lookup table planned |

### Status Legend

- ✅ **LIVE**: Fully functional with real data queries
- ⚠️ **STUB**: Returns realistic placeholder data for development/testing

## Quick Start

```python
from code.biotools import TOOL_REGISTRY

# Get available tools
print(list(TOOL_REGISTRY.keys()))
# ['clinvar', 'spliceai', 'alphamissense', 'revel', 'omim']

# Query a tool
alphamissense = TOOL_REGISTRY['alphamissense']()
result = alphamissense.query(variant={
    'gene': 'SCN4A',
    'protein_change': 'p.Val781Ile'
})
```

## Architecture

All tools inherit from `BaseTool` and implement a standard interface:

```python
from code.biotools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    version = "1.0.0"
    description = "What this tool does"

    def query(self, variant: dict) -> dict:
        """Query the tool with a variant."""
        # Implementation here
        return {"score": 0.95, "classification": "pathogenic"}
```

## Tool Registry

Tools auto-register when imported. The `TOOL_REGISTRY` provides access:

```python
from code.biotools import TOOL_REGISTRY, BaseTool

# List all registered tools
for name, tool_class in TOOL_REGISTRY.items():
    tool = tool_class()
    print(f"{name}: {tool.description}")
```

## AlphaMissense (LIVE)

The only fully-live tool. Queries a DuckDB database of 71M AlphaMissense predictions.

### Data Setup

```bash
# Download AlphaMissense data (~2GB)
# From: gs://dm_alphamissense/AlphaMissense_aa_substitutions.tsv.gz

# The tool auto-indexes to DuckDB on first query
```

### Query Examples

```python
from code.biotools.alphamissense import AlphaMissenseTool

tool = AlphaMissenseTool()

# Query by protein variant
result = tool.query({
    'uniprot_id': 'P35499',
    'position': 781,
    'ref_aa': 'V',
    'alt_aa': 'I'
})
# Returns: {'am_pathogenicity': 0.87, 'am_class': 'likely_pathogenic'}
```

## Contributing New Tools

We actively welcome contributions! Follow the guide in [CONTRIBUTING.md](CONTRIBUTING.md).

### Quick Template

```python
from code.biotools.base_tool import BaseTool, register_tool

@register_tool
class MyNewTool(BaseTool):
    name = "my_new_tool"
    version = "1.0.0"
    description = "Describe what this tool does"

    def __init__(self, stub_mode: bool = True):
        super().__init__()
        self.stub_mode = stub_mode

    def query(self, variant: dict) -> dict:
        if self.stub_mode:
            return self._stub_response(variant)
        return self._live_query(variant)

    def _stub_response(self, variant: dict) -> dict:
        """Return realistic placeholder for development."""
        return {"status": "stub", "score": 0.5}

    def _live_query(self, variant: dict) -> dict:
        """Implement real API/database query."""
        # Your implementation here
        pass
```

### Requirements for New Tools

1. **Inherit from `BaseTool`**: Ensures consistent interface
2. **Implement `query()` method**: Takes variant dict, returns result dict
3. **Support stub mode**: For testing without real data/API
4. **Add to registry**: Use `@register_tool` decorator or manual registration
5. **Document**: Add entry to this README and CONTRIBUTING.md

## Planned Implementations

### ClinVar (High Priority)
- Use NCBI E-Utils API
- Query by rsID or HGVS notation
- Return clinical significance and review status

### OMIM (Medium Priority)
- Requires institutional API key
- Query disease-gene relationships
- Return phenotype descriptions and inheritance patterns

### SpliceAI (Medium Priority)
- Use Illumina's pre-computed scores or API
- Predict splice site alterations
- Return delta scores for acceptor/donor sites

### REVEL (Low Priority)
- Ensemble of 13 pathogenicity predictors
- Pre-computed lookup table from dbNSFP
- Return REVEL score (0-1)

---

*See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.*
