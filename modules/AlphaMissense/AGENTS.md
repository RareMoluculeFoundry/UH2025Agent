# Agent Operational Manual: AlphaMissense Variant Pathogenicity Lookup

## Purpose

This document provides AI agents with comprehensive operational instructions for working with the AlphaMissense module. It follows Anthropic's best practices for context engineering and enables effective agent-assisted variant analysis.

## Core Capabilities

**What This Module Does**:
- Query pre-computed pathogenicity predictions for 71M human missense variants
- Annotate VCF files with AlphaMissense scores
- Filter variants by pathogenicity threshold
- Perform gene-level burden analysis
- Visualize pathogenicity on protein structures (via PyMOL integration)
- Compare AlphaMissense predictions with other tools (SIFT, PolyPhen-2)

**What This Module Does NOT Do**:
- Run new predictions (model weights not available)
- Handle non-missense variants (indels, splice variants, CNVs)
- Require GPU or specialized hardware (CPU-only data lookup)
- Make clinical diagnoses (provides probabilities, not diagnoses)

## Execution Modes

### Mode 1: Interactive Analysis (Primary)

**Use when**: Exploring variants, iterative analysis, visualization

**Pattern**:
```python
# Launch Jupyter Lab
jupyter lab notebooks/main.ipynb

# Follow notebook workflow:
# 1. Load variants (VCF, TSV, or manual input)
# 2. Query AlphaMissense database
# 3. Filter and prioritize
# 4. Visualize and export
```

**Expected Runtime**: Real-time (< 1 second per query)

### Mode 2: Batch Processing

**Use when**: Processing large VCF files (>1000 variants)

**Pattern**:
```python
# In notebook or script
from code.analysis import filtering

results = filtering.annotate_vcf(
    input_vcf="patient_exome.vcf",
    output_vcf="annotated_exome.vcf",
    batch_size=1000,  # Process in chunks
    progress=True     # Show progress bar
)
```

**Expected Runtime**: ~10 seconds per 10k variants

### Mode 3: Programmatic (Python API)

**Use when**: Integrating with other modules or pipelines

**Pattern**:
```python
# Import module functions
from code.data import loader
from code.analysis import filtering

# Query single variant
score = loader.lookup_variant("chr17", 43044295, "G", "A")

# Batch query
variants_df = pd.read_csv("variants.tsv", sep="\t")
annotated = filtering.annotate_dataframe(variants_df)
```

**Expected Runtime**: < 1 ms per variant

## Parameter Tuning

### Tunable Parameters

| Parameter | Type | Range | Default | Purpose |
|-----------|------|-------|---------|---------|
| `threshold` | float | 0.0 - 1.0 | 0.564 | Pathogenicity cutoff (likely_pathogenic) |
| `ambiguous_range` | tuple | (0.0-1.0, 0.0-1.0) | (0.34, 0.564) | VUS classification range |
| `batch_size` | int | 100 - 10000 | 1000 | Variants per batch query |
| `cache_results` | bool | True/False | True | Cache queries in memory |

### Threshold Selection Guidance

**Conservative (High Specificity)**:
- Threshold: 0.7
- Use case: Clinical diagnosis, avoid false positives
- Trade-off: May miss some pathogenic variants

**Balanced (Recommended)**:
- Threshold: 0.564
- Use case: General research, variant prioritization
- Trade-off: AlphaMissense's calibrated cutoff

**Sensitive (High Sensitivity)**:
- Threshold: 0.4
- Use case: Discovery research, cast wide net
- Trade-off: More false positives

### Hyperparameter Optimization

Not applicable (no model training, only data lookup).

## Error Handling

### Common Errors and Resolutions

#### Error 1: Variant Not Found

**Symptom**:
```python
KeyError: "Variant chr1:12345:A:G not found in database"
```

**Causes**:
- Variant not in pre-computed predictions (not a missense variant)
- Incorrect coordinates or reference genome (hg38 required)
- Indel or non-SNV variant

**Resolution**:
```python
# Check if variant exists before querying
from code.data import loader

if loader.variant_exists("chr1", 12345, "A", "G"):
    score = loader.lookup_variant("chr1", 12345, "A", "G")
else:
    print("Variant not in AlphaMissense database (not a missense variant)")
```

#### Error 2: Invalid Chromosome Format

