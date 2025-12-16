# API Context: AlphaGenome API Usage and Best Practices

## Overview

Comprehensive guide for using the AlphaGenome API effectively.

## API Access

**URL**: https://deepmind.google.com/science/alphagenome
**Protocol**: gRPC
**Authentication**: API key (free for non-commercial use)
**Rate Limits**: Dynamic (suitable for 1000s of predictions)

## API Key Management

### Setup

```bash
# Method 1: Environment variable
export ALPHAGENOME_API_KEY="your_key_here"

# Method 2: Config file (gitignored)
echo "ALPHAGENOME_API_KEY=your_key_here" > config/api_key.env

# Method 3: Python
import os
os.environ["ALPHAGENOME_API_KEY"] = "your_key_here"
```

### Security

- Never commit API keys
- Use environment variables
- Gitignore config/api_key.env
- Rotate keys periodically

## Core API Methods

### 1. predict_interval

Predict genomic features for a region (no variant).

```python
from alphagenome.data import genome
from alphagenome.models import dna_client

model = dna_client.create(API_KEY)

interval = genome.Interval('chr1', 100000, 200000)

outputs = model.predict_interval(
    interval=interval,
    ontology_terms=['UBERON:0002107'],  # Liver
    requested_outputs=[
        dna_client.OutputType.RNA_SEQ,
        dna_client.OutputType.ATAC
    ]
)
```

### 2. predict_variant

Compare reference vs alternate allele.

```python
variant = genome.Variant('chr1', 150000, 'A', 'G')

outputs = model.predict_variant(
    interval=interval,
    variant=variant,
    ontology_terms=['UBERON:0002107'],
    requested_outputs=[dna_client.OutputType.RNA_SEQ]
)

# Access reference and alternate predictions
ref = outputs.reference.rna_seq
alt = outputs.alternate.rna_seq
effect = alt.values - ref.values
```

### 3. score_ism_variants

In silico mutagenesis (all possible mutations).

```python
from alphagenome.models.variant_scorers import RnaExpressionScorer

promoter = genome.Interval('chr17', 43044000, 43046000)

ism_results = model.score_ism_variants(
    interval=promoter,
    ontology_terms=['UBERON:0000310'],  # Breast
    scorer=RnaExpressionScorer(gene_id='ENSG00000012048')  # BRCA1
)

# Returns AnnData with scores
ism_results.X  # Scores (n_variants × n_tracks)
ism_results.obs  # Variant metadata
```

## Output Types

### Expression

| Type | Description | Use Case |
|------|-------------|----------|
| RNA_SEQ | Gene expression (TPM) | eQTL analysis |
| CAGE | TSS activity | Promoter variants |
| PROCAP | Nascent transcription | Transcription regulation |

### Chromatin

| Type | Description | Use Case |
|------|-------------|----------|
| ATAC | Open chromatin | Regulatory elements |
| DNASE | DNase hypersensitivity | Enhancer/promoter |
| CHIP_HISTONE | Histone modifications | Epigenetic state |
| CHIP_TF | TF binding | Binding site disruption |

### Splicing

| Type | Description | Use Case |
|------|-------------|----------|
| SPLICE_SITES | Donor/acceptor predictions | Splice site variants |
| SPLICE_SITE_USAGE | Usage frequency | Alternative splicing |
| SPLICE_JUNCTIONS | Junction read counts | Splice quantification |

### 3D Genome

| Type | Description | Use Case |
|------|-------------|----------|
| CONTACT_MAPS | Chromatin interactions | TAD boundaries |

## Context Window Sizes

| Size | Value | Use Case |
|------|-------|----------|
| 2 KB | 2048 | Single exon |
| 16 KB | 16384 | Gene + promoter |
| 100 KB | 131072 | Gene cluster (default) |
| 500 KB | 524288 | Regulatory domain |
| 1 MB | 1048576 | TAD |

**Guidance**:
- Start with 100 KB
- Larger = more context, slower
- Smaller = faster, less context

## Cell Types (UBERON Ontology)

### Common Tissues

```python
tissues = {
    'liver': 'UBERON:0002107',
    'brain': 'UBERON:0000955',
    'heart': 'UBERON:0000948',
    'lung': 'UBERON:0002048',
    'kidney': 'UBERON:0002113',
    'blood': 'UBERON:0000178'
}
```

