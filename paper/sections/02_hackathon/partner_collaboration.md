# Partner Collaboration Model

## Overview

The Undiagnosed Hackathon's success stems not from individual expertise but from a carefully designed **collaboration architecture** that brings together academic institutions, technology companies, and philanthropic organizations in a structured partnership model.

This document describes the partner ecosystem, how partners contribute, and the unique "tech teams" structure that enables real-time tool optimization.

---

## 2.4.1 Academic Partner Network

### Founding & Lead Partners

| Institution | Country | Role | Key Contributions |
|------------|---------|------|-------------------|
| **Karolinska Institutet** | Sweden | Founding Host | Event infrastructure, Northern European expertise |
| **Mayo Clinic** | USA | Lead Host (2024-25) | US clinical expertise, patient coordination |
| **Wilhelm Foundation** | Sweden | Organizer | Funding, mission, family coordination |

### Global Academic Partners

The hackathon draws clinical geneticists and diagnosticians from leading institutions worldwide:

**North America:**

- Mayo Clinic (Rochester, MN)
- Stanford University
- UCLA
- National Institutes of Health (NIH)
- Broad Institute (MIT/Harvard)

**Europe:**

- Karolinska Institutet (Sweden)
- Copenhagen University Hospital (Denmark)
- Radboudumc (Netherlands)
- Hospices Civils de Lyon (France)
- University of Tübingen (Germany)

**Asia-Pacific:**

- Rare Care Centre (Australia)
- KK Women's and Children's Hospital (Singapore)
- Sir Ganga Ram Hospital (India)

**Specialized Networks:**

- Undiagnosed Diseases Network (UDN) - USA
- Solve-RD Consortium - Europe
- IRUD (Initiative on Rare and Undiagnosed Diseases) - Japan

### Academic Partner Contributions

Each academic partner brings:

1. **Clinical Expertise**: Deep phenotyping capabilities, disease-specific knowledge
2. **Case Referrals**: Pre-screened families who have exhausted local diagnostics
3. **Follow-up Care**: Post-hackathon validation and clinical implementation
4. **Training Data**: Expert reasoning that feeds into RLHF systems

---

## 2.4.2 Industry Technology Partners

### Sequencing Platform Companies

| Company | Technology | Hackathon Role |
|---------|-----------|----------------|
| **Illumina** | Short-read sequencing | Baseline WGS/WES for all cases, DRAGEN pipeline |
| **Oxford Nanopore** | Long-read sequencing | SV detection, methylation, real-time sequencing |
| **PacBio** | HiFi long-read | High-accuracy phasing, tandem repeats |

**What Makes This Unique:**

Unlike typical vendor relationships, these companies send **active technical participants**, not sales representatives:

> "Representatives from Illumina, Oxford Nanopore, and PacBio were present not just as sponsors but as active participants in the 'tech teams,' tweaking their algorithms and pipelines in real-time to meet the needs of the diagnosticians."

### AI & Computational Partners

| Company | Technology | Hackathon Role |
|---------|-----------|----------------|
| **Google DeepMind** | AlphaMissense, AlphaGenome | AI pathogenicity prediction |
| **Chan Zuckerberg Initiative (CZI)** | Rare disease infrastructure | Data sharing platforms, funding |
| **Fabric Genomics** | Clinical decision support | Variant interpretation software |

### Diagnostic Platform Companies

| Company | Technology | Hackathon Role |
|---------|-----------|----------------|
| **Invitae** | Clinical genomic testing | Validation support |
| **Blueprint Genetics** | Panel testing expertise | Gene-phenotype correlation |
| **Nostos Genomics** | AI interpretation (AION) | Commercial implementation pathway |

---

## 2.4.3 The "Tech Teams" Structure

The hackathon's most innovative organizational feature is the **Tech Teams** model, which embeds tool developers directly into the diagnostic process.

### How Tech Teams Work

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       TECH TEAMS STRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   DIAGNOSTIC TEAM (per case)           TECH TEAM (shared resource)       │
│   ┌───────────────────────┐           ┌───────────────────────┐         │
│   │ Lead Diagnostician    │           │ Illumina Engineers    │         │
│   │ Clinical Geneticist   │ ◄───────► │ ONT Specialists       │         │
│   │ Bioinformatician      │  Request  │ PacBio Engineers      │         │
│   │ Case Coordinator      │  & Feedback│ DeepMind Scientists  │         │
│   └───────────────────────┘           └───────────────────────┘         │
│                                                                          │
│   Diagnostic teams request analyses;                                     │
│   Tech teams execute and refine in real-time.                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Feedback Loop

The Tech Teams structure creates a **continuous improvement loop**:

1. **Clinician identifies need**: "I need splice predictions for this intronic region"
2. **Tech team executes**: Runs SpliceAI with appropriate parameters
3. **Results delivered**: Within minutes, not days
4. **Clinician evaluates**: "This threshold is missing known pathogenics"
5. **Tech team adjusts**: Modifies parameters, re-runs
6. **Iteration continues**: Until clinically useful results achieved

This is **RLHF in human form**—the exact dynamic we formalize in Section 7.

