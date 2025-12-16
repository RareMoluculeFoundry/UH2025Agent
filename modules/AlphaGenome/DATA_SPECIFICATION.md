# Data Specification: AlphaGenome API Data Formats

## Overview

Comprehensive specifications for AlphaGenome API input/output data formats.

## 1. Input Data Formats

### 1.1 Genomic Interval

**Class**: `alphagenome.data.genome.Interval`

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| chromosome | str | Chromosome name | 'chr1', 'chrX' |
| start | int | Start position (0-based) | 100000 |
| end | int | End position (exclusive) | 200000 |

**Constraints**:
- Chromosome: Must be valid (chr1-22, chrX, chrY, chrM)
- Start: Must be non-negative
- End: Must be > start
- Length: Must be ≤ 1,048,576 (1 MB)

**Example**:
```python
from alphagenome.data import genome

interval = genome.Interval(
    chromosome='chr1',
    start=100000,
    end=200000  # 100 KB region
)
```

### 1.2 Genetic Variant

**Class**: `alphagenome.data.genome.Variant`

**Attributes**:
| Attribute | Type | Description | Example |
|-----------|------|-------------|---------|
| chromosome | str | Chromosome name | 'chr1' |
| position | int | Position (1-based) | 150000 |
| reference_bases | str | Reference allele | 'A' |
| alternate_bases | str | Alternate allele | 'G' |

**Constraints**:
- Position: Must be within interval
- Bases: {A, C, G, T} (currently SNVs only)
- Length: reference and alternate must be same (SNV)

**Example**:
```python
variant = genome.Variant(
    chromosome='chr1',
    position=150000,
    reference_bases='A',
    alternate_bases='G'
)
```

### 1.3 Ontology Terms (Cell Types/Tissues)

**Format**: List of UBERON or Cell Ontology IDs

**Examples**:
```python
# Tissues
ontology_terms = ['UBERON:0002107']  # Liver

# Multiple tissues
ontology_terms = [
    'UBERON:0002107',  # Liver
    'UBERON:0002048',  # Lung
    'UBERON:0000955'   # Brain
]

# Cell types
ontology_terms = ['CL:0000084']  # T cell
```

**Common Terms**:
- Liver: UBERON:0002107
- Brain: UBERON:0000955
- Heart: UBERON:0000948
- Lung: UBERON:0002048
- Blood: UBERON:0000178

**Full ontology**: https://www.ebi.ac.uk/ols/ontologies/uberon

### 1.4 Requested Output Types

**Enum**: `alphagenome.models.dna_client.OutputType`

**Values**:
```python
OutputType.RNA_SEQ
OutputType.ATAC
OutputType.DNASE
OutputType.CAGE
OutputType.PROCAP
OutputType.CHIP_HISTONE
OutputType.CHIP_TF
OutputType.SPLICE_SITES
OutputType.SPLICE_SITE_USAGE
OutputType.SPLICE_JUNCTIONS
OutputType.CONTACT_MAPS
```

**Usage**:
```python
requested_outputs = [
    dna_client.OutputType.RNA_SEQ,
    dna_client.OutputType.ATAC
]
```

## 2. Output Data Formats

### 2.1 TrackData (1D Genomic Signals)

**Class**: `alphagenome.data.track_data.TrackData`

**Attributes**:
| Attribute | Type | Shape | Description |
|-----------|------|-------|-------------|
| interval | Interval | - | Genomic coordinates |
| values | np.ndarray | (n_tracks, n_positions) | Signal values |
| metadata | pd.DataFrame | (n_tracks,) | Track annotations |

**Example**:
```python
rna_seq = outputs.reference.rna_seq

# Access data
rna_seq.interval  # Interval('chr1', 100000, 200000)
rna_seq.values    # numpy array (10, 100000) - 10 transcripts, 100K positions
rna_seq.metadata  # DataFrame with track info

# Methods
resized = rna_seq.resize(50000)  # Change to 50 KB
sliced = rna_seq.slice(120000, 130000)  # Extract 10 KB region
df = rna_seq.to_dataframe()  # Convert to pandas
```

### 2.2 JunctionData (Splice Junctions)

**Class**: `alphagenome.data.junction_data.JunctionData`

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| interval | Interval | Genomic coordinates |
| values | np.ndarray | Junction read counts |
| junctions | List[Junction] | Junction annotations |

**Junction Class**:
| Attribute | Type | Description |
|-----------|------|-------------|
| start | int | Donor site position |
| end | int | Acceptor site position |
| strand | str | '+' or '-' |

**Example**:
```python
junctions = outputs.reference.splice_junctions

# Access junctions
for junction in junctions.junctions:
    print(f"{junction.start} -> {junction.end} ({junction.strand})")

# Read counts
counts = junctions.values  # numpy array
```

### 2.3 AnnData (ISM Results)

**Class**: `anndata.AnnData`

**Structure**:
```python
ism_results = model.score_ism_variants(...)

# Main data matrix
ism_results.X  # (n_variants, n_tracks) - scores

# Observations (variants)
ism_results.obs  # DataFrame with columns:
    # - position: int
    # - reference_base: str
    # - alternate_base: str
    # - variant_type: str

# Variables (tracks)
ism_results.var  # DataFrame with columns:
    # - modality: str (e.g., 'rna_seq')
    # - track_name: str

# Unstructured data
ism_results.uns  # Dict with:
    # - interval: Interval
    # - gene_id: str (if applicable)
    # - scorer_type: str
```