### Common Cell Types

```python
cell_types = {
    'hepatocyte': 'UBERON:0000026',
    'neuron': 'UBERON:0000540',
    'cardiomyocyte': 'UBERON:0002349',
    't_cell': 'CL:0000084',
    'b_cell': 'CL:0000236'
}
```

**Full ontology**: https://www.ebi.ac.uk/ols/ontologies/uberon

## Rate Limiting

### Strategy

- Free tier: ~100 predictions per minute
- Built-in exponential backoff
- Dynamic rate limits (adjust based on demand)

### Best Practices

```python
from concurrent.futures import ThreadPoolExecutor
import time

def predict_with_rate_limit(variant, delay):
    time.sleep(delay)
    return model.predict_variant(...)

# Limit concurrent requests
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = []
    for i, variant in enumerate(variants):
        delay = i * (60 / 100)  # ~100 per minute
        future = executor.submit(predict_with_rate_limit, variant, delay)
        futures.append(future)
    
    results = [f.result() for f in futures]
```

## Error Handling

### Common Errors

**RESOURCE_EXHAUSTED**:
```python
try:
    outputs = model.predict_variant(...)
except grpc._channel._InactiveRpcError as e:
    if e.code() == grpc.StatusCode.RESOURCE_EXHAUSTED:
        # Rate limit exceeded
        time.sleep(10)
        outputs = model.predict_variant(...)
```

**UNAUTHENTICATED**:
```python
# Invalid API key
# Check: os.getenv("ALPHAGENOME_API_KEY")
```

**INVALID_ARGUMENT**:
```python
# Invalid coordinates or parameters
# Verify: interval.end > interval.start
```

## Caching Strategy

### Cache Key Generation

```python
def generate_cache_key(interval, variant, ontology_terms, requested_outputs):
    return hash((
        interval.chromosome,
        interval.start,
        interval.end,
        variant.position if variant else None,
        variant.reference_bases if variant else None,
        variant.alternate_bases if variant else None,
        tuple(sorted(ontology_terms)),
        tuple(sorted(str(o) for o in requested_outputs))
    ))
```

### Cache Storage (Zarr)

```python
import zarr

cache = zarr.open("cache/predictions.zarr", mode='a')
key = generate_cache_key(...)

# Check cache
if key in cache:
    return cache[key]

# Query API
result = model.predict_variant(...)

# Store in cache
cache[key] = result
```

## Performance Optimization

### 1. Cache Aggressively

```python
# Cache all API calls
# ~100 MB per 1000 predictions
# Persist across sessions
```

### 2. Request Only Needed Modalities

```python
# Instead of:
requested_outputs = [
    OutputType.RNA_SEQ,
    OutputType.ATAC,
    OutputType.DNASE,
    OutputType.CAGE,
    # ... many more
]

# Do:
requested_outputs = [OutputType.RNA_SEQ]  # Only what you need
```

### 3. Use Appropriate Context Windows

```python
# For single exon variant
interval = expand_around_variant(variant, size=16_000)  # 16 KB

# For regulatory variant
interval = expand_around_variant(variant, size=500_000)  # 500 KB
```

### 4. Batch Similar Queries

```python
# Group by tissue/modality
liver_variants = [v for v in variants if v.tissue == 'liver']
for variant in liver_variants:
    # Same ontology_terms, more efficient caching
    outputs = model.predict_variant(..., ontology_terms=['UBERON:0002107'])
```

## Best Practices Summary

### DO

✅ Cache all API calls
✅ Use specific ontology terms
✅ Request only needed output types
✅ Handle rate limits gracefully
✅ Validate inputs before API call
✅ Use appropriate context windows
✅ Monitor API usage

### DON'T

❌ Don't make redundant API calls
❌ Don't request all modalities if not needed
❌ Don't exceed rate limits
❌ Don't commit API keys
❌ Don't use oversized context windows
❌ Don't ignore error handling

## References

- AlphaGenome API Docs: https://deepmind.google.com/science/alphagenome
- GitHub: https://github.com/google-deepmind/alphagenome
- UBERON Ontology: https://www.ebi.ac.uk/ols/ontologies/uberon
- gRPC Python: https://grpc.io/docs/languages/python/

---

**Version**: 1.0.0
**Last Updated**: October 2025
