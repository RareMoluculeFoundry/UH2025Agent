# Hackathon Case Studies: Breakthroughs in 48 Hours

## Overview

The Undiagnosed Hackathon has produced diagnostic breakthroughs that validate both the collaborative model and the multi-omics approach. This document presents three detailed case studies that illustrate how cases that stumped specialists for years were solved in hours.

Each case study highlights:

- **The diagnostic odyssey**: Years of failed attempts
- **The hackathon approach**: What made the difference
- **The technical breakthrough**: Specific tools and data that cracked the case
- **The system lesson**: What this teaches us about AI system design

---

## Case Study 1: DNA2 / Rothmund-Thomson Syndrome

### The Patient

A child presenting with:

- Poikiloderma (mottled skin pigmentation)
- Skeletal abnormalities
- Growth retardation
- Premature aging features

### The Diagnostic Odyssey (Pre-Hackathon)

| Year | Workup | Result |
|------|--------|--------|
| Year 1 | Clinical genetics evaluation | "Suspected RTS, gene unknown" |
| Year 2 | Whole Exome Sequencing (WES) | No pathogenic variants |
| Year 3 | Targeted RECQL4 sequencing | Negative |
| Year 4 | Re-analysis with updated databases | Still negative |
| Year 5 | Referred to hackathon | "Diagnostic odyssey" |

**Five years. Multiple institutions. No diagnosis.**

### The Hackathon Breakthrough (48 Hours)

**Hour 0-4: Case Assignment**

The diagnostic team reviewed the phenotype and prior workup:

- Strong clinical suspicion for Rothmund-Thomson Syndrome (RTS)
- RECQL4 negative (the known RTS gene)
- WES negative
- Hypothesis: "There must be a variant WES couldn't see"

**Hour 4-12: Multi-Omics Analysis**

The team requested long-read sequencing data from Oxford Nanopore:

```
Request: "Run ONT long-read on regions surrounding RECQL4 and related genes"
```

Simultaneously, RNA-seq was analyzed for aberrant splicing patterns.

**Hour 12-18: The Discovery**

Long-read sequencing revealed a **deep intronic variant in DNA2**:

```
Variant: DNA2:c.1764+1542G>A
Location: Deep intronic (1.5kb from exon)
Short-read: NOT DETECTED (insufficient coverage in intronic regions)
Long-read: DETECTED with 25x coverage
```

**Hour 18-24: Functional Validation**

RNA-seq confirmed the variant's pathogenicity:

```
Normal:   Exon 14 ────────────── Exon 15
Patient:  Exon 14 ── CRYPTIC EXON ── Exon 15
          (aberrant splicing confirmed)
```

**Hour 24-36: Literature and Confirmation**

- DNA2 had recently been associated with RTS-like phenotypes
- SpliceAI predicted the variant would create a cryptic splice site
- AlphaMissense: N/A (intronic variant)
- Functional impact: Premature termination codon

**Hour 36-48: Diagnosis Confirmed**

🔔 **Bell rings**: Rothmund-Thomson Syndrome Type 3 (DNA2-related)

### Technical Lessons

| What Failed | What Worked | System Implication |
|-------------|-------------|-------------------|
| WES | Long-read sequencing | Multi-omics is essential |
| Known gene panels | Unbiased genome-wide analysis | Don't anchor on "usual suspects" |
| Standard pipelines | Deep intronic variant calling | Custom analysis pipelines |
| Sequential workup | Parallel RNA + DNA analysis | Concurrent data integration |

### System Design Lesson

> **The Executor Agent must integrate long-read and RNA-seq data by default for WES-negative cases.**

---

## Case Study 2: Low-Level Mosaicism Detection

### The Patient

An adult with:

