# Build Plan: AlphaMissense Variant Pathogenicity Lookup Module

## Overview

This document provides a comprehensive implementation plan for building the AlphaMissense module from scratch. It includes phases, milestones, checkpoints, validation criteria, and test data specifications.

## Project Timeline

**Total Estimated Time**: 26 hours (3-4 days for Minimal Viable Product)

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1: Data Infrastructure | 4 hours | Download, indexing, query interface |
| Phase 2: Analysis Functions | 4 hours | VCF annotation, filtering, gene analysis |
| Phase 3: Notebook Development | 6 hours | Interactive notebooks with literate programming |
| Phase 4: Testing & Documentation | 6 hours | Unit tests, integration tests, docs |
| Phase 5: Visualization & Polish | 6 hours | PyMOL integration, plots, examples |

**Production-Grade Extension**: Add 1-2 weeks for:
- Advanced visualizations
- CLI interface
- MCP server
- Ray distributed processing
- Comprehensive edge case handling

## Phase 1: Data Infrastructure (Day 1, 4 hours)

### Objectives
- Download AlphaMissense predictions from Google Cloud Storage
- Index predictions with DuckDB for fast queries
- Implement query interface for variants

### Milestones

#### Milestone 1.1: Data Downloader (1 hour)

**File**: `code/data/downloader.py`

**Requirements**:
```python
def download_predictions(
    target: str = "hg38",
    output_dir: str = "data/",
    force: bool = False
) -> str:
    """
    Download AlphaMissense predictions from Google Cloud Storage.

    Args:
        target: "hg38" (genomic) or "aa_substitutions" (protein)
        output_dir: Directory to save downloaded file
        force: Re-download even if file exists

    Returns:
        Path to downloaded file

    GCS URLs:
        - hg38: gs://dm_alphamissense/AlphaMissense_hg38.tsv.gz (642 MB)
        - aa_substitutions: gs://dm_alphamissense/AlphaMissense_aa_substitutions.tsv.gz (1.2 GB)
    """
```

**Implementation Steps**:
1. Check if file exists (skip if not `force`)
2. Use `requests` or `gsutil` to download from Google Cloud
3. Add progress bar with `tqdm`
4. Validate file size and checksum
5. Handle network errors with retry logic

**Validation Checkpoint**:
```python
# Test download
path = downloader.download_predictions(target="hg38")
assert os.path.exists(path)
assert os.path.getsize(path) > 600_000_000  # >600 MB
```

#### Milestone 1.2: Data Indexer (1.5 hours)

**File**: `code/data/indexer.py`

**Requirements**:
```python
def create_index(
    tsv_path: str,
    db_path: str = "data/hg38.duckdb"
) -> None:
    """
    Create DuckDB index from AlphaMissense TSV file.

    Args:
        tsv_path: Path to AlphaMissense_hg38.tsv.gz
        db_path: Path to output DuckDB database

    Creates:
        - Table: variants (CHROM, POS, REF, ALT, ..., am_pathogenicity, am_class)
        - Index on (CHROM, POS, REF, ALT)
        - Index on (uniprot_id, protein_variant)
    """
```

**Implementation Steps**:
1. Read compressed TSV with DuckDB (handles gzip automatically)
2. Create table schema matching AlphaMissense format
3. Create indexes for fast lookup
4. Validate record count (should be ~71M for hg38)
5. Add metadata table (data version, creation date)

**Validation Checkpoint**:
```python
# Test indexing
indexer.create_index("data/AlphaMissense_hg38.tsv.gz", "data/hg38.duckdb")
conn = duckdb.connect("data/hg38.duckdb")
count = conn.execute("SELECT COUNT(*) FROM variants").fetchone()[0]
assert count > 70_000_000  # ~71M variants
conn.close()
```

#### Milestone 1.3: Query Interface (1.5 hours)

**File**: `code/data/loader.py`

