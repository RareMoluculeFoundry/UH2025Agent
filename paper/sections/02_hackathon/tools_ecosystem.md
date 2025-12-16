# The Hackathon Tools Ecosystem

## Overview

The Undiagnosed Hackathon is not just a gathering of experts—it is a **technology integration laboratory**. The tools used at the hackathon represent the cutting edge of genomic analysis, carefully selected and integrated to maximize diagnostic yield within the 48-hour constraint.

This document catalogs the complete tools ecosystem, explaining not just what each tool does, but **how it integrates into the diagnostic workflow** and **why it was chosen**.

---

## 2.3.1 Sequencing Platform Partners

The hackathon uniquely integrates multiple sequencing technologies, each with distinct strengths:

### Illumina (Short-Read Sequencing)

| Aspect | Details |
|--------|---------|
| **Technology** | Short-read sequencing (150-300bp reads) |
| **Primary Use** | WGS, WES baseline analysis |
| **Strengths** | High accuracy, cost-effective, established pipelines |
| **Hackathon Role** | Foundation layer—all cases have Illumina data |
| **Integration** | DRAGEN pipeline for variant calling |

**Representative Present**: Technical team providing real-time pipeline support.

### Oxford Nanopore (Long-Read Sequencing)

| Aspect | Details |
|--------|---------|
| **Technology** | Nanopore long-read sequencing (10kb-100kb+ reads) |
| **Primary Use** | Structural variant detection, repeat expansions |
| **Strengths** | Detects variants invisible to short-read |
| **Hackathon Role** | "Second look" for WES-negative cases |
| **Key Tools** | Sniffles (SV calling), Modkit (methylation) |

**Critical Contribution**: The DNA2/Rothmund-Thomson case was solved using ONT long-read data that detected a deep intronic variant invisible to Illumina WGS.

### PacBio (HiFi Long-Read)

| Aspect | Details |
|--------|---------|
| **Technology** | HiFi long-read sequencing (15-20kb reads, >99.9% accuracy) |
| **Primary Use** | Phasing, tandem repeats, methylation |
| **Strengths** | Combines long-read length with high accuracy |
| **Hackathon Role** | Complex structural variants, phased haplotypes |
| **Key Tools** | pbsv (SV calling), TRGT (tandem repeats) |

**Unique Capability**: Native methylation calling enables episignature analysis without separate methylation arrays.

---

## 2.3.2 Variant Analysis Tools

### ClinVar (NCBI)

| Aspect | Details |
|--------|---------|
| **Type** | Curated variant-disease database |
| **Source** | National Center for Biotechnology Information |
| **Primary Use** | Known pathogenic variant lookup |
| **Hackathon Role** | First-pass filtering for known variants |
| **Query Rate** | ~10,000 variants per case |

**Integration**: ClinVar is the first tool queried after variant calling. Variants with "Pathogenic" or "Likely Pathogenic" classifications receive immediate attention.

### OMIM (Online Mendelian Inheritance in Man)

| Aspect | Details |
|--------|---------|
| **Type** | Disease gene catalog |
| **Source** | Johns Hopkins University |
| **Primary Use** | Gene-phenotype correlation |
| **Hackathon Role** | Phenotype-driven gene prioritization |
| **Coverage** | 7,000+ gene-disease relationships |

**Integration**: When clinicians propose candidate genes, OMIM validates whether the gene is associated with the observed phenotype.

### gnomAD (Genome Aggregation Database)

| Aspect | Details |
|--------|---------|
| **Type** | Population frequency database |
| **Source** | Broad Institute |
| **Primary Use** | Filter common variants |
| **Hackathon Role** | Identify rare variants (MAF < 0.01%) |
| **Coverage** | 140,000+ genomes, 125,000+ exomes |

**Critical Filter**: Variants present at >1% frequency in any population are deprioritized, as they are unlikely to cause rare disease.

---

## 2.3.3 Deep Learning Pathogenicity Tools

### AlphaMissense (DeepMind/Google)

