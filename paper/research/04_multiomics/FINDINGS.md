# Research Findings: Multi-Omics & Long-Reads (2024-2025)

**Date:** 2025-12-03
**Topic:** Section 04 - Multi-Omics Integration
**Source:** Native Web Search

## 1. Key Trends & Definitions
*   **The "Exome Ceiling"**: Standard Whole Exome Sequencing (WES) solves ~30-40% of rare disease cases. The remaining 60% are "hidden" in the non-coding genome or complex structural variants.
*   **Long-Read Sequencing (LRS)**: Technologies like PacBio (HiFi) and Oxford Nanopore (ONT) read DNA in long strands (10kb+ vs 150bp).
    *   *Yield Increase*: 2025 studies show LRS increases diagnostic yield by 10-15% over Short-Read WGS.
    *   *Mechanism*: Resolves repetitive regions, large insertions/deletions (SVs), and phasing (knowing which parent a mutation came from).
*   **Transcriptomics (RNA-seq)**: Measuring gene *expression*. "We see the mutation in DNA, but does it actually break the RNA?"
    *   *Splicing*: Critical for variants that don't look dangerous in DNA but cause "exon skipping" in RNA.
*   **Epigenetics (Methylation)**: "Is the gene turned off?" Nanopore sequencing now captures methylation *natively* (simultaneously with DNA), adding a 4th dimension to diagnosis.

## 2. Technical Context for UH2025
*   **The "Multi-Omics Tensor"**: Our agents view a patient not as a list of variants, but as a "Tensor" of stacked data layers:
    *   Layer 1: DNA (Short Read - SNVs)
    *   Layer 2: DNA (Long Read - SVs)
    *   Layer 3: RNA (Expression Z-scores)
    *   Layer 4: Methylation (Promoter status)
*   **Data Integration**: It is impossible for a human to mentally overlay these 4 layers. This is the **primary justification for Agentic AI**. The agent checks Layer 1, finds a VUS (Variant of Uncertain Significance), checks Layer 3 (RNA) to see if expression is low, and Layer 4 (Methylation) to see if it's silenced.

## 3. Wilhelm Foundation Context
*   **Hackathon Innovation**: The 2025 Hackathon was unique because it provided "native multi-omics" datasets for the challenge cases, forcing teams to build tools that could handle ONT+RNA+WGS simultaneously.
*   **Cost Barrier**: Acknowledge that LRS is expensive ($1000 vs $300). The agent's job is to recommend LRS *only when needed* (Diagnostic Stewardship).

## 4. Synthesis for UH2025
*   **"The Deep Dive"**: Define a workflow where the agent starts with cheap data (WES), fails to diagnose, and then *orders* (simulated) deeper data (LRS/RNA), justifying the cost with specific hypothesis generation.
*   **Tooling**: Mention specific tools like `Squid` (transcriptomics), `Sniffles` (SVs), and `Modkit` (Methylation).