**Requirements**:
```python
class AlphaMissenseDB:
    def __init__(self, db_path: str = "data/hg38.duckdb"):
        """Initialize database connection."""

    def lookup_variant(self, chrom: str, pos: int, ref: str, alt: str) -> dict:
        """Lookup variant by genomic coordinate."""

    def lookup_protein_variant(self, uniprot_id: str, position: int, ref: str, alt: str) -> dict:
        """Lookup variant by protein position."""

    def lookup_variants_batch(self, variants: List[Variant]) -> pd.DataFrame:
        """Batch lookup for multiple variants (much faster)."""

    def get_gene_variants(self, gene_id: str, source: str = "ensembl") -> pd.DataFrame:
        """Get all variants for a gene."""

    def variant_exists(self, chrom: str, pos: int, ref: str, alt: str) -> bool:
        """Check if variant exists in database."""
```

**Implementation Steps**:
1. Create database connection class
2. Implement single variant lookup (genomic and protein)
3. Implement batch lookup (10-100x faster)
4. Add caching layer (LRU cache for repeated queries)
5. Error handling for missing variants

**Validation Checkpoint**:
```python
# Test query interface
db = loader.AlphaMissenseDB()

# Test known pathogenic variant (TP53 R175H)
result = db.lookup_variant("chr17", 7577548, "C", "T")
assert result is not None
assert result["am_pathogenicity"] > 0.7  # Known pathogenic

# Test batch query
variants = [...]  # List of 1000 variants
results = db.lookup_variants_batch(variants)
assert len(results) <= len(variants)  # Some may not exist
```

### Phase 1 Deliverables
- ✅ `code/data/downloader.py` (tested)
- ✅ `code/data/indexer.py` (tested)
- ✅ `code/data/loader.py` (tested)
- ✅ DuckDB database (`data/hg38.duckdb`)
- ✅ Unit tests for all components

---

## Phase 2: Analysis Functions (Day 2, 4 hours)

### Objectives
- Implement VCF annotation with AlphaMissense scores
- Create filtering and prioritization functions
- Build gene-level burden analysis

### Milestones

#### Milestone 2.1: VCF Annotation (2 hours)

**File**: `code/analysis/filtering.py`

**Requirements**:
```python
def annotate_vcf(
    input_vcf: str,
    output_vcf: str,
    threshold: float = 0.564,
    batch_size: int = 1000
) -> pd.DataFrame:
    """
    Annotate VCF with AlphaMissense scores.

    Adds INFO fields:
        - AM_SCORE: Pathogenicity score (0-1)
        - AM_CLASS: Classification (likely_benign/ambiguous/likely_pathogenic)
    """

def annotate_dataframe(
    variants_df: pd.DataFrame,
    chrom_col: str = "CHROM",
    pos_col: str = "POS",
    ref_col: str = "REF",
    alt_col: str = "ALT"
) -> pd.DataFrame:
    """Annotate pandas DataFrame with AlphaMissense scores."""

def filter_pathogenic(
    variants_df: pd.DataFrame,
    threshold: float = 0.564
) -> pd.DataFrame:
    """Filter variants above pathogenicity threshold."""
```

**Implementation Steps**:
1. Parse VCF file (use `pysam` or `cyvcf2`)
2. Extract variants (CHROM, POS, REF, ALT)
3. Batch query AlphaMissense database
4. Add annotations to VCF INFO field
5. Write annotated VCF
6. Handle multi-allelic sites

**Validation Checkpoint**:
```python
# Test VCF annotation
annotated = filtering.annotate_vcf(
    "tests/fixtures/sample.vcf",
    "/tmp/annotated.vcf"
)

# Check annotations exist
with open("/tmp/annotated.vcf") as f:
    for line in f:
        if line.startswith("#"):
            assert "##INFO=<ID=AM_SCORE" in f.read()
            break
```

#### Milestone 2.2: Gene-Level Analysis (2 hours)

**File**: `code/analysis/gene_analysis.py`

