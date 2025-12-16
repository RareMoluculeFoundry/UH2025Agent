# Federated Training & Diagnostic Arena

**Version**: 1.0.0
**Last Updated**: November 25, 2025

This document describes the federated training architecture, Diagnostic Arena, and RLHF system for the UH2025-CDS-Agent.

---

## Vision: Global Collaboration, Local Privacy

The UH2025-CDS-Agent is designed for a federated future where:

1. **Inference is Local**: Patient data never leaves the hospital
2. **Training is Global**: Expert feedback improves models worldwide
3. **Contribution is Open**: Anyone can help improve diagnostic AI

This creates a "Democracy of Medical Data" where sophisticated AI tools are accessible to clinics everywhere, not just elite research centers.

---

## The Diagnostic Arena

### Concept

The Diagnostic Arena is a "citizen science" platform where clinicians and geneticists worldwide can contribute to improving the AI by reviewing diagnostic decisions on **synthetic patients**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    DIAGNOSTIC ARENA                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Synthetic  │    │   UH2025    │    │   Expert    │        │
│   │   Patient   │───▶│    Agent    │───▶│   Review    │        │
│   │  Generator  │    │  Pipeline   │    │  Interface  │        │
│   └─────────────┘    └─────────────┘    └──────┬──────┘        │
│                                                 │               │
│                                                 ▼               │
│                                        ┌─────────────┐         │
│                                        │    RLHF     │         │
│                                        │  Feedback   │         │
│                                        │ Collection  │         │
│                                        └──────┬──────┘         │
│                                                │               │
└────────────────────────────────────────────────│───────────────┘
                                                 │
                                                 ▼
                                        ┌─────────────┐
                                        │   Global    │
                                        │   Model     │
                                        │   Weights   │
                                        └─────────────┘
```

### How It Works

1. **Generate**: System creates synthetic patient from disease seed prompts
2. **Run**: UH2025 Agent pipeline processes the synthetic patient
3. **Review**: Expert reviews outputs in JupyterLab interface
4. **Annotate**: Expert marks corrections, adjusts confidence, adds notes
5. **Submit**: Feedback is collected for federated training

### Synthetic Patient Generation

We generate realistic-but-fake patients to enable RLHF without exposing real PHI:

```yaml
# Disease seed prompt example
disease_category: "Ion Channelopathy"
example_conditions:
  - "Paramyotonia Congenita"
  - "Hyperkalemic Periodic Paralysis"
genes_of_interest:
  - SCN4A
  - CLCN1
phenotype_features:
  - "muscle stiffness"
  - "cold sensitivity"

generation_prompt: |
  Generate a realistic clinical summary for a patient
  with suspected {condition}. Include demographics,
  chief complaint, history, family history, and exam findings.
  Add diagnostic complexity with red herrings.
