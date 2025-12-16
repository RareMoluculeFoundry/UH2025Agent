# Data Specification: AlphaMissense Predictions

## Overview

This document provides comprehensive specifications for AlphaMissense prediction data files, database schemas, and data formats used in the module.

## 1. Source Data Files

### 1.1 AlphaMissense_hg38.tsv.gz

**Description**: Pre-computed pathogenicity predictions for all possible missense variants in canonical transcripts.

**Source**: https://console.cloud.google.com/storage/browser/dm_alphamissense
**GCS Path**: `gs://dm_alphamissense/AlphaMissense_hg38.tsv.gz`
**Size**: 642 MB (compressed), ~2.8 GB (uncompressed)
**Records**: ~71 million variants
**Format**: Tab-separated values (TSV), gzip compressed
**Reference Genome**: hg38/GRCh38
**Transcripts**: Canonical transcripts only (MANE Select when available)

**Columns** (10 total):
```
#CHROM  POS     REF  ALT  genome  uniprot_id     transcript_id        protein_variant  am_pathogenicity  am_class
chr1    69094   G    T    hg38    Q8NH21         ENST00000335137.4    V2L              0.2937            likely_benign
chr1    69094   G    C    hg38    Q8NH21         ENST00000335137.4    V2L              0.2937            likely_benign
chr1    69094   G    A    hg38    Q8NH21         ENST00000335137.4    V2S              0.0285            likely_benign
```

**Column Specifications**:
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| CHROM | STRING | Chromosome | chr1, chr2, ..., chrX, chrY, chrM |
| POS | INTEGER | Position (1-based, hg38) | 69094 |
| REF | STRING | Reference allele | A, C, G, T |
| ALT | STRING | Alternate allele | A, C, G, T |
| genome | STRING | Reference genome | hg38 |
| uniprot_id | STRING | UniProt accession | Q8NH21 |
| transcript_id | STRING | Ensembl transcript ID | ENST00000335137.4 |
| protein_variant | STRING | Protein variant (HGVS-like) | V2L (Val2Leu) |
| am_pathogenicity | FLOAT | Pathogenicity score [0-1] | 0.2937 |
| am_class | STRING | Classification | likely_benign, ambiguous, likely_pathogenic |

**Classification Thresholds**:
- **likely_benign**: am_pathogenicity < 0.34
- **ambiguous**: 0.34 ≤ am_pathogenicity ≤ 0.564
- **likely_pathogenic**: am_pathogenicity > 0.564

### 1.2 AlphaMissense_aa_substitutions.tsv.gz

**Description**: Pre-computed predictions for all amino acid substitutions (protein-centric, no genomic coordinates).

**GCS Path**: `gs://dm_alphamissense/AlphaMissense_aa_substitutions.tsv.gz`
**Size**: 1.2 GB (compressed)
**Records**: ~216 million substitutions
**Format**: Tab-separated values (TSV), gzip compressed

**Columns** (5 total):
```
uniprot_id     protein_variant  am_pathogenicity  am_class           transcript_id
Q8NH21         V2L              0.2937            likely_benign      ENST00000335137.4
Q8NH21         V2A              0.0412            likely_benign      ENST00000335137.4
```

**Use Cases**:
- Protein-centric analysis
- Saturation mutagenesis analysis
- No genomic coordinates needed

### 1.3 AlphaMissense_gene_hg38.tsv.gz

**Description**: Gene-level average pathogenicity scores.

**GCS Path**: `gs://dm_alphamissense/AlphaMissense_gene_hg38.tsv.gz`
**Size**: 254 KB (compressed)
**Records**: ~19,000 genes
**Format**: Tab-separated values (TSV), gzip compressed

**Columns**:
```
transcript_id        gene_symbol  mean_am_pathogenicity
ENST00000335137.4    OR4F5        0.4523
```

**Use Cases**:
- Gene burden analysis
- Gene prioritization
- Fast lookup without variant-level detail

---

## 2. Database Schema

### 2.1 DuckDB Index Structure

**Database**: `data/hg38.duckdb`
**Engine**: DuckDB 0.9.1+
**Size**: ~2 GB

#### Table: `variants`

