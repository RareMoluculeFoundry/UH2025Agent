# AGENTS.md: Operational Manual for UH2025-CDS-Agent

## Purpose

This operational manual provides instructions for AI agents and automation systems to effectively work with the UH2025 Clinical Decision Support Agent. It follows Anthropic's best practices for agent-readable documentation and enables autonomous operation.

## Topology Overview

**Name:** UH2025-CDS-Agent
**Version:** 2.1.0 (LangChain + Federated Standard)
**Purpose:** Privacy-first rare disease diagnostic pipeline integrating multiple AI agents with human-in-the-loop validation for clinical decision support.

**Input Requirements:**
- Patient clinical summary (markdown or PDF)
- Patient genomic variants (JSON from VCF)
- Configuration parameters (params.yaml)

**Output Artifacts:**
- Normalized patient context (JSON)
- Diagnostic table with ranked hypotheses (JSON)
- Variants table with annotations (JSON)
- Tool-usage plan (JSON)
- Bio-tool execution results (JSON)
- Final clinical report (Markdown)
- RLHF feedback annotations (JSON)

**Execution Modes:**
- Local (LangGraph Orchestration)
- Elyra (JupyterLab visual pipeline)
- Command line (`python -m code.pipeline_executor`)

## Execution Instructions

### Quick Start

```bash
# 1. Navigate to topology
cd /path/to/DeLab/lab/obs/topologies/UH2025Agent

# 2. Activate environment
conda activate lab-env

# 3. Run interactive notebook (recommended)
jupyter lab notebooks/UH2025Agent.ipynb

# 4. Or run via command line
python -m code.pipeline_executor --config params.yaml --patient PatientX
```

### Parameter Configuration

**Required Parameters:**
```yaml
patient_id: "PatientX"
  type: string
  default: "PatientX"
  description: Patient identifier (directory name under Data/)

privacy_mode: true
  type: boolean
  default: true
  description: Enable HIPAA-compliant execution (local only)
```

**Model Parameters:**
```yaml
llm_temperature_diagnostic: 0.3
  type: float
  default: 0.3
  range: [0.0, 1.0]
  description: Lower = more focused for diagnostic reasoning

llm_temperature_tools: 0.2
  type: float
  default: 0.2
  range: [0.0, 1.0]
  description: Very low for deterministic tool calls

llm_temperature_report: 0.4
  type: float
  default: 0.4
  range: [0.0, 1.0]
  description: Moderate for fluent report writing
```

**Analysis Thresholds:**
```yaml
pathogenicity_threshold: 0.564
  type: float
  default: 0.564
  description: AlphaMissense threshold (likely_pathogenic)

max_differential_diagnoses: 5
  type: integer
  default: 5
  range: [3, 10]
  description: Top N diagnoses to consider
```

### Dataset Configuration

**Required Datasets:**

| Dataset ID | Purpose | Format | Location | Required |
|-----------|---------|--------|----------|----------|
| patient-data | Clinical + genomic data | MD + JSON | Data/{patient_id}/ | Yes |

**Patient Data Structure:**
```
Data/
└── PatientX/
    ├── patientX_Clinical.md    # Clinical summary
    └── patientX_Genomic.json   # Genomic variants
```

## Workflow Steps

### Step Dependency Graph

```
Entry Points (Parallel):
  ├─ step_01_ingestion
  │
  Sequential Chain:
  └─ step_01_ingestion
       └─ step_02_structuring
            └─ step_03_execution
                 └─ step_04_synthesis
                      └─ step_05_review (HITL)
```

### Step Details

#### Step 01: Ingestion (Patient Data Parsing)

**Module:** `code/agents/ingestion_agent.py`
**Model:** Llama 3.2 3B (Q4_K_M quantization)
**Purpose:** Parse clinical summary and genomic data into normalized structure

**Dependencies:** None (entry point)

**Inputs:**
- `clinical_summary_path`: Path to clinical markdown (from params)
- `genomic_data_path`: Path to genomic JSON (from params)
- `patient_id`: Patient identifier (from params)

**Outputs:**
- `patient_context`: Normalized patient context → `outputs/01_ingestion/patient_context.json`

**Resources:**
- CPU: 2 cores
- Memory: 4GB
- GPU: Optional (accelerates inference)

**HITL Checkpoint:** After this step, expert can verify clinical data was parsed correctly

#### Step 02: Structuring (Diagnostic Artifacts)

**Module:** `code/agents/structuring_agent.py`
**Model:** Qwen 2.5 14B (Q4_K_M quantization)
**Purpose:** Generate diagnostic hypotheses, variant annotations, and tool plan

**Dependencies:** step_01_ingestion

**Inputs:**
- `patient_context`: From step 01

