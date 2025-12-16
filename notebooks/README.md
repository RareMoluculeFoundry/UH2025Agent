# UH2025Agent Demo Notebook

## Overview

The **demo.ipynb** notebook provides an interactive dashboard for the UH2025Agent diagnostic pipeline, created for the Mayo Clinic Healthcare Hackathon 2025 - Undiagnosed Diseases Network challenge.

## Features

### 1. **Mayo Clinic Hackathon Introduction**
- Embedded images from the Mayo Clinic News Network
- YouTube video showcasing the hackathon
- Project overview and mission statement

### 2. **Interactive Patient Dashboard**
- **Patient Selection**: Dropdown to choose from available patient cases
- **Clinical Summary Viewer**: Display patient phenotypes and clinical history
- **Genomic Data Viewer**: JSON viewer for variant data

### 3. **Pipeline Execution Control**
- One-click pipeline execution button
- Real-time progress tracking (5 stages)
- Execution log with timestamps
- Automatic execution ID generation

### 4. **Results Visualization**
- **Differential Diagnosis Table**: Ranked list with confidence scores
- **Tool Calls Summary**: Evidence validation recommendations with priorities
- **Clinical Report**: Full markdown report viewer
- **Confidence Score Chart**: Visual bar chart of diagnostic confidence

### 5. **FAIR Metadata Explorer**
- Browse complete provenance information
- Verify SHA-256 checksums
- View execution metadata and quality metrics

## Usage

### Quick Start

1. **Open the notebook in JupyterLab:**
   ```bash
   cd /Users/stanley/Projects/DeLab/lab/obs/topologies/UH2025Agent
   jupyter lab notebooks/demo.ipynb
   ```

2. **Run all cells:**
   - Click "Kernel" → "Restart & Run All"
   - Or press `Shift+Enter` through each cell

3. **Select a patient:**
   - Use the dropdown to select "PatientX" (or other available patients)
   - Clinical and genomic data will load automatically

4. **Execute the pipeline:**
   - Click the "▶ Run Diagnostic Pipeline" button
   - Watch the progress bar as each stage executes
   - Results will appear in the accordion sections below

5. **Review results:**
   - Expand each section in the results accordion
   - Review differential diagnoses, tool calls, and clinical report
   - Examine the confidence score visualization

### Presentation Mode (5-minute demo)

1. **Introduction (1 minute)**
   - Show Mayo Clinic hackathon images
   - Play YouTube video (30 seconds)
   - Explain project mission

2. **Live Demo (3 minutes)**
   - Select PatientX
   - Show clinical summary (complex phenotype)
   - Show genomic variants (SCN4A p.Lys260Glu)
   - Run pipeline (if pre-executed, show progress log)
   - Reveal results:
     - Top diagnosis: Paramyotonia Congenita (confidence ~0.92)
     - Supporting evidence tool calls
     - Professional clinical report

3. **Technology Overview (1 minute)**
   - Explain AlphaGenome + AlphaMissense + RareLLM integration
   - Highlight FAIR principles
   - Mention Qwen2.5-32B LLM with LoRA fine-tuning

## Requirements

### Python Packages
```bash
pip install jupyter jupyterlab ipywidgets pandas matplotlib seaborn pyyaml
```

### JupyterLab Extensions
```bash
jupyter labextension install @jupyter-widgets/jupyterlab-manager
```

### Enable ipywidgets
```bash
jupyter nbextension enable --py widgetsnbextension
```

## Directory Structure

```
notebooks/
├── demo.ipynb          # Interactive dashboard notebook
├── demo.py             # Jupytext-synced Python version
├── jupytext.toml      # Jupytext configuration
└── README.md          # This file
```

## Troubleshooting

### Issue: "No results found"
**Solution**: Run the pipeline notebooks first to generate outputs:
```bash
# Execute all notebooks in order
cd ../../../modules/AlphaGenome/notebooks && jupyter nbconvert --execute main.ipynb
cd ../../../modules/AlphaMissense/notebooks && jupyter nbconvert --execute main.ipynb
cd ../../../modules/RareLLM/notebooks && jupyter nbconvert --execute differential_diagnosis.ipynb
cd ../../../modules/RareLLM/notebooks && jupyter nbconvert --execute tool_call_generation.ipynb
cd ../../../modules/RareLLM/notebooks && jupyter nbconvert --execute report_generation.ipynb
```

Or use the Elyra pipeline:
```bash
# Open Elyra pipeline in JupyterLab
cd /Users/stanley/Projects/DeLab/lab/obs/topologies/UH2025Agent
jupyter lab elyra/UH2025Agent.pipeline
# Click "Run Pipeline" in Elyra editor
```

### Issue: Widgets not displaying
**Solution**: Ensure ipywidgets is installed and enabled:
```bash
pip install ipywidgets
jupyter nbextension enable --py widgetsnbextension
```

### Issue: Images not loading
**Solution**: Check internet connection (Mayo Clinic images are loaded from external URL)

### Issue: YouTube video not playing
**Solution**: Ensure you're connected to the internet and YouTube is accessible

## Customization

### Adding New Patients

1. Create patient data directory:
   ```bash
   mkdir -p ../Data/Patient1
   ```

2. Add clinical summary:
   ```bash
   # Create ../Data/Patient1/patient1_Clinical.md
   ```

3. Add genomic data:
   ```bash
   # Create ../Data/Patient1/patient1_Genomic.json
   ```

4. Refresh the notebook:
   - Re-run the "Define Paths and Configuration" cell
   - Patient will appear in dropdown

### Customizing Visualizations

Edit the "Visualization: Confidence Scores" cell to modify:
- Chart type (bar, pie, radar)
- Color scheme
- Size and layout
- Additional plots

## Related Documentation

- **Topology README**: `../README.md`
- **Pipeline Definition**: `../topology.yaml`
- **Output Schema**: `../metadata/output_schema.yaml`
- **Build Documentation**: `../BUILD_COMPLETE.md`
- **Demo Script**: `../DEMO.md`

## Version Control

- **Track**: `demo.py` (Jupytext-synced Python file)
- **Ignore**: `demo.ipynb` (regenerated from .py)

Sync command:
```bash
jupytext --sync demo.py
```

## License

CC-BY-4.0 - Attribution to RareResearch / Stanley Lab / DeLab Platform

---

**Last Updated**: November 3, 2025
**Version**: 1.0.0
**Maintainer**: Stanley Lab / RareResearch