**Schema**:
```sql
CREATE TABLE variants (
    CHROM VARCHAR NOT NULL,
    POS INTEGER NOT NULL,
    REF VARCHAR(1) NOT NULL,
    ALT VARCHAR(1) NOT NULL,
    genome VARCHAR DEFAULT 'hg38',
    uniprot_id VARCHAR,
    transcript_id VARCHAR,
    protein_variant VARCHAR,
    am_pathogenicity FLOAT NOT NULL,
    am_class VARCHAR NOT NULL,
    PRIMARY KEY (CHROM, POS, REF, ALT)
);

CREATE INDEX idx_uniprot ON variants(uniprot_id, protein_variant);
CREATE INDEX idx_transcript ON variants(transcript_id);
CREATE INDEX idx_pathogenicity ON variants(am_pathogenicity DESC);
CREATE INDEX idx_class ON variants(am_class);
```

**Constraints**:
- CHROM: Must match pattern `chr[1-22XYM]`
- POS: Must be positive integer
- REF, ALT: Must be one of {A, C, G, T}
- am_pathogenicity: Must be in range [0, 1]
- am_class: Must be one of {likely_benign, ambiguous, likely_pathogenic}

#### Table: `metadata`

**Schema**:
```sql
CREATE TABLE metadata (
    key VARCHAR PRIMARY KEY,
    value VARCHAR
);

INSERT INTO metadata VALUES
    ('data_version', '2023-09'),
    ('reference_genome', 'hg38'),
    ('n_variants', '71185048'),
    ('created_date', '2025-10-30'),
    ('source_url', 'gs://dm_alphamissense/AlphaMissense_hg38.tsv.gz');
```

### 2.2 Query Patterns

**Single Variant Lookup**:
```sql
SELECT am_pathogenicity, am_class, protein_variant, uniprot_id
FROM variants
WHERE CHROM = 'chr17' AND POS = 43044295 AND REF = 'G' AND ALT = 'A';
```

**Batch Lookup** (parameterized):
```sql
SELECT *
FROM variants
WHERE (CHROM, POS, REF, ALT) IN (VALUES
    ('chr1', 12345, 'A', 'G'),
    ('chr2', 23456, 'C', 'T'),
    ...
);
```

**Gene Variants**:
```sql
SELECT *
FROM variants
WHERE transcript_id LIKE 'ENST00000269305%'  -- TP53
ORDER BY am_pathogenicity DESC;
```

**Pathogenic Filtering**:
```sql
SELECT *
FROM variants
WHERE am_pathogenicity > 0.564
  AND CHROM IN ('chr1', 'chr2', ...)
ORDER BY am_pathogenicity DESC
LIMIT 1000;
```

---

## 3. Input Data Formats

### 3.1 VCF (Variant Call Format)

**Standard**: VCF 4.2+
**Coordinates**: 1-based, hg38/GRCh38

**Required Fields**:
```vcf
##fileformat=VCFv4.2
##reference=GRCh38
#CHROM  POS      ID   REF  ALT  QUAL  FILTER  INFO
chr17   43044295  .    G    A    100   PASS    .
chr13   32890572  .    C    T    95    PASS    .
```

**After Annotation** (added INFO fields):
```vcf
##INFO=<ID=AM_SCORE,Number=1,Type=Float,Description="AlphaMissense pathogenicity score">
##INFO=<ID=AM_CLASS,Number=1,Type=String,Description="AlphaMissense classification">
#CHROM  POS      ID   REF  ALT  QUAL  FILTER  INFO
chr17   43044295  .    G    A    100   PASS    AM_SCORE=0.789;AM_CLASS=likely_pathogenic
```

**Multi-allelic Sites**:
```vcf
chr1    12345    .    A    G,T    100   PASS    AM_SCORE=0.45,0.78;AM_CLASS=ambiguous,likely_pathogenic
```

### 3.2 TSV (Tab-Separated Values)

**Format**: Tab-delimited text file
**Header**: Required

**Required Columns**:
- CHROM (or chromosome, chr)
- POS (or position, start)
- REF (or reference, ref_allele)
- ALT (or alternate, alt_allele)

**Example**:
```tsv
CHROM\tPOS\tREF\tALT\tGENE
chr17\t43044295\tG\tA\tBRCA1
chr13\t32890572\tC\tT\tBRCA2
```

**After Annotation**:
```tsv
CHROM\tPOS\tREF\tALT\tGENE\tam_pathogenicity\tam_class
chr17\t43044295\tG\tA\tBRCA1\t0.789\tlikely_pathogenic
chr13\t32890572\tC\tT\tBRCA2\t0.456\tambiguous
```