**Symptom**:
```python
ValueError: "Chromosome '1' not recognized. Use 'chr1' format."
```

**Causes**:
- Missing "chr" prefix
- Invalid chromosome name

**Resolution**:
```python
# Normalize chromosome names
from code.data import loader

chrom = "1"  # Wrong
chrom = f"chr{chrom}" if not chrom.startswith("chr") else chrom  # Right
score = loader.lookup_variant(chrom, 12345, "A", "G")
```

#### Error 3: Database Not Initialized

**Symptom**:
```python
FileNotFoundError: "AlphaMissense database not found at data/hg38.duckdb"
```

**Causes**:
- Predictions not downloaded
- Setup notebook not run

**Resolution**:
```python
# Run setup notebook first
jupyter lab notebooks/setup.ipynb
# This downloads and indexes predictions (~10 minutes, one-time)
```

#### Error 4: Memory Exhaustion (Batch Processing)

**Symptom**:
```python
MemoryError: "Unable to allocate array"
```

**Causes**:
- Batch size too large
- Too many results held in memory

**Resolution**:
```python
# Reduce batch size, process in chunks
from code.analysis import filtering

results = filtering.annotate_vcf(
    "large_file.vcf",
    "annotated.vcf",
    batch_size=500,  # Reduce from 1000
    stream=True      # Stream results to disk
)
```

### Recovery Strategies

**Data Corruption**:
```python
# Re-download and re-index predictions
from code.data import downloader, indexer

downloader.download_predictions(force=True)  # Force re-download
indexer.rebuild_index()  # Rebuild database
```

**Partial Results**:
```python
# Resume from last successful batch
from code.analysis import filtering

results = filtering.annotate_vcf(
    "input.vcf",
    "output.vcf",
    resume=True,  # Skip already processed variants
    checkpoint_file=".checkpoint.json"
)
```

## Composition Patterns

### Pattern 1: Sequential Pipeline

**Use case**: Variant calling → AlphaMissense annotation → Clinical reporting

```python
# Step 1: Variant calling (hypothetical module)
vcf = variant_caller.call_variants(bam_file)

# Step 2: AlphaMissense annotation
from code.analysis import filtering
annotated = filtering.annotate_vcf(vcf, "annotated.vcf")

# Step 3: Clinical report (hypothetical module)
report = clinical_reporter.generate_report(annotated)
```

### Pattern 2: Parallel Annotation

**Use case**: Annotate with multiple predictors simultaneously

```python
from concurrent.futures import ThreadPoolExecutor

def annotate_alphamissense(vcf):
    from code.analysis import filtering
    return filtering.annotate_vcf(vcf)

def annotate_sift(vcf):
    # Hypothetical SIFT module
    return sift_module.annotate(vcf)

with ThreadPoolExecutor(max_workers=3) as executor:
    am_future = executor.submit(annotate_alphamissense, "input.vcf")
    sift_future = executor.submit(annotate_sift, "input.vcf")

    am_results = am_future.result()
    sift_results = sift_future.result()
```

### Pattern 3: Integration with PyMOL Tool

**Use case**: Visualize pathogenicity on protein structure

```python
# Get variants for protein
from code.data import loader
variants = loader.get_protein_variants(uniprot_id="P04637")  # TP53

# Load structure in PyMOL
from lab.obs.tools.pymol.code import core as pymol
pymol.load_alphafold_structure("P04637")

# Color by pathogenicity
from code.visualization import protein_viz
protein_viz.color_by_pathogenicity(variants, structure="P04637")

# Save session
pymol.save_session("TP53_pathogenicity.pse")
```

### Pattern 4: Gene Burden Analysis

**Use case**: Prioritize genes by pathogenicity burden

```python
# Get gene list
genes = ["BRCA1", "BRCA2", "TP53", "PTEN", "ATM"]

# Compute burden
from code.analysis import gene_analysis
burden = gene_analysis.compute_gene_burden(
    genes,
    metric="mean",  # or "max", "weighted"
    weights="gnomad_frequency"  # Weight by allele frequency
)

# Rank genes
burden_ranked = burden.sort_values("burden_score", ascending=False)
```

## Module Dependencies

### Required Modules
- None (standalone module)

