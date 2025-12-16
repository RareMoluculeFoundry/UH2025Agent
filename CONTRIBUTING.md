# Contributing to UH2025-CDS-Agent

Thank you for your interest in contributing! This guide will help you get started.

## Quick Links

- [Issue Tracker](https://github.com/your-org/delab/issues)
- [Stub Improvement Roadmap](/.agentic/plans/active/STUB_IMPROVEMENT_ROADMAP.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Agent Operational Manual](AGENTS.md)

## Getting Started

### Prerequisites

1. macOS with Apple Silicon (M1/M2/M3/M4) or Linux with CUDA
2. Python 3.10+
3. 32GB+ RAM recommended
4. Conda environment: `lab-env`

### Setup

```bash
cd lab/obs/topologies/UH2025Agent/
conda activate lab-env
pip install -r requirements.txt
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=code/
```

## Ways to Contribute

### 1. Implement Stub Bio-Tools (High Priority)

Several bio-tools are stub implementations. See the [Stub Improvement Roadmap](/.agentic/plans/active/STUB_IMPROVEMENT_ROADMAP.md) for details.

**Priority Tools**:

- ClinVar - Implement NCBI E-Utils API
- SpliceAI - Add local model or API integration
- REVEL - Implement dbNSFP lookup
- gnomAD - Add privacy-aware querying
- OMIM - Implement API with key management

**Bio-Tool Interface**:

```python
from code.biotools.base_tool import BaseTool, ToolResult, Variant

class MyTool(BaseTool):
    name = "my_tool"
    version = "1.0.0"
    description = "Brief description"

    def _validate_variant(self, variant: Variant) -> Optional[str]:
        """Return error message if variant is invalid, None if valid."""
        if not variant.chromosome:
            return "Requires chromosome"
        return None

    def _query_single(self, variant: Variant) -> Dict[str, Any]:
        """Query data source for a single variant."""
        # Your implementation here
        return {"score": 0.5, "source": "MyTool v1.0"}
```

### 2. Improve Prompts

Prompt templates are in `code/agents/prompts/`. Contributions welcome:

- Fix edge cases in parsing
- Add few-shot examples
- Improve diagnostic reasoning

**Prompt Files**:

- `ingestion_v1.yaml` - Clinical data parsing
- `structuring_v1.yaml` - Hypothesis generation
- `synthesis_v1.yaml` - Report generation

### 3. Add Test Cases

We need more test coverage:

- Unit tests for bio-tools
- Integration tests for the pipeline
- Synthetic patient cases for validation

### 4. Documentation

- Fix typos and clarify explanations
- Add examples and tutorials
- Improve architecture documentation

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints
- Write docstrings (numpy style)
- Keep functions focused (single responsibility)

### Jupytext Sync

All notebooks must be Jupytext-synced:

```bash
# After editing a notebook
jupytext --sync notebooks/your_notebook.ipynb
```

### DeLab Standard Compliance

This project follows the DeLab v2.0 standard:

- Code in `code/` directory
- Notebooks in `notebooks/` with `.py` pairs
- Configuration in `params.yaml`
- Documentation: README.md, AGENTS.md, ARCHITECTURE.md

## Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make changes** following code standards
4. **Test** your changes: `pytest tests/`
5. **Sync notebooks**: `jupytext --sync notebooks/*.ipynb`
6. **Commit** with clear messages
7. **Push** and create a Pull Request

### PR Checklist

- [ ] Tests pass
- [ ] Jupytext sync is clean
- [ ] Documentation updated
- [ ] No secrets or PHI in code
- [ ] STUB markers removed if implementing real functionality

## Privacy and Security

### Absolute Rules

1. **No PHI/PII** in code, tests, or documentation
2. **No secrets** (API keys, tokens) committed
3. **Privacy mode** must be respected by all tools
4. **Research use only** - no clinical claims

### PatientX Data

The PatientX test case is an open-source consented case. Use it for testing, but do not add additional real patient data.

## Questions?

- Check existing issues and documentation
- Open a new issue with the "question" label
- Tag maintainers for guidance

---

*Thank you for helping improve rare disease diagnostics!*