**Requirements**:
```python
def compute_gene_burden(
    genes: List[str],
    metric: str = "mean",
    weights: Optional[str] = None
) -> pd.DataFrame:
    """
    Compute pathogenicity burden per gene.

    Args:
        genes: List of gene symbols or Ensembl IDs
        metric: "mean", "max", "weighted_mean"
        weights: Optional weights ("gnomad_frequency", "phylop")

    Returns:
        DataFrame with: gene, burden_score, n_variants, mean_score, max_score
    """

def get_pathogenic_variants_per_gene(
    gene: str,
    threshold: float = 0.564
) -> pd.DataFrame:
    """Get all likely pathogenic variants for a gene."""
```

**Implementation Steps**:
1. Map gene symbols to Ensembl transcript IDs
2. Query all variants for transcript
3. Compute burden metrics (mean, max, weighted)
4. Handle missing genes gracefully
5. Return ranked results

**Validation Checkpoint**:
```python
# Test gene burden
genes = ["BRCA1", "BRCA2", "TP53"]
burden = gene_analysis.compute_gene_burden(genes)

assert len(burden) == 3
assert "burden_score" in burden.columns
assert burden["burden_score"].notna().all()
```

### Phase 2 Deliverables
- ✅ `code/analysis/filtering.py` (tested)
- ✅ `code/analysis/gene_analysis.py` (tested)
- ✅ Unit tests for VCF annotation
- ✅ Unit tests for gene burden

---

## Phase 3: Notebook Development (Day 3, 6 hours)

### Objectives
- Create interactive notebooks following DeLab standards
- Literate programming (1:2-3 code:docs ratio)
- Jupytext synchronization (.ipynb ↔ .py)

### Milestones

#### Milestone 3.1: Setup Notebook (1 hour)

**File**: `notebooks/setup.ipynb`

**Structure** (following 1:2-3 ratio):
```
Cell 1: Markdown - Introduction and overview
Cell 2: Markdown - System requirements
Cell 3: Code - Import dependencies and check installation
Cell 4: Markdown - Download instructions
Cell 5: Code - Download predictions
Cell 6: Markdown - Indexing explanation
Cell 7: Code - Create DuckDB index
Cell 8: Markdown - Validation instructions
Cell 9: Code - Validate installation
Cell 10: Markdown - Next steps
```

**Cell Tags**:
- Cell 5: `["parameters", "agent-configurable"]` (download options)
- Cell 7: `["export"]` (export indexing function)

**Validation Checkpoint**:
```bash
# Test notebook execution
jupyter nbconvert --to notebook --execute notebooks/setup.ipynb
```

#### Milestone 3.2: Main Analysis Notebook (3 hours)

**File**: `notebooks/main.ipynb`

**Structure** (30-60 cells, 1:2-3 ratio):
1. **Introduction** (3 cells)
   - Overview of AlphaMissense
   - Notebook objectives
   - Required setup

2. **Load Variants** (6 cells)
   - Markdown: Input formats
   - Code: Load from VCF
   - Markdown: Load from TSV
   - Code: Load from TSV
   - Markdown: Manual input
   - Code: Manual variant specification

3. **Query AlphaMissense** (9 cells)
   - Markdown: Query methods
   - Code: Single variant lookup
   - Markdown: Interpretation
   - Code: Batch query
   - Markdown: Performance notes
   - Code: Gene-level query
   - Markdown: Results summary
   - Code: Display results table
   - Markdown: Next steps

4. **Filter and Prioritize** (6 cells)
   - Markdown: Filtering strategies
   - Code: Filter by threshold
   - Markdown: Prioritization approaches
   - Code: Rank by pathogenicity
   - Markdown: Gene prioritization
   - Code: Gene burden analysis

5. **Visualize** (6 cells)
   - Markdown: Visualization options
   - Code: Score distribution plot
   - Markdown: Protein structure visualization
   - Code: PyMOL integration
   - Markdown: Custom plots
   - Code: Publication-ready figures

