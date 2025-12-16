# AlphaMissense Variant Pathogenicity Lookup Module

## Overview

The AlphaMissense module provides efficient lookup and analysis of variant pathogenicity predictions from Google DeepMind's AlphaMissense model. This module focuses on **querying pre-computed predictions** rather than running inference, making it lightweight and fast for clinical genomics workflows.

## Scientific Background

**Missense variants** are single nucleotide changes that result in amino acid substitutions in proteins. They are the most common type of genetic variation, with ~71 million possible variants across 19,000 human protein-coding genes. Most variants have unknown clinical significance (VUS - Variants of Uncertain Significance).

**AlphaMissense** is an AI model built on AlphaFold 2 architecture that predicts pathogenicity scores (0-1 scale) for missense variants. It uses:
- Multiple sequence alignments (MSA) for evolutionary context
- Optional AlphaFold structures for spatial context
- Per-residue logits aggregated into variant-level scores

**Key Publication**:
- Cheng et al. (2023). "Accurate proteome-wide missense variant effect prediction with AlphaMissense." *Science*. DOI: 10.1126/science.adg7492

## What This Module Does

✅ **Lookup pre-computed predictions** for 71M possible human missense variants
✅ **Query by genomic coordinate** (chr:pos:ref:alt) or protein variant (UniProt:pos:ref:alt)
✅ **Batch process VCF files** with pathogenicity annotations
✅ **Gene-level analysis** (burden scores, variant prioritization)
✅ **Visualize pathogenicity** on protein structures (via PyMOL tool integration)
✅ **Compare with other predictors** (SIFT, PolyPhen-2)

❌ **Does NOT run new predictions** (model weights not released)
❌ **Does NOT require GPU** (pure data lookup, CPU-only)

## Quick Start

### 1. Installation

```bash
cd /lab/obs/modules/AlphaMissense
pip install -r requirements.txt
```

### 2. Download Pre-computed Predictions

```python
# Run setup notebook to download and index predictions (~2 GB)
jupyter lab notebooks/setup.ipynb
# This will download predictions from Google Cloud Storage and create local DuckDB index
```

### 3. Query Variants

```python
# Launch main notebook
jupyter lab notebooks/main.ipynb

# Example: Lookup single variant
from code.data import loader

# By genomic coordinate
score = loader.lookup_variant(chrom="chr17", pos=43044295, ref="G", alt="A")
print(f"Pathogenicity score: {score:.3f}")
# Output: Pathogenicity score: 0.789 (likely_pathogenic)

# By protein variant
score = loader.lookup_protein_variant(
    uniprot_id="P04637",  # TP53
    position=175,
    ref="R",
    alt="H"
)
```

### 4. Process VCF File

```python
from code.analysis import filtering

# Annotate VCF with AlphaMissense scores
results = filtering.annotate_vcf("patient_variants.vcf", output="annotated.vcf")

# Filter pathogenic variants
pathogenic = filtering.filter_pathogenic(
    results,
    threshold=0.564  # AlphaMissense recommended cutoff
)
```

## Pathogenicity Score Interpretation

AlphaMissense outputs a continuous score from 0 to 1:

| Score Range | Classification | Interpretation |
|-------------|----------------|----------------|
| **< 0.34** | likely_benign | Probably not disease-causing |
| **0.34 - 0.564** | ambiguous | Uncertain significance (VUS) |
| **> 0.564** | likely_pathogenic | Probably disease-causing |

**Note**: These thresholds are recommendations. Adjust based on your use case (clinical diagnosis vs research prioritization).

## Data Files

AlphaMissense provides pre-computed predictions in three formats:

### 1. AlphaMissense_hg38.tsv.gz (642 MB compressed)
- All possible missense variants (71M predictions)
- Canonical transcripts, hg38 genomic coordinates
- **Primary file for clinical use**

### 2. AlphaMissense_aa_substitutions.tsv.gz (1.2 GB compressed)
- All amino acid substitutions (216M predictions)
- 20k UniProt canonical isoforms
- Protein-centric (no genomic coordinates)

