# Genomics and Variant Interpretation Primer

**Understanding the Technical Foundation of Genetic Diagnosis**

---

## From DNA to Diagnosis

### The Central Flow

```
Patient → Sample → Sequencing → Variants → Interpretation → Diagnosis
```

Each step involves technology, expertise, and potential for error:

| Step | Technology | Key Considerations |
|------|------------|-------------------|
| **Sample** | Blood, saliva, tissue | Quality, contamination |
| **Sequencing** | NGS platforms | Coverage, accuracy |
| **Alignment** | Bioinformatics | Reference genome choice |
| **Variant Calling** | Computational | Sensitivity vs specificity |
| **Annotation** | Databases | Completeness, currency |
| **Interpretation** | Clinical expertise | Guidelines, judgment |
| **Diagnosis** | Integration | Phenotype-genotype correlation |

### Sequencing Technologies

| Technology | Description | Use Case |
|------------|-------------|----------|
| **Targeted panels** | Specific gene sets | Known disease families |
| **Whole Exome (WES)** | All coding regions (~2% of genome) | Most clinical rare disease |
| **Whole Genome (WGS)** | Complete genome | Research, comprehensive analysis |
| **RNA-seq** | Expressed genes | Functional validation |
| **Long-read** | PacBio, Oxford Nanopore | Structural variants, repeats |

### Reference Genomes

All variants are defined relative to a reference:

| Version | Name | Notes |
|---------|------|-------|
| **GRCh37** | hg19 | Legacy, still widely used |
| **GRCh38** | hg38 | Current standard |
| **T2T-CHM13** | Complete | Telomere-to-telomere, newest |

**Critical**: Ensure consistent reference use throughout analysis. Mixing references causes errors.

---

## Understanding Variants

### Types of Genetic Variants

#### Single Nucleotide Variants (SNVs)

The most common type—a single base change:

```
Reference: ...ATCGATCG...
Variant:   ...ATCAATCG...
                 ^
             G → A
```

**Effects:**
- **Synonymous**: Same amino acid (often benign)
- **Missense**: Different amino acid (variable effect)
- **Nonsense**: Premature stop codon (usually damaging)

#### Insertions and Deletions (Indels)

Small additions or removals of bases:

```
Reference: ...ATCGATCG...
Insertion: ...ATCGAATCG...
                 ^
              Added 'A'

Reference: ...ATCGATCG...
Deletion:  ...ATCGTCG...
               ^
            Removed 'A'
```

**Frameshift**: If indel length isn't divisible by 3, it shifts the reading frame—usually severe.

#### Copy Number Variants (CNVs)

Larger deletions or duplications of genomic segments:

- **Deletion**: Loss of a region (can lose entire genes)
- **Duplication**: Extra copies of a region
- Range from kilobases to megabases

#### Structural Variants (SVs)

Large-scale rearrangements:

- **Inversions**: Segment flipped
- **Translocations**: Segment moved between chromosomes
- **Complex rearrangements**: Multiple events

#### Repeat Expansions

Repeated sequences that grow abnormally:

- **Trinucleotide repeats**: e.g., CAG in Huntington's
- **Larger repeats**: Various neurological conditions
- Often not detected by standard short-read sequencing

---

## Variant Annotation

### Genomic Position

Every variant has coordinates:

```
Chromosome: Position Reference>Alternate

Example: chr17:7579472 G>A
         ^^^^^ ^^^^^^^ ^ ^
         chr   position ref alt
```

### HGVS Nomenclature

Standard naming system for variants:

| Type | Format | Example |
|------|--------|---------|
| **Genomic** | g. | NC_000017.11:g.7579472G>A |
| **Coding** | c. | NM_000546.6:c.817C>T |
| **Protein** | p. | NP_000537.3:p.Arg273Cys |

### Transcript Consequences

Same genomic variant can have different effects depending on transcript:

```
Gene: TP53
Variant: chr17:7579472 G>A

Transcript 1: NM_000546 → Missense (p.Arg273Cys)
Transcript 2: NM_001126112 → Synonymous
Transcript 3: NM_001276695 → Intronic
```

**Always consider canonical/clinical transcript for interpretation.**

---

## The ACMG/AMP Classification Framework

### The Five-Tier System

The 2015 ACMG/AMP guidelines standardized variant classification:

| Class | Meaning | Clinical Action |
|-------|---------|-----------------|
| **Pathogenic** | Causes disease | Report, act on |
| **Likely Pathogenic** | >90% likely to cause disease | Report, act with caution |
| **VUS** | Uncertain significance | Report, don't act on |
| **Likely Benign** | >90% likely benign | Usually don't report |
| **Benign** | Does not cause disease | Don't report |

### Evidence Categories

Classification combines multiple types of evidence:

