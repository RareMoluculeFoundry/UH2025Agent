# Topology Metadata (TOPOLOGY.md)

This file contains FAIR-compliant metadata for the UH2025-CDS-Agent topology.

## Findable

### Identifiers
- **DOI**: Pending (pre-release)
- **DID**: `did:defact:topology:uh2025-cds-agent-v2`
- **Version**: `2.0.0`
- **Git Repository**: Internal (DeLab)

### Title
**UH2025-CDS-Agent**: Privacy-First Clinical Decision Support for Rare Disease Diagnosis

### Description
The UH2025-CDS-Agent is a clinical decision support system for rare and undiagnosed diseases. It implements a 4-agent architecture with human-in-the-loop validation at every step, designed to run entirely on local hardware (M4 MacBook Pro "edge envelope") for privacy-first operation.

The topology processes clinical summaries and genomic variant data through:
1. **Ingestion Agent**: Parses clinical and genomic data
2. **Structuring Agent**: Generates diagnostic hypotheses and tool-usage plans
3. **Executor Agent**: Runs bio-tools (ClinVar, OMIM, etc.) in sandboxed environment
4. **Synthesis Agent**: Generates comprehensive clinical report

Expert review with RLHF feedback collection occurs at each checkpoint.

### Keywords
- rare-disease
- clinical-decision-support
- diagnostic-pipeline
- llm-agents
- human-in-the-loop
- rlhf
- genomics
- variant-annotation
- edge-computing
- privacy-first

### Authors
- **Name**: RareResearch Consortium
  - **Affiliation**: Wilhelm Foundation / Stanley Lab
  - **Role**: Creator, Maintainer

- **Name**: Mayo Clinic Hackathon Team
  - **Affiliation**: Mayo Clinic
  - **Role**: Clinical Validation Partner

### Dates
- **Created**: 2025-10-22
- **Modified**: 2025-11-26
- **Published**: Pending (RFC circulating)

## Accessible

### Repository
- **Type**: Git (local development)
- **Location**: `lab/obs/topologies/UH2025Agent`
- **Branch**: `main`

### Container Registry
- **Status**: Not yet containerized (local execution only)

### License
- **License Type**: MIT License (Research Use)
- **License URL**: https://opensource.org/licenses/MIT
- **Notes**: Production clinical deployment may require additional regulatory approvals

### Access Control
- **Access Type**: `consortium`
- **Authentication Required**: No (local execution)
- **Restrictions**: Research use only; clinical deployment pending regulatory approval

## Interoperable

### Data Formats

#### Input Formats
- **Clinical Summary**
  - **Format**: Markdown
  - **Schema**: Free-form clinical narrative
  - **Location**: `Data/{patient_id}/patientX_Clinical.md`

- **Genomic Variants**
  - **Format**: JSON (VCF-derived)
  - **Schema**: See `metadata/input_schema.yaml`
  - **Location**: `Data/{patient_id}/patientX_Genomic.json`

#### Output Formats
- **Diagnostic Outputs**
  - **Format**: JSON
  - **Schema**: See `metadata/output_schema.yaml`
  - **Artifacts**: patient_context, diagnostic_table, variants_table, tool_results

- **Clinical Report**
  - **Format**: Markdown
  - **Schema**: Structured clinical report template
  - **Location**: `outputs/04_synthesis/clinical_report.md`

- **RLHF Feedback**
  - **Format**: JSON
  - **Schema**: Step-annotated feedback with corrections
  - **Location**: `outputs/feedback/`

### Standards Compliance
- **Privacy**: HIPAA-compliant (local execution mode)
- **Genomics**: VCF 4.x compatible input
- **Ontologies**: HPO (Human Phenotype Ontology), OMIM

### Execution Platforms
- Local (Papermill via Jupyter notebook) - Primary
- Elyra (JupyterLab visual pipeline)
- Command line (`python -m code.pipeline_executor`)

### Interoperability Notes
- Designed for edge/local execution (M4 MacBook Pro)
- LLM inference via llama.cpp (CPU/Metal acceleration)
- Bio-tool APIs: ClinVar (NCBI), OMIM, AlphaMissense DB

## Reusable

### Documentation
- **README**: See `README.md` (overview, quick start)
- **RFC**: See `RFC.md` (design rationale)
- **Architecture**: See `ARCHITECTURE.md` (detailed diagrams)
- **Operational Manual**: See `AGENTS.md` (agent instructions)
- **Federation Vision**: See `FEDERATED.md` (RLHF/Arena design)

### Dependencies

#### Modules Required
None (self-contained - agents are in `code/agents/`)

#### Datasets Required
- Patient data in `Data/{patient_id}/` format

#### Tools Required
- `code/biotools/clinvar.py` - ClinVar API wrapper
- `code/biotools/spliceai.py` - SpliceAI lookup
- `code/biotools/alphamissense.py` - AlphaMissense DB
- `code/biotools/revel.py` - REVEL scores
- `code/biotools/omim.py` - OMIM API wrapper

#### Software Dependencies
- Python 3.10+
- llama-cpp-python (>=0.2.0)
- ipywidgets
- pandas, pydantic, httpx
- See `requirements.txt` for complete list

### Usage Examples

