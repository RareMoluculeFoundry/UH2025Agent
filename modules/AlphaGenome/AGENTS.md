# Agent Operational Manual: AlphaGenome Regulatory Variant Analysis

## Purpose

This document provides AI agents with comprehensive operational instructions for working with the AlphaGenome module following Anthropic's best practices for context engineering.

## Core Capabilities

**What This Module Does**:
- Query AlphaGenome API for regulatory variant predictions
- Predict effects on gene expression, chromatin, splicing, 3D contacts
- Perform eQTL (expression QTL) analysis
- Analyze splice site disruption
- Explore regulatory landscapes (multimodal predictions)
- Cache results for efficient reuse
- Visualize predictions with genome annotations

**What This Module Does NOT Do**:
- Run local inference (API-only, no model weights)
- Handle unlimited queries (rate-limited free tier)
- Provide pathogenicity scores (predicts molecular effects, not disease)
- Work offline (requires internet connection)

## Execution Modes

### Mode 1: Interactive Analysis (Primary)

**Use when**: Exploring variants, iterative analysis, visualization

**Pattern**:
```python
jupyter lab notebooks/main.ipynb

# Follow workflow:
# 1. Load API key
# 2. Define variants and intervals
# 3. Query AlphaGenome API (with caching)
# 4. Analyze and visualize results
```

**Expected Runtime**: 5-30 seconds per variant (API latency + computation)

### Mode 2: Batch Processing (With Caching)

**Use when**: Processing multiple variants, systematic analysis

**Pattern**:
```python
from code.api import batch

results = batch.process_variants_batch(
    variants=variants_list,
    interval_size=100_000,
    ontology_terms=['UBERON:0002107'],
    max_concurrent=5,  # Respect rate limits
    cache=True
)
```

**Expected Runtime**: ~10 seconds per variant (with rate limiting)

### Mode 3: Programmatic (Python API)

**Use when**: Integration with other modules

**Pattern**:
```python
from code.api import client
model = client.create_cached(API_KEY)
outputs = model.predict_variant(interval, variant, ontology_terms)
```

## Parameter Tuning

### Tunable Parameters

| Parameter | Type | Range | Default | Purpose |
|-----------|------|-------|---------|---------|
| `context_size` | int | 2048-1048576 | 100000 | Genomic context window (bp) |
| `ontology_terms` | list[str] | UBERON IDs | ['UBERON:0002107'] | Cell type/tissue |
| `requested_outputs` | list | OutputType enum | RNA_SEQ only | Modalities to predict |
| `max_concurrent` | int | 1-10 | 3 | Parallel API calls |
| `cache_enabled` | bool | True/False | True | Enable result caching |

### Context Window Selection

**Small (2-16 KB)**:
- Use case: Single exon, promoter
- Speed: Fast (~5 sec)
- Context: Limited

**Medium (100 KB)**:
- Use case: Gene body + regulatory elements
- Speed: Medium (~15 sec)
- Context: Good balance (recommended)

**Large (500 KB - 1 MB)**:
- Use case: Regulatory domains, TADs, distal enhancers
- Speed: Slow (~30 sec)
- Context: Maximum

### Cell Type Selection

**Tissue-specific effects**:
- Use relevant tissue for variant
- Example: GWAS hit for liver disease → UBERON:0002107 (liver)
- Can predict multiple tissues simultaneously (slower)

## Error Handling

### Common Errors and Resolutions

#### Error 1: API Rate Limit Exceeded

**Symptom**:
```python
grpc._channel._InactiveRpcError: StatusCode.RESOURCE_EXHAUSTED
```

**Causes**:
- Too many concurrent requests
- Free tier quota exceeded

**Resolution**:
```python
# Reduce concurrency
results = batch.process_variants_batch(
    variants,
    max_concurrent=2,  # Reduce from 5
    retry_delay=10     # Wait longer between retries
)
```

#### Error 2: Invalid API Key