| Aspect | Details |
|--------|---------|
| **Type** | AI pathogenicity predictor |
| **Source** | DeepMind / Google |
| **Primary Use** | Classify missense variants |
| **Coverage** | 89% of 71M possible missense variants |
| **Hackathon Role** | Prioritize novel missense variants |

**Key Insight**: Only ~7,000 missense variants have been manually classified. AlphaMissense extends coverage to 63+ million, enabling confident calls on novel variants.

```
Manual Classification:    ~7,000 variants (0.01%)
AlphaMissense Coverage:   ~63,000,000 variants (89%)
Gap Closed:               >9,000x improvement
```

### SpliceAI (Illumina)

| Aspect | Details |
|--------|---------|
| **Type** | Deep learning splice predictor |
| **Source** | Illumina |
| **Primary Use** | Predict splice-altering variants |
| **Accuracy** | ~95% for high-confidence predictions |
| **Hackathon Role** | Evaluate intronic and synonymous variants |

**Critical Contribution**: SpliceAI identified the pathogenic deep intronic variant in the DNA2 case that was missed by standard WGS pipelines.

### REVEL (Ensemble Score)

| Aspect | Details |
|--------|---------|
| **Type** | Ensemble pathogenicity score |
| **Source** | Multiple research groups |
| **Primary Use** | Combine multiple predictors |
| **Components** | 13 individual tools integrated |
| **Hackathon Role** | Meta-score for variant ranking |

### PrimateAI-3D (Illumina)

| Aspect | Details |
|--------|---------|
| **Type** | Cross-species conservation predictor |
| **Source** | Illumina |
| **Primary Use** | Identify functionally constrained positions |
| **Data** | 800+ primate genomes |
| **Hackathon Role** | Validate missense pathogenicity |

**Rationale**: Positions conserved across 800 primate species are likely functionally critical. Variants at these positions receive higher pathogenicity scores.

---

## 2.3.4 Long-Read Analysis Tools

### Sniffles (Structural Variant Caller)

| Aspect | Details |
|--------|---------|
| **Type** | Long-read SV caller |
| **Input** | ONT or PacBio aligned reads |
| **Primary Use** | Detect insertions, deletions, inversions, translocations |
| **Size Range** | 50bp to megabase-scale SVs |
| **Hackathon Role** | Find variants invisible to short-read |

**Example Command**:
```bash
sniffles --input aligned.bam --vcf output.vcf --reference hg38.fa
```

### Modkit (Methylation Analysis)

| Aspect | Details |
|--------|---------|
| **Type** | Methylation extraction tool |
| **Input** | ONT native methylation calls |
| **Primary Use** | Episignature analysis |
| **Output** | BED file with methylation frequencies |
| **Hackathon Role** | Identify methylation episignatures |

**Clinical Value**: Many imprinting disorders and epigenetic conditions have characteristic methylation patterns that serve as diagnostic episignatures.

### Squid (Transcriptomics Integration)

| Aspect | Details |
|--------|---------|
| **Type** | RNA-seq fusion/splice analyzer |
| **Primary Use** | Detect aberrant splicing, gene fusions |
| **Integration** | Validates DNA variants with RNA evidence |
| **Hackathon Role** | Functional validation of splice predictions |

---

## 2.3.5 Infrastructure Tools

### DRAGEN (Illumina)

| Aspect | Details |
|--------|---------|
| **Type** | Hardware-accelerated analysis pipeline |
| **Primary Use** | Rapid variant calling |
| **Speed** | WGS analysis in ~30 minutes |
| **Hackathon Role** | Foundation pipeline for all cases |

### Matchmaker Exchange

| Aspect | Details |
|--------|---------|
| **Type** | Federated case matching system |
| **Primary Use** | Find phenotypically similar cases globally |
| **Partners** | 9+ international databases |
| **Hackathon Role** | Identify n=2 matches for novel variants |

**The n=2 Solution**: When a novel variant-phenotype correlation is identified, Matchmaker Exchange can find confirming cases from partner databases without sharing patient data.

---

## 2.3.6 Tool Integration Model

