# Contributing to the Bio-Tools Library

Thank you for your interest in contributing to the UH2025-CDS Bio-Tools Library!

This library is designed to be **modular and community-driven**. We actively encourage contributions from the rare disease community, bioinformaticians, and clinical geneticists.

---

## Quick Start: Adding a New Tool

Adding a new bio-tool is straightforward. Follow these steps:

### 1. Create Your Tool File

Create a new file in `code/biotools/` named `your_tool.py`:

```python
"""
YourTool: Brief description of what this tool does.

Data Source: Where does the data come from?
Reference: Citation to relevant publication
"""

from typing import Any, Dict, Optional
from .base_tool import BaseTool, Variant

class YourTool(BaseTool):
    """
    One-sentence description of your tool.

    More detailed explanation of what the tool provides
    and when it should be used.
    """

    name = "your_tool"
    version = "1.0.0"
    description = "Brief description for registry"

    def _validate_variant(self, variant: Variant) -> Optional[str]:
        """
        Validate that a variant can be queried by this tool.

        Return None if valid, or error message if invalid.
        """
        # Example: Require genomic coordinates
        if not all([variant.chromosome, variant.position]):
            return "This tool requires genomic coordinates"
        return None

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        """
        Query your data source for a single variant.

        Returns a dictionary of annotations.
        Return empty dict {} if variant not found.
        """
        # Implement your query logic here
        # Can call APIs, query databases, etc.

        return {
            "score": 0.5,
            "prediction": "uncertain",
            # ... your annotations
        }
```

### 2. Register Your Tool

Add your tool to `__init__.py`:

```python
from .your_tool import YourTool

TOOL_REGISTRY = {
    # ... existing tools ...
    "your_tool": YourTool,
}

__all__ = [
    # ... existing exports ...
    "YourTool",
]
```

### 3. Add Tests

Create `tests/test_your_tool.py`:

```python
import pytest
from code.biotools import YourTool, Variant

def test_your_tool_basic():
    tool = YourTool()
    variant = Variant(chromosome="1", position=12345, reference="A", alternate="G")
    result = tool.query(variant)
    assert result.status.value in ["success", "not_found"]

def test_your_tool_validation():
    tool = YourTool()
    invalid_variant = Variant()  # Missing required fields
    result = tool.query(invalid_variant)
    assert result.status.value == "error"
```

### 4. Document Your Tool

Add documentation to your tool's docstring explaining:
- What data source it queries
- What annotations it provides
- When it should be used
- Any limitations or caveats

---

## The BaseTool Interface

All tools inherit from `BaseTool`, which provides:

### Automatic Features
- **Caching**: Results are cached to avoid duplicate queries
- **Rate Limiting**: Prevents exceeding API rate limits
- **Error Handling**: Consistent error wrapping
- **Logging**: Query timing and status tracking

### Required Methods

You must implement these two methods:

#### `_validate_variant(self, variant: Variant) -> Optional[str]`

Checks if a variant can be queried. Return:
- `None` if the variant is valid for this tool
- An error message string if the variant cannot be queried

#### `_query_single(self, variant: Variant) -> Dict[str, Any]`

Performs the actual query. Return:
- A dictionary of annotations if found
- An empty dictionary `{}` if the variant was not found
- Raise an exception for errors (will be caught and wrapped)

### Optional Methods

Override these for advanced functionality:

#### `query_batch(self, variants: List[Variant]) -> List[ToolResult]`

For tools that support efficient batch queries (e.g., API batching).

#### `_get_data_version(self) -> Optional[str]`

Return the version/date of the underlying data source.

---

## The Variant Class

The `Variant` class supports multiple input formats:

```python
from code.biotools import Variant

# By genomic coordinates
v1 = Variant(chromosome="chr1", position=12345, reference="A", alternate="G")

# By rsID
v2 = Variant(rsid="rs123456")

# By HGVS notation
v3 = Variant(hgvs_c="c.123A>G", gene="BRCA1", transcript="NM_007294.4")

# By protein change
v4 = Variant(hgvs_p="p.Arg123Gly", gene="SCN4A")

# Full variant with all information
v5 = Variant(
    chromosome="chr17",
    position=43092919,
    reference="T",
    alternate="C",
    gene="BRCA1",
    hgvs_c="c.5123T>C",
    hgvs_p="p.Leu1708Pro",
    zygosity="heterozygous",
)
```

---

## Best Practices

### 1. Data Sources

- Prefer pre-computed databases over real-time API calls when possible
- Document data versions clearly
- Provide instructions for downloading/updating data

### 2. Performance

- Implement batch queries if the data source supports them
- Use appropriate timeouts
- Cache aggressively (results don't change often)

### 3. Error Handling

- Validate inputs early with clear error messages
- Handle network errors gracefully
- Return `NOT_FOUND` status (not error) when variant simply isn't in database

### 4. Documentation

- Include reference to the original publication
- Explain what the scores/predictions mean
- Note any limitations (e.g., only works for missense variants)

### 5. Testing

- Test with real variant examples
- Test edge cases (missing fields, invalid input)
- Test timeout handling if using APIs

---

## Tool Ideas We'd Love to See

Here are some tools that would be valuable additions:

### High Priority
- [ ] **gnomAD**: Population allele frequencies
- [ ] **CADD**: Combined annotation-dependent depletion scores
- [ ] **PrimateAI**: Deep learning pathogenicity prediction
- [ ] **EVE**: Evolutionary model of variant effect

### Medium Priority
- [ ] **MutationTaster**: Prediction of disease-causing variants
- [ ] **GERP**: Conservation scores
- [ ] **HPO**: Human Phenotype Ontology annotations
- [ ] **GTEx**: Expression quantitative trait loci

### Specialized
- [ ] **miRDB**: microRNA target predictions
- [ ] **dbSNP**: Variant identifiers and frequency
- [ ] **PharmGKB**: Pharmacogenomic annotations
- [ ] **COSMIC**: Cancer somatic mutation database

---

## Contribution Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-new-tool`
3. **Implement** your tool following this guide
4. **Test** thoroughly
5. **Document** your tool
6. **Submit** a pull request

### Pull Request Checklist

- [ ] Tool follows `BaseTool` interface
- [ ] Validation handles edge cases
- [ ] Tests pass
- [ ] Documentation is complete
- [ ] Added to `TOOL_REGISTRY` in `__init__.py`

---

## Questions?

- Open an issue on GitHub
- Join our monthly consortium calls
- Email: biotools@rare-cds.org (placeholder)

---

## Recognition

Contributors who add new tools will be:
- Listed in the CONTRIBUTORS file
- Acknowledged in publications using the tool
- Invited to co-author methodology papers (for significant contributions)

Thank you for helping improve rare disease diagnosis worldwide!

---

*This contribution guide follows the UH2025-CDS community guidelines.*
*Version 1.0.0 - November 2025*