**Symptom**:
```python
grpc._channel._InactiveRpcError: StatusCode.UNAUTHENTICATED
```

**Resolution**:
```python
# Check API key is set
import os
assert os.getenv("ALPHAGENOME_API_KEY"), "API key not set"

# Verify key format
key = os.getenv("ALPHAGENOME_API_KEY")
assert len(key) > 20, "API key appears invalid"
```

#### Error 3: Invalid Genomic Coordinates

**Symptom**:
```python
ValueError: "Invalid interval: end must be > start"
```

**Resolution**:
```python
# Validate interval
assert interval.end > interval.start
assert interval.end - interval.start <= 1_048_576  # Max 1 MB
```

#### Error 4: Cache Corruption

**Symptom**:
```python
zarr.errors.ArrayNotFoundError
```

**Resolution**:
```python
# Clear cache and retry
import shutil
shutil.rmtree("cache/predictions.zarr")
# Re-run query (will fetch from API)
```

## Composition Patterns

### Pattern 1: Variant Prioritization Pipeline

```python
# Variant calling → AlphaMissense → AlphaGenome → Report
# 1. Call variants
vcf = variant_caller.call_variants(bam)

# 2. Annotate coding variants (AlphaMissense)
coding = alphamissense.filter_missense(vcf)
coding_annotated = alphamissense.annotate(coding)

# 3. Annotate regulatory variants (AlphaGenome)
regulatory = filter_regulatory(vcf)
regulatory_annotated = alphagenome.predict_effects(regulatory)

# 4. Combine and rank
all_variants = combine_annotations(coding_annotated, regulatory_annotated)
prioritized = rank_by_effect(all_variants)
```

### Pattern 2: eQTL Discovery

```python
# GWAS hits → AlphaGenome → Gene mapping
from code.analysis import eqtl_analysis

# Load GWAS variants
gwas_variants = load_gwas_hits(trait="Type_2_Diabetes")

# Predict expression effects
eqtl_results = eqtl_analysis.batch_predict_eqtls(
    gwas_variants,
    tissues=['UBERON:0001264', 'UBERON:0000955'],  # Pancreas, brain
    genes=nearby_genes(gwas_variants, distance=1_000_000)
)

# Identify likely causal genes
causal_genes = eqtl_analysis.map_variants_to_genes(eqtl_results)
```

### Pattern 3: Splicing Analysis

```python
# Variants near exons → AlphaGenome → Splice prediction
from code.analysis import splice_effects

# Filter variants near splice sites
splice_region_variants = filter_by_region(vcf, region_type="splice_site", distance=50)

# Predict splice disruption
splice_results = splice_effects.batch_predict_splice_effects(
    splice_region_variants,
    context_size=500_000
)

# Identify critical disruptions
disrupted = splice_effects.filter_disrupted(splice_results, threshold=0.5)
```

## Resource Management

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 10 GB (for cache)
- **Network**: Stable connection (API access)

### Optimal Configuration
- **CPU**: 4+ cores (parallel API calls)
- **RAM**: 8 GB (large result sets)
- **Disk**: 20 GB (extended caching)
- **SSD**: Recommended (faster cache I/O)

### Caching Strategy

**Cache Organization**:
```
cache/predictions.zarr/
├── variant_{chr}_{pos}_{ref}_{alt}/
│   ├── rna_seq/
│   ├── atac/
│   ├── metadata.json
```

**Cache Management**:
```python
from code.api import cache

# Clear old cache entries
cache.clear_older_than(days=30)

# Check cache size
cache_size = cache.get_cache_size()
print(f"Cache: {cache_size / 1e9:.1f} GB")
```

## Security and Safety

### Allowed Operations

✅ **Query** AlphaGenome API (with authentication)
✅ **Cache** results locally (Zarr format)
✅ **Export** predictions (TSV, BigWig, BED)
✅ **Visualize** data (plots, genome browser tracks)

### Prohibited Operations