### 3.3 DataFrame (pandas)

**Format**: pandas DataFrame
**Required Columns**: CHROM, POS, REF, ALT

**Example**:
```python
import pandas as pd

variants = pd.DataFrame({
    'CHROM': ['chr17', 'chr13'],
    'POS': [43044295, 32890572],
    'REF': ['G', 'C'],
    'ALT': ['A', 'T'],
    'gene': ['BRCA1', 'BRCA2']
})
```

**After Annotation**:
```python
# Adds columns: am_pathogenicity, am_class, protein_variant, uniprot_id
annotated = filtering.annotate_dataframe(variants)
```

---

## 4. Output Data Formats

### 4.1 Annotated VCF

**INFO Fields Added**:
```vcf
##INFO=<ID=AM_SCORE,Number=A,Type=Float,Description="AlphaMissense pathogenicity score [0-1]">
##INFO=<ID=AM_CLASS,Number=A,Type=String,Description="AlphaMissense classification (likely_benign|ambiguous|likely_pathogenic)">
##INFO=<ID=AM_PROTEIN,Number=A,Type=String,Description="Protein variant (HGVS-like, e.g., V175H)">
##INFO=<ID=AM_UNIPROT,Number=A,Type=String,Description="UniProt accession">
```

### 4.2 TSV Export

**Columns**:
- All input columns (preserved)
- `am_pathogenicity`: Float [0-1]
- `am_class`: String {likely_benign, ambiguous, likely_pathogenic}
- `protein_variant`: String (e.g., "V175H")
- `uniprot_id`: String (e.g., "P04637")
- `transcript_id`: String (e.g., "ENST00000269305.8")

### 4.3 Parquet Export

**Format**: Apache Parquet (columnar)
**Schema**:
```python
{
    'CHROM': 'string',
    'POS': 'int32',
    'REF': 'string',
    'ALT': 'string',
    'am_pathogenicity': 'float32',
    'am_class': 'category',  # Efficient for categorical data
    'protein_variant': 'string',
    'uniprot_id': 'string',
    'transcript_id': 'string'
}
```

**Compression**: Snappy (default) or Gzip
**Use Case**: Efficient storage and fast queries

---

## 5. Validation Datasets

### 5.1 ClinVar Gold Standard

**File**: `tests/fixtures/clinvar_subset.tsv`
**Size**: 10,000 variants
**Composition**: 5,000 pathogenic + 5,000 benign
**Purpose**: Validation of AlphaMissense predictions

