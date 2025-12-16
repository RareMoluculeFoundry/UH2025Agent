# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-ExecuteTime
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # UH2025Agent: AI-Powered Diagnostic Assistant
#
# **Mayo Clinic Healthcare Hackathon 2025 - Undiagnosed Diseases Network**
#
# ---
#
# ## 🎯 Mission
#
# The **Undiagnosed Diseases Network (UDN)** aims to solve medical mysteries for patients who have spent years without a diagnosis. This AI agent combines cutting-edge genomic analysis with clinical reasoning to accelerate rare disease diagnosis.
#
# **Key Innovation**: Integration of:
# - **AlphaGenome** - Regulatory impact prediction
# - **AlphaMissense** - Pathogenicity scoring
# - **RareLLM** - LLM-powered differential diagnosis
#
# ---

# %% [markdown]
# ## 🏥 Mayo Clinic Undiagnosed Hackathon
#
# ![Mayo Clinic Hackathon](https://undiagnosedhackathon.org/sites/undiagnosedhackathon/files/styles/large/public/2025-04/Undiagnosed%20Hackathon%20logo%201.png?itok=B2mDLQ7n)
#
# *Mayo Clinic Healthcare Hackathon participants collaborate to solve challenges in undiagnosed diseases.*
#
# [Read More](https://newsnetwork.mayoclinic.org/discussion/sounds-of-discovery-ring-at-the-undiagnosed-hackathon/)
#
# ---

# %% [markdown]
# ## 📹 Hackathon Overview Video

# %%
from IPython.display import YouTubeVideo, display

# Embed YouTube video
video = YouTubeVideo('-RggoRAScRQ', width=800, height=450)
display(video)

# %% [markdown]
# ---
# # System Architecture
#
# This notebook provides an interactive runtime and configuration interface for the UH2025Agent diagnostic pipeline. The pipeline follows a **5-stage architecture**:
#
# ```
# Stage 1: AlphaGenome      → Regulatory variant analysis
# Stage 2: AlphaMissense    → Pathogenicity prediction
# Stage 3: RareLLM Diff     → Differential diagnosis
# Stage 4: RareLLM Tools    → Evidence validation tools
# Stage 5: RareLLM Report   → Clinical report generation
# ```
#
# **Design Principles**:
# - **Privacy-First**: All analysis runs locally
# - **Modular**: Each stage is independent
# - **Federated**: Deploy from local (L1) to cluster (L2) to cloud (L3)
# - **FAIR**: Outputs include complete provenance metadata
#
# ---

# %% [markdown]
# ## 🏥 On-Premises AI: Bringing Expertise to the Point of Care
#
# **The Challenge**: Rare disease diagnosis requires world-class expertise that's concentrated in just a handful of academic medical centers. Patients often wait months or years for evaluation, with their sensitive medical data traveling across multiple institutions.
#
# **The Solution**: Deploy AI diagnostic expertise **directly at the point of care**—the local clinic or hospital where the patient is being treated.
#
# ### Why On-Premises?
#
# **🔒 Privacy First**
# - Patient data **never leaves** the local machine
# - HIPAA compliant by design (no cloud transmission)
# - No third-party data processing
# - Complete institutional control
#
# **⚡ Zero Latency**
# - No network round-trips to cloud services
# - Sub-minute response times for diagnostic queries
# - Works offline (no internet dependency)
# - Emergency/rural settings supported
#
# **💪 Democratization of Expertise**
# - World-class AI diagnostics available at **every** clinic
# - Not just major academic centers
# - Reduces health disparities
# - Accelerates diagnosis for underserved populations
#
# **🎯 Cost Effective**
# - No recurring cloud API costs
# - One-time deployment per institution
# - Scales to unlimited patients locally
# - No per-query billing
#
# ### The Vision
#
# Imagine a future where:
# - Every clinic has access to UDN-level diagnostic expertise
# - Rare disease patients get answers in **days, not years**
# - Medical data remains private and secure
# - Healthcare costs decrease through faster diagnosis
#
# This demo showcases that future—**AI running locally, diagnosing globally**.
#
# ---

