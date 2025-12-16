# UH2025Agent Model Downloads

Required GGUF models for local LLM inference (HIPAA-compliant, no cloud APIs).

## Quick Download

```bash
# From UH2025Agent directory:
cd models

# Llama 3.2 3B (Ingestion Agent) - ~1.9GB
huggingface-cli download lmstudio-community/Llama-3.2-3B-Instruct-GGUF \
    Llama-3.2-3B-Instruct-Q4_K_M.gguf --local-dir .

# Qwen 2.5 14B (Structuring Agent) - ~8.4GB
huggingface-cli download bartowski/Qwen2.5-14B-Instruct-GGUF \
    Qwen2.5-14B-Instruct-Q4_K_M.gguf --local-dir .

# Qwen 2.5 32B (Synthesis Agent) - ~18.5GB
huggingface-cli download bartowski/Qwen2.5-32B-Instruct-GGUF \
    Qwen2.5-32B-Instruct-Q4_K_M.gguf --local-dir .
```

## Model Requirements

| Agent | Model | File | Size | Purpose |
|-------|-------|------|------|---------|
| Ingestion | Llama 3.2 3B Q4_K_M | `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | ~1.9GB | Clinical phenotype extraction |
| Structuring | Qwen 2.5 14B Q4_K_M | `Qwen2.5-14B-Instruct-Q4_K_M.gguf` | ~8.4GB | Diagnostic hypothesis generation |
| Synthesis | Qwen 2.5 32B Q4_K_M | `Qwen2.5-32B-Instruct-Q4_K_M.gguf` | ~18.5GB | Clinical report synthesis |

**Total disk space required**: ~28GB

## Hardware Requirements

- **Minimum**: 32GB RAM (models load sequentially)
- **Recommended**: 64GB+ unified memory (Apple Silicon) or equivalent VRAM
- **Supported Platforms**:
  - macOS with Apple Silicon (M1/M2/M3/M4) - uses Metal acceleration
  - Linux with NVIDIA GPU - uses CUDA
  - Linux with AMD GPU - uses ROCm
  - CPU-only fallback available (slower)

## Why Local Models?

UH2025Agent uses local GGUF models for **HIPAA compliance**:

- Patient data never leaves your machine
- No API keys or cloud dependencies
- Works offline in air-gapped clinical environments
- Full audit trail of inference

## Verification

After downloading, verify the models load correctly:

```python
from llama_cpp import Llama

# Quick test with smallest model
llm = Llama(
    model_path="models/Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    n_gpu_layers=-1  # Use all GPU layers
)
print("Model loaded successfully!")
```

## Alternative Sources

If the primary sources are unavailable:

| Model | Alternative Source |
|-------|-------------------|
| Llama 3.2 3B | `TheBloke/Llama-3.2-3B-Instruct-GGUF` |
| Qwen 2.5 14B | `Qwen/Qwen2.5-14B-Instruct-GGUF` |
| Qwen 2.5 32B | `Qwen/Qwen2.5-32B-Instruct-GGUF` |

## Troubleshooting

**"Out of memory" error**:
- Reduce `n_gpu_layers` to load part of model on GPU
- Models are loaded sequentially, so only one is in memory at a time

**Slow inference**:
- Ensure GPU acceleration is enabled (`n_gpu_layers=-1`)
- Check Metal/CUDA is available: `llama_cpp.llama_supports_gpu_offload()`

**Model not found**:
- Verify file names match exactly (case-sensitive)
- Check `params.yaml` model paths are correct

---

*These models are excluded from git via `.gitignore` to keep the repository lightweight.*
