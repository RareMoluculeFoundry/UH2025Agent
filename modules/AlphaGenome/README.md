# AlphaGenome Regulatory Variant Analysis Module

## Overview

The AlphaGenome module provides comprehensive regulatory variant analysis using Google DeepMind's AlphaGenome API. This module enables **multimodal genomic predictions** at single base-pair resolution, helping researchers understand how genetic variants affect gene regulation, chromatin accessibility, splicing, and 3D genome organization.

## Scientific Background

**Regulatory Variants** are genetic changes that affect when, where, and how much a gene is expressed, without changing the protein sequence itself. These variants:
- Comprise ~98% of the human genome (non-coding regions)
- Are enriched in GWAS hits for complex diseases
- Are challenging to interpret (no clear "genetic code" for regulation)

**AlphaGenome** is Google DeepMind's unifying AI model for deciphering regulatory DNA sequences. It can:
- Analyze sequences up to **1 million base pairs** in length
- Predict multiple regulatory modalities simultaneously
- Achieve state-of-the-art variant effect prediction
- Provide single base-pair resolution predictions

**Key Publication**:
- Avsec et al. (2025). "AlphaGenome: advancing regulatory variant effect prediction with a unified DNA sequence model." *bioRxiv*. DOI: 10.1101/2025.06.25.661532

## What This Module Does

✅ **Predict variant effects** on gene expression, chromatin, and splicing
✅ **Multimodal predictions** (RNA-seq, ATAC-seq, ChIP-seq, Hi-C, splice sites)
✅ **eQTL analysis** (expression quantitative trait loci)
✅ **Splice variant interpretation** (splice site disruption)
✅ **Regulatory landscape exploration** (genome-wide predictions)
✅ **Tissue-specific predictions** (100+ cell types/tissues via UBERON ontology)
✅ **In silico mutagenesis** (systematic variant scanning)

❌ **Does NOT run local inference** (API-only, no local model)
❌ **Does NOT handle unlimited queries** (rate-limited free tier)
❌ **Does NOT provide pathogenicity scores** (predicts molecular effects, not disease)

## Quick Start

### 1. Get API Key

Request API key from: https://deepmind.google.com/science/alphagenome

Free for non-commercial use (rate-limited).

### 2. Installation

```bash
cd /lab/obs/modules/AlphaGenome
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Create API key file (gitignored)
echo "ALPHAGENOME_API_KEY=your_api_key_here" > config/api_key.env

# Or set environment variable
export ALPHAGENOME_API_KEY="your_api_key_here"
```

### 4. Run Analysis

```python
# Launch main notebook
jupyter lab notebooks/main.ipynb

# Example: Predict variant effect
from alphagenome.data import genome
from alphagenome.models import dna_client
import os

# Load API key
API_KEY = os.getenv("ALPHAGENOME_API_KEY")
model = dna_client.create(API_KEY)

# Define variant
variant = genome.Variant(
    chromosome='chr22',
    position=36201698,
    reference_bases='A',
    alternate_bases='C'
)

# Define context window
interval = genome.Interval(
    chromosome='chr22',
    start=36101698,    # 100 KB upstream
    end=36301698       # 100 KB downstream
)

# Predict effect on gene expression (liver)
outputs = model.predict_variant(
    interval=interval,
    variant=variant,
    ontology_terms=['UBERON:0002107'],  # Liver
    requested_outputs=[dna_client.OutputType.RNA_SEQ]
)

# Compare reference vs alternate
effect = outputs.alternate.rna_seq.values - outputs.reference.rna_seq.values
print(f"Expression change: {effect.max():.3f}")
```

## Multimodal Predictions

AlphaGenome provides predictions across multiple regulatory modalities:

### Gene Expression
- **RNA-seq**: Gene expression levels (transcripts per million)
- **CAGE**: Transcription start site activity
- **PRO-CAP**: Nascent transcription (promoter-proximal)

