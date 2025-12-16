# The Six Discoveries: What Observing the Hackathon Revealed

## Introduction

The Undiagnosed Hackathon is not just an event—it's an **empirical observation window** into how world-class experts actually solve impossible diagnostic cases. By watching 100+ experts from 28 countries work in parallel for 48 hours, we extracted six transferable principles that became the blueprint for the UH2025-CDS-Agent system.

Each discovery answers a design question we couldn't answer from first principles.

---

## Discovery 1: The Planner-Executor Dynamic

**What We Observed:**
At the hackathon, a clear division of labor emerged between two types of experts:

- **Planners** (senior diagnosticians, clinical geneticists): Formulate hypotheses, propose candidate genes, reason about phenotypes
- **Executors** (bioinformaticians, computational biologists): Translate hypotheses into pipeline commands, run analyses, return results

The Planner says: *"Check SCN4A for splice variants."*
The Executor runs: `spliceai --variant SCN4A:c.1234+5G>A --model spliceai_human`

**The Bottleneck:**
Planners were never the bottleneck—there were plenty of brilliant diagnosticians. The bottleneck was always **Executor availability**. Skilled bioinformaticians who could translate clinical hypotheses into technical analyses were scarce.

**Design Implication:**
→ **Automate the Executor, augment the Planner.**
The Executor Agent handles command-line translation. The Planner's reasoning is the scarce resource we preserve.

---

## Discovery 2: The Tool List as Reasoning Artifact

**What We Observed:**
When clinicians formulated diagnostic hypotheses, they didn't just propose a gene—they created explicit **tool lists** specifying which analyses to run:

```
1. Query ClinVar for known pathogenic variants in KCNQ1
2. Run SpliceAI on all intronic variants within 50bp of exon boundaries
3. Check gnomAD for population frequency of candidate variants
4. Run AlphaMissense on all missense variants
5. Cross-reference with OMIM for phenotype match
```

These tool lists are **implicit reasoning made explicit**. They encode the clinician's mental model of how to validate a hypothesis.

**The Insight:**
The tool list is not just a to-do list—it's a proxy for diagnostic reasoning. By collecting tool lists from expert diagnosticians, we capture **how they think**, not just what they conclude.

**Design Implication:**
→ **The Structuring Agent produces tool lists as its primary output.**
The tool list becomes the shareable, auditable artifact of AI reasoning.

---

## Discovery 3: Real-Time Optimization (Human RLHF)

**What We Observed:**
Tool developers from Illumina, Oxford Nanopore, and PacBio were present not as sponsors but as **active participants**:

> "Representatives from Illumina, Oxford Nanopore, and PacBio were present not just as sponsors but as active participants in the 'tech teams,' tweaking their algorithms and pipelines in real-time to meet the needs of the diagnosticians."

When a pipeline failed or produced unexpected results, the engineers who built it were in the room to debug and improve—immediately.

**The Dynamic:**
```
Clinician: "This AlphaMissense call doesn't match the phenotype."
Engineer: [adjusts threshold, re-runs]
Clinician: "Better, but now we're missing known pathogenics."
Engineer: [further refinement]
```

This is **RLHF in human form**—direct expert feedback improving tool performance in real-time.

**Design Implication:**
→ **Formalize this feedback loop as the Doctor-in-the-Loop RLHF system.**
The Evaluator Agent + clinician review interface captures the same dynamic at scale.

---

## Discovery 4: Multi-Omics Necessity

**What We Observed:**
Several cases that remained unsolved after years of WES-based analysis were cracked at the hackathon using multi-omics data:

**The DNA2 Case (Rothmund-Thomson Syndrome):**
- Standard WGS: No pathogenic variants detected
- Long-read sequencing: Deep intronic variant identified in DNA2
- RNA-seq: Aberrant splicing confirmed
- Diagnosis: Rothmund-Thomson syndrome

The variant was **invisible to short-read sequencing**—it required long-read to detect and RNA-seq to validate.

**The Pattern:**
Of the 4 diagnoses in Stockholm 2023, 3 required data beyond WES:
- Long-read for structural variants
- RNA-seq for functional validation
- Methylation for episignature confirmation

**Design Implication:**
→ **The agent must orchestrate multi-modal data.**
The Multi-Omics Tensor concept: DNA (short + long) + RNA + Methylation, integrated by AI.

---

## Discovery 5: Swarm Intelligence (Parallel > Sequential)

**What We Observed:**
Traditional care is sequential:
```
Patient → Specialist A → Wait → Specialist B → Wait → Lab → Wait → Review
```

