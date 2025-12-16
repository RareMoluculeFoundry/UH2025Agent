# Scientific Context: AlphaGenome and Regulatory Genomics

## Overview

Comprehensive scientific background on regulatory genomics and AlphaGenome's approach to variant effect prediction.

## 1. Regulatory Genomics Background

### The Non-Coding Genome

**Key Facts**:
- 98% of human genome is non-coding
- Contains regulatory elements (enhancers, promoters, silencers)
- GWAS hits enriched in regulatory regions
- No simple "genetic code" for regulation

**Regulatory Elements**:
- **Promoters**: Near transcription start sites (~200 bp)
- **Enhancers**: Distal elements (10s of KB away)
- **Silencers**: Repressive elements
- **Insulators**: Boundary elements (TADs)

### Regulatory Variants

**Impact**:
- Change gene expression levels
- Alter tissue specificity
- Affect developmental timing
- Contribute to complex disease risk

**Examples**:
- FTO obesity risk variants (in enhancer)
- LDL cholesterol variants (SORT1 enhancer)
- Type 2 diabetes variants (regulatory regions)

## 2. Computational Challenges

### Why Regulatory Prediction is Hard

1. **No Simple Code**: Unlike protein-coding mutations
2. **Long-Range Effects**: Enhancers affect distant genes
3. **Tissue Specificity**: Effect depends on cell type
4. **Combinatorial Logic**: Multiple TFs cooperate
5. **3D Genome**: Chromatin loops bring distant elements together

### Previous Approaches

**Evolutionary Conservation**:
- PhyloP, GERP
- Limitation: Can't distinguish functional vs neutral

**Epigenomic Data**:
- ENCODE, Roadmap Epigenomics
- Limitation: Limited cell types, no variant effects

**Machine Learning**:
- DeepSEA, Basset, Sei
- Limitation: Trained on specific assays, limited resolution

## 3. AlphaGenome Model

### Architecture

**Model Type**: Transformer-based sequence model
**Input**: DNA sequence (up to 1 MB)
**Outputs**: Multiple modalities (RNA-seq, ATAC-seq, ChIP-seq, etc.)
**Training**: Diverse genomic datasets

**Key Innovation**: Unified model predicting multiple regulatory modalities from sequence alone.

### Training Data

**Modalities**:
- Gene expression (RNA-seq, CAGE, PRO-CAP)
- Chromatin accessibility (ATAC-seq, DNase-seq)
- Histone modifications (ChIP-seq for H3K4me3, H3K27ac, etc.)
- TF binding (ChIP-seq for transcription factors)
- Splicing (splice site predictions, junction reads)
- 3D genome (Hi-C-like contact maps)

**Data Sources**:
- ENCODE
- Roadmap Epigenomics
- GTEx
- 4D Nucleome

**Coverage**: 100+ cell types/tissues

### Prediction Process

```
[DNA Sequence] → [Transformer Encoder] → [Multiple Heads] → [Predictions]
                                          ├── RNA-seq head
                                          ├── ATAC head
                                          ├── ChIP head
                                          ├── Splice head
                                          └── Contact head
```

### Variant Effect Prediction

**Approach**: In silico mutagenesis
1. Predict reference sequence
2. Predict alternate sequence
3. Compute difference (effect size)

**Advantage**: Direct measure of variant impact

## 4. Performance and Validation

### Benchmarks

**Variant Effect Prediction**:
- State-of-the-art on MPRA benchmarks
- Outperforms DeepSEA, Sei, Enformer
- High correlation with experimental data

**Multi-Modal Predictions**:
- Accurate across all modalities
- Single base-pair resolution
- Long-range context (1 MB)

**Tissue Specificity**:
- Captures tissue-specific effects
- Distinguishes cell type-specific regulation

### Validation Datasets

**MPRA** (Massively Parallel Reporter Assays):
- Direct measure of regulatory activity
- AlphaGenome correlates with experimental results

**eQTL Studies**:
- Predicts expression changes
- Matches GTEx eQTL effect sizes

**Saturation Mutagenesis**:
- Agrees with deep mutational scanning
- Identifies critical positions

## 5. Applications

### eQTL Analysis

**Definition**: Expression quantitative trait loci - variants affecting gene expression

**AlphaGenome Use**:
1. Identify GWAS variant
2. Predict expression effect in relevant tissue
3. Map to candidate causal gene
4. Prioritize for functional studies

**Example**:
```
GWAS hit → Liver eQTL → LDL cholesterol gene → Mechanism
```

### Splice Variant Interpretation

**Challenges**:
- Splice sites: GT-AG consensus but many variations
- Intronic variants: Can disrupt splicing
- Clinical significance: Often VUS