### Chromatin Accessibility
- **ATAC-seq**: Open chromatin regions
- **DNase-seq**: DNase hypersensitivity (alternative accessibility assay)
- **ChIP-seq (Histones)**: Histone modifications (H3K4me3, H3K27ac, etc.)
- **ChIP-seq (TFs)**: Transcription factor binding

### Splicing
- **Splice Sites**: Donor and acceptor site predictions
- **Splice Site Usage**: Frequency of splice site usage
- **Splice Junctions**: Full junction predictions with read counts

### 3D Genome Organization
- **Contact Maps**: Hi-C-like chromatin interaction predictions

## Usage Examples

### Example 1: eQTL Analysis

```python
# Analyze expression quantitative trait locus (eQTL)
from code.analysis import eqtl_analysis

# Load GWAS variant near gene
variant = genome.Variant(
    chromosome='chr1',
    position=12345678,
    reference_bases='G',
    alternate_bases='A'
)

# Define interval around gene
interval = genome.Interval(
    chromosome='chr1',
    start=12245678,    # 100 KB context
    end=12445678
)

# Predict expression effect in multiple tissues
tissues = ['UBERON:0002107', 'UBERON:0002048', 'UBERON:0000955']  # Liver, Lung, Brain
results = eqtl_analysis.predict_variant_effect_multitissue(
    variant, interval, tissues
)

# Visualize expression changes
eqtl_analysis.plot_tissue_effects(results, output="eqtl_effect.png")
```

### Example 2: Splice Variant Interpretation

```python
# Analyze variant near splice site
from code.analysis import splice_effects

variant = genome.Variant(
    chromosome='chr7',
    position=55241707,
    reference_bases='G',
    alternate_bases='A'
)

# Predict splice site disruption
splice_effect = splice_effects.predict_splice_disruption(
    variant,
    context_size=500_000  # 500 KB context
)

# Visualize splice site usage
splice_effects.plot_splice_junctions(
    splice_effect,
    output="splice_disruption.png"
)
```

### Example 3: Regulatory Landscape

```python
# Explore regulatory features across genomic region
from code.analysis import regulatory_landscape

# Define 1 MB region
interval = genome.Interval(
    chromosome='chr11',
    start=5200000,
    end=6200000      # 1 MB region
)

# Predict all modalities
landscape = regulatory_landscape.predict_region(
    interval,
    ontology_terms=['UBERON:0002107'],  # Liver
    modalities=['rna_seq', 'atac', 'chip_histone', 'contact_maps']
)

# Visualize multimodal landscape
regulatory_landscape.plot_multimodal(
    landscape,
    genes=genes_in_region,
    output="regulatory_landscape.png"
)
```

### Example 4: In Silico Mutagenesis

```python
# Systematically mutate all positions in promoter
from code.analysis import ism_analysis

# Define promoter region
promoter = genome.Interval(
    chromosome='chr17',
    start=43044000,
    end=43046000      # 2 KB promoter
)

# Scan all possible mutations
ism_results = ism_analysis.scan_mutations(
    interval=promoter,
    ontology_terms=['UBERON:0002107'],
    modality='rna_seq',
    gene_id='ENSG00000012048'  # BRCA1
)

# Identify critical positions
critical_positions = ism_analysis.find_critical_mutations(
    ism_results,
    threshold=0.5  # 50% expression change
)
```

## Available Modalities and Output Types

| Category | Output Type | Description | Use Case |
|----------|-------------|-------------|----------|
| **Expression** | RNA_SEQ | Gene expression | eQTL analysis |
| | CAGE | TSS activity | Promoter variants |
| | PROCAP | Nascent transcription | Transcription regulation |
| **Chromatin** | ATAC | Open chromatin | Regulatory element discovery |
| | DNASE | DNase hypersensitivity | Enhancer/promoter activity |
| | CHIP_HISTONE | Histone modifications | Epigenetic state |
| | CHIP_TF | TF binding | Binding site disruption |
| **Splicing** | SPLICE_SITES | Donor/acceptor | Splice site variants |
| | SPLICE_SITE_USAGE | Usage frequency | Alternative splicing |
| | SPLICE_JUNCTIONS | Junction reads | Splice event quantification |
| **3D Genome** | CONTACT_MAPS | Chromatin contacts | TAD boundary variants |

