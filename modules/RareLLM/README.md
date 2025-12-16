# RareLLM: Rare Disease Diagnostic LLM Module

## Overview

**RareLLM** is a privacy-first AI research agent for rare genetic disease diagnosis, designed for the Mayo Clinic Undiagnosed Hackathon 2025. It uses large language models (Qwen3-32B) with specialized LoRA adapters to assist clinicians in analyzing complex genetic cases.

**🔬 Purpose**: Democratize diagnostic tools for rare genetic diseases through AI-assisted analysis

**🔒 Privacy**: HIPAA-compliant, local-only inference, no patient data leaves L1 systems

**🧬 Approach**: 4-stage pipeline combining LLM reasoning with computational tools

---

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Download Qwen3-32B-GGUF model (~20GB)
# Download from: https://huggingface.co/unsloth/Qwen3-32B-GGUF
# Place in: models/base/qwen3-32b.gguf
```

### Basic Usage

```python
# Run the complete diagnostic pipeline
import papermill as pm

pm.execute_notebook(
    'notebooks/main.ipynb',
    'output.ipynb',
    parameters={
        'patient_id': 'PatientX',
        'clinical_summary_path': '../topologies/UH2025Agent/Data/PatientX/patientX_Clinical.md',
        'genomic_data_path': '../topologies/UH2025Agent/Data/PatientX/patientX_Genomic.json',
        'privacy_mode': True
    }
)
```

### Interactive Mode

```bash
# Open in JupyterLab
jupyter lab notebooks/main.ipynb
```

---

## 4-Stage Diagnostic Pipeline

### Stage 1: Differential Diagnosis Generation
**Purpose**: Generate ranked differential diagnosis from clinical summary and genomic findings

**Input**:
- Clinical summary (patient history, symptoms, labs)
- Genomic data (variants, inheritance patterns)

**Output**:
```json
{
  "candidates": [
    {
      "disease": "Paramyotonia Congenita (SCN4A-related)",
      "confidence": 0.85,
      "rationale": "SCN4A c.780A>G variant strongly associated...",
      "genes_implicated": ["SCN4A"],
      "evidence_strength": "strong"
    }
  ]
}
```

**LoRA Adapter**: `diagnostic_analysis.gguf` (placeholder)

---

### Stage 2: Tool Call Generation
**Purpose**: Generate specifications for variant pathogenicity analysis tools

**Input**:
- Differential diagnosis from Stage 1
- Variants of interest

**Output**:
```json
{
  "tool_calls": [
    {
      "tool": "alphamissense",
      "target": "SCN4A:c.780A>G",
      "parameters": {
        "gene": "SCN4A",
        "variant_cDNA": "c.780A>G",
        "variant_protein": "p.Ile260Val"
      }
    },
    {
      "tool": "alphafold",
      "target": "SCN4A protein structure",
      "parameters": {
        "protein": "SCN4A",
        "variant_position": 260
      }
    }
  ]
}
```

**LoRA Adapter**: `variant_analysis.gguf` (placeholder)

---

### Stage 3: Tool Execution
**Purpose**: Execute AlphaMissense and AlphaFold analyses

**Tools**:
- **AlphaMissense**: Variant pathogenicity prediction
- **AlphaFold**: Protein structure prediction

**Output**:
```json
{
  "alphamissense_results": [
    {
      "variant": "SCN4A:c.780A>G",
      "score": 0.82,
      "classification": "likely_pathogenic"
    }
  ],
  "alphafold_results": [
    {
      "protein": "SCN4A",
      "structure_file": "outputs/SCN4A_wild_type.pdb",
      "variant_structure": "outputs/SCN4A_p.Ile260Val.pdb"
    }
  ]
}
```

**Note**: Real API integration with caching for development

---

### Stage 4: Clinical Report Generation
**Purpose**: Synthesize all findings into comprehensive clinical report

**Input**:
- Clinical summary (original)
- Differential diagnosis (Stage 1)
- Tool analysis results (Stage 3)

**Output**: Markdown-formatted clinical report with:
- Patient demographics (de-identified)
- Clinical presentation summary
- Genomic findings analysis
- Differential diagnosis with evidence
- Tool analysis interpretation
- Recommendations for confirmatory testing
- References

**LoRA Adapter**: `report_generation.gguf` (placeholder)

---

## Module Structure

```
RareLLM/
├── README.md                      # This file
├── AGENTS.md                      # Operational manual
├── CLAUDE.md                      # Agent development context
├── notebooks/
│   ├── main.ipynb                 # Primary diagnostic pipeline
│   ├── main.py                    # Jupytext-synced version
│   └── jupytext.toml              # Jupytext configuration
├── code/
│   ├── inference/
│   │   ├── differential.py        # Stage 1: Differential diagnosis
│   │   ├── tool_calls.py          # Stage 2: Tool call generation
│   │   └── report.py              # Stage 4: Report generation
│   ├── tools/
│   │   ├── alphamissense.py       # AlphaMissense API wrapper
│   │   └── alphafold.py           # AlphaFold API wrapper
│   ├── privacy/
│   │   ├── validator.py           # HIPAA compliance validation
│   │   └── sanitizer.py           # Data sanitization
│   └── utils/
│       ├── prompt_templates.py    # LLM prompt templates
│       └── parser.py              # Output parsing utilities
├── backends/
│   ├── manager.py                 # Multi-backend manager
│   └── llm_manager.py             # LLM-specific manager
├── models/
│   ├── base/                      # Base model (Qwen3-32B-GGUF)
│   ├── lora/                      # LoRA adapters (placeholders)
│   └── MODEL_REGISTRY.yaml        # Model version tracking
├── config/
│   ├── lora_config.yaml           # LoRA adapter configuration
│   ├── prompts.yaml               # Prompt templates
│   └── tools_config.yaml          # Tool integration configuration
├── docker/
│   ├── Dockerfile                 # Container with llama.cpp
│   └── DOCKER_CONTEXT.md          # Docker deployment docs
├── tests/
│   ├── test_inference.py          # Inference pipeline tests
│   ├── test_privacy.py            # Privacy validation tests
│   ├── test_tools.py              # Tool integration tests
│   └── fixtures/
│       └── test_patient.json      # Synthetic test data
├── requirements.txt               # Python dependencies
└── pyproject.toml                 # Project metadata
```

---

## Privacy & Compliance

### HIPAA Compliance

This module is designed for HIPAA-compliant operation:

✅ **Local-only inference**: No patient data sent to external APIs
✅ **Privacy mode**: Enforced at module level
✅ **PHI sanitization**: Automatic removal of identifiers
✅ **Audit logging**: All data access logged
✅ **Access controls**: PatientX-only for development/testing

### Privacy Validator

The module includes `PrivacyValidator` that:
1. Validates patient data access (PatientX only in test mode)
2. Prevents remote execution in privacy mode
3. Prevents PHI logging
4. Sanitizes outputs for research use
5. Generates audit trails

### Usage

```python
from code.privacy.validator import PrivacyValidator

