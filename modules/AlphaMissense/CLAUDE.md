# Agent Context: AlphaMissense Variant Pathogenicity Lookup Module

## Purpose

This file provides AI agents (particularly Claude Code) with technical context for building and maintaining the AlphaMissense module. It complements `AGENTS.md` (operational instructions) with implementation-level details.

## Module Classification

**Type**: Data Lookup and Analysis Module (Simplified)
**Compute**: CPU-only (no GPU, no ML inference)
**Dependencies**: Pre-computed predictions (downloaded once)
**Backend Detection**: NOT REQUIRED (no multi-backend support needed)
**Deployment**: Simplified (Docker optional, Ray/Kubeflow optional for batch)

## Adaptation from DeLab Module Standard

This module is **simplified** from the full DeLab module standard because:

1. **No inference**: Queries pre-computed predictions (no model weights, no training)
2. **No backend detection**: CPU-only operations (no CUDA/ROCm/MLX/MPS)
3. **No compute backends**: Pure data operations (DuckDB queries, pandas)
4. **Lightweight deployment**: Minimal containerization needs

### What to SKIP from Standard Template

❌ **backends/manager.py**: No multi-backend detection needed
❌ **backends/BACKENDS.md**: CPU-only module
❌ **GPU tags in notebooks**: `gpu-required` tag not applicable
❌ **models/MODEL_REGISTRY.yaml**: No model weights to manage
❌ **kubeflow/**: Optional (not needed for typical use)

### What to KEEP from Standard Template

✅ **Jupytext synchronization**: `.ipynb` ↔ `.py` pairing
✅ **Literate programming**: 1:2-3 code:docs ratio
✅ **Cell tagging**: `parameters`, `export`, `agent-configurable`
✅ **AGENTS.md**: Operational manual following Anthropic patterns
✅ **Docker/**: Minimal containerization (Python + dependencies)
✅ **tests/**: Comprehensive test suite
✅ **ray/**: Optional, for massive batch processing

## Technical Architecture

### Data Flow

```
[Google Cloud Storage]
         ↓ (one-time download)
[AlphaMissense_hg38.tsv.gz] (642 MB compressed)
         ↓ (extract & index)
   [DuckDB database] (2 GB)
         ↓ (SQL queries)
    [Query Results]
         ↓ (pandas/numpy)
   [Analysis & Viz]
```

### Key Components

#### 1. Data Layer (`code/data/`)

**downloader.py**:
```python
def download_predictions(target="hg38", force=False):
    """
    Download pre-computed predictions from Google Cloud Storage.

    Args:
        target: "hg38" (genomic) or "aa_substitutions" (protein-centric)
        force: Re-download if file exists

    Downloads:
        - AlphaMissense_hg38.tsv.gz (642 MB) → data/hg38.tsv.gz
    """
```

**indexer.py**:
```python
def create_index(tsv_path, db_path):
    """
    Index TSV file with DuckDB for fast queries.

    Creates:
        - Table: variants(CHROM, POS, REF, ALT, uniprot_id, am_pathogenicity, am_class)
        - Index: (CHROM, POS, REF, ALT)
        - Index: (uniprot_id, protein_variant)

    Performance:
        - ~1 ms per variant lookup
        - ~1000 variants/sec batch query
    """
```

**loader.py**:
```python
import duckdb

class AlphaMissenseDB:
    def __init__(self, db_path="data/hg38.duckdb"):
        self.conn = duckdb.connect(db_path, read_only=True)

    def lookup_variant(self, chrom, pos, ref, alt):
        """Query by genomic coordinate."""
        query = """
            SELECT am_pathogenicity, am_class
            FROM variants
            WHERE CHROM=? AND POS=? AND REF=? AND ALT=?
        """
        result = self.conn.execute(query, [chrom, pos, ref, alt]).fetchone()
        return result if result else None

    def lookup_protein_variant(self, uniprot_id, position, ref, alt):
        """Query by protein variant."""
        protein_variant = f"{ref}{position}{alt}"
        query = """
            SELECT am_pathogenicity, am_class
            FROM variants
            WHERE uniprot_id=? AND protein_variant=?
        """
        result = self.conn.execute(query, [uniprot_id, protein_variant]).fetchone()
        return result if result else None
```

#### 2. Analysis Layer (`code/analysis/`)

**filtering.py**:
```python
def annotate_vcf(input_vcf, output_vcf, threshold=0.564):
    """
    Annotate VCF with AlphaMissense scores.

    Adds INFO fields:
        - AM_SCORE: Pathogenicity score (0-1)
        - AM_CLASS: Classification (likely_benign/ambiguous/likely_pathogenic)
    """

def filter_pathogenic(variants_df, threshold=0.564):
    """Filter variants above pathogenicity threshold."""
    return variants_df[variants_df["am_pathogenicity"] >= threshold]
```

**gene_analysis.py**:
```python
def compute_gene_burden(genes, metric="mean"):
    """
    Compute pathogenicity burden per gene.

    Args:
        genes: List of gene symbols or Ensembl IDs
        metric: "mean", "max", "weighted_mean"

    Returns:
        DataFrame with columns: gene, burden_score, n_variants
    """
```

#### 3. Visualization Layer (`code/visualization/`)

**protein_viz.py**:
```python
def color_by_pathogenicity(variants_df, structure_id, pymol_instance):
    """
    Color protein structure by pathogenicity scores.

    Integration with PyMOL tool:
        1. Load structure via PyMOL tool
        2. Map variants to residue positions
        3. Color by score (blue=benign, red=pathogenic)
    """
```

### Database Schema

**Table: variants**

| Column | Type | Description |
|--------|------|-------------|
| CHROM | VARCHAR | Chromosome (chr1-22, chrX, chrY, chrM) |
| POS | INTEGER | Position (1-based, hg38) |
| REF | VARCHAR | Reference allele (A/C/G/T) |
| ALT | VARCHAR | Alternate allele (A/C/G/T) |
| genome | VARCHAR | Reference genome ("hg38") |
| uniprot_id | VARCHAR | UniProt protein ID |
| transcript_id | VARCHAR | Ensembl transcript ID |
| protein_variant | VARCHAR | Protein variant (e.g., "V175H") |
| am_pathogenicity | FLOAT | Pathogenicity score (0-1) |
| am_class | VARCHAR | Classification (likely_benign/ambiguous/likely_pathogenic) |

**Indexes**:
- PRIMARY KEY: (CHROM, POS, REF, ALT)
- INDEX: (uniprot_id, protein_variant)
- INDEX: (am_pathogenicity) for fast filtering

## AlphaMissense Background

### Model Architecture (Reference Only)

**Not Implemented** (model weights not released):

- Base: AlphaFold 2.3.2 architecture
- Input: Protein sequence + MSA + optional structure
- Output: Per-residue logits → variant pathogenicity score
- Training: Supervised on known pathogenic/benign variants

**Why Reference Only**:
- Model weights NOT publicly available
- Cannot run new predictions
- Can only query pre-computed predictions

### Pre-computed Predictions

**Available Files** (from https://console.cloud.google.com/storage/browser/dm_alphamissense):

1. **AlphaMissense_hg38.tsv.gz** (642 MB compressed, 2.8 GB uncompressed)
   - All possible missense variants (71M)
   - Canonical transcripts, hg38 coordinates
   - **Use this for module** ✅

2. **AlphaMissense_aa_substitutions.tsv.gz** (1.2 GB compressed)
   - All amino acid substitutions (216M)
   - Protein-centric, no genomic coordinates
   - Optional, for protein-level analysis

3. **AlphaMissense_gene_hg38.tsv.gz** (254 KB compressed)
   - Gene-level average scores
   - Fast lookup for gene burden

### Score Interpretation

**Continuous Score** (0-1):
- 0.0 = Definitely benign
- 0.5 = Uncertain
- 1.0 = Definitely pathogenic

**Thresholds** (from publication):
- < 0.34: likely_benign
- 0.34 - 0.564: ambiguous (VUS)
- > 0.564: likely_pathogenic

**Calibration**:
- Trained on ClinVar variants
- Balanced accuracy ~87.5%
- Sensitivity ~85%, Specificity ~90%

## Integration Patterns

### With PyMOL Tool

```python
# Pattern: Structure visualization with pathogenicity
from code.data import loader
from code.visualization import protein_viz
from lab.obs.tools.pymol.code import core as pymol

# 1. Get variants for protein
variants = loader.get_protein_variants("P04637")  # TP53

# 2. Load AlphaFold structure
pymol.load_alphafold_structure("P04637")

# 3. Color by pathogenicity
protein_viz.color_by_pathogenicity(variants, "P04637", pymol)

# 4. Save visualization
pymol.save_session("TP53_pathogenicity.pse")
pymol.save_image("TP53_pathogenicity.png", width=1920, height=1080)
```

### With Variant Calling Pipelines

```python
# Pattern: Post-calling annotation
def annotate_called_variants(vcf_path):
    from code.analysis import filtering

    # Annotate with AlphaMissense
    annotated = filtering.annotate_vcf(vcf_path, "annotated.vcf")

    # Filter pathogenic
    pathogenic = filtering.filter_pathogenic(annotated, threshold=0.564)

    return pathogenic
```

### With Gene Prioritization

```python
# Pattern: Gene burden analysis
from code.analysis import gene_analysis

# Candidate genes from GWAS or linkage
candidate_genes = ["GENE1", "GENE2", "GENE3"]

# Compute burden
burden = gene_analysis.compute_gene_burden(
    candidate_genes,
    metric="weighted_mean",
    weights="gnomad_frequency"
)

# Rank by burden
ranked = burden.sort_values("burden_score", ascending=False)
```

## Implementation Guidance

### For Building the Module

**Phase 1: Data Infrastructure** (Day 1, 4 hours)
1. Implement `code/data/downloader.py`
   - Use `gsutil` or `requests` for Google Cloud Storage
   - Add progress bars with `tqdm`
   - Implement resume capability
2. Implement `code/data/indexer.py`
   - Use DuckDB for indexing
   - Create appropriate indexes for fast queries
   - Validate data integrity
3. Implement `code/data/loader.py`
   - Query interface for genomic and protein variants
   - Batch query support
   - Caching layer

**Phase 2: Analysis Functions** (Day 2, 4 hours)
1. Implement `code/analysis/filtering.py`
   - VCF annotation (using `pysam` or `cyvcf2`)
   - Threshold-based filtering
   - Batch processing
2. Implement `code/analysis/gene_analysis.py`
   - Gene-level burden calculations
   - Variant aggregation
   - Statistical summaries

**Phase 3: Notebooks** (Day 3, 6 hours)
1. Create `notebooks/setup.ipynb`
   - Download predictions
   - Index database
   - Validate installation
2. Create `notebooks/main.ipynb`
   - Load variants (VCF/TSV/manual)
   - Query AlphaMissense
   - Filter and visualize
   - Export results
   - Follow 1:2-3 code:docs ratio
3. Create `notebooks/visualization.ipynb`
   - Score distributions
   - Gene burden plots
   - Protein structure integration

**Phase 4: Testing & Documentation** (Day 4, 6 hours)
1. Write unit tests
   - `tests/test_loader.py`
   - `tests/test_filtering.py`
   - `tests/test_gene_analysis.py`
2. Write integration tests
   - ClinVar concordance
   - Large VCF processing
3. Test notebook execution with `pytest-nbmake`
4. Complete documentation (README, AGENTS, this file)

**Phase 5: Visualization & Polish** (Day 5, 6 hours)
1. Implement `code/visualization/protein_viz.py`
   - PyMOL integration
   - Structure coloring
2. Implement `code/visualization/plots.py`
   - Score distributions
   - Gene burden plots
   - Publication-ready figures
3. Polish notebooks (add examples, improve docs)
4. Create sample datasets

### Jupytext Configuration

**notebooks/jupytext.toml**:
```toml
formats = "ipynb,py:percent"
notebook_metadata_filter = "kernelspec,jupytext"
cell_metadata_filter = "tags,execution_group,depends_on,-ExecuteTime"
```

**Cell Tags**:
- `parameters`: Papermill parameters (for automation)
- `export`: Export functions to `.py` module (nbdev style)
- `agent-configurable`: AI agents can modify this cell

**Example Cell**:
```python
# %% tags=["parameters", "agent-configurable"]
# Configurable parameters
input_vcf = "variants.vcf"
threshold = 0.564  # Pathogenicity cutoff
output_format = "tsv"  # "tsv", "vcf", or "csv"
```

## Testing Strategy

### Unit Tests

**test_loader.py**:
```python
def test_variant_lookup():
    db = loader.AlphaMissenseDB()
    score = db.lookup_variant("chr17", 43044295, "G", "A")
    assert score is not None
    assert 0 <= score["am_pathogenicity"] <= 1

def test_protein_lookup():
    db = loader.AlphaMissenseDB()
    score = db.lookup_protein_variant("P04637", 175, "R", "H")
    assert score is not None
```

**test_filtering.py**:
```python
def test_vcf_annotation():
    annotated = filtering.annotate_vcf(
        "tests/fixtures/sample.vcf",
        "/tmp/annotated.vcf"
    )
    assert os.path.exists("/tmp/annotated.vcf")

def test_pathogenic_filter():
    df = pd.DataFrame({
        "am_pathogenicity": [0.1, 0.5, 0.9]
    })
    pathogenic = filtering.filter_pathogenic(df, threshold=0.564)
    assert len(pathogenic) == 1
```

### Integration Tests

**test_clinvar_concordance.py**:
```python
def test_clinvar_concordance():
    """Validate against ClinVar gold standard."""
    clinvar = load_clinvar_subset()  # 10k variants

    # Annotate with AlphaMissense
    annotated = filtering.annotate_dataframe(clinvar)

    # Compute concordance
    sensitivity = compute_sensitivity(annotated)
    specificity = compute_specificity(annotated)

    # AlphaMissense publication reports ~85% / ~90%
    assert sensitivity > 0.80
    assert specificity > 0.85
```

### Notebook Tests

```bash
# Execute notebooks end-to-end
pytest --nbmake notebooks/main.ipynb
pytest --nbmake notebooks/visualization.ipynb
```

## Performance Optimization

### Query Optimization

1. **Use indexes** (DuckDB auto-creates on primary key)
2. **Batch queries** (10-100x faster than individual)
3. **Enable caching** (avoid repeated queries)
4. **Use SSD storage** (faster I/O)

**Example Batch Query**:
```python
# Instead of:
for variant in variants:
    score = db.lookup_variant(variant.chrom, variant.pos, variant.ref, variant.alt)

# Do:
scores = db.lookup_variants_batch(variants)  # 100x faster
```

### Memory Management

For large VCF files (>100k variants):
```python
# Stream processing (avoid loading entire VCF)
def annotate_vcf_streaming(input_vcf, output_vcf, batch_size=1000):
    with open(input_vcf) as infile, open(output_vcf, 'w') as outfile:
        for batch in read_vcf_batches(infile, batch_size):
            annotated = db.lookup_variants_batch(batch)
            write_vcf_batch(outfile, annotated)
```

## Troubleshooting for Builders

### Issue: DuckDB installation fails
**Solution**: DuckDB requires Python 3.7+, install with `pip install duckdb==0.9.1`

### Issue: Download from Google Cloud fails
**Solution**: Use `requests` with retry logic, or pre-download with `gsutil`

### Issue: Jupytext sync conflicts
**Solution**: Always edit `.ipynb`, let Jupytext generate `.py`. Never edit both.

### Issue: PyMOL integration fails
**Solution**: Ensure PyMOL tool is installed at `/lab/obs/tools/pymol/`

## Version Control

**.gitignore**:
```
# Ignore data files
data/*.duckdb
data/*.tsv
data/*.tsv.gz

# Ignore notebooks (track .py only)
*.ipynb
!notebooks/example.ipynb  # Keep template

# Ignore cache
__pycache__/
.pytest_cache/
.ipynb_checkpoints/

# Ignore outputs
output/
*.pse
*.png
```

## Related Documentation

- **README.md**: Human-readable overview
- **AGENTS.md**: Operational manual for AI agents
- **BUILD_PLAN.md**: Detailed implementation roadmap
- **SCIENTIFIC_CONTEXT.md**: Scientific background and references
- **DATA_SPECIFICATION.md**: Data formats and schemas

---

**This context file follows Anthropic's best practices for effective context engineering. It provides implementation-level guidance for AI agents building the AlphaMissense module.**

**Version**: 1.0.0
**Last Updated**: October 2025