6. **Export** (3 cells)
   - Markdown: Export formats
   - Code: Export to TSV/VCF
   - Markdown: Summary and conclusions

**Total**: ~33 cells (within 30-60 range)

**Cell Tags**:
- Parameters cell: `["parameters", "agent-configurable"]`
- Export functions: `["export"]`

**Validation Checkpoint**:
```bash
# Test notebook with sample data
pytest --nbmake notebooks/main.ipynb
```

#### Milestone 3.3: Visualization Notebook (2 hours)

**File**: `notebooks/visualization.ipynb`

**Focus**: Advanced visualizations and PyMOL integration

**Validation Checkpoint**:
```bash
pytest --nbmake notebooks/visualization.ipynb
```

### Phase 3 Deliverables
- ✅ `notebooks/setup.ipynb` (synced with `setup.py`)
- ✅ `notebooks/main.ipynb` (synced with `main.py`)
- ✅ `notebooks/visualization.ipynb` (synced with `visualization.py`)
- ✅ `notebooks/jupytext.toml` (sync configuration)
- ✅ All notebooks executable without errors

---

## Phase 4: Testing & Documentation (Day 4, 6 hours)

### Objectives
- Comprehensive unit and integration tests
- Test coverage >80%
- Complete documentation

### Milestones

#### Milestone 4.1: Unit Tests (2 hours)

**Files**:
- `tests/test_loader.py`
- `tests/test_filtering.py`
- `tests/test_gene_analysis.py`

**Test Coverage**:
```python
# tests/test_loader.py
def test_database_connection()
def test_variant_lookup_genomic()
def test_variant_lookup_protein()
def test_batch_lookup()
def test_missing_variant()
def test_invalid_chromosome()

# tests/test_filtering.py
def test_annotate_vcf()
def test_annotate_dataframe()
def test_filter_pathogenic()
def test_threshold_sensitivity()

# tests/test_gene_analysis.py
def test_gene_burden_mean()
def test_gene_burden_max()
def test_gene_burden_weighted()
def test_missing_gene()
```

**Validation Checkpoint**:
```bash
pytest tests/ -v --cov=code --cov-report=term-missing
# Target: >80% coverage
```

#### Milestone 4.2: Integration Tests (2 hours)

**File**: `tests/test_integration.py`

**Tests**:
```python
def test_clinvar_concordance():
    """Validate against ClinVar gold standard."""
    # Load ClinVar pathogenic/benign variants
    # Annotate with AlphaMissense
    # Compute sensitivity, specificity, accuracy
    # Assert: sensitivity > 0.80, specificity > 0.85

def test_large_vcf_processing():
    """Test processing large VCF file."""
    # Create synthetic VCF with 10k variants
    # Annotate with AlphaMissense
    # Assert: completes in <30 seconds

def test_pymol_integration():
    """Test integration with PyMOL tool."""
    # Load variants for TP53
    # Color structure by pathogenicity
    # Assert: session file created
```

**Test Data Requirements**:
- ClinVar subset: 10k variants (5k pathogenic, 5k benign)
- Sample VCF: 100 variants (mix)
- Large VCF: 10k synthetic variants

**Validation Checkpoint**:
```bash
pytest tests/test_integration.py -v -m integration
```

#### Milestone 4.3: Documentation Completion (2 hours)

**Tasks**:
1. Review and polish README.md
2. Review and polish AGENTS.md
3. Review and polish CLAUDE.md
4. Complete BUILD_PLAN.md (this file)
5. Write SCIENTIFIC_CONTEXT.md
6. Write DATA_SPECIFICATION.md
7. Add code docstrings (Google style)
8. Generate API documentation (Sphinx)

**Validation Checkpoint**:
```bash
# Check documentation completeness
ls -lh *.md
# Should see: README.md, AGENTS.md, CLAUDE.md, BUILD_PLAN.md,
#             SCIENTIFIC_CONTEXT.md, DATA_SPECIFICATION.md
```

