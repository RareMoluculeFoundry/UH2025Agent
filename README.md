# UH2025-CDS-Agent: Edge-Native Diagnostic Agents for Rare Diseases

<p align="center">
  <img width="280" height="280" alt="image" src="https://github.com/user-attachments/assets/80ea12d7-8de0-40c1-aa6d-0d15e993694f" />
</p>

---

> **RESEARCH USE ONLY**: This software is intended for research purposes only and is NOT approved for clinical use. It should not be used for making medical decisions or diagnosing patients in a clinical setting. See [SECURITY.md](/SECURITY.md) for details.

---

## Mission

> *"We are not just building software; we are encoding a culture of collaboration."*

The UH2025-CDS-Agent is a **Clinical Decision Support system** for rare and undiagnosed diseases that brings the "hackathon effect" to any clinic, anywhere, anytime. Built on the principles established at the Mayo Clinic Undiagnosed Patient Hackathon, this system demonstrates how AI agents can function as **supportive colleagues**—organizing data, running bio-tools, and structuring evidence—so that human experts can focus on high-level diagnostic reasoning.

**Core Philosophy**: AI is supportive, not replacive. Every critical juncture requires physician review.

---

## Architecture Overview

### The 4-Agent + HITL Pipeline

This system implements a modular agentic workflow that mirrors the operational process of a hackathon diagnostic team:

![85B47C58-E1AB-439B-89D1-061F85D95577_1_105_c](https://github.com/user-attachments/assets/8a3a0509-d7b8-494c-9d41-e2753fa52ae6)


```
┌─────────────────────────────────────────────────────────────────┐
│              LOCAL EDGE COMPUTE (M4 Envelope)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐                                               │
│  │   Clinical   │                                               │
│  │  Summary &   │                                               │
│  │     VCF      │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  INGESTION   │  ← Llama 3.2 3B (fast parsing)                │
│  │    AGENT     │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐     ┌─────────────────────────────────────┐   │
│  │ STRUCTURING  │────▶│  Diagnostic Table                   │   │
│  │    AGENT     │────▶│  Variants Table                     │   │
│  │              │────▶│  Tool-Usage Plan                    │   │
│  └──────┬───────┘     └─────────────────────────────────────┘   │
│         │              ↑ Qwen 2.5 14B (reasoning)               │
│         ▼                                                       │
│  ┌──────────────┐     ┌─────────────────────────────────────┐   │
│  │  EXECUTOR    │────▶│  Open Source Bio-Tools Library      │   │
│  │    AGENT     │     │  (ClinVar, SpliceAI, AlphaMissense, │   │
│  │              │     │   REVEL, OMIM)                      │   │
│  └──────┬───────┘     └─────────────────────────────────────┘   │
│         │              ↑ Python (sandboxed, deterministic)      │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │  SYNTHESIS   │  ← Qwen 2.5 32B (comprehensive reports)       │
│  │    AGENT     │                                               │
│  └──────┬───────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────┐                                               │
│  │ Final Tool   │                                               │
│  │ Usage Report │                                               │
│  └──────────────┘                                               │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│              HUMAN-IN-THE-LOOP (RLHF)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         ┌──────────────┐                                        │
│         │  Physician   │                                        │
│         │   Review     │                                        │
│         └──────┬───────┘                                        │
│                │                                                │
│         ┌──────▼───────┐      ┌─────────────────┐               │
│         │    RLHF      │─────▶│  Global Model   │               │
│         │  Feedback    │      │    Weights      │               │
│         └──────────────┘      └─────────────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

| Agent | Model | Purpose | Outputs |
|-------|-------|---------|---------|
| **Ingestion** | Llama 3.2 3B | Parse clinical summary and VCF | Normalized patient context |
| **Structuring** | Qwen 2.5 14B | Generate diagnostic artifacts | Diagnostic Table, Variants Table, Tool-Usage Plan |
| **Executor** | Python (no LLM) | Run bio-tools in sandbox | Raw tool outputs (JSON) |
| **Synthesis** | Qwen 2.5 32B | Generate clinician report | Final Tool Usage Report |

---

## Key Features

### Privacy-First / Edge-Native Design

- **100% Local Execution**: All inference runs on local hardware (M4 MacBook Pro)
- **PHI Never Leaves Device**: Patient data stays in the secure hospital environment
- **No Cloud Dependency**: Works offline for highest-security environments
- **HIPAA Compliant**: Audit logging, encryption, access controls

### Expert-in-the-Loop at Every Step

Unlike black-box AI systems, UH2025-CDS provides validation checkpoints at **every pipeline stage**:

1. **After Ingestion**: Verify clinical data was parsed correctly
2. **After Structuring**: Review diagnostic hypotheses and tool selection
3. **After Execution**: Validate bio-tool outputs
4. **After Synthesis**: Edit and approve final report

### Modular & Contribution-Ready

Every component is designed for community extension:

- **Models**: Swap LLMs without changing agent logic
- **Prompts**: Version-controlled prompt templates
- **Bio-Tools**: Add new tools via simple Python interface
- **Context**: Inject domain knowledge and few-shot examples

### Federated Training via Diagnostic Arena

The system supports a "citizen science" model where clinicians and geneticists worldwide can contribute to improving the AI:

- **Synthetic Patients**: Test agents on generated cases
- **RLHF Collection**: Capture expert feedback at each step
- **Global Weights**: Aggregate improvements across consortium
- **Local Deployment**: Pull updated models to edge devices

---

## The "M4 Envelope" Standard

We standardize deployment on high-end consumer hardware to ensure global accessibility:

```yaml
compute:
  hardware: "M4 MacBook Pro Max"
  memory: "64-128GB unified"
  inference: "100% local via llama.cpp"

models:
  ingestion_agent:
    model: "llama-3.2-3b-instruct"
    quantization: "Q4_K_M"
    memory: "~2GB"

  structuring_agent:
    model: "qwen2.5-14b-instruct"
    quantization: "Q4_K_M"
    memory: "~10GB"

  synthesis_agent:
    model: "qwen2.5-32b-instruct"
    quantization: "Q4_K_M"
    memory: "~20GB"
```

**Why this matters**: A hospital in a resource-constrained setting can deploy the exact same diagnostic tools as a top-tier academic center.

---

## Bio-Tools Library

The Executor Agent orchestrates a library of open-source bioinformatics tools:

| Tool | Purpose | Data Source | Status |
|------|---------|-------------|--------|
| **AlphaMissense** | Missense pathogenicity | DeepMind 71M variants | **LIVE** |
| **ClinVar** | Variant clinical significance | NCBI ClinVar API | STUB |
| **SpliceAI** | Splice site impact prediction | Illumina pre-computed | STUB |
| **REVEL** | Ensemble pathogenicity scores | dbNSFP integration | STUB |
| **OMIM** | Disease-gene relationships | OMIM API | STUB |
| **gnomAD** | Population allele frequencies | gnomAD GraphQL API | STUB |

> **Note**: STUB tools return mock data for testing. See `.agentic/plans/active/STUB_IMPROVEMENT_ROADMAP.md` for implementation roadmap.

### Contributing New Tools

We actively welcome contributions! See `code/biotools/CONTRIBUTING.md` for the simple interface:

```python
from code.biotools import BaseTool

class MyNewTool(BaseTool):
    name = "my_tool"
    version = "1.0.0"

    def query(self, variant: Variant) -> ToolResult:
        # Your implementation
        pass
```

---

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4) or Linux with CUDA
- Python 3.10+
- 32GB+ RAM recommended
- llama.cpp installed

### Installation

```bash
# Clone and navigate
cd /path/to/DeLab/lab/obs/topologies/UH2025Agent/

# Activate environment
conda activate lab-env

# Install dependencies
pip install -r requirements.txt
```

### Model Download

Models must be downloaded separately (~31GB total). Place in `models/` directory:

```bash
# Create models directory
mkdir -p models

# Download from Hugging Face (example using huggingface-cli)
huggingface-cli download TheBloke/Llama-3.2-3B-Instruct-GGUF \
    --local-dir models/ --include "*.gguf"

huggingface-cli download bartowski/Qwen2.5-14B-Instruct-GGUF \
    --local-dir models/ --include "*Q4_K_M.gguf"

huggingface-cli download bartowski/Qwen2.5-32B-Instruct-GGUF \
    --local-dir models/ --include "*Q4_K_M.gguf"
```

**Required Models**:
| Model | Size | Purpose |
|-------|------|---------|
| Llama-3.2-3B-Instruct-Q4_K_M.gguf | ~2GB | Ingestion Agent |
| Qwen2.5-14B-Instruct-Q4_K_M.gguf | ~9GB | Structuring Agent |
| Qwen2.5-32B-Instruct-Q4_K_M.gguf | ~20GB | Synthesis Agent |

### Running the Pipeline

#### Option 1: Interactive Notebook (Recommended for RLHF)

```bash
jupyter lab notebooks/RLHF_Demo.ipynb
```

The notebook provides a **tabbed interface** where each tab corresponds to a pipeline step:
- Configure agents (model, prompt, temperature)
- View outputs
- Provide RLHF feedback

#### Option 2: Visual Pipeline (Elyra)

```bash
jupyter lab elyra/UH2025Agent_RLHF.pipeline
```

#### Option 3: Command Line

```bash
python -m code.pipeline_executor \
    --config params.yaml \
    --patient PatientX
```

---

## Directory Structure

```
UH2025Agent/
├── README.md                    # This file
├── RFC.md                       # Circulating RFC document
├── ARCHITECTURE.md              # Detailed architecture docs
├── FEDERATED.md                 # Diagnostic Arena / RLHF vision
├── DEVELOPMENT_NOTES.md         # Development history
│
├── topology.yaml                # Pipeline definition
├── params.yaml                  # Default parameters
│
├── code/                        # DeLab v2.0 standard
│   ├── agents/                  # Agent implementations
│   │   ├── base_agent.py
│   │   ├── ingestion_agent.py
│   │   ├── structuring_agent.py
│   │   ├── executor_agent.py
│   │   ├── synthesis_agent.py
│   │   └── prompts/             # Prompt templates
│   │
│   ├── biotools/                # Bio-tool wrappers
│   │   ├── clinvar.py
│   │   ├── spliceai.py
│   │   ├── alphamissense.py
│   │   ├── revel.py
│   │   ├── omim.py
│   │   └── CONTRIBUTING.md
│   │
│   ├── arena/                   # RLHF infrastructure
│   │   ├── feedback_collector.py
│   │   ├── annotation_schema.py
│   │   └── arena_interface.py
│   │
│   ├── configurator.py          # Parameter configuration UI
│   ├── output_viewer.py         # Output display with RLHF
│   ├── pipeline_executor.py     # Execution engine
│   └── widgets.py               # Reusable UI components
│
├── AGENTS.md                    # Agent operational manual (DeLab v2.0)
├── TOPOLOGY.md                  # FAIR metadata (DeLab v2.0)
│
├── synthetic_patients/          # Synthetic patient generator
│   ├── generator.py
│   └── prompts/
│       └── rare_disease_seeds/
│
├── Data/
│   └── PatientX/                # Example patient data
│
├── outputs/                     # Pipeline outputs
│   ├── 01_ingestion/
│   ├── 02_structuring/
│   ├── 03_executor/
│   ├── 04_synthesis/
│   └── feedback/                # RLHF annotations
│
├── elyra/                       # Visual pipeline
├── notebooks/                   # Interactive interface
└── metadata/                    # Output schemas
```

---

## RLHF Interface

The system provides expert feedback collection at every step:

### Feedback Schema

```yaml
step_feedback:
  step_id: "structuring"
  timestamp: "2025-11-25T10:30:00Z"
  reviewer:
    id: "clinician_001"
    role: "geneticist"

  assessment:
    correctness: "partial"  # correct | partial | incorrect
    confidence: 0.75

  corrections:
    - field: "diagnostic_table.diagnosis_1"
      original: "Paramyotonia Congenita"
      corrected: "Hyperkalemic Periodic Paralysis"
      rationale: "Episode pattern suggests HyperKPP over PMC"

  notes: "Good variant identification, needs diagnosis ranking work"
```

### Diagnostic Arena

The Arena enables citizen science contribution:

1. **Generate** synthetic patient from disease seed
2. **Run** pipeline to produce diagnostic outputs
3. **Review** outputs in JupyterLab interface
4. **Annotate** with corrections and feedback
5. **Submit** to federated training pool

---

## Consortium & Community

This project unites organizations at the frontier of rare disease diagnosis:

- **Mayo Clinic** - Clinical validation and hackathon framework
- **Wilhelm Foundation** - Patient advocacy and alignment
- **Rare Care Centre Network** - Global clinical partnerships
- **Open Source Community** - Technical expertise and contributions

### How to Contribute

| Level | Contribution | Recognition |
|-------|--------------|-------------|
| **Heavy** | Write code for new bio-tools or agents | Co-authorship on publications |
| **Medium** | Participate in Diagnostic Arena reviews | Acknowledgment + credit |
| **Light** | Attend review calls, provide RFC feedback | Community recognition |

---

## Roadmap

### Phase 1: Mapping (November 2025) ✅
- [x] Map full hackathon workflow
- [x] Define M4 Envelope constraints
- [x] Create 4-agent architecture

### Phase 2: Arena (December 2025 - January 2026)
- [ ] Launch Diagnostic Arena for RLHF
- [ ] Generate synthetic patient corpus
- [ ] Collect initial expert feedback

### Phase 3: Execution (February 2026)
- [ ] Integrate 5 key bio-tools
- [ ] Real llama.cpp backend execution
- [ ] End-to-end pipeline validation

### Phase 4: Validation (March 2026)
- [ ] Run alongside human teams in "Shadow Hackathon"
- [ ] Measure utility, safety, hallucination rates
- [ ] Publish methodology paper

---

## Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file - quick start and overview |
| [AGENTS.md](AGENTS.md) | Operational manual for AI agents (DeLab v2.0) |
| [TOPOLOGY.md](TOPOLOGY.md) | FAIR-compliant metadata (DeLab v2.0) |
| [RFC.md](RFC.md) | Circulating request for comments |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed technical architecture |
| [FEDERATED.md](FEDERATED.md) | Diagnostic Arena and RLHF vision |

### Scientific Foundation

| Document | Description |
|----------|-------------|
| [docs/HACKATHON.md](docs/HACKATHON.md) | The Wilhelm Foundation hackathon story and inspiration |
| [docs/PHILOSOPHY.md](docs/PHILOSOPHY.md) | Design principles: colleague model, privacy-first, HITL |
| [docs/LIMITATIONS.md](docs/LIMITATIONS.md) | Honest assessment of what this system can and cannot do |
| [docs/REFERENCES.md](docs/REFERENCES.md) | Curated scientific bibliography (50+ references) |

### Scientific Primers

For those new to rare disease, genomics, or clinical AI:

| Primer | Description |
|--------|-------------|
| [docs/primers/RARE_DISEASE.md](docs/primers/RARE_DISEASE.md) | Introduction to rare diseases and the diagnostic odyssey |
| [docs/primers/GENOMICS.md](docs/primers/GENOMICS.md) | Variant interpretation, ACMG guidelines, pathogenicity tools |
| [docs/primers/CDS.md](docs/primers/CDS.md) | Clinical decision support and AI in medicine |

### Key References

1. **AlphaMissense**: Cheng et al. (2023). *Science*, 381(6664)
2. **SpliceAI**: Jaganathan et al. (2019). *Cell*, 176(3)
3. **ACMG Guidelines**: Richards et al. (2015). *Genetics in Medicine*
4. **gnomAD**: Karczewski et al. (2020). *Nature*

See [docs/REFERENCES.md](docs/REFERENCES.md) for the complete bibliography

---

## License

MIT License (Research Use)

For production clinical deployment, additional regulatory approvals may be required.

---

## Contact

**Wilhelm Foundation / RareResearch Consortium**
- GitHub: [github.com/wilhelm-foundation](https://github.com/wilhelm-foundation)
- RFC Feedback: Open an issue or join monthly review calls

---

**Version**: 2.1.0 (LangGraph 4-Agent Architecture)
**Last Updated**: November 29, 2025
**Status**: E2E Test Passed - Active Development