The hackathon's power comes not from any single tool, but from **how tools are integrated** into a coherent workflow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    HACKATHON TOOL INTEGRATION MODEL                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   LAYER 1: DATA GENERATION                                               │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│   │  Illumina   │  │   Oxford    │  │   PacBio    │                     │
│   │  (WGS/WES)  │  │  Nanopore   │  │   (HiFi)    │                     │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│          │                │                │                             │
│          ▼                ▼                ▼                             │
│   LAYER 2: VARIANT CALLING                                               │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│   │   DRAGEN    │  │  Sniffles   │  │    pbsv     │                     │
│   │  (SNV/Indel)│  │    (SV)     │  │ (SV/Repeat) │                     │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│          │                │                │                             │
│          └────────────────┼────────────────┘                             │
│                           ▼                                              │
│   LAYER 3: ANNOTATION & FILTERING                                        │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│   │   ClinVar   │  │   gnomAD    │  │    OMIM     │                     │
│   │  (Known)    │  │ (Frequency) │  │ (Phenotype) │                     │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│          │                │                │                             │
│          └────────────────┼────────────────┘                             │
│                           ▼                                              │
│   LAYER 4: AI PATHOGENICITY                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│   │AlphaMissense│  │  SpliceAI   │  │   REVEL     │                     │
│   │ (Missense)  │  │  (Splice)   │  │ (Ensemble)  │                     │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     │
│          │                │                │                             │
│          └────────────────┼────────────────┘                             │
│                           ▼                                              │
│   LAYER 5: VALIDATION                                                    │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│   │   RNA-seq   │  │Methylation  │  │ Matchmaker  │                     │
│   │  (Squid)    │  │  (Modkit)   │  │  Exchange   │                     │
│   └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2.3.7 The "Tool List" as Diagnostic Currency

At the hackathon, clinicians don't just request "an analysis"—they create explicit **tool lists** that encode their diagnostic reasoning:

**Example Tool List (Ion Channel Disorder Hypothesis)**:

```yaml
hypothesis: "SCN4A-related periodic paralysis"
tool_list:
  - tool: ClinVar
    query: "SCN4A pathogenic variants"
    rationale: "Check for known disease-causing variants"

  - tool: SpliceAI
    query: "All intronic variants within 100bp of exon boundaries"
    rationale: "Identify cryptic splice sites"

  - tool: AlphaMissense
    query: "All missense variants in SCN4A"
    rationale: "Classify novel missense variants"

  - tool: gnomAD
    query: "Population frequency for candidates"
    rationale: "Filter variants >0.1% frequency"

  - tool: OMIM
    query: "SCN4A phenotype match"
    rationale: "Validate phenotype correlation"
```

This tool list format became the inspiration for the **Structuring Agent's output** in the UH2025-CDS-Agent system.

---

## 2.3.8 Tool Selection Philosophy

The hackathon's tool selection follows three principles:

### 1. Complementary Coverage

No single tool solves all cases. Tools are selected to cover different variant types:

| Variant Type | Primary Tool | Backup Tool |
|-------------|--------------|-------------|
| Missense | AlphaMissense | REVEL, PrimateAI-3D |
| Splice | SpliceAI | RNA-seq validation |
| Structural | Sniffles | pbsv |
| Repeat Expansion | TRGT | ExpansionHunter |
| Methylation | Modkit | Methylation array |

### 2. Validation Chains

Every AI prediction is validated by orthogonal evidence:

```
AlphaMissense "Pathogenic" → Functional study OR
                            Conservation (PrimateAI-3D) OR
                            Phenotype match (OMIM)

SpliceAI "Splice-altering" → RNA-seq aberrant splicing OR
                             In silico functional impact
```

### 3. Real-Time Adaptability

Tool developers are present to adjust parameters:

> "When the default AlphaMissense threshold produced too many false positives for a specific protein family, the Illumina team adjusted the model parameters during the hackathon."

This real-time optimization is formalized in the RLHF system (Section 7).

---

## References

- [3] Illumina Feature Article - Hackathon Technology Integration
- [11] Nature Genetics - Multi-omics Integration
- [15] Hackathon Participant Observations
- AlphaMissense: Science 2023
- SpliceAI: Cell 2019
- Sniffles: Nature Methods 2018