The hackathon inverts this:
```
                  ┌─► Bioinformatician Team A ─┐
                  │                             │
Patient Data ─────┼─► Clinical Genetics Team ──┼──► Synthesis
                  │                             │
                  └─► Multi-omics Team B ───────┘
```

**The Speed:**
A hypothesis-validation cycle that takes **weeks** in standard care completes in **under an hour** at the hackathon:

1. Hypothesis Generation: 2-5 minutes
2. Technical Translation: 5-10 minutes
3. Execution: 10-30 minutes
4. Evaluation: 5-10 minutes
5. Iteration: immediate

**Design Implication:**
→ **Multi-agent concurrent processing, not sequential pipeline.**
The 4-agent architecture enables parallel hypothesis testing, just like the hackathon teams.

---

## Discovery 6: Emotional Milestones (The Bell Ceremony)

**What We Observed:**
Each breakthrough is marked by ceremonial bell-ringing:

> "Each time the bell rang, scientists cheered and exchanged hugs, symbolizing not just a technical success but the end of years of uncertainty for a family."

The ritual serves multiple functions:
1. **Psychological milestone**: Marks progress in abstract work
2. **Team morale**: Celebrates collective achievement
3. **Data generation**: Timestamps successful diagnostic pathways

**The Insight:**
The bell is not just ceremony—it's a **checkpoint marker**. When the bell rings, we know: (a) a diagnosis was confirmed, (b) the reasoning path was validated, (c) the team can move on.

**Design Implication:**
→ **Checkpoint system with Human-in-the-Loop gates.**
After Ingestion, Structuring, Execution, and Synthesis, clinician approval acts as the "bell."

---

## Summary: Discovery → System Component Mapping

| Discovery | Human Pattern | System Component | Section |
|-----------|---------------|------------------|---------|
| 1 | Clinicians propose, bioinformaticians execute | Planner + Executor Agents | 03, 05 |
| 2 | Experts create tool lists as reasoning artifacts | Structuring Agent output | 03 |
| 3 | Tool developers optimize based on clinician feedback | RLHF training loop | 07 |
| 4 | Multi-omics data cracks WES-unsolvable cases | Multi-modal orchestration | 04 |
| 5 | Parallel teams outperform sequential specialists | Multi-agent concurrency | 05 |
| 6 | Bell ceremony marks progress milestones | Checkpoint system + HITL | 05, 07 |

---

## The Meta-Insight

The hackathon didn't just **prove** that collaboration works—it **revealed** how collaboration works. Each discovery is an empirical observation that couldn't have been designed from first principles.

**The thesis holds:** The hackathon reveals the model; we automate the model.

---

## The Three-Layer Framework

Beyond the six discoveries, the hackathon demonstrates three simultaneous layers of value creation:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    THE THREE-LAYER FRAMEWORK                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   LAYER 1: IMMEDIATE                                                 │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ Diagnoses for waiting families                              │   │
│   │ • 4/10 families diagnosed in 48 hours (40% rate)            │   │
│   │ • Years of uncertainty ended with a bell ring               │   │
│   │ • What works: Parallel expertise, real-time feedback        │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│   LAYER 2: TRAINING                                                 │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ High-quality RLHF data from natural collaboration           │   │
│   │ • Experts reason aloud, generating "tool lists"             │   │
│   │ • Corrections happen in real-time                           │   │
│   │ • Tacit knowledge becomes explicit                          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│   LAYER 3: VALIDATION                                               │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ Discovery of what matters vs. what's theoretical            │   │
│   │ • Which technologies actually crack cases?                  │   │
│   │ • Long-read sequencing found DNA2 (invisible to WES)        │   │
│   │ • Tool developers refine in real-time                       │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Layer 1 (Immediate)**: The hackathon delivers direct patient benefit. Families receive diagnoses. This is the primary mission.

**Layer 2 (Training)**: Every interaction generates training data. When a clinician critiques an AI prediction, that critique becomes a training signal. When experts create tool lists, those lists encode diagnostic reasoning. The hackathon is a **data generation engine** for AI alignment.

**Layer 3 (Validation)**: The hackathon is a **clinical trial for AI tools**. Technologies are tested in real diagnostic contexts. Tools that fail under pressure are deprioritized. Tools that crack cases are validated. This is prospective validation, not retrospective analysis.

---

## Expanding the Space of Possibility

The hackathon doesn't just solve individual cases—it **expands what's possible** in rare disease diagnosis. This section articulates the paradigm shifts enabled by the hackathon model.

### 2.8.1 From Sequential to Parallel

