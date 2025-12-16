# AGENTS.md: RareLLM Operational Manual

## Purpose

This file provides operational instructions for AI agents (particularly Claude Code) working with the RareLLM module. It follows the DeLab FAIR CDS Standard and enables effective agent-assisted development and execution.

---

## Module Overview

**RareLLM** is a privacy-first AI research agent for rare genetic disease diagnosis. It uses large language models (Qwen 2.5 32B) with optional LoRA adapters to assist clinicians in analyzing complex genetic cases.

### Key Constraints

| Constraint | Requirement |
|------------|-------------|
| **HIPAA Compliance** | All inference MUST be local-only |
| **No Cloud APIs** | FORBIDDEN: OpenAI, Anthropic, Google LLM APIs |
| **Local Backend** | REQUIRED: llama-cpp-python with Metal/CUDA |
| **Privacy Mode** | PatientX only in development |
| **Memory Budget** | ~20GB for Qwen 32B Q4_K_M |

---

## Agent Capabilities

### What Agents CAN Do

- Run the 4-stage diagnostic pipeline via Papermill
- Modify prompt templates and inference parameters
- Add new bio-tool integrations
- Update LoRA adapter configurations
- Run tests and validation

### What Agents MUST NOT Do

- Send patient data to external APIs
- Load cloud-based LLM backends
- Access patient data other than PatientX in development
- Disable privacy mode without explicit authorization
- Modify PHI-related logging

---

## Execution Instructions

### 1. Interactive Mode (Jupyter)

```bash
cd /Users/stanley/Projects/DeLab/lab/obs/modules/RareLLM
jupyter lab notebooks/main.ipynb
```

### 2. Batch Mode (Papermill)

```bash
cd /Users/stanley/Projects/DeLab/lab/obs/modules/RareLLM
papermill notebooks/main.ipynb output.ipynb \
  -p patient_id PatientX \
  -p privacy_mode true
```

### 3. Docker Mode

```bash
cd /Users/stanley/Projects/DeLab/lab/obs/modules/RareLLM
docker build -t rarellm:latest -f docker/Dockerfile .
docker run -v $(pwd)/models:/app/models rarellm:latest
```

---

## Pipeline Stages

### Stage 1: Differential Diagnosis

**Purpose**: Generate ranked differential diagnosis
**Input**: Clinical summary + genomic data
**Output**: JSON with candidate diagnoses and confidence scores
**Model**: Qwen 2.5 32B with diagnostic_analysis LoRA (optional)

### Stage 2: Tool Call Generation

**Purpose**: Generate specifications for variant analysis tools
**Input**: Differential diagnosis + variants of interest
**Output**: JSON with tool calls (AlphaMissense, AlphaGenome, etc.)
**Model**: Qwen 2.5 32B with variant_analysis LoRA (optional)

### Stage 3: Tool Execution

**Purpose**: Execute bio-informatics tools
**Tools**: AlphaMissense, AlphaGenome, ClinVar, SpliceAI, OMIM
**Output**: JSON with tool results and annotations
**No LLM**: Pure Python orchestration

### Stage 4: Report Generation

**Purpose**: Synthesize findings into clinical report
**Input**: All previous stage outputs
**Output**: Markdown-formatted clinical report
**Model**: Qwen 2.5 32B with report_generation LoRA (optional)

---

## Model Configuration

### Base Model

| Property | Value |
|----------|-------|
| Name | Qwen 2.5 32B Instruct |
| Quantization | Q4_K_M |
| Size | ~19GB |
| Context | 32,768 tokens |
| RAM Required | 32-48GB |

### Model Path

```
models/base/Qwen2.5-32B-Instruct-Q4_K_M.gguf
```

### LoRA Adapters (Optional)

```
models/lora/diagnostic_analysis.gguf
models/lora/variant_analysis.gguf
models/lora/report_generation.gguf
```

**Note**: LoRA adapters are placeholders. Base model works without them.

---

## Configuration Files

### `config/lora_config.yaml`

```yaml
adapters:
  diagnostic_analysis:
    path: models/lora/diagnostic_analysis.gguf
    enabled: false
  variant_analysis:
    path: models/lora/variant_analysis.gguf
    enabled: false
  report_generation:
    path: models/lora/report_generation.gguf
    enabled: false
```

### Inference Parameters

| Parameter | Stage 1 | Stage 2 | Stage 4 |
|-----------|---------|---------|---------|
| Temperature | 0.3 | 0.1 | 0.4 |
| Max Tokens | 4096 | 2048 | 8192 |
| Top P | 0.9 | 0.9 | 0.95 |

---

## Tool Integration

### Available Tools

| Tool | Purpose | API Type |
|------|---------|----------|
| AlphaMissense | Missense pathogenicity | Local DB / GCS |
| AlphaGenome | Regulatory effects | API (requires key) |
| ClinVar | Clinical significance | NCBI E-utilities |
| SpliceAI | Splice impact | Local model |
| OMIM | Disease-gene relations | API (requires key) |

### API Keys

Set environment variables:
```bash
export ALPHAGENOME_API_KEY="your_key"
export OMIM_API_KEY="your_key"
```

---

## Privacy Validation

### PatientX Rule

In development mode, only PatientX is accessible. The privacy validator enforces this:

```python
from code.privacy.validator import PrivacyValidator

validator = PrivacyValidator(privacy_mode=True)
if validator.validate_patient_data_access("PatientX"):
    # Proceed
else:
    raise PermissionError("Access denied")
```

### Audit Logging

All data access is logged to `logs/data_access.log`:
- Timestamp
- Patient ID
- Action (read/write)
- Status (allowed/denied)

---

## Testing

### Run All Tests

```bash
cd /Users/stanley/Projects/DeLab/lab/obs/modules/RareLLM
pytest tests/ -v
```

### Test Specific Stage

```bash
pytest tests/test_inference.py::test_differential_diagnosis -v
```

### Test Privacy

```bash
pytest tests/test_privacy.py -v
```

---

## Troubleshooting

### Model Not Loading

1. Verify model exists: `ls models/base/*.gguf`
2. Check RAM: Need 32-48GB free
3. Verify llama-cpp-python: `pip show llama-cpp-python`

### LoRA Not Found

LoRA adapters are optional. Disable in config:
```yaml
adapters:
  diagnostic_analysis:
    enabled: false
```

### Privacy Validation Fails

1. Ensure patient_id is "PatientX"
2. Check privacy_mode is True
3. Review logs in `logs/data_access.log`

### Tool API Fails

1. Check API key environment variables
2. Verify network connectivity
3. Check rate limits (see tool configs)

---

## Integration with UH2025Agent

This module is used by the UH2025Agent topology. The topology provides:
- LangGraph-based orchestration
- 4-agent pipeline (Ingestion, Structuring, Executor, Synthesis)
- HITL checkpoint mechanism

See: `lab/obs/topologies/UH2025Agent/`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-02 | Initial release |
| 1.1.0 | 2025-11-29 | LangChain integration, AGENTS.md added |

---

**Maintained by**: Stanley Lab / RareResearch
**Part of**: DeLab FAIR CDS Standard Implementation
