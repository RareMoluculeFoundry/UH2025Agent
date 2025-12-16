# Build Plan: AlphaGenome Regulatory Variant Analysis Module

## Overview

Implementation plan for the AlphaGenome module with phases, checkpoints, and validation criteria.

## Project Timeline

**Total Estimated Time**: 26 hours (3-4 days for MVP)

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1: API Wrapper | 4 hours | Client, caching, retry logic |
| Phase 2: Analysis Functions | 4 hours | eQTL, splice, landscape analysis |
| Phase 3: Notebook Development | 6 hours | Interactive notebooks (1:2-3 ratio) |
| Phase 4: Testing & Documentation | 6 hours | Unit/integration tests, docs |
| Phase 5: Visualization | 6 hours | Track plots, exports |

## Phase 1: API Wrapper (Day 1, 4 hours)

### Milestone 1.1: API Client Wrapper (1.5 hours)

**File**: `code/api/client.py`

**Requirements**:
```python
def create_cached(api_key, cache_dir="cache/predictions.zarr"):
    """Create API client with caching layer."""
    
class CachedClient:
    def predict_variant(self, interval, variant, ontology_terms, requested_outputs):
        """Predict variant effect with automatic caching."""
    
    def score_ism_variants(self, interval, ontology_terms, scorer):
        """Run in silico mutagenesis with caching."""
```

**Validation**:
```python
model = create_cached(API_KEY)
outputs = model.predict_variant(...)
assert outputs.reference.rna_seq is not None
```

### Milestone 1.2: Zarr Cache (1.5 hours)

**File**: `code/api/cache.py`

**Cache Structure**:
```
cache/predictions.zarr/
├── variant_chr1_12345_A_G/
│   ├── rna_seq/
│   ├── atac/
│   └── metadata.json
```

**Validation**:
```python
cache = PredictionCache("cache/predictions.zarr")
cache.set(key, value)
assert cache.get(key) == value
```

### Milestone 1.3: Retry Logic (1 hour)

**File**: `code/api/retry.py`

**Features**:
- Exponential backoff
- Rate limit detection
- Error classification

## Phase 2: Analysis Functions (Day 2, 4 hours)

### Milestone 2.1: eQTL Analysis (1.5 hours)

**File**: `code/analysis/eqtl_analysis.py`

**Functions**:
```python
def predict_variant_effect_multitissue(variant, interval, tissues)
def compute_expression_effect_size(ref, alt)
def map_variants_to_genes(results, gene_annotations)
```

### Milestone 2.2: Splice Analysis (1.5 hours)

**File**: `code/analysis/splice_effects.py`

**Functions**:
```python
def predict_splice_disruption(variant, context_size=500_000)
def identify_affected_junctions(outputs)
def quantify_splice_site_change(ref, alt)
```

### Milestone 2.3: Regulatory Landscape (1 hour)

**File**: `code/analysis/regulatory_landscape.py`

**Functions**:
```python
def predict_region(interval, ontology_terms, modalities)
def compare_modalities(outputs)
```

## Phase 3: Notebooks (Day 3, 6 hours)

### Milestone 3.1: Main Notebook (4 hours)

**File**: `notebooks/main.ipynb`

**Structure** (45 cells, 1:2-3 ratio):
1. Introduction (3 cells)
2. API Setup (6 cells)
3. Single Variant Analysis (9 cells)
4. Multimodal Predictions (9 cells)
5. eQTL Analysis (6 cells)
6. Splice Analysis (6 cells)
7. Export Results (3 cells)
8. Summary (3 cells)

**Validation**:
```bash
jupyter nbconvert --to notebook --execute notebooks/main.ipynb
```

### Milestone 3.2: Visualization Notebook (2 hours)

**File**: `notebooks/visualization.ipynb`

**Focus**: Track plots, heatmaps, exports

## Phase 4: Testing & Documentation (Day 4, 6 hours)

### Milestone 4.1: Unit Tests (2 hours)

**Files**:
- `tests/test_api.py` (mock API)
- `tests/test_cache.py`
- `tests/test_analysis.py`

**Expected Coverage**: >80%

### Milestone 4.2: Integration Tests (2 hours)

**File**: `tests/test_integration.py`

**Tests**:
- Real API call (requires key)
- Cache persistence
- Batch processing

### Milestone 4.3: Documentation (2 hours)