### 3. AlphaMissense_gene_hg38.tsv.gz (254 KB compressed)
- Gene-level average pathogenicity scores
- Mean over all possible variants per transcript

This module downloads and indexes the **hg38 file** by default.

## Usage Examples

### Example 1: Clinical Variant Interpretation

```python
# Process exome sequencing VCF
from code.analysis import filtering

# Load and annotate variants
variants = filtering.load_vcf("patient_exome.vcf")
annotated = filtering.annotate_alphamissense(variants)

# Filter likely pathogenic
pathogenic = annotated[annotated["am_class"] == "likely_pathogenic"]

# Export for clinical review
pathogenic.to_csv("pathogenic_variants.tsv", sep="\t", index=False)
```

### Example 2: Gene Burden Analysis

```python
# Analyze pathogenicity burden for gene list
from code.analysis import gene_analysis

genes = ["BRCA1", "BRCA2", "TP53", "PTEN"]
burden = gene_analysis.compute_gene_burden(genes)

# Results: mean/max pathogenicity per gene
burden.sort_values("mean_pathogenicity", ascending=False)
```

### Example 3: Protein Structure Visualization

```python
# Visualize pathogenicity on protein structure
from code.visualization import protein_viz
from lab.obs.tools.pymol import core as pymol

# Get variants for TP53
variants = loader.get_protein_variants(uniprot_id="P04637")

# Load AlphaFold structure
pymol.load_structure("P04637")

# Color by pathogenicity score
protein_viz.color_by_pathogenicity(variants, structure_id="P04637")

# Save session
pymol.save_session("TP53_pathogenicity.pse")
```

### Example 4: Comparison with Other Predictors

```python
# Compare AlphaMissense vs SIFT vs PolyPhen-2
from code.analysis import comparison

# Load variants with multiple annotations
variants = comparison.load_multi_annotated_vcf("variants_annotated.vcf")

# Compute concordance
concordance = comparison.compute_concordance(
    variants,
    predictors=["AlphaMissense", "SIFT", "PolyPhen2"]
)

# Plot agreement
comparison.plot_venn_diagram(concordance, output="predictor_comparison.png")
```

## Integration with DeLab Tools

### PyMOL Tool Integration

The AlphaMissense module integrates seamlessly with the PyMOL tool for protein structure visualization:

```python
# Color protein structure by pathogenicity
from lab.obs.tools.pymol.code import core as pymol
from code.visualization import protein_viz

# Load structure and variants
pymol.load_alphafold_structure("P04637")  # TP53
variants = loader.get_protein_variants("P04637")

# Color residues by max pathogenicity score
protein_viz.map_scores_to_structure(variants, color_scheme="RedWhiteBlue")
```

### Composition with Other Modules

```python
# Example: Integrate with variant calling pipeline
# 1. Variant calling module → VCF
# 2. AlphaMissense module → Pathogenicity annotation
# 3. Clinical reporting module → Interpretive report

from code.analysis import filtering

def variant_pipeline(bam_file, output_dir):
    # Step 1: Call variants (hypothetical module)
    vcf = variant_caller.call_variants(bam_file)

    # Step 2: Annotate with AlphaMissense
    annotated = filtering.annotate_vcf(vcf)

    # Step 3: Filter and export
    pathogenic = filtering.filter_pathogenic(annotated, threshold=0.564)
    pathogenic.to_csv(f"{output_dir}/pathogenic_variants.tsv", sep="\t")

    return pathogenic
```

## Module Structure