```

### Reviewer Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  Diagnostic Arena - Review Interface                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Patient: SYNTH-2025-0042 (Ion Channelopathy Seed)              │
│  Time Estimate: 15 minutes                                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Step 2: Structuring Agent Output                            ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │                                                             ││
│  │ Diagnostic Table:                                           ││
│  │ ┌─────────────────────────────────────────────────────────┐ ││
│  │ │ 1. Paramyotonia Congenita     [92%] ✅ ○ ○              │ ││
│  │ │ 2. Hyperkalemic Periodic      [65%] ○ ✅ ○              │ ││
│  │ │ 3. Myotonia Congenita         [48%] ○ ○ ✅              │ ││
│  │ └─────────────────────────────────────────────────────────┘ ││
│  │                              [Correct] [Partial] [Wrong]    ││
│  │                                                             ││
│  │ Your Assessment: ○ Correct  ● Partially Correct  ○ Wrong    ││
│  │ Confidence Adjustment: [────●────────] 0.75                 ││
│  │                                                             ││
│  │ Corrections:                                                ││
│  │ ┌─────────────────────────────────────────────────────────┐ ││
│  │ │ Swap #1 and #2: Episode pattern suggests HyperKPP       │ ││
│  │ └─────────────────────────────────────────────────────────┘ ││
│  │                                                             ││
│  │ Notes: [Good variant identification, ranking needs work   ] ││
│  │                                                             ││
│  │                    [Save & Next Step]                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## RLHF Feedback System

### Feedback Schema

Every annotation follows a structured schema:

```yaml
step_feedback:
  # Identification
  feedback_id: "uuid-v4"
  session_id: "arena-session-123"
  synthetic_patient_id: "SYNTH-2025-0042"
  step_id: "structuring"
  timestamp: "2025-11-25T10:30:00Z"

  # Reviewer
  reviewer:
    id: "reviewer-456"
    role: "geneticist"  # clinician | geneticist | data_scientist
    institution: "Mayo Clinic"  # optional
    expertise_level: "senior"  # junior | mid | senior | expert

  # Assessment
  assessment:
    correctness: "partial"  # correct | partial | incorrect
    confidence: 0.75        # 0.0 - 1.0

  # Detailed Corrections
  corrections:
    - field: "diagnostic_table.diagnosis_1"
      original: "Paramyotonia Congenita"
      corrected: "Hyperkalemic Periodic Paralysis"
      rationale: "Episode pattern with potassium sensitivity suggests HyperKPP"

    - field: "diagnostic_table.diagnosis_1.confidence"
      original: 0.92
      corrected: 0.65
      rationale: "Reduced confidence - need EMG confirmation"

  # Free-form notes
  notes: |
    Good variant identification. SCN4A p.Arg1448His correctly flagged.
    However, phenotype analysis missed the potassium-triggered episodes
    which are key to differentiating HyperKPP from PMC.

  # Metadata
  time_spent_seconds: 180
  difficulty_rating: "medium"  # easy | medium | hard
```

### Feedback Aggregation

Feedback from multiple reviewers is aggregated to improve signal:

```
Reviewer 1 (Geneticist): Partial Correct, Confidence 0.75
Reviewer 2 (Clinician):  Correct, Confidence 0.85
Reviewer 3 (Geneticist): Partial Correct, Confidence 0.70
                         ────────────────────────────
Aggregated:              Partial Correct (2/3), Mean Confidence 0.77
```

---

## Federated Training Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEDERATED TRAINING                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │
│  │  Site A   │  │  Site B   │  │  Site C   │  │  Site D   │    │
│  │  (Mayo)   │  │ (Stanford)│  │  (Tokyo)  │  │ (Berlin)  │    │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘    │
│        │              │              │              │          │
│        │   Feedback   │   Feedback   │   Feedback   │          │
│        │   Gradients  │   Gradients  │   Gradients  │          │
│        │              │              │              │          │
│        └──────────────┼──────────────┼──────────────┘          │
│                       │              │                          │
│                       ▼              ▼                          │
│                ┌─────────────────────────┐                      │
│                │   Aggregation Server    │                      │
│                │   (Dell Lattice)        │                      │
│                └───────────┬─────────────┘                      │
│                            │                                    │
│                            ▼                                    │
│                ┌─────────────────────────┐                      │
│                │   Global Model Weights  │                      │
│                │   (Version N+1)         │                      │
│                └───────────┬─────────────┘                      │
│                            │                                    │
│        ┌───────────────────┼───────────────────┐                │
│        │                   │                   │                │
│        ▼                   ▼                   ▼                │
│  ┌───────────┐      ┌───────────┐      ┌───────────┐           │
│  │  Site A   │      │  Site B   │      │  Site C   │           │
│  │ (Updated) │      │ (Updated) │      │ (Updated) │           │
│  └───────────┘      └───────────┘      └───────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Privacy Preservation

**Key Principle**: Raw patient data and feedback text NEVER leave the local site.

What IS shared:
- Aggregated gradients (differential privacy applied)
- Model performance metrics
- Anonymized error patterns

What is NOT shared:
- Patient data (synthetic or real)
- Individual feedback text
- Reviewer identities

### Dell Lattice Integration (Future)

The Dell Lattice federated computing network provides infrastructure for:

1. **Secure Aggregation**: Combine gradients without exposing individual contributions
2. **Model Distribution**: Push updated weights to edge devices
3. **Version Management**: Track model lineage and reproducibility
4. **Audit Trail**: Compliance logging for healthcare deployments

```yaml
# Lattice integration configuration (conceptual)
lattice:
  network_id: "rare-disease-consortium"
  aggregation_server: "lattice.dell.com/rare-cds"

  privacy:
    differential_privacy:
      enabled: true
      epsilon: 1.0
      delta: 1e-5
    secure_aggregation: true

  model_distribution:
    auto_update: false  # Require manual approval
    checksum_validation: true
    rollback_enabled: true

  compliance:
    audit_logging: true
    retention_days: 2555  # 7 years for HIPAA