# %% [markdown]
# ## 🌐 Best of Both Worlds: Train Hyperscale, Deploy Local
#
# **The Federated Architecture**: This system demonstrates a revolutionary approach to AI deployment—**train on massive infrastructure, deploy to edge devices**.
#
# ### How It Works
#
# ```
# ┌─────────────────────────────────────────────────────────────────────┐
# │                    TRAINING PHASE (L3 Hyperscale)                   │
# │                                                                     │
# │  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐             │
# │  │ AlphaGenome  │   │AlphaMissense │   │   RareLLM    │             │
# │  │  Training    │   │  Training    │   │  Fine-Tuning │             │
# │  │              │   │              │   │              │             │
# │  │ • 1000s GPUs │   │ • DeepMind   │   │ • Qwen 32B   │             │
# │  │ • ENCODE DB  │   │ • 71M vars   │   │ • Clinical   │             │
# │  │ • Weeks      │   │ • AlphaFold  │   │   corpus     │             │
# │  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘             │
# │         │                   │                   │                   │
# │         └───────────────────┴───────────────────┘                   │
# │                             │                                       │
# │                    Trained Models (GB)                              │
# └─────────────────────────────┼───────────────────────────────────────┘
#                               │
#                               ↓ Download Once
# ┌─────────────────────────────────────────────────────────────────────┐
# │              DEPLOYMENT PHASE (L1 Local Clinic/Hospital)            │
# │                                                                     │
# │  ┌────────────────────────────────────────────────────────┐         │
# │  │       💻 MacBook / Workstation (this demo)             │         │
# │  │                                                        │         │
# │  │  ┌─────────────────────────────────────────────────┐   │         │
# │  │  │          UH2025Agent Pipeline                   │   │         │
# │  │  │                                                 │   │         │
# │  │  │  AlphaGenome → AlphaMissense → RareLLM          │   │         │
# │  │  │                                                 │   │         │
# │  │  │  Input: Patient VCF + Clinical Summary          │   │         │
# │  │  │  Output: Differential + Report + Tool Calls     │   │         │
# │  │  │                                                 │   │         │
# │  │  │  Runtime: 3 minutes (for 47 variants)           │   │         │
# │  │  │  Privacy: All data stays local                  │   │         │
# │  │  └─────────────────────────────────────────────────┘   │         │
# │  │                                                        │         │
# │  │  Patient Data → Process → Results                      │         │
# │  │  (never leaves machine)                                │         │
# │  └────────────────────────────────────────────────────────┘         │
# └─────────────────────────────────────────────────────────────────────┘
# ```
#
# ### The DEFACT Platform
#
# This is built on **DEFACT** (Decentralized Federated AI Computational Topology):
#
# **L1 (Local)**: This demo—MacBook/workstation at clinic
# - Development and testing
# - Clinical deployment
# - Patient data processing
# - Privacy-preserving inference
#
# **L2 (Regional)**: University/hospital cluster
# - Ray clusters
# - Multi-GPU workstations  
# - Research deployments
# - Validation studies
#
# **L3 (Hyperscale)**: Cloud datacenter
# - Model training at scale
# - Kubeflow pipelines
# - Kubernetes orchestration
# - Global model distribution
#
# ### Why This Matters for UDN
#
# The **Undiagnosed Diseases Network** has transformed rare disease diagnosis by bringing together expertise from multiple academic medical centers. This AI system takes the next step:
#
# 1. **Capture UDN Expertise**: Train models on published UDN cases, OMIM, ClinVar, literature
# 2. **Distill to Deployable Models**: Compress to MacBook-deployable size (GB not TB)
# 3. **Deploy Everywhere**: Every clinic gets UDN-level diagnostic capability
# 4. **Maintain Privacy**: Patient data never needs to leave local institution
# 5. **Accelerate Discovery**: Diagnoses that took years now take minutes
#
# ### Live Demo Connection
#
# This notebook demonstrates:
# - ✅ **Models trained at scale** (AlphaGenome, AlphaMissense, RareLLM)
# - ✅ **Running locally** (on this machine, no cloud required)
# - ✅ **Processing patient data** (PatientX with SCN4A variants)
# - ✅ **Generating clinical insights** (differential diagnosis, report, tool calls)
# - ✅ **All in ~3 minutes** (from VCF to clinical report)
#
# **This is the future of AI in medicine**—world-class expertise, locally deployed, privacy-preserving, accessible to all.
#
# ---