### Phase 4 Deliverables
- ✅ Unit tests (>80% coverage)
- ✅ Integration tests
- ✅ Test data fixtures
- ✅ Complete documentation (6 MD files)
- ✅ Code docstrings

---

## Phase 5: Visualization & Polish (Day 5, 6 hours)

### Objectives
- PyMOL integration for protein structure visualization
- Publication-ready plots
- Sample datasets and examples

### Milestones

#### Milestone 5.1: Protein Visualization (3 hours)

**File**: `code/visualization/protein_viz.py`

**Requirements**:
```python
def color_by_pathogenicity(
    variants_df: pd.DataFrame,
    structure_id: str,
    pymol_instance: Any,
    color_scheme: str = "RedWhiteBlue"
) -> None:
    """Color protein structure by pathogenicity scores."""

def find_pathogenic_clusters(
    variants_df: pd.DataFrame,
    threshold: float = 0.7,
    cluster_distance: float = 10.0
) -> List[dict]:
    """Identify clusters of pathogenic variants in 3D space."""

def create_pathogenicity_map(
    uniprot_id: str,
    output_path: str
) -> None:
    """Create publication-ready protein pathogenicity map."""
```

**Implementation Steps**:
1. Load AlphaFold structure via PyMOL tool
2. Map variants to residue positions
3. Color residues by pathogenicity score
4. Add labels for key variants
5. Save PyMOL session and PNG

**Validation Checkpoint**:
```python
# Test PyMOL integration
protein_viz.create_pathogenicity_map("P04637", "TP53_map.png")
assert os.path.exists("TP53_map.png")
assert os.path.exists("TP53_map.pse")
```

#### Milestone 5.2: Statistical Plots (2 hours)

**File**: `code/visualization/plots.py`

**Plots to Implement**:
1. Score distribution histogram
2. Gene burden bar chart
3. ROC curve (vs ClinVar)
4. Comparison with other predictors (SIFT, PolyPhen-2)

**Validation Checkpoint**:
```python
# Test plot generation
from code.visualization import plots

plots.plot_score_distribution(variants, output="dist.png")
plots.plot_gene_burden(burden_df, output="burden.png")
assert os.path.exists("dist.png")
assert os.path.exists("burden.png")
```

#### Milestone 5.3: Sample Datasets (1 hour)

**Create**:
- `tests/fixtures/sample.vcf`: 100 variants (mix)
- `tests/fixtures/clinvar_subset.tsv`: 10k ClinVar variants
- `tests/fixtures/genes.txt`: List of 100 disease genes

**Validation Checkpoint**:
```bash
ls -lh tests/fixtures/
# Should see sample data files
```

### Phase 5 Deliverables
- ✅ `code/visualization/protein_viz.py` (tested)
- ✅ `code/visualization/plots.py` (tested)
- ✅ Sample datasets in `tests/fixtures/`
- ✅ Example outputs (figures, PyMOL sessions)
- ✅ Polished notebooks with examples

---

## Test Data Specifications

### 1. ClinVar Validation Dataset

**File**: `tests/fixtures/clinvar_subset.tsv`
**Size**: 10,000 variants
**Composition**:
- 5,000 pathogenic variants (ClinVar classification)
- 5,000 benign variants (ClinVar classification)
- Balanced across genes

**Columns**:
- CHROM, POS, REF, ALT
- gene, transcript_id
- clinvar_classification (Pathogenic/Benign)
- clinvar_review_status

**Download Source**:
```bash
# Download from ClinVar
wget ftp://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
# Filter for missense variants with known classification
# Sample 10k variants (balanced)
```

### 2. Sample VCF

**File**: `tests/fixtures/sample.vcf`
**Size**: 100 variants
**Composition**:
- 30 likely pathogenic (AM score > 0.564)
- 40 ambiguous (AM score 0.34-0.564)
- 30 likely benign (AM score < 0.34)
- Include edge cases (chrX, chrY, high/low confidence)

### 3. Gene List