### Real-Time Optimization Examples

**Example 1: AlphaMissense Threshold Tuning**

```
Hour 8:  Clinician: "Too many benign variants flagged as pathogenic"
Hour 8.5: Engineer: "Raising threshold from 0.7 to 0.85"
Hour 9:  Clinician: "Better, but now missing the known SCN4A pathogenic"
Hour 9.5: Engineer: "Implementing gene-specific thresholds"
Hour 10: Clinician: "Perfect—clinically actionable list"
```

**Example 2: Long-Read Coverage Optimization**

```
Hour 14: Diagnostician: "Need to resolve this complex SV"
Hour 14.5: ONT team: "Current coverage is 15x, insufficient"
Hour 15: ONT team: "Running targeted enrichment protocol"
Hour 18: Diagnostician: "SV resolved—pathogenic inversion confirmed"
```

---

## 2.4.4 Collaboration Governance

### Data Sharing Agreements

All partners operate under pre-negotiated agreements that enable rapid data sharing:

| Data Type | Sharing Model | Access Duration |
|----------|---------------|-----------------|
| **Patient genomic data** | Secure enclave, no download | Event + 3 months |
| **Tool outputs** | Full sharing among participants | Permanent |
| **Diagnostic conclusions** | Returned to referring clinician | Permanent |
| **De-identified learnings** | Publication and training use | Permanent |

### Intellectual Property

The hackathon follows an **open science** model:

- **No IP claims** on diagnostic discoveries made during the event
- **Tool improvements** remain property of tool developers
- **Methodological advances** are published openly
- **Patient data** remains property of referring institutions

### Conflict of Interest Management

| Potential Conflict | Mitigation |
|-------------------|------------|
| Vendor bias toward own tools | Multiple competing tools available |
| Academic publication pressure | Focus on patient outcomes first |
| Commercial exploitation | Open publication of methods |

---

## 2.4.5 Partner Value Exchange

### What Partners Contribute

| Partner Type | Contribution |
|-------------|-------------|
| **Academic** | Clinical expertise, cases, follow-up care |
| **Sequencing** | Technology, engineers, real-time support |
| **AI/Tech** | Algorithms, scientists, infrastructure |
| **Philanthropic** | Funding, coordination, mission alignment |

### What Partners Receive

| Partner Type | Value Received |
|-------------|----------------|
| **Academic** | Access to cutting-edge tools, publication opportunities, professional development |
| **Sequencing** | Real-world validation, feedback for product improvement, clinical credibility |
| **AI/Tech** | Training data (expert reasoning), clinical use cases, validation |
| **Philanthropic** | Mission fulfillment, model demonstration, network expansion |

### The Virtuous Cycle

```
Academic Partners ──► Case expertise ──► Diagnoses
                                              │
                                              ▼
Technology Partners ◄── Feedback ◄── Tool usage
                                              │
                                              ▼
AI Partners ◄────── Training data ◄── Expert reasoning
                                              │
                                              ▼
Philanthropic ◄──── Mission fulfillment ◄── Family outcomes
```

---

## 2.4.6 The Global Movement

The hackathon has evolved from a single event to a **global movement**, with each new location expanding the partner network:

### Event Evolution

| Year | Location | New Partners Added |
|------|----------|-------------------|
| 2023 | Stockholm | Karolinska, Northern European network |
| 2024 | Mayo Clinic | US academic centers, NIH, Broad |
| 2025 | Mayo Clinic (continued) | Expanded Asia-Pacific participation |
| 2026 | Hyderabad, India | Sir Ganga Ram Hospital, Indian genetics community |
| 2026 | Singapore | KK Hospital, SingHealth, AVPN |

### Future Expansion Model

Each new hackathon location:

1. **Onboards regional partners**: Local hospitals, genomics centers
2. **Trains local experts**: In hackathon methodology
3. **Generates regional data**: For locally-relevant AI training
4. **Establishes permanent node**: For the Rare Arena Network (Section 6)

---

## 2.4.7 Lessons for AI System Design

The partner collaboration model directly informs the UH2025-CDS-Agent architecture:

| Hackathon Pattern | System Implementation |
|------------------|----------------------|
| Tech teams as shared resource | Tool integration layer |
| Real-time feedback loop | RLHF training pipeline |
| Academic-industry collaboration | Federated learning across institutions |
| Open science IP model | Open-source agent framework |
| Multi-vendor tool integration | Tool-agnostic executor agent |

**The Core Insight:**

The hackathon succeeds because it creates **structured collaboration** between complementary experts. The AI system must replicate this structure:

- **Multiple tools** (not vendor lock-in)
- **Feedback loops** (not black-box predictions)
- **Expert oversight** (not autonomous operation)
- **Open sharing** (not data silos)

---

## References

- [3] Illumina Feature Article - Hackathon Technology Integration
- [10] Mayo Clinic News Network - 2024 Hackathon Coverage
- [15] Hackathon Participant Observations
- Wilhelm Foundation Annual Reports
- AVPN (Asian Venture Philanthropy Network) Partnership Announcement