# %% [markdown]
# ## Import Dependencies
#
# We import our custom modules from the `code/` directory. This follows the **module standard** where implementation details are hidden in reusable Python modules, and the notebook provides a clean narrative interface.

# %%
import sys
from pathlib import Path

# Get topology root (parent of notebooks directory)
# Handle both file execution and interactive notebook modes
if '__file__' in globals():
    TOPOLOGY_ROOT = Path(__file__).parent.parent
else:
    # In interactive mode, cwd should be the notebooks directory
    TOPOLOGY_ROOT = Path.cwd().parent

# Add topology root to Python path if not already present
if str(TOPOLOGY_ROOT) not in sys.path:
    sys.path.insert(0, str(TOPOLOGY_ROOT))

# Import our custom modules from code package
from code import (
    TopologyConfigurator,
    OutputBrowser,
    PipelineExecutor,
    PatientSelector,
    ProgressTracker,
    RunButton,
    StatusDisplay
)

# Standard imports
from IPython.display import display
import ipywidgets as widgets

# %% [markdown]
# ## Initialize System
#
# We start by configuring paths and validating that all required directories and modules exist.

# %%
# Define paths
DATA_DIR = TOPOLOGY_ROOT / "Data"
OUTPUTS_DIR = TOPOLOGY_ROOT / "outputs"
MODULES_DIR = TOPOLOGY_ROOT.parent.parent / "modules"

# Validate directories
assert DATA_DIR.exists(), f"Data directory not found: {DATA_DIR}"
assert OUTPUTS_DIR.exists(), f"Outputs directory not found: {OUTPUTS_DIR}"
assert MODULES_DIR.exists(), f"Modules directory not found: {MODULES_DIR}"

print(f"✓ System initialized")
print(f"  Data: {DATA_DIR}")
print(f"  Outputs: {OUTPUTS_DIR}")
print(f"  Modules: {MODULES_DIR}")

# %% [markdown]
# ---
# # Part 1: Patient Selection
#
# Select a patient case to analyze. Each patient has:
# - **Clinical Summary**: Phenotypes, symptoms, family history
# - **Genomic Variants**: VCF-derived variant list with annotations
#
# The system loads patient data from the `Data/` directory.

# %%
# Create patient selector
patient_selector = PatientSelector(DATA_DIR)

# Display patient selector interface
display(patient_selector.get_widget())

# %% [markdown]
# ---
# # Part 2: Pipeline Configuration
#
# Configure parameters for each module in the diagnostic pipeline. This creates a configuration object that can be:
# - **Exported** to `params.yaml` for Kubeflow/Elyra deployment
# - **Modified** via the interactive interface
# - **Saved** and loaded between sessions
#
# The configurator uses **ipywidgets** to provide a tabbed interface with one tab per module.

# %% [markdown]
# ## Configure Pipeline Parameters
#
# Adjust parameters for each stage of the pipeline:
#
# - **AlphaGenome**: Regulatory analysis settings
# - **AlphaMissense**: Pathogenicity thresholds
# - **RareLLM Stages**: LLM temperature, output limits
# - **Global Settings**: Patient ID, privacy mode, timeouts

# %%
# Create configurator
configurator = TopologyConfigurator(TOPOLOGY_ROOT)

# Display configurator interface
display(configurator.get_widget())