**Outputs:**
- `diagnostic_table`: Ranked diagnostic hypotheses → `outputs/02_structuring/diagnostic_table.json`
- `variants_table`: Annotated variants → `outputs/02_structuring/variants_table.json`
- `tool_usage_plan`: Bio-tools to execute → `outputs/02_structuring/tool_usage_plan.json`

**Resources:**
- CPU: 4 cores
- Memory: 16GB
- GPU: Optional

**HITL Checkpoint:** Expert reviews diagnostic hypotheses and can edit rankings

#### Step 03: Execution (Bio-Tool Execution)

**Module:** `code/agents/executor_agent.py`
**Model:** None (Python orchestration)
**Purpose:** Execute bio-tools in sandboxed environment

**Dependencies:** step_02_structuring

**Inputs:**
- `variants_table`: From step 02
- `tool_usage_plan`: From step 02

**Outputs:**
- `tool_results`: Raw bio-tool outputs → `outputs/03_execution/tool_results.json`

**Bio-Tools Available:**
| Tool | Purpose | API |
|------|---------|-----|
| ClinVar | Variant clinical significance | NCBI E-utilities |
| SpliceAI | Splice site prediction | Pre-computed DB |
| AlphaMissense | Missense pathogenicity | Local DB |
| REVEL | Ensemble pathogenicity | dbNSFP |
| OMIM | Disease-gene relationships | OMIM API |

**Resources:**
- CPU: 2 cores
- Memory: 8GB
- Network: Required for API calls

**HITL Checkpoint:** Expert can flag tool errors or request additional tools

#### Step 04: Synthesis (Report Generation)

**Module:** `code/agents/synthesis_agent.py`
**Model:** Qwen 2.5 32B (Q4_K_M quantization)
**Purpose:** Generate comprehensive clinical report

**Dependencies:** step_03_execution

**Inputs:**
- `patient_context`: From step 01
- `diagnostic_table`: From step 02
- `variants_table`: From step 02
- `tool_results`: From step 03

**Outputs:**
- `clinical_report`: Final report → `outputs/04_synthesis/clinical_report.md`
- `report_metadata`: Report metadata → `outputs/04_synthesis/report_metadata.json`

**Resources:**
- CPU: 4 cores
- Memory: 24GB
- GPU: Recommended

**HITL Checkpoint:** Expert reviews and edits final report before approval

#### Step 05: Review (HITL Feedback Collection)

**Module:** `code/review_interface.py`
**Purpose:** Collect expert feedback for RLHF training

**Dependencies:** step_04_synthesis

**Inputs:**
- All previous outputs
- Expert annotations

**Outputs:**
- `feedback`: RLHF annotations → `outputs/feedback/session_{timestamp}.json`

**RLHF Feedback Schema:**
```yaml
step_feedback:
  step_id: string           # e.g., "structuring"
  timestamp: datetime
  reviewer:
    id: string
    role: string            # clinician | geneticist | data_scientist
  assessment:
    correctness: string     # correct | partial | incorrect
    confidence: float       # 0-1 scale
  corrections:
    - field: string
      original: string
      corrected: string
      rationale: string
  notes: string
```

## Privacy and Security (Local-Only Standard)

### HIPAA Compliance

This topology is engineered for **HIPAA-compliant** environments:
1.  **No Cloud LLMs**: All models (Llama, Qwen) run via `llama.cpp` on local hardware.
2.  **No Data Egress**: Patient data never leaves the `Data/` directory.
3.  **Local Vector Store**: Usage of `Chroma` or `FAISS` with local persistence only.

**Strict Prohibitions**:
- ❌ `from langchain_openai import ChatOpenAI`
- ❌ `from langchain_anthropic import ChatAnthropic`
- ❌ Using `LANGCHAIN_TRACING_V2=true` pointing to cloud LangSmith.

### Privacy Mode

```yaml
execution:
  privacy_mode: true
```

**Compliance Notes:**
- Designed for HIPAA-compliant environments
- Audit logging enabled for all operations
- Data retention follows institutional policies

## Version History

### Version 2.1.0 (November 29, 2025)
- **LangChain Integration**: Adopted LangChain/LangGraph for robust orchestration.
- **Privacy Standard**: Explicit "Local-Only" constraint for HIPAA compliance.

### Version 2.0.0 (November 2025)
- Restructured to 4-agent architecture
- Added HITL checkpoints at every step
- Integrated RLHF feedback collection
- DeLab v2.0 standard compliance (code/ directory)

### Version 1.0.0 (October 2025)
- Initial 5-stage pipeline (legacy)
- Demo for Mayo Clinic Hackathon

---

**This operational manual is maintained alongside the topology definition. Update when execution patterns, parameters, or workflow structure changes.**

*Template Version: 1.0.0*
*Last Updated: November 29, 2025*
*Part of DeLab Topologies Standard*
