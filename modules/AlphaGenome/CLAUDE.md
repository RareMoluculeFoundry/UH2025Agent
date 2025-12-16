# Agent Context: AlphaGenome Regulatory Variant Analysis Module

## Purpose

This file provides AI agents with technical context for building and maintaining the AlphaGenome module.

## Module Classification

**Type**: API-Based Regulatory Analysis Module (Simplified)
**Compute**: CPU-only (API calls, no local inference)
**Dependencies**: AlphaGenome API (requires key)
**Backend Detection**: NOT REQUIRED (network-bound, not compute-bound)
**Deployment**: Simplified (Docker optional, Ray optional for batch)

## Adaptation from DeLab Module Standard

This module is **simplified** from the full DeLab module standard:

1. **No local inference**: All predictions via API (no model weights)
2. **No backend detection**: CPU-only (no CUDA/ROCm/MLX)
3. **No compute backends**: Network I/O bound (API calls)
4. **Lightweight deployment**: Minimal containerization

### What to SKIP

❌ **backends/manager.py**: No multi-backend detection
❌ **GPU tags**: All operations are CPU
❌ **models/**: No local model weights
❌ **kubeflow/**: Not practical (rate-limited API)

### What to KEEP

✅ **Jupytext synchronization**: .ipynb ↔ .py
✅ **Literate programming**: 1:2-3 code:docs ratio
✅ **Cell tagging**: `parameters`, `agent-configurable`
✅ **AGENTS.md**: Operational manual
✅ **tests/**: Comprehensive testing

## Technical Architecture

### Data Flow

```
[User Query]
     ↓
[AlphaGenome API] (gRPC)
     ↓
[Zarr Cache] (local disk)
     ↓
[Analysis & Visualization]
```

### Key Components

#### 1. API Layer (`code/api/`)

**client.py**:
```python
def create_cached(api_key, cache_dir="cache/predictions.zarr"):
    """Create API client with caching."""
    base_client = dna_client.create(api_key)
    return CachedClient(base_client, cache_dir)

class CachedClient:
    def predict_variant(self, interval, variant, ontology_terms, requested_outputs):
        # Check cache first
        cache_key = hash((interval, variant, tuple(ontology_terms)))
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Query API
        result = self.client.predict_variant(...)

        # Store in cache
        self.cache[cache_key] = result
        return result
```

**cache.py** (Zarr-based):
```python
import zarr

class PredictionCache:
    def __init__(self, cache_dir):
        self.store = zarr.open(cache_dir, mode='a')

    def get(self, key):
        if key in self.store:
            return self.store[key]
        return None

    def set(self, key, value):
        self.store[key] = value
```

#### 2. Analysis Layer (`code/analysis/`)

**eqtl_analysis.py**:
```python
def predict_variant_effect_multitissue(variant, interval, tissues):
    """Predict expression effect across tissues."""
    results = {}
    for tissue in tissues:
        outputs = model.predict_variant(
            interval, variant,
            ontology_terms=[tissue],
            requested_outputs=[OutputType.RNA_SEQ]
        )
        effect = outputs.alternate.rna_seq.values - outputs.reference.rna_seq.values
        results[tissue] = effect
    return results
```

**splice_effects.py**:
```python
def predict_splice_disruption(variant, context_size=500_000):
    """Predict splice site disruption."""
    interval = expand_around_variant(variant, context_size)
    outputs = model.predict_variant(
        interval, variant,
        ontology_terms=['UBERON:0002107'],  # Liver
        requested_outputs=[
            OutputType.SPLICE_SITES,
            OutputType.SPLICE_JUNCTIONS,
            OutputType.SPLICE_SITE_USAGE
        ]
    )
    return analyze_splice_changes(outputs)
```

## AlphaGenome API Patterns

### Basic Usage

```python
from alphagenome.data import genome
from alphagenome.models import dna_client

# Create client
model = dna_client.create(API_KEY)

# Define genomic elements
interval = genome.Interval('chr1', 100000, 200000)
variant = genome.Variant('chr1', 150000, 'A', 'G')

# Predict
outputs = model.predict_variant(
    interval=interval,
    variant=variant,
    ontology_terms=['UBERON:0002107'],  # Liver
    requested_outputs=[dna_client.OutputType.RNA_SEQ]
)

# Access results
ref_expression = outputs.reference.rna_seq.values
alt_expression = outputs.alternate.rna_seq.values
effect = alt_expression - ref_expression
```

### Available Output Types

```python
from alphagenome.models import dna_client

OutputType.RNA_SEQ        # Gene expression
OutputType.ATAC           # Chromatin accessibility
OutputType.DNASE          # DNase hypersensitivity
OutputType.CAGE           # TSS activity
OutputType.PROCAP         # Nascent transcription
OutputType.CHIP_HISTONE   # Histone modifications
OutputType.CHIP_TF        # TF binding
OutputType.SPLICE_SITES   # Splice donor/acceptor
OutputType.SPLICE_SITE_USAGE  # Splice frequency
OutputType.SPLICE_JUNCTIONS   # Splice reads
OutputType.CONTACT_MAPS   # Hi-C-like contacts
```

### Data Structures

**TrackData** (1D genomic signals):
```python
track = outputs.reference.rna_seq
track.interval  # genome.Interval
track.values    # numpy array (n_tracks, n_positions)
track.metadata  # pandas DataFrame
```

**JunctionData** (splice junctions):
```python
junctions = outputs.reference.splice_junctions
junctions.values     # junction read counts
junctions.junctions  # junction annotations
```

**AnnData** (ISM results):
```python
ism_results = model.score_ism_variants(...)
ism_results.X       # Scores (variants × tracks)
ism_results.obs     # Variant metadata
ism_results.var     # Track metadata
```

## Implementation Guidance

### Phase 1: API Wrapper (Day 1, 4 hours)

1. Implement `code/api/client.py`
   - Wrapper around `alphagenome.models.dna_client`
   - Add caching layer
   - Environment variable API key management

2. Implement `code/api/cache.py`
   - Zarr-based caching
   - Cache key generation
   - Cache management (clear, size, stats)

3. Implement `code/api/retry.py`
   - Exponential backoff
   - Rate limit detection
   - Error handling

### Phase 2: Analysis Functions (Day 2, 4 hours)

1. Implement `code/analysis/eqtl_analysis.py`
2. Implement `code/analysis/splice_effects.py`
3. Implement `code/analysis/regulatory_landscape.py`

### Phase 3: Notebooks (Day 3, 6 hours)

1. Create `notebooks/main.ipynb`
   - API key setup
   - Single variant analysis
   - Multimodal predictions
   - Visualization examples
   - Follow 1:2-3 code:docs ratio

2. Create `notebooks/visualization.ipynb`
   - Track plots
   - Heatmaps
   - Export formats (BigWig, BED)

### Phase 4: Testing & Docs (Day 4, 6 hours)

1. Unit tests (with mock API)
2. Integration tests (require API key)
3. Complete documentation

### Phase 5: Visualization (Day 5, 6 hours)

1. Extend AlphaGenome visualization library
2. Add custom plot types
3. Export utilities

## Jupytext Configuration

**notebooks/jupytext.toml**:
```toml
formats = "ipynb,py:percent"
notebook_metadata_filter = "kernelspec,jupytext"
cell_metadata_filter = "tags,execution_group,depends_on,-ExecuteTime"
```

## Testing Strategy

### Mock API for Unit Tests

```python
from unittest.mock import Mock, patch

@pytest.fixture
def mock_api():
    with patch('alphagenome.models.dna_client.create') as mock:
        mock_client = Mock()
        mock_client.predict_variant.return_value = MockOutputs()
        mock.return_value = mock_client
        yield mock_client
```

### Integration Tests (Require API Key)

```python
@pytest.mark.integration
def test_real_api_call():
    api_key = os.getenv("ALPHAGENOME_API_KEY")
    if not api_key:
        pytest.skip("API key not available")

    model = create_cached(api_key)
    outputs = model.predict_variant(...)
    assert outputs.reference.rna_seq is not None
```

## Performance Optimization

### Caching Strategy

**Always cache**:
- Identical queries return instantly
- Persist across sessions
- ~100 MB per 1000 predictions

**Cache key**:
```python
cache_key = hash((
    interval.chromosome,
    interval.start,
    interval.end,
    variant.position,
    variant.reference_bases,
    variant.alternate_bases,
    tuple(sorted(ontology_terms)),
    tuple(sorted(requested_outputs))
))
```

### Batch Processing

```python
def batch_predict_variants(variants, max_concurrent=5):
    """Process variants with rate limiting."""
    from concurrent.futures import ThreadPoolExecutor
    import time

    def predict_with_delay(variant, delay):
        time.sleep(delay)
        return model.predict_variant(...)

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = []
        for i, variant in enumerate(variants):
            delay = i * (60 / 100)  # Rate limit: ~100 per minute
            future = executor.submit(predict_with_delay, variant, delay)
            futures.append(future)

        results = [f.result() for f in futures]
    return results
```

## Related Documentation

- **README.md**: User guide
- **AGENTS.md**: Operational manual
- **BUILD_PLAN.md**: Implementation roadmap
- **API_CONTEXT.md**: API best practices
- **SCIENTIFIC_CONTEXT.md**: Scientific background
- **DATA_SPECIFICATION.md**: Data formats

---

**Version**: 1.0.0
**Last Updated**: October 2025