**Source**: ClinVar (https://ftp.ncbi.nlm.nih.gov/pub/clinvar/)
**Filters**:
- Review status: ≥1 star (single submitter or better)
- Classification: Pathogenic/Likely_pathogenic OR Benign/Likely_benign
- Molecular consequence: Missense variant
- Reference genome: GRCh38

**Schema**:
```tsv
CHROM\tPOS\tREF\tALT\tgene\tclinvar_class\treview_status\tam_pathogenicity\tam_class
chr17\t43044295\tG\tA\tBRCA1\tPathogenic\t2\t0.789\tlikely_pathogenic
```

**Expected Performance**:
- Sensitivity: >80% (pathogenic correctly classified)
- Specificity: >85% (benign correctly classified)
- Balanced accuracy: >82%

### 5.2 Sample VCF

**File**: `tests/fixtures/sample.vcf`
**Size**: 100 variants
**Composition**: Balanced across pathogenicity classes

**Breakdown**:
- 30 likely pathogenic (AM score > 0.564)
- 40 ambiguous (AM score 0.34-0.564)
- 30 likely benign (AM score < 0.34)

**Use Case**: Quick testing, example data

### 5.3 Gene List

**File**: `tests/fixtures/genes.txt`
**Size**: 100 genes
**Purpose**: Gene burden analysis testing

**Composition**:
- 50 known disease genes (high burden expected)
- 50 housekeeping genes (low burden expected)

---

## 6. Data Quality and Validation

### 6.1 Data Integrity Checks

**File-Level Checks**:
```python
def validate_download(file_path):
    """Validate downloaded file."""
    # Check file size
    assert os.path.getsize(file_path) > 600_000_000  # >600 MB

    # Check gzip integrity
    with gzip.open(file_path, 'rt') as f:
        first_line = f.readline()
        assert first_line.startswith('#CHROM')

    # Check record count (sample)
    line_count = count_lines(file_path)
    assert line_count > 70_000_000  # ~71M + header
```

**Database-Level Checks**:
```python
def validate_database(db_path):
    """Validate DuckDB database."""
    conn = duckdb.connect(db_path)

    # Check record count
    count = conn.execute("SELECT COUNT(*) FROM variants").fetchone()[0]
    assert count > 70_000_000

    # Check score range
    min_score, max_score = conn.execute(
        "SELECT MIN(am_pathogenicity), MAX(am_pathogenicity) FROM variants"
    ).fetchone()
    assert 0 <= min_score <= max_score <= 1

    # Check chromosome coverage
    chroms = conn.execute("SELECT DISTINCT CHROM FROM variants").fetchall()
    expected_chroms = {f'chr{i}' for i in range(1, 23)} | {'chrX', 'chrY'}
    assert set(c[0] for c in chroms) >= expected_chroms
```

### 6.2 Query Validation

**Lookup Validation**:
```python
def validate_query_result(result):
    """Validate query result."""
    if result is not None:
        assert 'am_pathogenicity' in result
        assert 0 <= result['am_pathogenicity'] <= 1
        assert result['am_class'] in {'likely_benign', 'ambiguous', 'likely_pathogenic'}
```

---

## 7. Performance Specifications

### 7.1 Query Performance

| Operation | Variants | Expected Time | Throughput |
|-----------|----------|---------------|------------|
| Single lookup | 1 | <1 ms | >1000/sec |
| Batch lookup | 100 | <100 ms | >1000/sec |
| Batch lookup | 1,000 | <1 sec | ~1000/sec |
| VCF annotation | 10,000 | <10 sec | ~1000/sec |
| Gene query | 1 gene | <100 ms | ~10/sec |

### 7.2 Storage Requirements

| Component | Size | Notes |
|-----------|------|-------|
| Download (compressed) | 642 MB | One-time |
| Download (uncompressed) | ~2.8 GB | Temporary |
| DuckDB database | ~2 GB | Indexed, permanent |
| Cache (optional) | ~500 MB | LRU cache of queries |
| **Total** | **~3 GB** | |

### 7.3 Memory Requirements

| Operation | Peak Memory | Notes |
|-----------|-------------|-------|
| Indexing | ~4 GB | One-time setup |
| Query (single) | <100 MB | Typical usage |
| Query (batch 1k) | ~500 MB | Batch processing |
| VCF annotation | ~1 GB | Large VCF files |

---

## 8. Data Versioning

### 8.1 AlphaMissense Data Version

**Current Version**: 2023-09 (September 2023, publication release)
**Last Updated**: Not updated since publication
**Versioning**: No formal versioning system

**Tracking**:
```sql
SELECT value FROM metadata WHERE key = 'data_version';
-- Returns: '2023-09'
```

### 8.2 Database Schema Version

**Current Version**: 1.0.0
**Schema Changes**: Track in `metadata` table

```sql
INSERT INTO metadata VALUES ('schema_version', '1.0.0');
```

### 8.3 Future Updates

**If AlphaMissense releases new predictions**:
1. Download new file
2. Create new database (e.g., `hg38_v2.duckdb`)
3. Update metadata table with new version
4. Provide migration script for existing analyses

---

## 9. Data Licensing

**AlphaMissense Predictions**: CC-BY 4.0 (Google DeepMind)
- Free for academic and commercial use
- Attribution required (cite publication)
- Modifications allowed

**ClinVar Data**: Public domain (NCBI)
- Free for any use
- No attribution required (but recommended)

**Module Code**: Apache 2.0 (DeLab)
- Open source
- Free for any use

---

## 10. References

**Data Sources**:
- AlphaMissense predictions: https://console.cloud.google.com/storage/browser/dm_alphamissense
- ClinVar database: https://ftp.ncbi.nlm.nih.gov/pub/clinvar/
- gnomAD: https://gnomad.broadinstitute.org/
- Ensembl: https://www.ensembl.org/

**File Formats**:
- VCF specification: https://samtools.github.io/hts-specs/VCFv4.2.pdf
- TSV: Plain text, tab-separated
- Parquet: https://parquet.apache.org/

**Coordinate Systems**:
- hg38/GRCh38: https://www.ncbi.nlm.nih.gov/assembly/GCF_000001405.26/
- 1-based positions (VCF standard)

---

**Document Version**: 1.0.0
**Last Updated**: October 2025
