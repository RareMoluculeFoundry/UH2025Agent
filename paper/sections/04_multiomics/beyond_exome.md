# The Multi-Omics Frontier: High-Dimensional Data as the New Standard

## 4.1 Beyond the Exome: The Necessity of Multi-Omics

Standard clinical care for rare diseases often stops at Whole Exome Sequencing (WES), which analyzes only the coding regions of the genome (approximately 1-2%). However, the Undiagnosed Hackathon demonstrates that the answers for complex, unsolved cases often lie in the "dark matter" of the genome—the non-coding regions, structural variants, and epigenetic markers.[22] The transition from WES to comprehensive multi-omics is essential for solving the remaining 60% of undiagnosed cases.

## 4.2 Long-Read Sequencing and Structural Variants

Technologies like PacBio HiFi and Oxford Nanopore have revolutionized the detection of structural variants (SVs). Unlike short-read sequencing (Illumina), which chops DNA into small fragments (approx. 150 base pairs), long-read sequencing reads continuous stretches of DNA (up to millions of base pairs). This allows for the resolution of complex rearrangements, repetitive regions, and phasing (determining which chromosome a variant is on).[2]

At the Hackathon, this capability was crucial. For instance, participants used long-read sequencing to identify deep intronic variants in the DNA2 gene that caused Rothmund-Thomson syndrome—variants that were invisible to standard short-read WGS.[24] The ability to span large structural variations is particularly important for neurodevelopmental disorders, where large deletions or duplications are common causes.[2]

## 4.3 Methylation and Transcriptomics: Functional Context

The integration of RNA sequencing (transcriptomics) and methylation data adds a layer of functional context that is often the "tie-breaker" in complex diagnoses.

- **Transcriptomics (RNA-seq):** This technology reveals whether a genetic variant actually affects gene expression. A variant might look benign in the DNA sequence, but RNA-seq can show that it causes exon skipping or nonsense-mediated decay, proving its pathogenicity.[22]

- **Methylation:** This involves identifying "episignatures"—unique patterns of chemical modification on the DNA that are characteristic of specific syndromes. Tools using Nanopore data can now detect methylation concurrently with sequencing, providing two layers of data in a single assay.[22] This was instrumental in the Hackathon for solving cases where the DNA sequence appeared normal but the gene regulation was disrupted.[27]

## 4.4 The Data Integration Challenge

The sheer volume and heterogeneity of multi-omics data (DNA, RNA, Methylation, Phenotype) overwhelm traditional manual analysis. A "standard bioinformatics pipeline" is no longer sufficient; a rigid pipeline cannot decide to look at methylation data only if the RNA-seq shows an anomaly.[28] The complexity requires dynamic pipelines that can adapt based on intermediate findings—precisely the capability offered by the emerging field of Agentic AI.