### Optional Integrations
- **PyMOL Tool** (`/lab/obs/tools/pymol/`): Protein structure visualization
- **Variant Caller Modules**: Upstream variant calling
- **Clinical Reporting Modules**: Downstream interpretation

### Data Dependencies
- **AlphaMissense predictions** (downloaded from Google Cloud Storage)
- **hg38 reference genome** (for coordinate validation, optional)
- **ClinVar database** (for validation and comparison, optional)

## Resource Management

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 2 GB
- **Disk**: 3 GB (2 GB for indexed data, 1 GB for cache/temp)
- **Network**: One-time download (600 MB compressed)

### Optimal Configuration
- **CPU**: 4+ cores (for batch processing)
- **RAM**: 4 GB (for large VCF files)
- **Disk**: 5 GB (for additional datasets)
- **SSD**: Recommended (faster database queries)

### Autoscaling Guidance

Not applicable (lightweight module, no autoscaling needed).

**Ray Cluster** (optional for massive batch processing):
```python
# Deploy to Ray cluster for very large datasets (>100k variants)
from code.ray import submit_job

job_id = submit_job.annotate_vcf_distributed(
    "huge_population.vcf",
    num_workers=10
)
```

### Resource Monitoring

```python
# Monitor query performance
from code.data import loader

stats = loader.get_performance_stats()
print(f"Queries/sec: {stats['queries_per_second']}")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Avg query time: {stats['avg_query_ms']:.2f} ms")
```

## Security and Safety

### Allowed Operations

✅ **Read** pre-computed predictions
✅ **Query** local database (DuckDB)
✅ **Annotate** VCF files
✅ **Export** results (TSV, CSV, VCF)
✅ **Visualize** data (plots, protein structures)
✅ **Cache** query results (local memory/disk)

### Prohibited Operations

❌ **Do NOT** upload patient data to external servers (all processing is local)
❌ **Do NOT** modify pre-computed predictions (read-only database)
❌ **Do NOT** run predictions without model weights (not available)
❌ **Do NOT** bypass input validation (chromosome names, coordinates)
❌ **Do NOT** interpret scores as clinical diagnoses (provide probabilities only)

### Input Validation

**Always validate**:
- Chromosome names (chr1-22, chrX, chrY, chrM)
- Positions (positive integers, within chromosome bounds)
- Reference/alternate alleles (A, C, G, T only)
- File formats (VCF, TSV with required columns)

**Example validation**:
```python
from code.data import validator

# Validate variant before querying
is_valid, error = validator.validate_variant(
    chrom="chr17",
    pos=43044295,
    ref="G",
    alt="A"
)

if not is_valid:
    print(f"Validation error: {error}")
else:
    score = loader.lookup_variant("chr17", 43044295, "G", "A")
```

### Privacy and Ethics

- **Patient data**: Keep all data local, never upload to external services
- **Interpretation**: AlphaMissense scores are predictions, not clinical diagnoses
- **Reporting**: Always include uncertainty ranges and limitations
- **Consent**: Ensure appropriate consent for genetic analysis

## Integration Points

### MCP Server (Optional)

This module can expose an MCP server for integration with AI coding assistants:

```python
# Start MCP server
python mcp_server.py --port 3000

# Available tools:
# - lookup_variant(chr, pos, ref, alt) → score
# - annotate_vcf(input_path, output_path) → status
# - get_gene_variants(gene_id) → variants
```

### CLI Interface

```bash
# Command-line interface for batch processing
python -m code.cli annotate \
    --input patient_variants.vcf \
    --output annotated_variants.vcf \
    --threshold 0.564 \
    --format vcf
```

### Python API

```python
# Programmatic access
from lab.obs.modules.AlphaMissense import AlphaMissenseModule

module = AlphaMissenseModule()
score = module.lookup("chr17", 43044295, "G", "A")
results = module.annotate_vcf("input.vcf", "output.vcf")
```

## Workflow Examples

### Workflow 1: Clinical Exome Analysis

