# UH2025Agent Pipeline Outputs

This directory contains outputs from UH2025Agent topology executions, organized following FAIR principles (Findable, Accessible, Interoperable, Reusable).

## Directory Structure

```
outputs/
├── README.md                    # This file
├── 01_regulatory/               # AlphaGenome regulatory analysis outputs
├── 02_pathogenicity/            # AlphaMissense pathogenicity scoring outputs
├── 03_differential/             # RareLLM differential diagnosis outputs
├── 04_toolcalls/                # RareLLM tool call generation outputs
└── 05_report/                   # RareLLM clinical report outputs
```

## FAIR Compliance

### Findable
- Each output has a unique identifier (DID format)
- Rich metadata accompanies every output file
- Timestamps and execution IDs enable precise lookup

### Accessible
- Standard file formats (JSON, Markdown)
- Clear directory organization by stage
- Documented schemas and structures

### Interoperable
- JSON Schema validation
- Standardized metadata format
- Cross-platform compatible paths

### Reusable
- Complete provenance tracking
- SHA-256 checksums for verification
- Explicit licensing (CC-BY-4.0)

## Output File Naming Convention

Each stage produces outputs following this pattern:

```
{stage_number}_{stage_name}/{output_name}.{ext}
{stage_number}_{stage_name}/{output_name}_metadata.yaml
```

**Example**:
```
03_differential/
├── differential_diagnosis.json           # Primary output
└── differential_diagnosis_metadata.yaml  # FAIR metadata
```

## Metadata Structure

Every output is accompanied by a metadata file containing:

- **Identity**: Unique ID, type, format
- **Provenance**: Module, version, timestamp, execution ID
- **Compute Environment**: Backend, model, system info
- **Inputs**: All input files used
- **Parameters**: All tunable parameters
- **Quality Metrics**: Validation status, performance metrics
- **Verification**: SHA-256 checksum
- **Licensing**: License, attribution, usage restrictions

See `metadata/output_schema.yaml` for complete schema definition.

## Usage

### Reading Outputs

```python
import json
import yaml
from pathlib import Path

# Load primary output
output_path = Path("outputs/03_differential/differential_diagnosis.json")
with open(output_path) as f:
    data = json.load(f)

# Load metadata
metadata_path = output_path.with_name(f"{output_path.stem}_metadata.yaml")
with open(metadata_path) as f:
    metadata = yaml.safe_load(f)

# Verify checksum
import hashlib
with open(output_path, 'rb') as f:
    computed_checksum = hashlib.sha256(f.read()).hexdigest()
assert computed_checksum == metadata['verification']['checksum_sha256']
```

### Validating Outputs

```python
from code.utils.output_manager import validate_output

# Validate output and metadata
is_valid, errors = validate_output(
    output_path="outputs/03_differential/differential_diagnosis.json",
    metadata_path="outputs/03_differential/differential_diagnosis_metadata.yaml"
)

if not is_valid:
    print("Validation errors:", errors)
```

## Output Types

### 01_regulatory: Regulatory Analysis
- **File**: `regulatory_analysis.json`
- **Source**: AlphaGenome module
- **Content**: Variant regulatory impact predictions
- **Size**: ~1-2 KB

### 02_pathogenicity: Pathogenicity Scoring
- **File**: `pathogenicity_scores.json`
- **Source**: AlphaMissense module
- **Content**: Variant pathogenicity predictions
- **Size**: ~1-2 KB

### 03_differential: Differential Diagnosis
- **File**: `differential_diagnosis.json`
- **Source**: RareLLM Stage 1
- **Content**: Ranked list of potential diagnoses with confidence scores
- **Size**: ~1-3 KB
- **LLM Inference**: 60-120 seconds

### 04_toolcalls: Tool Call Generation
- **File**: `tool_calls.json`
- **Source**: RareLLM Stage 2
- **Content**: Structured tool calls for evidence validation
- **Size**: ~2-4 KB
- **LLM Inference**: 30-60 seconds

### 05_report: Clinical Report
- **Files**: `clinical_report.md`, `clinical_report.json`
- **Source**: RareLLM Stage 3
- **Content**: Comprehensive diagnostic report
- **Size**: ~5-15 KB (Markdown), ~2-5 KB (JSON metadata)
- **LLM Inference**: 90-180 seconds

## Version Control

**Tracked**:
- ✅ README.md files
- ✅ .gitkeep placeholder files

**Ignored** (in .gitignore):
- ❌ Output files (*.json, *.md from pipeline)
- ❌ Metadata files (*_metadata.yaml)

Outputs are ephemeral and regenerated on each run. For reproducibility, we track:
- Pipeline code (topology.yaml, notebooks)
- Input data (Data/ directory)
- Execution parameters

## Troubleshooting

### Missing Metadata Files
**Problem**: Output exists but no `*_metadata.yaml`

**Solution**: Metadata generation may have failed. Check notebook execution logs.

### Checksum Mismatch
**Problem**: Computed checksum doesn't match metadata

**Solution**: File was modified after generation. Regenerate output.

### Validation Errors
**Problem**: Output doesn't pass schema validation

**Solution**: Check `validation_errors` field in metadata for specific issues.

## Related Documentation

- **Metadata Schema**: `metadata/output_schema.yaml`
- **Validation Utilities**: `code/utils/output_manager.py`
- **Pipeline Definition**: `topology.yaml`
- **Module Documentation**: `../../modules/RareLLM/README.md`

---

**Last Updated**: November 3, 2025
**Version**: 1.0.0
**Maintainer**: Stanley Lab / RareResearch