- Segmental skin abnormalities (following Blaschko's lines)
- Asymmetric limb development
- Normal intelligence
- No family history

### The Diagnostic Odyssey (Pre-Hackathon)

| Year | Workup | Result |
|------|--------|--------|
| Year 1 | Clinical evaluation | "Possible mosaic condition" |
| Year 2 | Blood WES | No pathogenic variants |
| Year 3 | Skin biopsy WES | No variants at standard threshold |
| Year 4 | Repeat analysis | "Variant of Uncertain Significance" at 8% VAF |
| Year 6 | Referred to hackathon | VUS remained unresolved |

**The Challenge**: Mosaic variants occur at low allele frequencies (5-20%), below the detection threshold of standard variant calling.

### The Hackathon Breakthrough (48 Hours)

**Hour 0-8: Hypothesis Formation**

The diagnostic team hypothesized:

> "This is likely mosaic PIK3CA or a related pathway gene. The VUS at 8% VAF is probably real but below confidence threshold."

**Hour 8-16: Deep Sequencing Analysis**

The team requested:

1. Ultra-deep targeted sequencing (1000x coverage)
2. Tissue-specific analysis (affected skin vs. blood)
3. Low-frequency variant calling with specialized parameters

```yaml
Tool: Mutect2 (mosaic mode)
Parameters:
  min_allele_fraction: 0.03
  min_reads: 5
  tissue_comparison: skin_vs_blood
```

**Hour 16-24: Confirmation**

The variant was confirmed as mosaic:

| Tissue | VAF | Reads |
|--------|-----|-------|
| Blood | 3% | 30/1000 |
| Affected skin | 18% | 180/1000 |
| Unaffected skin | 5% | 50/1000 |

**Hour 24-36: Functional Validation**

- Gene: PIK3CA
- Variant: c.3140A>G (p.His1047Arg)
- Known oncogenic mutation (somatic in cancer)
- In germline mosaic form: PIK3CA-related Overgrowth Spectrum (PROS)

**Hour 36-48: Clinical Correlation**

The mosaic distribution explained:

- Segmental pattern (affected cells carry variant)
- No family history (post-zygotic mutation)
- Normal development in unaffected regions

🔔 **Bell rings**: PIK3CA-related Overgrowth Spectrum (PROS)

### Technical Lessons

| What Failed | What Worked | System Implication |
|-------------|-------------|-------------------|
| Standard VAF threshold (20%) | Low-frequency calling (3%) | Adjustable thresholds |
| Blood-only sampling | Tissue-specific analysis | Multi-tissue support |
| Binary pathogenic/benign | Probability-based calling | Confidence scoring |
| Single-sample analysis | Paired tissue comparison | Comparative analysis |

### System Design Lesson

> **The Structuring Agent must recognize mosaic phenotypes and request tissue-specific, low-frequency variant analysis.**

---

## Case Study 3: Methylation Episignature Discovery

### The Patient

A child with:

- Intellectual disability
- Distinctive facial features
- Hypotonia
- No pathogenic variants on comprehensive testing

### The Diagnostic Odyssey (Pre-Hackathon)

| Year | Workup | Result |
|------|--------|--------|
| Year 1 | Chromosomal microarray | Normal |
| Year 2 | WES | No pathogenic variants |
| Year 3 | Trio WES (parents included) | De novo VUS in chromatin modifier |
| Year 4 | Functional studies | Inconclusive |
| Year 5 | Referred to hackathon | "Is this VUS pathogenic?" |

**The Challenge**: A de novo variant in a gene associated with chromatin modification, but insufficient evidence for pathogenicity.

### The Hackathon Breakthrough (48 Hours)

**Hour 0-8: Hypothesis Formation**

The team noted:

> "Chromatin modifier genes often have characteristic methylation episignatures. If this VUS is pathogenic, the patient should have the episignature."

**Hour 8-16: Methylation Analysis**

Using native methylation from long-read sequencing (Oxford Nanopore + Modkit):

```bash
modkit pileup patient.bam methylation.bed --ref hg38.fa
```

The team compared the patient's methylation profile to:

1. Reference population (gnomAD-like for methylation)
2. Known disease episignatures (EpiSign database)
3. Family members (parents as controls)

**Hour 16-28: Pattern Recognition**

The patient's methylation profile showed:

```
Episignature Match Score:
- Kabuki Syndrome Type 1:     0.12 (no match)
- Kabuki Syndrome Type 2:     0.08 (no match)
- CHARGE Syndrome:            0.15 (no match)
- Novel Chromatin Disorder:   0.89 (STRONG MATCH)
```

The VUS created a novel episignature matching 3 other patients in the global database with the same gene disruption.

**Hour 28-40: Validation**

- The episignature was absent in parents (confirming de novo)
- The pattern was consistent across CpG sites genome-wide
- Functional prediction: Loss of histone methyltransferase activity

**Hour 40-48: Diagnosis and Publication Preparation**

🔔 **Bell rings**: Novel chromatin modification disorder

The case contributed to defining a new disease entity, with the hackathon providing the n=4 confirmation needed for publication.

### Technical Lessons

| What Failed | What Worked | System Implication |
|-------------|-------------|-------------------|
| Variant-only analysis | Epigenetic profiling | Multi-layer data integration |
| Binary classification | Signature matching | Pattern recognition |
| Single-case analysis | Global database comparison | Federated case matching |
| Waiting for functional studies | Computational episignature | Rapid functional inference |

### System Design Lesson

> **The Executor Agent must include methylation analysis for chromatin-related VUS, using episignature matching against global databases.**

---

## Summary: What the Cases Teach Us

### Pattern 1: WES is Necessary but Not Sufficient

All three cases had negative WES. The breakthroughs required:

- Long-read sequencing (Case 1)
- Tissue-specific deep sequencing (Case 2)
- Methylation profiling (Case 3)

**System Implication**: The agent must recommend multi-omics escalation for WES-negative cases.

### Pattern 2: Standard Parameters Miss Cases

Default thresholds and standard pipelines failed:

- Deep intronic variants (Case 1): Outside standard coverage
- Low-frequency mosaics (Case 2): Below standard VAF threshold
- Episignatures (Case 3): Not in standard variant workflow

**System Implication**: The Structuring Agent must recognize when to adjust parameters based on phenotype.

### Pattern 3: Global Comparison Enables Confirmation

Each case benefited from global data:

- DNA2 literature (Case 1): Recent gene-disease association
- PIK3CA knowledge (Case 2): Known oncogenic variant in new context
- EpiSign database (Case 3): Novel episignature matching n=4

**System Implication**: The Rare Arena Network must enable secure global case matching.

### Pattern 4: The 48-Hour Cycle Works

All cases were solved within 48 hours, after years of diagnostic odyssey:

| Case | Odyssey Duration | Hackathon Time |
|------|------------------|----------------|
| DNA2 | 5 years | 36 hours |
| Mosaicism | 6 years | 32 hours |
| Episignature | 5 years | 40 hours |

**System Implication**: The parallel, multi-expert model is fundamentally more effective than sequential care.

---

## References

- [24] PubMed - DNA2 Case Study
- [11] Nature Genetics - Multi-omics Necessity
- [15] Hackathon Participant Observations
- EpiSign Database (episignatures.com)
- gnomAD v4.0 (population frequencies)
- ClinVar (variant classification)