```python
# 1. Load patient exome variants
from code.data import loader
from code.analysis import filtering

variants = filtering.load_vcf("patient_exome.vcf")

# 2. Annotate with AlphaMissense
annotated = filtering.annotate_dataframe(variants)

# 3. Filter likely pathogenic
pathogenic = annotated[annotated["am_class"] == "likely_pathogenic"]

# 4. Prioritize by gene (known disease genes)
disease_genes = ["BRCA1", "BRCA2", "TP53", "PTEN", "ATM"]
prioritized = pathogenic[pathogenic["gene"].isin(disease_genes)]

# 5. Export for clinical review
prioritized.to_csv("prioritized_variants.tsv", sep="\t", index=False)
```

### Workflow 2: Gene Discovery

```python
# 1. Get all variants for candidate genes
from code.analysis import gene_analysis

candidate_genes = ["GENE1", "GENE2", "GENE3"]
variants = gene_analysis.get_variants_for_genes(candidate_genes)

# 2. Compute burden scores
burden = gene_analysis.compute_gene_burden(
    candidate_genes,
    metric="weighted_mean",
    weights="gnomad_frequency"
)

# 3. Rank by burden
ranked = burden.sort_values("burden_score", ascending=False)

# 4. Visualize top genes
from code.visualization import plots
plots.plot_gene_burden(ranked, top_n=10, output="gene_burden.png")
```

### Workflow 3: Structural Analysis

```python
# 1. Get variants for protein
from code.data import loader
variants = loader.get_protein_variants(uniprot_id="P04637")  # TP53

# 2. Map to AlphaFold structure
from code.visualization import protein_viz
from lab.obs.tools.pymol.code import core as pymol

pymol.load_alphafold_structure("P04637")
protein_viz.map_scores_to_structure(variants)

# 3. Identify pathogenic hotspots
hotspots = protein_viz.find_pathogenic_clusters(
    variants,
    threshold=0.7,
    cluster_distance=10  # angstroms
)

# 4. Export annotated structure
pymol.save_session("TP53_hotspots.pse")
```

## Validation and Testing

### Unit Tests

Run unit tests before deploying:
```bash
pytest tests/ -v
```

**Expected tests**:
- `test_loader.py`: Database queries
- `test_filtering.py`: VCF annotation
- `test_gene_analysis.py`: Burden calculations
- `test_visualization.py`: Plot generation

### Integration Tests

Test with real data:
```python
# Test with ClinVar variants (gold standard)
from tests import integration

results = integration.test_clinvar_concordance()
# Expected: >85% sensitivity, >90% specificity
```

### Notebook Tests

Validate notebooks execute without errors:
```bash
pytest --nbmake notebooks/main.ipynb
```

## Performance Benchmarks

### Expected Performance

| Operation | Variants | Time | Rate |
|-----------|----------|------|------|
| Single query | 1 | <1 ms | 1000+/sec |
| Batch query | 1,000 | ~1 sec | 1000/sec |
| VCF annotation | 10,000 | ~10 sec | 1000/sec |
| Gene analysis | 100 genes | ~1 sec | 100/sec |

### Optimization Tips

1. **Use batch queries** (10-100x faster than individual queries)
2. **Enable caching** (avoid repeated queries)
3. **Index VCF files** (for random access)
4. **Use SSD storage** (faster database queries)
5. **Process in chunks** (for large files)

## Troubleshooting Checklist

Before reporting issues, check:

- [ ] Database initialized (run `notebooks/setup.ipynb`)
- [ ] Predictions downloaded (check `data/hg38.duckdb` exists)
- [ ] Input format correct (VCF with chr prefix, 1-based coordinates)
- [ ] Variants are missense (not indels, splice, or non-coding)
- [ ] Reference genome is hg38 (not hg19/GRCh37)
- [ ] Sufficient disk space (3+ GB available)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Jupytext synchronized (`jupytext --sync notebooks/*.ipynb`)

## Version Information

- **Module Version**: 1.0.0
- **AlphaMissense Data Version**: 2023-09 (from publication)
- **Reference Genome**: hg38/GRCh38
- **Last Updated**: October 2025

## Related Documentation

- **README.md**: Human-readable overview and quick start
- **CLAUDE.md**: Agent-specific context and technical details
- **BUILD_PLAN.md**: Implementation roadmap and checkpoints
- **SCIENTIFIC_CONTEXT.md**: Detailed scientific background
- **DATA_SPECIFICATION.md**: Data formats and schemas

---

**This operational manual follows Anthropic's best practices for effective context engineering. It provides clear, actionable instructions for AI agents working with the AlphaMissense module.**