validator = PrivacyValidator(privacy_mode=True)

# Validate before accessing patient data
if validator.validate_patient_data_access(patient_path):
    # Access allowed
    load_patient_data(patient_path)
else:
    raise PermissionError("Access denied")
```

---

## Model Configuration

### Base Model: Qwen3-32B-Instruct

- **Parameters**: 32 billion
- **Context**: 32,768 tokens
- **Quantization**: Q4_K_M (4-bit)
- **Size**: ~20GB
- **RAM Required**: 32-48GB
- **Source**: https://huggingface.co/unsloth/Qwen3-32B-GGUF

**Why Qwen3-32B?**
- Excellent medical reasoning capabilities
- Large context window (full clinical summaries)
- Strong multilingual support
- Efficient 4-bit quantization
- Open source and commercially usable

### LoRA Adapters (Placeholders)

**Current Status**: Infrastructure in place, adapters are placeholders

**Future Training**:
1. **diagnostic_analysis**: Train on medical literature, rare disease cases
2. **variant_analysis**: Train on variant annotation examples, tool call patterns
3. **report_generation**: Train on clinical report corpus

---

## Tool Integration

### AlphaMissense

**Purpose**: Predict variant pathogenicity using AlphaFold-based model

**API**: Real API integration with authentication
**Caching**: Aggressive caching for development
**Rate Limiting**: 10 requests/minute

```python
from code.tools.alphamissense import AlphaMissenseClient

client = AlphaMissenseClient(api_key=API_KEY)
result = client.predict_pathogenicity(
    variant="SCN4A:c.780A>G",
    transcript="NM_000334.5"
)
```

### AlphaFold

**Purpose**: Predict 3D protein structures and variant effects

**API**: Real API integration
**Local Cache**: PDB files cached locally
**Fallback**: Use precomputed structures from AlphaFold DB

```python
from code.tools.alphafold import AlphaFoldClient

