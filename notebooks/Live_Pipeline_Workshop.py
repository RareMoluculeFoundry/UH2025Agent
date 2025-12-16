# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-ExecuteTime
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Live Pipeline Workshop: UH2025-CDS-Agent v3.0
#
# ## Interactive Demonstration of the Rare Disease Diagnostic Pipeline
#
# This notebook provides a hands-on walkthrough of the UH2025-CDS-Agent pipeline, demonstrating:
#
# 1. **Bio-Tool API Integration** - Real ClinVar and OMIM queries
# 2. **Multi-Turn Feedback** - Clinician review and reanalysis workflow
# 3. **Federation Export** - Preparing contributions for the Rare Arena Network
# 4. **RLHF Training Data** - Generating training data from feedback
#
# ---
#
# **Prerequisites:**
# - Run `pip install requests ipywidgets` if not already installed
# - Optional: Set `NCBI_API_KEY` environment variable for faster ClinVar queries
# - Optional: Set `OMIM_API_KEY` for real OMIM data (register at https://omim.org/api)

# %%
# Setup: Add code directory to path
import sys
from pathlib import Path

# Navigate to project root
project_root = Path.cwd().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")
print(f"Working directory: {Path.cwd()}")

# %% [markdown]
# ## Part 1: Bio-Tool API Integration
#
# ### 1.1 ClinVar E-Utils API
#
# The ClinVarTool now uses real NCBI E-utilities API calls to fetch variant annotations.

# %%
# Import ClinVar tool
from code.biotools.clinvar import ClinVarTool
from code.biotools.base_tool import Variant

# Initialize with real API (no stub)
clinvar = ClinVarTool(use_stub=False)
print(f"ClinVar Tool v{clinvar.version}")
print(f"API Key: {'Configured' if clinvar.api_key else 'Not configured (using default rate limits)'}")

# %%
# Query a well-known pathogenic variant: BRCA1 c.68_69del
# This variant is known to cause Hereditary Breast and Ovarian Cancer Syndrome

test_variant = Variant(
    gene="BRCA1",
    hgvs_c="c.68_69del",
    chromosome="17",
)

print(f"Querying ClinVar for: {test_variant.gene} {test_variant.hgvs_c}")
result = clinvar.query(test_variant)

print(f"\nStatus: {result.status}")
print(f"Data Source: {result.annotations.get('data_source', 'N/A')}")
print(f"\nClinical Significance: {result.annotations.get('clinical_significance', 'N/A')}")
print(f"Review Status: {result.annotations.get('review_status', 'N/A')}")
print(f"Review Stars: {result.annotations.get('review_stars', 'N/A')}")

# %%
# Query by rsID - another common method
# rs80357906 is associated with BRCA1

rsid_variant = Variant(
    rsid="rs80357906",
    gene="BRCA1"
)

print(f"Querying ClinVar for rsID: {rsid_variant.rsid}")
result = clinvar.query(rsid_variant)

import json
print("\nFull result:")
print(json.dumps(result.annotations, indent=2, default=str))

# %% [markdown]
# ### 1.2 OMIM API
#
# The OMIMTool queries gene-disease relationships. It requires an API key for real data.

# %%
# Import OMIM tool
from code.biotools.omim import OMIMTool

# Initialize - will use stub if no API key
omim = OMIMTool(use_stub=False)
print(f"OMIM Tool v{omim.version}")
print(f"API Key: {'Configured' if omim.api_key else 'Not configured (using stub data)'}")

# %%
# Query gene-disease relationships for SCN4A (Sodium Voltage-Gated Channel Alpha Subunit 4)
# This gene is associated with multiple myotonia and periodic paralysis disorders

result = omim.query_by_gene("SCN4A")

print(f"Data Source: {result.get('data_source', 'N/A')}")
print(f"\nGene: {result.get('gene', {}).get('gene_symbol', 'N/A')}")
print(f"Gene Name: {result.get('gene', {}).get('gene_name', 'N/A')}")
print(f"Cyto Location: {result.get('gene', {}).get('cyto_location', 'N/A')}")
print(f"\nAssociated Phenotypes: {result.get('total_phenotypes', 0)}")
print(f"Inheritance Patterns: {result.get('inheritance_patterns', [])}")

# Show phenotypes
print("\nPhenotypes:")
for phe in result.get('phenotypes', [])[:5]:  # Show first 5
    print(f"  - {phe.get('phenotype_name', 'Unknown')}")
    print(f"    MIM: {phe.get('mim_number', 'N/A')}, Inheritance: {phe.get('inheritance', 'N/A')}")