**Example**:
```python
# Get scores for all variants
scores = ism_results.X

# Filter high-impact variants
high_impact = ism_results[ism_results.X[:, 0] < -0.5]

# Export
ism_results.write('results.h5ad')  # Save to disk
```

### 2.4 VariantOutput (Variant Effect)

**Class**: `alphagenome.models.dna_output.VariantOutput`

**Attributes**:
| Attribute | Type | Description |
|-----------|------|-------------|
| reference | IntervalOutput | Reference allele predictions |
| alternate | IntervalOutput | Alternate allele predictions |

**IntervalOutput Attributes**:
```python
outputs.reference.rna_seq       # TrackData
outputs.reference.atac          # TrackData
outputs.reference.chip_histone  # TrackData
# ... (one attribute per requested output type)
```

**Example**:
```python
outputs = model.predict_variant(...)

# Compare reference vs alternate
ref_expr = outputs.reference.rna_seq.values
alt_expr = outputs.alternate.rna_seq.values
effect = alt_expr - ref_expr

# Effect size
max_effect = np.abs(effect).max()
mean_effect = np.abs(effect).mean()
```

## 3. Export Formats

### 3.1 BigWig (Genome Browser)

**Format**: Binary format for UCSC Genome Browser, IGV

**Export**:
```python
from code.visualization import exports

exports.to_bigwig(
    track_data,
    output_path='expression.bw',
    genome='hg38'
)
```

**Usage**:
- Upload to UCSC Genome Browser
- Load in IGV
- Visualize genomic tracks

### 3.2 BED (Peak Annotations)

**Format**: Tab-separated text file

**Columns**:
```
chrom    chromStart    chromEnd    name    score    strand
chr1     100000        100500      peak1   100      +
```

**Export**:
```python
exports.to_bed(
    peaks,
    output_path='peaks.bed',
    name_prefix='peak'
)
```

### 3.3 TSV (Variant Scores)

**Format**: Tab-separated values

**Columns**:
```
chromosome    position    ref    alt    effect_size    modality    tissue
chr1          150000      A      G      -0.45          rna_seq     liver
```

**Export**:
```python
exports.to_tsv(
    variant_effects,
    output_path='effects.tsv'
)
```

### 3.4 Parquet (Efficient Storage)

**Format**: Columnar binary format

**Export**:
```python
df.to_parquet('results.parquet', compression='snappy')
```

**Usage**: Fast queries, efficient storage

### 3.5 HDF5/Zarr (Arrays)

**Format**: Hierarchical data format

**Export**:
```python
# AnnData (HDF5)
ism_results.write('ism.h5ad')

# Zarr (cache format)
import zarr
zarr.save('predictions.zarr', predictions)
```

## 4. Cache Data Format

### Zarr Structure

```
cache/predictions.zarr/
├── variant_chr1_150000_A_G/
│   ├── interval
│   │   ├── chromosome
│   │   ├── start
│   │   └── end
│   ├── reference/
│   │   ├── rna_seq/
│   │   │   ├── values.array
│   │   │   └── metadata.json
│   │   ├── atac/
│   │   │   ├── values.array
│   │   │   └── metadata.json
│   └── alternate/
│       └── ... (same structure)
├── metadata.json
└── .zattrs
```

**Metadata**:
```json
{
    "cache_version": "1.0.0",
    "created": "2025-10-30T12:00:00",
    "alphagenome_version": "1.0.0"
}
```

## 5. Coordinate Systems

**AlphaGenome Uses**:
- **Interval**: 0-based, half-open [start, end)
- **Variant position**: 1-based

**Example**:
```python
# 0-based interval
interval = Interval('chr1', 100000, 100100)  # 100 bp region

# 1-based variant position
variant = Variant('chr1', 100050, 'A', 'G')  # Position 100050
```

**Conversion**:
```python
# VCF (1-based) to Interval (0-based)
vcf_pos = 100050
interval_start = vcf_pos - 1
interval_end = vcf_pos

# Interval (0-based) to VCF (1-based)
vcf_pos = interval_start + 1
```

## 6. Reference Genome

**Default**: hg38/GRCh38
**Assemblies**: Currently hg38 only

**Chromosome Names**:
- Autosomes: chr1, chr2, ..., chr22
- Sex chromosomes: chrX, chrY
- Mitochondrial: chrM

## 7. Data Quality and Validation

### Input Validation

```python
def validate_interval(interval):
    assert interval.end > interval.start
    assert interval.end - interval.start <= 1_048_576  # Max 1 MB
    assert interval.chromosome.startswith('chr')

def validate_variant(variant, interval):
    assert interval.start <= variant.position <= interval.end
    assert variant.reference_bases in {'A', 'C', 'G', 'T'}
    assert variant.alternate_bases in {'A', 'C', 'G', 'T'}
```

### Output Validation

```python
def validate_output(outputs):
    assert outputs.reference is not None
    assert outputs.alternate is not None
    assert outputs.reference.rna_seq.values.shape[1] > 0
    assert not np.isnan(outputs.reference.rna_seq.values).any()
```

## References

- AlphaGenome Data Classes: https://github.com/google-deepmind/alphagenome/tree/main/src/alphagenome/data
- Zarr Documentation: https://zarr.readthedocs.io/
- AnnData Documentation: https://anndata.readthedocs.io/
- UCSC BigWig: https://genome.ucsc.edu/goldenPath/help/bigWig.html
- BED Format: https://genome.ucsc.edu/FAQ/FAQformat.html#format1

---

**Version**: 1.0.0
**Last Updated**: October 2025