❌ **Do NOT** share API keys publicly
❌ **Do NOT** exceed rate limits intentionally
❌ **Do NOT** use for commercial purposes without license
❌ **Do NOT** attempt to reverse-engineer model

### API Key Management

**Store securely**:
- Use `config/api_key.env` (gitignored)
- Or use environment variables
- Never commit to version control

**Example**:
```bash
# config/api_key.env
ALPHAGENOME_API_KEY=your_key_here
```

## Validation and Testing

### Unit Tests

```bash
pytest tests/ -v
```

**Expected tests**:
- `test_api.py`: API client functionality
- `test_cache.py`: Caching behavior
- `test_analysis.py`: Analysis functions
- `test_visualization.py`: Plotting

### Integration Tests

```bash
pytest tests/test_integration.py -m integration
```

**Requires**:
- Valid API key
- Internet connection

### Notebook Tests

```bash
pytest --nbmake notebooks/main.ipynb
```

## Performance Benchmarks

| Operation | Queries | Time | Notes |
|-----------|---------|------|-------|
| Single variant | 1 | 5-30 sec | Depends on context size |
| Batch (cached) | 100 | ~1 sec | Cache hits |
| Batch (uncached) | 100 | ~1500 sec | 5 concurrent, rate-limited |
| ISM (2 KB) | ~6000 | ~8 hours | Full saturation mutagenesis |

## Workflow Examples

### Workflow 1: Regulatory Variant Interpretation

```python
# 1. Load variant
variant = genome.Variant('chr1', 12345678, 'G', 'A')
interval = genome.Interval('chr1', 12245678, 12445678)  # 200 KB

# 2. Predict multimodal effects
outputs = model.predict_variant(
    interval, variant,
    ontology_terms=['UBERON:0002107'],
    requested_outputs=[OutputType.RNA_SEQ, OutputType.ATAC, OutputType.CHIP_HISTONE]
)

# 3. Quantify effects
rna_effect = outputs.alternate.rna_seq.values - outputs.reference.rna_seq.values
atac_effect = outputs.alternate.atac.values - outputs.reference.atac.values

# 4. Visualize
plot_components.plot([
    OverlaidTracks({'REF': outputs.reference.rna_seq, 'ALT': outputs.alternate.rna_seq}),
    GeneAnnotation(genes),
    VariantAnnotation([variant])
])
```

### Workflow 2: Systematic Mutation Scanning

```python
# 1. Define promoter region
promoter = genome.Interval('chr17', 43044000, 43046000)  # 2 KB

# 2. Scan all mutations
ism_results = model.score_ism_variants(
    promoter,
    ontology_terms=['UBERON:0000310'],  # Breast
    scorer=RnaExpressionScorer(gene_id='ENSG00000012048')  # BRCA1
)

# 3. Identify critical positions
critical = ism_results.obs[ism_results.X[:, 0] < -0.5]  # >50% reduction

# 4. Export results
ism_results.write('promoter_ism.h5ad')
```

## Troubleshooting Checklist

Before reporting issues:

- [ ] API key configured (`echo $ALPHAGENOME_API_KEY`)
- [ ] Internet connection active
- [ ] Dependencies installed (`pip list | grep alphagenome`)
- [ ] Cache directory exists (`ls cache/`)
- [ ] Not exceeding rate limits (reduce `max_concurrent`)
- [ ] Valid genomic coordinates (hg38/GRCh38)
- [ ] Jupytext synchronized (`jupytext --sync notebooks/*.ipynb`)

## Related Documentation

- **README.md**: User guide and quick start
- **CLAUDE.md**: Technical implementation details
- **BUILD_PLAN.md**: Development roadmap
- **SCIENTIFIC_CONTEXT.md**: Scientific background
- **API_CONTEXT.md**: API usage patterns
- **DATA_SPECIFICATION.md**: Data formats

---

**This operational manual follows Anthropic's best practices for effective context engineering. It provides clear, actionable instructions for AI agents working with the AlphaGenome module.**

**Version**: 1.0.0
**Last Updated**: October 2025