# %% [markdown]
# ## Part 2: Multi-Turn Feedback Interface
#
# The multi-turn review interface allows clinicians to:
# 1. Review AI-generated diagnoses
# 2. Mark correct/incorrect
# 3. Adjust confidence scores
# 4. Request reanalysis with guidance

# %%
# Check if we have demo outputs to review
demo_outputs = project_root / "outputs" / "demo_run"
differential_file = demo_outputs / "03_differential" / "differential_diagnosis.json"

if not differential_file.exists():
    print("Demo outputs not found. Creating sample data for demonstration...")
    
    # Create sample differential diagnosis data
    sample_data = {
        "metadata": {
            "patient_id": "DEMO_001",
            "generated_at": "2025-11-29T10:00:00",
            "model": "UH2025-CDS-Agent"
        },
        "differential_diagnosis": [
            {
                "disease": "Myotonia Congenita, Thomsen Type",
                "omim_id": "160800",
                "confidence": 0.85,
                "genes": ["CLCN1"],
                "rationale": "Patient presents with muscle stiffness that improves with repeated movement (warm-up phenomenon), consistent with chloride channel myotonia. Autosomal dominant inheritance pattern matches family history."
            },
            {
                "disease": "Paramyotonia Congenita",
                "omim_id": "168300",
                "confidence": 0.72,
                "genes": ["SCN4A"],
                "rationale": "Cold-induced muscle stiffness reported. However, symptoms don't worsen with exercise which is atypical. SCN4A variant identified in sequencing."
            },
            {
                "disease": "Hyperkalemic Periodic Paralysis",
                "omim_id": "170500",
                "confidence": 0.45,
                "genes": ["SCN4A"],
                "rationale": "SCN4A variant present but no reported episodes of paralysis. Potassium levels were normal during testing."
            },
            {
                "disease": "Myotonic Dystrophy Type 1",
                "omim_id": "160900",
                "confidence": 0.30,
                "genes": ["DMPK"],
                "rationale": "Myotonia present but no systemic features (cataracts, cardiac involvement). DMPK repeat expansion testing negative."
            },
            {
                "disease": "Sodium Channel Myotonia",
                "omim_id": "608390",
                "confidence": 0.65,
                "genes": ["SCN4A"],
                "rationale": "SCN4A variant of uncertain significance identified. Clinical presentation could fit sodium channel myotonia spectrum."
            }
        ]
    }
    
    # Save sample data
    demo_outputs.mkdir(parents=True, exist_ok=True)
    (demo_outputs / "03_differential").mkdir(parents=True, exist_ok=True)
    
    with open(differential_file, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Sample data created at: {differential_file}")
else:
    print(f"Using existing demo outputs at: {demo_outputs}")

# %%
# Load the multi-turn review interface
from code.review_interface import create_multiturn_review_interface, ReanalysisRequest
from IPython.display import display

# Define callback for reanalysis requests
def on_reanalysis_request(request: ReanalysisRequest):
    print(f"\n{'='*60}")
    print(f"REANALYSIS REQUEST RECEIVED")
    print(f"{'='*60}")
    print(f"Type: {request.request_type.value}")
    print(f"Iteration: {request.iteration}")
    print(f"Guidance: {request.clinician_guidance[:100]}..." if request.clinician_guidance else "No guidance")
    print(f"Focus Genes: {request.focus_genes}")
    print(f"\nIn a production system, this would trigger pipeline rerun...")
    print(f"{'='*60}\n")

# Create the interface
review_interface = create_multiturn_review_interface(
    outputs_dir=demo_outputs,
    reanalysis_callback=on_reanalysis_request
)

print("Multi-turn review interface loaded. Display widget below.")

# %%
# Display the interactive review interface
# You can:
# 1. Mark diagnoses as correct/incorrect
# 2. Adjust confidence sliders
# 3. Add clinical notes
# 4. Request reanalysis with guidance

display(review_interface.get_widget())

# %% [markdown]
# ## Part 3: Federation Export (Arena Bundle)
#
# The FeedbackCollector can export feedback as a privacy-preserving bundle for the Rare Arena Network.

# %%
# Import the feedback collector
from code.arena.feedback_collector import FeedbackCollector, create_collector

# Create collector for demo run
collector = create_collector(
    run_dir=demo_outputs,
    reviewer_id="workshop_participant"
)

print(f"Feedback Collector initialized")
print(f"Run ID: {collector.run_id}")
print(f"Patient ID: {collector.patient_id}")

# %%
# Add some sample feedback programmatically
collector.add_diagnosis_correction(
    disease_name="Myotonia Congenita, Thomsen Type",
    is_correct=True,
    original_confidence=0.85,
    adjusted_confidence=0.90,
    notes="EMG findings strongly support this diagnosis. Family history is consistent."
)

collector.add_diagnosis_correction(
    disease_name="Paramyotonia Congenita",
    is_correct=False,
    original_confidence=0.72,
    adjusted_confidence=0.30,
    notes="Symptoms do not worsen with cold exposure. Should be lower priority."
)

collector.add_diagnosis_correction(
    disease_name="Sodium Channel Myotonia",
    is_correct=True,
    original_confidence=0.65,
    adjusted_confidence=0.75,
    notes="VUS warrants further investigation. Clinical presentation fits."
)

print(f"Added {len(collector.feedback_items)} feedback items")

# %%
# Get feedback statistics
stats = collector.get_statistics()

print("Feedback Statistics:")
print(f"  Total Items: {stats.get('total_items', 0)}")
print(f"  Correct: {stats.get('total_correct', 0)}")
print(f"  Incorrect: {stats.get('total_incorrect', 0)}")
print(f"  Accuracy Rate: {stats.get('accuracy_rate', 0):.1%}")
print(f"  Items with Corrections: {stats.get('items_with_corrections', 0)}")

confidence_stats = stats.get('confidence_adjustments', {})
print(f"\nConfidence Adjustments:")
print(f"  Count: {confidence_stats.get('count', 0)}")
print(f"  Mean Delta: {confidence_stats.get('mean_delta', 0):.2f}")

# %%
# Export Arena Bundle for federated learning
bundle_path = collector.export_arena_bundle(
    institution_id="workshop_demo",
    anonymize=True,
    include_pipeline_outputs=True
)

print(f"Arena bundle exported to: {bundle_path}")
print(f"Bundle size: {bundle_path.stat().st_size / 1024:.1f} KB")

# %%
# Inspect the bundle contents
import zipfile

print("Bundle Contents:")
with zipfile.ZipFile(bundle_path, 'r') as zf:
    for name in zf.namelist():
        info = zf.getinfo(name)
        print(f"  {name} ({info.file_size} bytes)")
    
    # Read and display manifest
    print("\nManifest:")
    manifest = json.loads(zf.read('manifest.json'))
    print(json.dumps(manifest, indent=2))

# %% [markdown]
# ## Part 4: RLHF Training Data Export
#
# Export feedback in formats suitable for model training:
# - JSONL for Direct Preference Optimization (DPO)
# - JSON for Supervised Fine-Tuning (SFT)

# %%
# Export training data in JSONL format
training_output = demo_outputs / "training" / "rlhf_training_data.jsonl"
training_output.parent.mkdir(parents=True, exist_ok=True)

collector.export_for_training(
    output_path=training_output,
    format="jsonl",
    include_correct=True  # Include both correct and incorrect examples
)

print(f"Training data exported to: {training_output}")

# Display the training data
print("\nTraining Data Records:")
with open(training_output, 'r') as f:
    for line in f:
        record = json.loads(line)
        print(json.dumps(record, indent=2))
        print("---")

# %% [markdown]
# ## Part 5: Complete Pipeline Demo
#
# Run a complete pipeline with Patient X data (if available).

# %%
# Check for Patient X data
patientx_data = project_root / "data" / "demo" / "patientx_vcf.json"

if patientx_data.exists():
    print(f"Patient X data found at: {patientx_data}")
    with open(patientx_data, 'r') as f:
        patient_data = json.load(f)
    
    print(f"\nPatient ID: {patient_data.get('patient_id', 'N/A')}")
    print(f"Variants: {len(patient_data.get('variants', []))}")
    print(f"HPO Terms: {len(patient_data.get('hpo_terms', []))}")
else:
    print("Patient X data not found. Run the E2E test first to generate demo data.")
    print(f"\nExpected location: {patientx_data}")

# %% [markdown]
# ## Summary
#
# This workshop demonstrated the key v3.0 features of the UH2025-CDS-Agent:
#
# ### 1. Real Bio-Tool APIs
# - **ClinVar**: E-utilities API (esearch + esummary) with rate limiting
# - **OMIM**: Gene-disease relationship queries (requires API key)
#
# ### 2. Multi-Turn Feedback
# - Interactive review interface with ipywidgets
# - Reanalysis request system with clinical guidance
# - Feedback history tracking across iterations
#
# ### 3. Federation Infrastructure
# - `export_arena_bundle()` for privacy-preserving contribution
# - Anonymization with differential privacy parameters
# - Gradient summary for federated learning
#
# ### 4. RLHF Training Pipeline
# - JSONL export for DPO training
# - Confidence calibration data
# - Preference pairs from corrections
#
# ---
#
# **Next Steps:**
# 1. Run the full E2E test: `python tests/test_patientx_e2e.py`
# 2. Configure OMIM API key for real gene-disease data
# 3. Integrate with your institution's federated learning network