Complete all markdown files:
- README.md
- AGENTS.md
- CLAUDE.md
- BUILD_PLAN.md (this file)
- API_CONTEXT.md
- SCIENTIFIC_CONTEXT.md
- DATA_SPECIFICATION.md

## Phase 5: Visualization (Day 5, 6 hours)

### Milestone 5.1: Track Plotting (3 hours)

**File**: `code/visualization/tracks.py`

**Functions**:
```python
def plot_variant_effect(ref_track, alt_track, variant, genes)
def plot_multimodal(outputs, modalities)
def create_publication_figure(...)
```

### Milestone 5.2: Export Utilities (2 hours)

**File**: `code/visualization/exports.py`

**Formats**:
- BigWig (genome browser)
- BED (peak annotations)
- TSV (variant scores)

### Milestone 5.3: Examples (1 hour)

Create example outputs in `examples/`:
- eQTL analysis figure
- Splice disruption plot
- Regulatory landscape

## Validation Criteria

### Functional Requirements

| Requirement | Validation | Success Criteria |
|-------------|------------|------------------|
| API connection | API key test | Successful authentication |
| Prediction | Single variant | Returns valid outputs |
| Caching | Repeated query | <1 sec from cache |
| Batch processing | 100 variants | Completes with rate limiting |
| Visualization | Track plot | PNG/PDF generated |

### Performance Requirements

| Metric | Target | Validation |
|--------|--------|------------|
| Single API call | 5-30 sec | Time single query |
| Cache hit | <1 sec | Time repeated query |
| Batch (100, cached) | <10 sec | Time batch from cache |
| Memory usage | <2 GB | Monitor during operation |

### Accuracy Requirements

| Metric | Target | Validation |
|--------|--------|------------|
| API response format | Valid TrackData | Check data structures |
| Cache integrity | Lossless | Compare cached vs fresh |
| Effect calculation | Correct | Validate ref - alt |

## Test Data Specifications

### 1. GWAS Validation Dataset

**File**: `tests/fixtures/gwas_variants.tsv`
**Size**: 100 variants
**Source**: GWAS Catalog
**Use**: eQTL analysis validation

### 2. Splice Variants

**File**: `tests/fixtures/splice_variants.tsv`
**Size**: 50 variants
**Source**: SpliceAI benchmark
**Use**: Splice disruption validation

### 3. Sample Genes

**File**: `tests/fixtures/genes.bed`
**Size**: 100 genes
**Source**: GENCODE
**Use**: Gene annotation

## Checkpoints Summary

### Phase 1 Checkpoint ✓
- [ ] API client working
- [ ] Caching implemented
- [ ] Retry logic functional
- [ ] Unit tests passing

### Phase 2 Checkpoint ✓
- [ ] eQTL analysis implemented
- [ ] Splice analysis implemented
- [ ] Landscape analysis implemented
- [ ] Unit tests passing

### Phase 3 Checkpoint ✓
- [ ] Main notebook executable
- [ ] Jupytext synchronized
- [ ] 1:2-3 ratio maintained
- [ ] Examples working

### Phase 4 Checkpoint ✓
- [ ] Test coverage >80%
- [ ] Integration tests passing
- [ ] Documentation complete

### Phase 5 Checkpoint ✓
- [ ] Visualizations working
- [ ] Export formats functional
- [ ] Examples generated

## Post-MVP Enhancements

### Week 2-3:
- CLI interface
- MCP server (optional)
- Advanced visualizations
- More analysis functions

### Week 4+:
- Web interface (Streamlit/Dash)
- Advanced caching strategies
- Comparative analysis tools

## Risk Mitigation

### Risk 1: API Rate Limits
**Mitigation**: Aggressive caching, rate limit detection, clear user warnings

### Risk 2: Network Issues
**Mitigation**: Retry logic, cache fallback, offline mode (cached results only)

### Risk 3: Memory (Large Predictions)
**Mitigation**: Streaming, lazy loading, zarr chunks

## Success Criteria (MVP Complete)

- ✅ All 5 phases completed
- ✅ All checkpoints passed
- ✅ Test coverage >80%
- ✅ API integration working
- ✅ Caching functional
- ✅ All notebooks executable
- ✅ Documentation complete (7 files)
- ✅ Examples generated
- ✅ Visualizations working

**Ready for**: Production use, integration workflows

---

**Document Version**: 1.0.0
**Last Updated**: October 2025
**Estimated Total Effort**: 26 hours (MVP), +2 weeks (production-grade)