#### Population Data (PM2, BA1, BS1)

| Code | Meaning | Example |
|------|---------|---------|
| **BA1** | Too common to be pathogenic | >5% in gnomAD |
| **BS1** | Greater than expected frequency | >1% depending on disease |
| **PM2** | Absent from controls | Not in gnomAD |

#### Computational Evidence (PP3, BP4)

| Code | Meaning | Tools |
|------|---------|-------|
| **PP3** | Computational evidence of damaging effect | REVEL, CADD, SpliceAI |
| **BP4** | Computational evidence of benign effect | Same tools, opposite prediction |

#### Functional Data (PS3, BS3)

| Code | Meaning | Example |
|------|---------|---------|
| **PS3** | Well-established functional studies show damaging | Cell assay shows loss of function |
| **BS3** | Well-established functional studies show benign | Assay shows normal function |

#### Segregation (PP1, BS4)

| Code | Meaning | Example |
|------|---------|---------|
| **PP1** | Co-segregates with disease in family | Variant present in all affected |
| **BS4** | Doesn't segregate with disease | Variant in unaffected family |

#### De Novo Data (PS2, PM6)

| Code | Meaning | Example |
|------|---------|---------|
| **PS2** | De novo with confirmed parentage | Both parents tested, neither has variant |
| **PM6** | Assumed de novo | Parents not tested |

### Combining Evidence

Rules for combining evidence into final classification:

**Pathogenic requires:**
- 1 Very Strong (PVS1) + 1 Strong (PS1-4), OR
- 1 Very Strong + 2 Moderate (PM1-6), OR
- 2 Strong, OR
- 1 Strong + 3 Moderate, OR
- 1 Strong + 2 Moderate + 2 Supporting (PP1-5)

**And similar rules for other categories...**

---

## Key Databases

### ClinVar

**Purpose**: Aggregates variant clinical interpretations

| Feature | Description |
|---------|-------------|
| **Submissions** | Labs submit interpretations |
| **Review status** | Stars indicate agreement level |
| **Conflicts** | Different labs may disagree |
| **Conditions** | Links variants to diseases |

**Interpretation:**
- ★★★★ Expert panel reviewed
- ★★★ Multiple submitters, no conflict
- ★★ Multiple submitters, some conflict
- ★ Single submitter

**Critical**: ClinVar reflects submitter opinions. Expert review essential.

### OMIM (Online Mendelian Inheritance in Man)

**Purpose**: Catalog of human genes and genetic disorders

| Content | Example |
|---------|---------|
| **Gene entries** | Gene function, associated diseases |
| **Phenotype entries** | Disease descriptions, genetics |
| **Genotype-phenotype** | Gene-disease relationships |

**MIM Numbers:**
- \* Gene with known sequence
- \# Phenotype with known molecular basis
- \+ Gene and phenotype combined
- % Phenotype with unknown molecular basis

### gnomAD (Genome Aggregation Database)

**Purpose**: Population allele frequencies

| Dataset | Samples | Use |
|---------|---------|-----|
| **gnomAD v4** | 800,000+ | Current standard |
| **ExAC** | 60,000 | Legacy, exome only |

**Key metrics:**
- **Allele frequency**: How common is this variant?
- **Homozygote count**: How many have two copies?
- **Population breakdown**: Frequency varies by ancestry

**Filtering:**
- AF >1% → Likely benign (most Mendelian diseases)
- AF >0.1% → Unlikely pathogenic for severe dominant
- Absent → Could be pathogenic (or very rare benign)

### HPO (Human Phenotype Ontology)

**Purpose**: Standardized vocabulary for clinical features

| Term | ID | Definition |
|------|-----|------------|
| Seizures | HP:0001250 | Abnormal brain electrical activity |
| Hypotonia | HP:0001252 | Decreased muscle tone |
| Intellectual disability | HP:0001249 | Below-average cognitive function |

**Uses:**
- Consistent phenotype description
- Computational phenotype matching
- Cross-referencing with gene databases

---

## Pathogenicity Prediction Tools

### AlphaMissense

**Developer**: DeepMind
**Method**: Protein structure-based prediction using AlphaFold

| Score | Interpretation |
|-------|---------------|
| >0.564 | Likely pathogenic |
| 0.34-0.564 | Uncertain |
| <0.34 | Likely benign |

**Coverage**: 71 million missense variants
**Limitation**: Missense only; doesn't predict splicing or truncation

### SpliceAI

**Developer**: Illumina
**Method**: Deep learning for splice site prediction

| Delta Score | Interpretation |
|-------------|---------------|
| >0.8 | High likelihood of splicing impact |
| 0.5-0.8 | Moderate evidence |
| 0.2-0.5 | Weak evidence |
| <0.2 | Unlikely to impact splicing |