## Cell Types and Tissues

AlphaGenome supports predictions for 100+ cell types/tissues using the UBERON ontology:

**Common Tissues**:
| Tissue | UBERON Term | Use Case |
|--------|-------------|----------|
| Liver | UBERON:0002107 | Metabolic variants |
| Brain | UBERON:0000955 | Neurological variants |
| Heart | UBERON:0000948 | Cardiovascular variants |
| Lung | UBERON:0002048 | Respiratory variants |
| Kidney | UBERON:0002113 | Renal variants |
| Blood | UBERON:0000178 | Hematological variants |

**Cell Types**:
| Cell Type | UBERON Term | Use Case |
|-----------|-------------|----------|
| Hepatocyte | UBERON:0000026 | Liver-specific |
| Neuron | UBERON:0000540 | Brain-specific |
| Cardiomyocyte | UBERON:0002349 | Heart-specific |
| T cell | CL:0000084 | Immune system |
| B cell | CL:0000236 | Immune system |

Full ontology: https://www.ebi.ac.uk/ols/ontologies/uberon

## Context Window Sizes

AlphaGenome supports variable context windows:

| Size | Bases | Use Case |
|------|-------|----------|
| 2 KB | 2,048 | Single exon/promoter |
| 16 KB | 16,384 | Gene body + promoter |
| 100 KB | 131,072 | Gene cluster |
| 500 KB | 524,288 | Regulatory domain |
| 1 MB | 1,048,576 | TAD (topological domain) |

**Guidance**:
- Larger windows → more context but slower
- Start with 100 KB for most variants
- Use 1 MB for distal enhancer variants

## Module Structure

```
AlphaGenome/
├── README.md                          # This file
├── AGENTS.md                          # Agent operational manual
├── CLAUDE.md                          # Agent-specific context
├── BUILD_PLAN.md                      # Implementation plan
├── SCIENTIFIC_CONTEXT.md              # Detailed scientific background
├── API_CONTEXT.md                     # API usage and best practices
├── DATA_SPECIFICATION.md              # Data formats and schemas
├── notebooks/
│   ├── main.ipynb                     # Primary analysis notebook
│   ├── visualization.ipynb            # Visualization examples
│   └── jupytext.toml                  # Jupytext configuration
├── code/
│   ├── api/
│   │   ├── client.py                  # API wrapper with caching
│   │   ├── cache.py                   # Result caching (Zarr)
│   │   ├── retry.py                   # Retry logic + rate limiting
│   │   └── batch.py                   # Batch processing
│   ├── analysis/
│   │   ├── eqtl_analysis.py           # Expression QTL analysis
│   │   ├── splice_effects.py          # Splicing impact analysis
│   │   ├── regulatory_landscape.py    # Regional analysis
│   │   └── ism_analysis.py            # In silico mutagenesis
│   ├── visualization/
│   │   ├── tracks.py                  # Track plotting
│   │   ├── heatmaps.py                # Multi-variant heatmaps
│   │   └── exports.py                 # BigWig, BED exports
│   └── data/
│       ├── gencode.py                 # Gene annotation loading
│       └── ontology.py                # Cell type/tissue ontologies
├── tests/
│   ├── test_api.py                    # API client tests
│   ├── test_cache.py                  # Caching tests
│   └── test_notebook.py               # Notebook execution tests
├── cache/                              # Cached API results (gitignored)
│   └── predictions.zarr               # Zarr format
├── config/
│   ├── api_key.env.template           # API key template
│   └── api_key.env                    # Actual key (gitignored)
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
└── .gitignore                         # Git ignore patterns
```