**File**: `tests/fixtures/genes.txt`
**Size**: 100 genes
**Composition**:
- Known disease genes (BRCA1, TP53, PTEN, etc.)
- High burden genes
- Low burden genes (controls)

---

## Validation Criteria

### Functional Requirements

| Requirement | Validation | Success Criteria |
|-------------|------------|------------------|
| Download predictions | File exists and size correct | >600 MB for hg38 |
| Index database | Record count | ~71M variants |
| Variant lookup | Query time | <1 ms per variant |
| Batch query | Throughput | >1000 variants/sec |
| VCF annotation | Annotated VCF created | INFO fields added |
| Gene burden | Burden scores computed | All genes have scores |
| Notebook execution | Runs without errors | All cells execute |

### Performance Requirements

| Metric | Target | Validation |
|--------|--------|------------|
| Single query | <1 ms | Benchmark 1000 queries |
| Batch query (1k) | <1 second | Time batch operations |
| VCF annotation (10k) | <10 seconds | Process sample VCF |
| Memory usage | <2 GB | Monitor during operation |
| Disk space | <3 GB | Check data directory size |

### Accuracy Requirements

| Metric | Target | Validation |
|--------|--------|------------|
| ClinVar sensitivity | >80% | Test with ClinVar subset |
| ClinVar specificity | >85% | Test with ClinVar subset |
| Balanced accuracy | >82% | Compute from confusion matrix |

---

## Checkpoints Summary

### Phase 1 Checkpoint ✓
- [ ] Predictions downloaded (600 MB)
- [ ] Database indexed (~71M records)
- [ ] Query interface working (<1 ms lookup)
- [ ] Unit tests passing

### Phase 2 Checkpoint ✓
- [ ] VCF annotation working
- [ ] Gene burden analysis implemented
- [ ] Unit tests passing

### Phase 3 Checkpoint ✓
- [ ] All notebooks executable
- [ ] Jupytext synchronized
- [ ] 1:2-3 code:docs ratio achieved
- [ ] Notebook tests passing

### Phase 4 Checkpoint ✓
- [ ] Test coverage >80%
- [ ] ClinVar concordance >82%
- [ ] All documentation complete

### Phase 5 Checkpoint ✓
- [ ] PyMOL integration working
- [ ] Plots publication-ready
- [ ] Sample datasets created

---

## Post-MVP Enhancements

### Week 2-3: Production Features
- **CLI interface**: Command-line tool for automation
- **MCP server**: Integration with AI coding assistants
- **Ray integration**: Distributed processing for massive datasets
- **Advanced filters**: Complex filtering logic
- **Comparison tools**: vs SIFT, PolyPhen-2, CADD

### Week 4+: Advanced Features
- **Web interface**: Simple web app for queries
- **API server**: REST API for remote access
- **Structural analysis**: 3D hotspot detection
- **Population analysis**: Integration with gnomAD
- **Clinical reporting**: Automated report generation

---

## Risk Mitigation

### Risk 1: Download Failures
**Mitigation**: Implement retry logic, provide pre-downloaded index

### Risk 2: Memory Issues (Large VCFs)
**Mitigation**: Streaming processing, batch size tuning

### Risk 3: PyMOL Integration Fails
**Mitigation**: Make optional, provide alternative visualizations

### Risk 4: Performance Issues
**Mitigation**: Optimize indexes, add caching, use SSD

---

## Success Criteria (MVP Complete)

- ✅ All 5 phases completed
- ✅ All checkpoints passed
- ✅ Test coverage >80%
- ✅ ClinVar concordance >82%
- ✅ All notebooks executable
- ✅ Documentation complete (6 files)
- ✅ Sample datasets created
- ✅ PyMOL integration working

**Ready for**: Integration into DeLab workflows, user testing, production deployment

---

**Document Version**: 1.0.0
**Last Updated**: October 2025
**Estimated Total Effort**: 26 hours (MVP), +2 weeks (production-grade)