**Outputs**: Predicts donor gain, donor loss, acceptor gain, acceptor loss

### REVEL

**Method**: Ensemble of 13 scores

| Score | Interpretation |
|-------|---------------|
| >0.75 | Likely pathogenic |
| 0.5-0.75 | Uncertain |
| <0.5 | Likely benign |

**Components**: Combines SIFT, PolyPhen, MutationTaster, and others

### CADD (Combined Annotation Dependent Depletion)

**Method**: Integrates diverse annotations

| Phred Score | Interpretation |
|-------------|---------------|
| >30 | Top 0.1% most deleterious |
| >20 | Top 1% |
| >10 | Top 10% |

**Use**: General pathogenicity ranking; not calibrated for clinical classification

### When to Trust Predictions

**Higher confidence:**
- Multiple tools agree
- Score is at extreme (very high or very low)
- Mechanism matches prediction (e.g., truncating + loss-of-function gene)

**Lower confidence:**
- Tools disagree
- Score is borderline
- Novel gene with limited training data
- Non-coding variants (less well validated)

**Critical**: Computational predictions are supporting evidence, not definitive.

---

## Variant Interpretation Workflow

### Step 1: Technical Review

- Is the variant real? (Quality metrics, IGV review)
- Is the call correct? (Reference/alternate bases)
- Is coverage adequate?

### Step 2: Population Filtering

- What's the frequency in gnomAD?
- Is it enriched in specific populations?
- Does frequency fit disease model?

### Step 3: Gene Relevance

- Is this gene associated with patient's phenotype?
- What's the inheritance pattern?
- Is the gene constrained (pLI, LOEUF)?

### Step 4: Variant Effect

- What's the predicted molecular consequence?
- Is it in a functional domain?
- What do computational tools predict?

### Step 5: Prior Knowledge

- Is it reported in ClinVar?
- Is it described in literature?
- Are there functional studies?

### Step 6: Clinical Correlation

- Does phenotype match known gene associations?
- Does family history fit?
- Are there other variants that could explain?

### Step 7: Classification

- Apply ACMG/AMP criteria
- Document evidence
- Assign five-tier classification

---

## Common Pitfalls

### Technical Errors

| Pitfall | Consequence | Avoidance |
|---------|-------------|-----------|
| Wrong reference genome | Mismatched coordinates | Always check and document |
| Poor coverage | Missed variants | Review coverage metrics |
| Batch effects | False positives | Compare across samples |

### Interpretation Errors

| Pitfall | Consequence | Avoidance |
|---------|-------------|-----------|
| Ignoring frequency data | Overcalling pathogenic | Always check gnomAD |
| Over-relying on predictions | Misclassification | Use as supporting only |
| Missing segregation | Incomplete evidence | Test family when possible |
| Transcript confusion | Wrong consequence | Use canonical transcript |

### Clinical Errors

| Pitfall | Consequence | Avoidance |
|---------|-------------|-----------|
| Phenotype mismatch | Wrong diagnosis | Correlate with HPO terms |
| Incomplete penetrance | Missing carriers | Consider reduced penetrance |
| Variable expressivity | Misinterpreting severity | Consider expressivity range |
| Phenocopies | Genetic red herring | Consider non-genetic causes |

---

## Glossary

| Term | Definition |
|------|------------|
| **Allele** | One version of a genetic sequence |
| **Annotation** | Adding information to variant calls |
| **Canonical transcript** | Main transcript used for reporting |
| **Coverage** | Number of reads spanning a position |
| **gnomAD** | Genome Aggregation Database |
| **HGVS** | Standard variant nomenclature |
| **IGV** | Integrative Genomics Viewer |
| **pLI** | Probability of loss-of-function intolerance |
| **Proband** | Index case in a family |
| **Trio** | Proband plus both parents |
| **VUS** | Variant of Uncertain Significance |

---

## Further Reading

### Guidelines

- Richards et al. (2015). "Standards and guidelines for the interpretation of sequence variants." *Genetics in Medicine*
- Riggs et al. (2020). "Technical standards for the interpretation and reporting of constitutional copy-number variants." *Genetics in Medicine*

### Key Papers

- Karczewski et al. (2020). "The mutational constraint spectrum quantified from variation in 141,456 humans." *Nature* (gnomAD)
- Cheng et al. (2023). "Accurate proteome-wide missense variant effect prediction with AlphaMissense." *Science*
- Jaganathan et al. (2019). "Predicting splicing from primary sequence with deep learning." *Cell* (SpliceAI)

### Training Resources

- ClinGen: Variant interpretation education
- ACMG/AMP Webinars: Guideline training
- gnomAD Browser: Tutorial documentation

---

*"A variant is just a letter change. Interpretation is what transforms it into clinical insight."*

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Part of**: UH2025-CDS-Agent Documentation