## System Requirements

- **Python**: 3.10+
- **RAM**: 4 GB minimum (for caching and data processing)
- **Disk**: 10 GB (for cached predictions)
- **Compute**: CPU-only (API calls, no local inference)
- **Network**: Stable internet connection (API access)
- **API Key**: Free for non-commercial use (rate-limited)

## Dependencies

Core dependencies (see `requirements.txt` for versions):
- `alphagenome` - Official AlphaGenome Python package
- `grpcio` - gRPC client for API
- `zarr` - Efficient caching format
- `pandas`, `numpy` - Data manipulation
- `matplotlib`, `seaborn` - Visualization
- `anndata` - Single-cell style data format (ISM results)
- `tqdm` - Progress bars
- `jupytext` - Notebook synchronization

## API Rate Limits and Caching

**Rate Limits**:
- Free tier: Suitable for **1000s of predictions**
- NOT suitable for **>1M predictions** (contact DeepMind for commercial access)
- Dynamic rate limits (adjust based on demand)
- Built-in retry logic with exponential backoff

**Caching Strategy**:
```python
# Results are automatically cached
from code.api import client

model = client.create_cached(API_KEY, cache_dir="cache/predictions.zarr")

# First call: API request
outputs1 = model.predict_variant(interval, variant, ontology_terms)

# Second call: Cache hit (instant, no API call)
outputs2 = model.predict_variant(interval, variant, ontology_terms)
```

**Cache Benefits**:
- Avoid redundant API calls
- Instant retrieval of previous results
- Persist across sessions
- ~100 MB per 1000 predictions

## Visualization

### Built-in Plotting

```python
from alphagenome.visualization import plot_components
import matplotlib.pyplot as plt

# Plot tracks with gene annotation
plot_components.plot([
    plot_components.OverlaidTracks(
        tdata={'REF': ref_track, 'ALT': alt_track},
        colors={'REF': 'dimgrey', 'ALT': 'red'}
    ),
    plot_components.GeneAnnotation(
        genes=genes,
        interval=interval
    ),
    plot_components.VariantAnnotation(
        variants=[variant]
    )
], interval=interval)

plt.savefig("variant_effect.png", dpi=300)
```

### Export Formats

- **BigWig**: Genome browser tracks (UCSC, IGV)
- **BED**: Peak annotations
- **TSV**: Variant scores
- **Parquet**: Efficient data storage
- **PNG/PDF**: Publication-ready figures

## Citation

If you use AlphaGenome in your research, please cite:

```
Avsec, Ž., et al. (2025). AlphaGenome: advancing regulatory variant effect prediction
with a unified DNA sequence model. bioRxiv, 2025.06.25.661532.
DOI: 10.1101/2025.06.25.661532
```

## License

- **Code**: Apache 2.0 (DeLab standard)
- **AlphaGenome API**: Free for non-commercial use (Google DeepMind)
- **Predictions**: Check AlphaGenome terms of service

## Support and Contributing

- **Issues**: Report bugs in DeLab issue tracker
- **Documentation**: See `AGENTS.md` for agent-specific guidance
- **Scientific context**: See `SCIENTIFIC_CONTEXT.md` for detailed background
- **API details**: See `API_CONTEXT.md` for API usage patterns

## Related Resources

- [AlphaGenome Blog Post](https://deepmind.google/discover/blog/alphagenome-ai-for-better-understanding-the-genome/)
- [AlphaGenome GitHub](https://github.com/google-deepmind/alphagenome)
- [AlphaGenome API Docs](https://deepmind.google.com/science/alphagenome)
- [GENCODE Gene Annotations](https://www.gencodegenes.org/)
- [UBERON Ontology](https://www.ebi.ac.uk/ols/ontologies/uberon)

---

**Module Version**: 1.0.0
**Last Updated**: October 2025
**Part of**: DeLab L1 Laboratory System
**Module Type**: API-Based Regulatory Analysis (no local inference)