```

---

## Citizen Science Contribution Model

### Participation Levels

| Level | Time/Week | Activities | Recognition |
|-------|-----------|------------|-------------|
| **Light** | 15 min | Review 3 Arena cases | Community badge |
| **Medium** | 1 hour | Regular Arena reviews | Paper acknowledgment |
| **Heavy** | 4+ hours | Arena + code contributions | Co-authorship |

### Gamification (Optional)

- **Leaderboards**: Top reviewers by volume and quality
- **Badges**: Disease specialty, consistency, accuracy
- **Impact Metrics**: "Your feedback improved X diagnoses"

### Quality Control

To ensure feedback quality:

1. **Calibration Cases**: Known-answer cases to assess reviewer accuracy
2. **Inter-Reviewer Agreement**: Flag cases with high disagreement
3. **Expert Override**: Senior reviewers can adjudicate disputes
4. **Feedback on Feedback**: Rate the quality of corrections

---

## Implementation Roadmap

### Phase 1: Local RLHF (Current)

- [x] Design feedback schema
- [x] Create annotation interface
- [ ] Implement feedback collector
- [ ] Store feedback locally in JSON/SQLite

### Phase 2: Synthetic Patient Generation (December 2025)

- [ ] Create disease seed prompts (5 categories)
- [ ] Implement LLM-based patient generator
- [ ] Validate synthetic patients with clinicians
- [ ] Build Arena case queue

### Phase 3: Multi-Site Collection (January 2026)

- [ ] Deploy Arena at 3+ consortium sites
- [ ] Collect initial RLHF dataset (1000+ annotations)
- [ ] Analyze inter-reviewer agreement
- [ ] Iterate on feedback interface

### Phase 4: Federated Training (February 2026)

- [ ] Implement gradient aggregation
- [ ] Add differential privacy
- [ ] Test on synthetic federation
- [ ] Prepare for Lattice integration

### Phase 5: Production (March 2026)

- [ ] Validate updated models
- [ ] Shadow hackathon deployment
- [ ] Measure real-world impact
- [ ] Publish methodology paper

---

## Governance

### Data Governance

- All feedback data owned by consortium
- CC-BY-4.0 license for aggregated datasets
- Individual sites retain local data sovereignty
- IRB approval required for real patient data

### Model Governance

- Model weights released under open license
- Version control with full provenance
- Reproducibility requirements for all updates
- Safety review before deployment updates

### Contribution Agreement

Contributors agree to:

1. Share feedback under consortium license
2. Not use Arena for competitive advantage
3. Report safety concerns immediately
4. Maintain patient privacy (real or synthetic)

---

## References

1. McMahan et al. (2017). Communication-Efficient Learning of Deep Networks from Decentralized Data. AISTATS.
2. Abadi et al. (2016). Deep Learning with Differential Privacy. CCS.
3. Rieke et al. (2020). The future of digital health with federated learning. NPJ Digital Medicine.
4. HIPAA Privacy Rule, 45 CFR Part 164

---

## Contact

For questions about federated training or Arena participation:

- GitHub Issues: UH2025-CDS-Agent repository
- Consortium Email: federation@rare-cds.org (placeholder)
- Monthly Calls: First Friday of each month