```
AlphaMissense/
├── README.md                          # This file
├── AGENTS.md                          # Agent operational manual
├── CLAUDE.md                          # Agent-specific context
├── BUILD_PLAN.md                      # Implementation plan
├── SCIENTIFIC_CONTEXT.md              # Detailed scientific background
├── DATA_SPECIFICATION.md              # Data formats and schemas
├── notebooks/
│   ├── setup.ipynb                    # Download and index predictions
│   ├── main.ipynb                     # Primary analysis notebook
│   ├── visualization.ipynb            # Visualization examples
│   └── jupytext.toml                  # Jupytext configuration
├── code/
│   ├── data/
│   │   ├── downloader.py              # Download from Google Cloud
│   │   ├── indexer.py                 # Index with DuckDB
│   │   └── loader.py                  # Query interface
│   ├── analysis/
│   │   ├── filtering.py               # Filter by pathogenicity
│   │   ├── gene_analysis.py           # Gene-level summaries
│   │   └── comparison.py              # Compare predictors
│   └── visualization/
│       ├── distributions.py           # Score distributions
│       ├── protein_viz.py             # Structure visualization
│       └── plots.py                   # General plotting
├── tests/
│   ├── test_loader.py                 # Query interface tests
│   ├── test_filtering.py              # Filtering tests
│   └── test_notebook.py               # Notebook execution tests
├── data/                               # Downloaded predictions (gitignored)
│   ├── hg38.duckdb                    # Indexed predictions
│   └── README.md                      # Data documentation
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project metadata
└── .gitignore                         # Git ignore patterns
```

## System Requirements

- **Python**: 3.10+
- **RAM**: 2 GB minimum (for DuckDB queries)
- **Disk**: 3 GB (2 GB for indexed data, 1 GB for downloads)
- **Compute**: CPU-only (no GPU required)
- **Network**: One-time download (~600 MB compressed)

## Dependencies

Core dependencies (see `requirements.txt` for versions):
- `duckdb` - Fast SQL queries on indexed predictions
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `biopython` - Sequence and VCF parsing
- `matplotlib`, `seaborn` - Visualization
- `tqdm` - Progress bars
- `jupytext` - Notebook synchronization
- `papermill` - Notebook parameterization

## Performance

- **Single variant lookup**: < 1 ms
- **Batch query (1000 variants)**: ~1 second
- **VCF annotation (10k variants)**: ~10 seconds
- **Gene-level analysis**: ~100 ms per gene

## Limitations

1. **No new predictions**: Model weights not released, can only query pre-computed predictions
2. **Human genome only**: Predictions limited to human proteins (hg38)
3. **Canonical transcripts**: Primary data is canonical transcripts only (isoforms available but less validated)
4. **Missense only**: Does not cover indels, splice variants, or non-coding variants
5. **Score interpretation**: Pathogenicity scores are probabilities, not clinical diagnoses

## Validation

This module uses validated test datasets:
- **ClinVar subset**: 10k variants with known clinical classifications
- **Sample VCF**: 100 test variants (mix of pathogenic/benign)

Expected concordance with ClinVar:
- Sensitivity (pathogenic): ~85%
- Specificity (benign): ~90%
- Balanced accuracy: ~87.5%

## Citation

If you use AlphaMissense predictions in your research, please cite:

```
Cheng, J., Novati, G., Pan, J., Bycroft, C., Žemgulytė, A., Applebaum, T., ... & Avsec, Ž. (2023).
Accurate proteome-wide missense variant effect prediction with AlphaMissense.
Science, 381(6664), eadg7492.
DOI: 10.1126/science.adg7492
```

## License

- **Code**: Apache 2.0 (DeLab standard)
- **AlphaMissense Predictions**: CC-BY 4.0 (Google DeepMind)

## Support and Contributing

- **Issues**: Report bugs in DeLab issue tracker
- **Documentation**: See `AGENTS.md` for agent-specific guidance
- **Scientific context**: See `SCIENTIFIC_CONTEXT.md` for detailed background

## Related Resources

- [AlphaMissense GitHub Repository](https://github.com/google-deepmind/alphamissense)
- [AlphaMissense Publication](https://doi.org/10.1126/science.adg7492)
- [ClinVar Database](https://www.ncbi.nlm.nih.gov/clinvar/)
- [gnomAD Browser](https://gnomad.broadinstitute.org/)
- [Ensembl Variant Effect Predictor](https://useast.ensembl.org/info/docs/tools/vep/index.html)

---

**Module Version**: 1.0.0
**Last Updated**: October 2025
**Part of**: DeLab L1 Laboratory System
**Module Type**: Data Lookup and Analysis (no inference)