# %% [markdown]
# ### Configuration Export
#
# The configuration can be exported to `params.yaml` for use with:
# - Local execution via `code/executor/local_executor.py`
# - Kubeflow Pipelines deployment
# - Elyra visual pipeline execution
# - Ray cluster job submission
#
# Click the **"💾 Export Config"** button above to save the current configuration.

# %% [markdown]
# ---
# # Part 3: Pipeline Execution
#
# Execute the diagnostic pipeline with the selected patient and configuration. The pipeline runs through all 5 stages sequentially, with progress tracking and real-time logging.
#
# **Execution Flow**:
# 1. Validate configuration
# 2. Execute Stage 1 & 2 in parallel (AlphaGenome + AlphaMissense)
# 3. Execute Stage 3 (Differential Diagnosis) using outputs from 1-2
# 4. Execute Stage 4 (Tool Calls) using outputs from 1-3
# 5. Execute Stage 5 (Report) using all previous outputs

# %% [markdown]
# ## Initialize Pipeline Executor
#
# The executor manages pipeline execution, progress tracking, and status updates.

# %%
# Create executor
executor = PipelineExecutor(TOPOLOGY_ROOT)

# Create progress tracker
progress_tracker = ProgressTracker(total_stages=5)

# Create run button
run_button = RunButton(
    description='▶ Run Diagnostic Pipeline',
    on_click=None  # Will set handler below
)

# Create status display
status = StatusDisplay(
    initial_message='Ready to run pipeline',
    initial_color='blue'
)

# %% [markdown]
# ## Define Pipeline Execution Handler
#
# This function is called when the "Run Pipeline" button is clicked. It:
# - Gets configuration from the configurator
# - Updates the patient ID from the patient selector
# - Executes the pipeline with progress callbacks
# - Refreshes output browser when complete

# %%
def run_pipeline(button):
    """Execute the pipeline with current configuration."""
    # Get configuration
    config = configurator.get_config()

    # Update patient ID from selector
    patient_id = patient_selector.get_patient_id()
    if patient_id:
        config['patient_id'] = patient_id

    # Update button state
    run_button.set_running()
    progress_tracker.reset()
    status.info('Pipeline starting...')

    # Define callbacks
    def on_progress(current, total, stage_name):
        progress_tracker.update_progress(current, total, stage_name)

    def on_log(message):
        progress_tracker.log_message(message)

    def on_complete(success):
        if success:
            run_button.set_complete()
            status.success('✅ Pipeline complete - view results below')
            # Refresh output browser
            if 'output_browser' in globals():
                output_browser.refresh_all()
        else:
            run_button.set_ready()
            status.error('❌ Pipeline failed - check log for details')

    # Execute pipeline
    executor.execute(
        config=config,
        progress_callback=on_progress,
        log_callback=on_log,
        completion_callback=on_complete
    )

# Set button handler
run_button.button.on_click(run_pipeline)

# %% [markdown]
# ## Run Pipeline
#
# Click the button below to execute the diagnostic pipeline. Progress will be displayed in real-time.

# %%
# Display execution interface
display(widgets.VBox([
    widgets.HTML(value='<h2 style="text-align: center;">⚙️ Pipeline Execution</h2>'),
    run_button.get_widget(),
    status.get_widget(),
    widgets.HTML(value='<hr>'),
    progress_tracker.get_widget()
]))

# %% [markdown]
# ---
# # Part 4: Browse Outputs
#
# View and analyze the results from each stage of the pipeline. The output browser provides:
# - **Tabbed interface** for each output type
# - **Automatic formatting** (tables, charts, markdown)
# - **Download buttons** for exporting results
# - **Refresh capability** to reload after re-execution
#
# **Available Outputs**:
# 1. Regulatory Analysis (JSON)
# 2. Pathogenicity Scores (JSON)
# 3. Differential Diagnosis (Styled Table)
# 4. Confidence Chart (Visualization)
# 5. Tool Calls (Formatted List)
# 6. Clinical Report (Markdown)