#### Interactive Notebook (Recommended)
```bash
cd /path/to/UH2025Agent
jupyter lab notebooks/UH2025Agent.ipynb
```

#### Command Line
```bash
python -m code.pipeline_executor --config params.yaml --patient PatientX
```

#### Elyra Visual Pipeline
```bash
jupyter lab elyra/UH2025Agent.pipeline
```

### Testing
- **Test Data**: PatientX (de-identified example)
- **Synthetic Patients**: 5 disease categories in `synthetic_patients/`
- **Validation**: Expert review at HITL checkpoints

### Provenance
- All outputs include timestamps and model versions
- RLHF feedback tracked per session
- Git commit tracked for reproducibility

## Scientific Context

### Research Domain
Clinical Genomics, Rare Disease Diagnosis, Medical AI

### Scientific Problem
Patients with rare diseases often endure a "diagnostic odyssey" lasting years. The UH2025 Agent aims to accelerate diagnosis by:
1. Organizing clinical and genomic evidence
2. Running specialized bio-tools
3. Generating structured diagnostic hypotheses
4. Producing clinician-readable reports

The system is designed as a "colleague" that handles data organization so human experts can focus on high-level diagnostic reasoning.

### Methodology
- **Agentic Architecture**: 4 specialized LLM agents
- **Edge Computing**: Local inference for privacy
- **Human-in-the-Loop**: Expert validation at every step
- **RLHF**: Federated learning from expert feedback

### Expected Outputs
1. Ranked differential diagnosis list
2. Annotated variant table with pathogenicity scores
3. Bio-tool evidence summaries
4. Comprehensive clinical report
5. RLHF training data from expert corrections

### Validation Approach
- Shadow mode alongside human diagnostic teams
- Expert review metrics (precision, recall, utility)
- Comparison to final diagnoses (when available)
- IRB-approved clinical validation studies (planned)

## Computational Requirements

### Minimum Requirements
- **CPU**: Apple Silicon M1 or Intel 8-core
- **Memory**: 32 GB
- **Storage**: 50 GB (models + data)
- **GPU**: Optional (CPU inference supported)

### Recommended Configuration (M4 Envelope)
- **CPU**: Apple M4 Max
- **Memory**: 64-128 GB unified
- **Storage**: 100 GB SSD
- **GPU**: Integrated (Metal acceleration)

### Model Memory Footprint
| Agent | Model | Quantization | Memory |
|-------|-------|--------------|--------|
| Ingestion | Llama 3.2 3B | Q4_K_M | ~2GB |
| Structuring | Qwen 2.5 14B | Q4_K_M | ~10GB |
| Synthesis | Qwen 2.5 32B | Q4_K_M | ~20GB |
| **Peak** | Sequential loading | | ~37GB |

### Execution Time
- **Single Patient**: ~5-15 minutes (depending on hardware)
- **With HITL Review**: Variable (depends on expert)

## Quality Assurance

### Validation Status
- [x] Topology validates against DeLab v2.0 schema
- [x] All agent stubs implemented
- [x] Bio-tool interfaces defined
- [x] Widget infrastructure functional
- [x] Synthetic patient generator operational
- [ ] LLM backend integration (pending)
- [ ] Pipeline orchestration (pending)
- [ ] RLHF persistence (pending)
- [ ] End-to-end validation (pending)

### Quality Metrics
- **Completeness**: 70% (stubs complete, integration pending)
- **Documentation**: 90% (comprehensive docs)
- **Test Data**: 1 real + 5 synthetic disease categories

## Citation

If you use this topology in your research, please cite:

```bibtex
@software{uh2025_cds_agent_2025,
  title = {UH2025-CDS-Agent: Privacy-First Clinical Decision Support for Rare Disease Diagnosis},
  author = {RareResearch Consortium and Wilhelm Foundation},
  year = {2025},
  version = {2.0.0},
  note = {RFC circulating - pre-release}
}
```

## Acknowledgments

This work was inspired by:
- Mayo Clinic Undiagnosed Patient Hackathon
- Undiagnosed Diseases Network (UDN)
- Wilhelm Foundation patient advocacy

We thank:
- Clinical geneticists for diagnostic workflow insights
- LLM community for open-source models (Llama, Qwen)
- DeepMind for AlphaMissense data

## Change Log

### Version 2.0.0 (November 2025)
- Restructured to 4-agent architecture
- DeLab v2.0 standard compliance
- HITL checkpoints at every step
- RLHF feedback collection
- Synthetic patient generator

### Version 1.0.0 (October 2025)
- Initial 5-stage pipeline
- Mayo Clinic Hackathon demo

## Related Resources

### Publications
- RFC: See `RFC.md` for design rationale

### Presentations
- Mayo Clinic Healthcare Hackathon 2025

### Related Work
- AlphaMissense: Cheng et al. (2023). Science, 381(6664)
- SpliceAI: Jaganathan et al. (2019). Cell, 176(3)
- HPO: Kohler et al. (2021). Nucleic Acids Research

## Contact

For questions or support:
- **Issue Tracker**: GitHub (consortium access)
- **RFC Feedback**: Monthly review calls
- **Email**: Contact via Wilhelm Foundation

---

**Metadata Version**: 1.0
**Last Updated**: 2025-11-26
**Metadata Schema**: FAIR DeLab Topology Metadata v1.0