client = AlphaFoldClient(api_key=API_KEY, use_local_cache=True)
result = client.predict_structure(
    protein_id="SCN4A",
    uniprot_id="P35499"
)
```

---

## Execution Modes

### 1. Interactive Mode (Jupyter)

Best for: Development, exploratory analysis

```bash
jupyter lab notebooks/main.ipynb
```

### 2. Batch Mode (Papermill)

Best for: Automated execution, reproducible runs

```bash
papermill notebooks/main.ipynb output.ipynb \
  -p patient_id PatientX \
  -p privacy_mode true
```

### 3. Topology Integration

Best for: Multi-step workflows, pipeline orchestration

Used by UH2025Agent topology (see `../topologies/UH2025Agent/`)

### 4. Docker Container

Best for: Deployment, reproducible environments

```bash
docker build -t rarellm:latest -f docker/Dockerfile .
docker run -v $(pwd)/models:/app/models rarellm:latest
```

---

## Performance

### Latency (Apple Silicon M2 Max, 64GB RAM)

| Stage | Expected | Actual (PatientX) |
|-------|----------|-------------------|
| Stage 1: Differential | 30-60s | TBD |
| Stage 2: Tool Calls | 15-30s | TBD |
| Stage 3: Tool Execution | 2-5min | TBD |
| Stage 4: Report | 45-90s | TBD |
| **Total Pipeline** | **<10min** | **TBD** |

### Resource Usage

- **RAM**: 32-48GB (Qwen3-32B with Metal acceleration)
- **VRAM**: N/A (Metal unified memory)
- **Storage**: 25GB (model + cache)

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_inference.py -v

# Run with coverage
pytest tests/ --cov=code --cov-report=html
```

**Coverage Target**: >80%

---

## Development

### Adding New LoRA Adapters

1. Train adapter using your preferred framework (PEFT, Unsloth, etc.)
2. Export to GGUF format
3. Place in `models/lora/`
4. Update `config/lora_config.yaml`
5. Test with `test_llm_backend.py`

### Adding New Tools

1. Create wrapper in `code/tools/`
2. Implement client interface
3. Add configuration to `config/tools_config.yaml`
4. Update Stage 2 inference to generate tool calls
5. Update Stage 3 to execute tool
6. Add tests to `tests/test_tools.py`

---

## Troubleshooting

### Issue: Model fails to load

**Symptoms**:
```
RuntimeError: Model loading failed
```

**Solutions**:
1. Verify model file exists: `ls models/base/qwen3-32b.gguf`
2. Check file size: Should be ~20GB
3. Verify sufficient RAM: Need 32-48GB
4. Check llama-cpp-python installation:
   ```bash
   pip install llama-cpp-python --force-reinstall --no-cache-dir
   ```

### Issue: LoRA adapters not found

**Symptoms**:
```
FileNotFoundError: LoRA adapter not found
```

**Solutions**:
1. LoRA adapters are placeholders - create stub files:
   ```bash
   mkdir -p models/lora
   touch models/lora/diagnostic_analysis.gguf
   touch models/lora/variant_analysis.gguf
   touch models/lora/report_generation.gguf
   ```
2. Update paths in `config/lora_config.yaml`

### Issue: Tool API authentication fails

**Symptoms**:
```
requests.exceptions.HTTPError: 401 Unauthorized
```

**Solutions**:
1. Set API keys as environment variables:
   ```bash
   export ALPHAMISSENSE_API_KEY="your_key"
   export ALPHAFOLD_API_KEY="your_key"
   ```
2. Or provide in code:
   ```python
   client = AlphaMissenseClient(api_key="your_key")
   ```

### Issue: Privacy validation fails

**Symptoms**:
```
PermissionError: Access to Patient1 not permitted
```

**Solutions**:
1. Only PatientX is allowed in development
2. Verify patient_id parameter: Should be "PatientX"
3. Check `Data/PatientX/` directory exists
4. Review privacy logs: `logs/data_access.log`

---

## Citations

If you use RareLLM in your research, please cite:

```bibtex
@software{rarellm2025,
  title={RareLLM: AI-Assisted Rare Disease Diagnosis},
  author={Mayo Clinic Undiagnosed Hackathon 2025 Team},
  year={2025},
  url={https://github.com/your-org/rarellm}
}
```

---

## License

[Specify license - e.g., MIT, Apache 2.0, or proprietary for medical use]

---

## Support

**For technical issues**: See AGENTS.md for operational manual
**For development context**: See CLAUDE.md for agent-specific documentation
**For Mayo Clinic Hackathon**: Contact [hackathon coordinators]

---

**Version**: 1.0.0
**Last Updated**: 2025-11-02
**Status**: Active Development (Mayo Clinic Undiagnosed Hackathon 2025)