**AlphaGenome Use**:
1. Predict splice site usage (reference)
2. Predict with variant (alternate)
3. Quantify disruption
4. Identify affected isoforms

### Regulatory Landscape Exploration

**Use Case**: Understand regulatory architecture of a region

**Workflow**:
1. Define genomic region (e.g., 1 MB around gene)
2. Predict all modalities (RNA-seq, ATAC, ChIP, etc.)
3. Visualize regulatory features
4. Identify enhancers, promoters, boundaries

**Application**: Disease mechanism studies, non-coding variant interpretation

### Fine-Mapping

**GWAS Fine-Mapping**:
- GWAS identifies regions, not causal variants
- Fine-mapping narrows to causal variant
- AlphaGenome predicts functional impact

**Workflow**:
1. LD-pruned variants from GWAS
2. Predict effect for each variant
3. Rank by predicted effect size
4. Prioritize for experimental validation

## 6. Limitations

### 1. Model Limitations

**Sequence-Only**:
- Cannot model trans-acting factors directly
- Missing some aspects of 3D genome
- No protein-DNA binding specificity (beyond training data)

**Training Bias**:
- Limited by training data diversity
- May underperform in rare cell types
- Biased toward well-studied genomic regions

### 2. Interpretation Challenges

**Not Pathogenicity Scores**:
- Predicts molecular effects, not disease risk
- Must integrate with other evidence
- Context-dependent effects

**Effect Size ≠ Clinical Significance**:
- Large molecular effect may not cause disease
- Small effect may be clinically important (threshold effects)
- Requires biological context

### 3. Technical Constraints

**Rate Limits**:
- Free tier limits queries
- Not suitable for >1M predictions
- Requires caching and batching

**Context Window**:
- Max 1 MB (may miss very long-range effects)
- Computational cost increases with size

## 7. Future Directions

### Model Improvements

**Longer Context**:
- Multi-megabase predictions
- Capture TAD-level organization

**More Modalities**:
- Single-cell resolution
- Temporal dynamics (development, differentiation)
- Disease-specific states

**Better Interpretation**:
- Attention mechanisms
- Motif discovery
- Mechanistic insights

### Clinical Integration

**Variant Interpretation Pipelines**:
- Integrate with VCF annotation
- ACMG classification support
- Clinical decision support

**Population Genomics**:
- Predict effects for all human variants
- Population-specific effects
- Evolutionary insights

### Research Applications

**Synthetic Biology**:
- Design regulatory elements
- Optimize gene expression
- Predict construct behavior

**Drug Discovery**:
- Target identification (regulatory variant → gene → drug)
- Off-target effects (regulatory disruption)
- Personalized medicine (variant-informed treatment)

## 8. Key Publications

### Primary Reference

**Avsec, Ž., et al. (2025)**. "AlphaGenome: advancing regulatory variant effect prediction with a unified DNA sequence model." *bioRxiv*. DOI: 10.1101/2025.06.25.661532

### Related Work

**Enformer** (Avsec et al., 2021):
- Predecessor model
- Long-range predictions (100 KB)
- Multi-task learning

**DeepSEA** (Zhou & Troyanskaya, 2015):
- Early deep learning for regulatory prediction
- Chromatin features from sequence

**Sei** (Chen et al., 2022):
- Sequence class prediction
- Regulatory element classification

## 9. Resources

**AlphaGenome**:
- Blog: https://deepmind.google/discover/blog/alphagenome-ai-for-better-understanding-the-genome/
- GitHub: https://github.com/google-deepmind/alphagenome
- API: https://deepmind.google.com/science/alphagenome

**Genomic Databases**:
- ENCODE: https://www.encodeproject.org/
- GTEx: https://gtexportal.org/
- GWAS Catalog: https://www.ebi.ac.uk/gwas/
- GENCODE: https://www.gencodegenes.org/

**Ontologies**:
- UBERON: https://www.ebi.ac.uk/ols/ontologies/uberon
- Cell Ontology: https://www.ebi.ac.uk/ols/ontologies/cl

## Summary

AlphaGenome represents a major advance in regulatory genomics by providing:
- **Multi-modal predictions** from sequence alone
- **Single base-pair resolution** for variant effects
- **Long-range context** (up to 1 MB)
- **Tissue-specific** predictions (100+ cell types)
- **State-of-the-art performance** on benchmarks

It enables researchers to:
- Interpret non-coding variants
- Discover disease mechanisms
- Prioritize functional studies
- Design regulatory elements

However, predictions must be interpreted in biological and clinical context, and integrated with other lines of evidence.

---

**Version**: 1.0.0
**Last Updated**: October 2025