# %% [markdown]
# ## Initialize Output Browser
#
# The output browser loads results from the `outputs/` directory and provides interactive viewing.

# %%
# Create output browser
output_browser = OutputBrowser(OUTPUTS_DIR)

# Display output browser
display(output_browser.get_widget())

# %% [markdown]
# ---
# # Part 5: Export & Deploy
#
# Once you've configured and tested the pipeline locally, you can deploy it to federated infrastructure.
#
# ## Export Configuration
#
# The configuration object can be exported to `params.yaml`:

# %%
# Export configuration
config_path = configurator.export_config()
print(f"✓ Configuration exported to: {config_path}")
print(f"\nContents:")
print("─" * 60)
with open(config_path, 'r') as f:
    print(f.read())

# %% [markdown]
# ## Deploy to Kubeflow Pipelines (L3)
#
# Compile and upload the pipeline to Kubeflow:
#
# ```bash
# cd /Users/stanley/Projects/DeLab/lab/obs/topologies/UH2025Agent
#
# # Compile pipeline
# python kubeflow/pipeline.py --compile
#
# # Upload to Kubeflow
# python kubeflow/pipeline.py --upload --host http://kubeflow-cluster:8080
#
# # Run pipeline
# python kubeflow/pipeline.py --run --params params.yaml
# ```

# %% [markdown]
# ## Deploy to Ray Cluster (L2/L3)
#
# Submit the pipeline as a Ray job:
#
# ```bash
# # Submit to Ray cluster
# python ray/submit_job.py \
#     --cluster-url http://ray-cluster:8265 \
#     --topology topology.yaml \
#     --params params.yaml
# ```

# %% [markdown]
# ## Execute via Elyra (L1/L2)
#
# Open the visual pipeline in JupyterLab:
#
# ```bash
# # Convert topology to Elyra format
# python code/elyra/convert.py --output elyra/UH2025Agent.pipeline
#
# # Open in JupyterLab
# jupyter lab elyra/UH2025Agent.pipeline
# ```

# %% [markdown]
# ---
# # Technology Stack
#
# ## AlphaGenome
# Predicts regulatory impact of variants on gene expression using deep learning trained on ENCODE data.
#
# ## AlphaMissense
# DeepMind's protein structure-based model for pathogenicity prediction of missense variants (71M pre-computed scores).
#
# ## RareLLM
# Qwen2.5-32B LLM with LoRA fine-tuning for clinical reasoning and differential diagnosis generation.
#
# ## FAIR Principles
# All outputs include complete provenance metadata, SHA-256 checksums, and quality metrics.
#
# ## Multi-Platform Deployment
# - **L1 Local**: Development and testing (this environment)
# - **L2 Academic**: University clusters with Ray
# - **L3 Hyperscale**: Kubernetes + Kubeflow production deployment
#
# ---

# %% [markdown]
# # Resources & References
#
# **Mayo Clinic Undiagnosed Hackathon**:
# - [Hackathon News Article](https://newsnetwork.mayoclinic.org/discussion/sounds-of-discovery-ring-at-the-undiagnosed-hackathon/)
# - [Undiagnosed Diseases Network](https://undiagnosed.hms.harvard.edu/)
#
# **Scientific References**:
# - AlphaGenome: Kelley DR et al. (2018). Sequential regulatory activity prediction. *Genome Res*.
# - AlphaMissense: Cheng et al. (2023). Accurate proteome-wide missense variant effect prediction. *Science*.
# - Qwen: Alibaba Cloud (2024). Qwen Technical Report. arXiv:2309.16609.
#
# **Platform**:
# - DEFACT: Stanley Lab (2025). Decentralized Federated AI Computational Topology.
#
# ---
#
# **Developed by**: Stanley Lab / RareResearch
# **Platform**: DeLab L1 Lab System
# **License**: CC-BY-4.0
# **Date**: November 2025