**Before the Hackathon:**
```
Week 1:  Referral to geneticist
Week 4:  Geneticist orders WES
Week 12: WES results return
Week 14: Specialist consultation
Week 20: Second opinion
Week 30: "Variant of Uncertain Significance"—impasse
```

**At the Hackathon:**
```
Hour 0-2:   Case presentation, parallel hypothesis generation
Hour 2-8:   Simultaneous analysis by 4+ teams
Hour 8-24:  Iterative refinement, cross-team consultation
Hour 24-48: Synthesis, validation, diagnosis
```

**What This Enables:**
- **Speed**: Weeks become hours
- **Redundancy**: Multiple independent analyses catch errors
- **Cross-pollination**: Insights from one team inform others

### 2.8.2 From Siloed to Integrated Multi-Omics

**Before:**
DNA → RNA → Methylation → Proteomics (sequential, if at all)

**At the Hackathon:**
All data types analyzed simultaneously, with real-time integration:

| Data Type | Traditional Workflow | Hackathon Workflow |
|-----------|---------------------|-------------------|
| WGS/WES | First-line, often only line | Foundation layer |
| Long-read | Rarely ordered | Standard second look |
| RNA-seq | Research only | Functional validation |
| Methylation | Specialized labs | Native to long-read |

**What This Enables:**
- **60%+ diagnostic yield** (vs. 25-40% for WES alone)
- Detection of **variants invisible to short-read**
- **Functional validation** of computational predictions

### 2.8.3 From Tool Users to Tool Builders

**Traditional Model:**
Clinicians use tools as black boxes. Feedback reaches developers months later, if ever.

**Hackathon Model:**
Tool developers are **in the room**, receiving real-time feedback:

> "This AlphaMissense call doesn't match the phenotype."
> [Engineer adjusts parameters]
> "Better, but now we're missing known pathogenics."
> [Further refinement]

**What This Enables:**
- **Clinical alignment**: Tools optimized for real-world use, not benchmark performance
- **Rapid iteration**: Months of development compressed into hours
- **Expert encoding**: Tacit clinical knowledge transferred into algorithms

### 2.8.4 From n=1 to n=2

**The Fundamental Problem:**
A novel variant-phenotype correlation cannot be confirmed with a single case. Medical certainty requires at least one confirming case (n=2).

**Traditional Reality:**
Cases are siloed in hospitals. The second case exists somewhere but is never connected.

**Hackathon Solution (Immediate):**
100+ experts from 28 countries bring collective memory:
> "I've seen this phenotype before—patient in Copenhagen had the same variant."

**Hackathon Solution (Scaled):**
The Rare Arena Network enables federated case matching without data sharing:
- Query: "Any institution seen SCN4A:c.1234+5G>A with periodic paralysis?"
- Response: "2 matches found (anonymized)"
- Result: **Confirmed causality**

### 2.8.5 From Event to Network

The ultimate expansion: **making the hackathon permanent**.

| Aspect | Hackathon (Event) | Rare Arena Network |
|--------|------------------|-------------------|
| Duration | 48 hours annually | 24/7/365 |
| Participation | 100 experts present | Global edge nodes |
| Knowledge | Tacit, in experts' heads | RLHF-trained models |
| Reach | 10 families per event | Every clinic worldwide |
| Data | Stays in the room | Stays at each institution |

**What This Enables:**
- **Democratized access**: Rural clinic in Kenya has same AI as Mayo Clinic
- **Continuous learning**: Every case improves the model
- **Scalability**: Expert knowledge replicated, not exhausted

---

## The Core Thesis Restated

> **"The hackathon reveals the model; we automate the model."**

The Undiagnosed Hackathon is not merely evidence that collaboration works—it IS the technology in human form. Every component of the UH2025-CDS-Agent system traces directly to a hackathon observation:

| What We Observed | What We Build |
|-----------------|---------------|
| Planner-Executor dynamics | Multi-agent architecture |
| Tool lists as reasoning | Structuring Agent output |
| Real-time developer feedback | RLHF training pipeline |
| Multi-omics integration | Multi-modal data orchestration |
| Parallel team structure | Concurrent agent processing |
| Bell ceremony checkpoints | HITL validation gates |
| Global expert collaboration | Federated learning network |

**The hackathon is not Phase 1. It is the pattern. The Rare Arena Network is how we scale it.**

---

## References

- [3] Illumina Feature Article - Hackathon Technology Integration
- [10] Mayo Clinic News Network - Bell Ceremony Description
- [11] Nature Genetics - Multi-omics Necessity
- [15] Hackathon Participant Observations
- Wilhelm Foundation Mission Statement
- Project Baby Bear Economic Analysis
