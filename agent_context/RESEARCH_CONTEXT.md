# UH2025 Agent Research Context

This document provides the scientific, operational, and architectural context for the UH2025 Clinical Decision Support (CDS) Agent. It is derived from the "Rare Arena Network" whitepaper and serves as the grounding truth for the agent's reasoning and "why" it operates the way it does.

## 1. The Mission: Ending the Diagnostic Odyssey

The "diagnostic odyssey" for rare disease patients averages 6 years, with 30% of children dying before their 5th birthday. The "undiagnosed" population often remains unsolved not due to a lack of data, but due to:
1.  **Siloed Knowledge**: Expertise is locked in academic centers.
2.  **Fragmented Data**: Genomic data is stuck in institutional silos (GDPR/HIPAA).
3.  **Cognitive Overload**: No single clinician can master the phenotypes of 10,000+ rare diseases.

**The Goal**: To create an "Agentic AI" system that replicates the workflow of the world's best diagnosticians—specifically the "Planner-Executor" dynamic observed at the Undiagnosed Hackathon.

## 2. The Agentic Architecture: Planner-Executor-Evaluator

The UH2025 Agent mimics the human "swarm" intelligence observed at the Hackathon:

### 2.1 The Planner (Structuring Agent)
*   **Role**: Senior Diagnostician / Geneticist.
*   **Function**: Decomposes the complex clinical picture into a structured analysis plan.
*   **Behavior**: It does not run the tools; it *decides* which tools to run. It prioritizes variants in known disease genes that explain the primary phenotype.
*   **Key Insight**: "The decision to look at long-read structural variants instead of short-read SNPs is the critical intellectual step."

### 2.2 The Executor (Executor Agent)
*   **Role**: Bioinformatician.
*   **Function**: Executes the specific tools requested by the Planner.
*   **Behavior**: Handles API calls, file parsing, and error handling. It uses "Sensors" (Deep Learning models) to generate data.
*   **Tools**:
    *   **AlphaMissense**: Google DeepMind's model for missense pathogenicity (Protein Language Model).
    *   **AlphaGenome**: Sequence-to-function prediction for non-coding variants.
    *   **SpliceAI**: Deep learning for splice site disruption.
    *   **ClinVar**: Known clinical significance.
    *   **OMIM**: Phenotype-Genotype relationships.

### 2.3 The Evaluator (Synthesis & Review)
*   **Role**: Quality Control / Peer Reviewer.
*   **Function**: Critiques the findings for biological plausibility.
*   **Mechanism**: RLHF (Reinforcement Learning from Human Feedback) via the "Doctor-in-the-Loop" interface.

## 3. The Multi-Omics Frontier

Standard Exome Sequencing (WES) misses 60% of diagnoses. The agent must be capable of reasoning about:
*   **Structural Variants (SVs)**: Large deletions/duplications often invisible to short-read sequencing.
*   **Non-Coding Variants**: Deep intronic variants affecting splicing (e.g., DNA2 case in Hackathon).
*   **Methylation**: Epigenetic signatures (episignatures) that indicate functional gene disruption without sequence change.

## 4. Federated Learning: The Rare Arena

The agent is designed to operate in a **Federated** environment.
*   **Privacy-First**: Raw patient data (genome) NEVER leaves the local environment (`Data/PatientX/`).
*   **Swarm Learning**: The agent learns from global patterns (gradient updates) without centralizing data.
*   **Standards**: It adheres to GA4GH Beacon and Matchmaker Exchange protocols (conceptually).

## 5. Deployment Tiers

The agent code must run across three tiers:
*   **L1 (Laptop)**: Apple Silicon / Consumer GPU. Quantized models (Q4_K_M).
*   **L2 (Hospital Cluster)**: On-premise NVIDIA/AMD GPUs.
*   **L3 (Cloud/HPC)**: Massive scale re-analysis.

## 6. Key Case Studies (Validation)

The agent's logic is validated against:
*   **Rothmund-Thomson Syndrome**: Deep intronic variant found via long-read sequencing.
*   **Project Baby Bear**: Rapid WGS in NICU saves $2.5M and 500+ hospital days.

---
*Context extracted from `lab/org/UH2025Agent.md` on 2025-12-02.*

