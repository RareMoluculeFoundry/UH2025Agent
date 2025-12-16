# Research Findings: RLHF and Doctor-in-the-Loop Systems

**Date:** 2025-12-08
**Topic:** Section 07 - RLHF (Reinforcement Learning from Human Feedback)
**Source:** UH2025Agent System Documentation, Hackathon Observations, Medical AI Literature

---

## Executive Summary

This research document synthesizes findings on RLHF (Reinforcement Learning from Human Feedback) as applied to medical AI systems, with specific focus on **doctor-in-the-loop** frameworks for rare disease diagnosis. The core insight: the UH2025 Hackathon demonstrated **human RLHF in action**—tool developers receiving real-time expert feedback and optimizing algorithms on the fly. Formalizing this dynamic as a systematic training loop enables continuous improvement while democratizing expert knowledge.

**Key Finding:** Discovery 3 from the hackathon ("Real-Time Optimization") reveals that RLHF is not a theoretical construct but an **observed human behavior** that can be automated and scaled.

---

## 1. RLHF Methodology in LLM Training

### 1.1 Core Concepts

**Reinforcement Learning from Human Feedback (RLHF)** is the training paradigm that transformed raw language models into aligned, helpful AI assistants. The methodology has three phases:

1. **Supervised Fine-Tuning (SFT)**: Train base model on high-quality human demonstrations
2. **Reward Modeling**: Train a reward model from human preference comparisons
3. **Policy Optimization**: Use reinforcement learning (PPO/DPO) to optimize model against learned rewards

**Key Papers:**
- **InstructGPT** (OpenAI, 2022): Established RLHF for aligning language models with human intent
- **Constitutional AI** (Anthropic, 2022): Extended RLHF with AI-generated feedback for scalability
- **Direct Preference Optimization** (Rafailov et al., 2023): Simplified RLHF by directly optimizing on preferences

### 1.2 The Alignment Problem

RLHF addresses the fundamental challenge: **statistical accuracy ≠ human preference**

In medical AI, this manifests as the **"Alignment Paradox"** (referenced in section 7.1):
- A model with 95% F1 score may be less trusted than one with 92% if the reasoning is opaque
- Clinicians prefer explainable, stepwise reasoning over black-box predictions
- Expert intuition often catches edge cases that metrics miss

**Critical Insight for UH2025:** The Structuring Agent must produce not just diagnoses, but **auditable reasoning artifacts** (tool lists) that align with clinical thought processes.

### 1.3 RLHF vs Traditional Supervised Learning

| Aspect | Supervised Learning | RLHF |
|--------|-------------------|------|
| Training Signal | Ground truth labels | Human preferences |
| Captures | What is correct | What is preferred |
| Alignment | Task accuracy | Human values/preferences |
| Medical Relevance | "Is this diagnosis right?" | "Is this reasoning sound?" |

**Medical AI Implication:** For rare diseases, ground truth is often unknown. RLHF captures **expert clinical reasoning** rather than requiring known diagnoses.

---

## 2. Doctor-in-the-Loop Systems

### 2.1 Clinical AI Oversight Requirements

**Regulatory Context:**
- **FDA Guidance on AI/ML Medical Devices** (2021): Requires human oversight for high-risk clinical decisions
- **HIPAA Security Rule**: Mandates audit trails for PHI access
- **Clinical Validation Standards**: AI recommendations must be verifiable by clinicians

**Trust Requirements:**
Clinicians are inherently skeptical of black-box algorithms (discovery from section 7.1). Doctor-in-the-loop addresses this through:

1. **Transparency**: Show the reasoning process (tool lists, evidence tables)
2. **Correctability**: Allow experts to override and annotate errors
3. **Auditability**: Log all AI decisions and human corrections
4. **Accountability**: Human clinician makes final diagnostic decision

### 2.2 Human-in-the-Loop Architectures

**Checkpoint Model** (UH2025 Implementation):
```
1. AI proposes → 2. Human reviews → 3. Human approves/corrects → 4. System learns
```

After each agent step (Ingestion, Structuring, Execution, Synthesis), clinician validation acts as a "quality gate" (analogous to the hackathon bell ceremony—Discovery 6).

**Benefits:**
- **Early error detection**: Catch mistakes before propagation
- **Training signal generation**: Human corrections become RLHF data
- **Trust building**: Clinician sees and validates every step
- **Compliance**: Meets regulatory human oversight requirements

### 2.3 Feedback Schema for Medical AI

The UH2025 feedback schema (detailed in `docs/FEDERATED.md`) captures:

```yaml
step_feedback:
  assessment:
    correctness: "partial"  # correct | partial | incorrect
    confidence: 0.75
  corrections:
    - field: "diagnostic_table.diagnosis_1"
      original: "Paramyotonia Congenita"
      corrected: "Hyperkalemic Periodic Paralysis"
      rationale: "Episode pattern suggests HyperKPP over PMC"
  notes: "Good variant identification, needs diagnosis ranking work"
```

**Key Elements:**
1. **Structured corrections**: Machine-readable edits to specific fields
2. **Rationale**: Captures clinical reasoning (the "why")
3. **Confidence**: Quantifies reviewer certainty
4. **Free-form notes**: Captures tacit knowledge and edge cases

**Novel Contribution:** Unlike generic RLHF (which uses binary preference), medical RLHF requires **field-level corrections with clinical rationale**.

---

## 3. Real-Time Feedback in Clinical AI

### 3.1 The Hackathon Model (Discovery 3)

**Observed Pattern:**
At the Mayo Clinic Undiagnosed Hackathon, tool developers from Illumina, Oxford Nanopore, and PacBio were physically present:

> *"Representatives from Illumina, Oxford Nanopore, and PacBio were present not just as sponsors but as active participants in the 'tech teams,' tweaking their algorithms and pipelines in real-time to meet the needs of the diagnosticians."*

**The Feedback Loop:**
```
Clinician: "This AlphaMissense call doesn't match the phenotype."
Engineer: [adjusts threshold, re-runs]
Clinician: "Better, but now we're missing known pathogenics."
Engineer: [further refinement]
```

**This is human RLHF:**
- **Immediate feedback**: Not days/weeks, but minutes
- **Expert correction**: Not crowd workers, but world-class clinicians
- **Contextual tuning**: Adjust for specific diagnostic context
- **Iterative refinement**: Multiple rounds until alignment

### 3.2 Formalizing Real-Time Optimization

**Phase 1 (Hackathon):** Human-to-human real-time feedback
**Phase 2 (UH2025 RLHF):** Formalized as structured training signal

| Hackathon (Informal) | UH2025 RLHF (Formal) |
|---------------------|---------------------|
| Verbal critique | JSON feedback schema |
| Manual parameter adjustment | Automated model update |
| One-time optimization | Continuous learning |
| Knowledge stays with engineer | Knowledge distributed globally |

**Implementation:**
1. **Diagnostic Arena**: Platform for clinicians to review synthetic cases
2. **Feedback Collector**: Captures structured corrections
3. **Gradient Aggregation**: Converts corrections to model updates
4. **Federated Distribution**: Updated weights pushed to all edge devices

### 3.3 The "Tool List" as RLHF Artifact

**Discovery 2** from hackathon: Tool lists are **implicit reasoning made explicit**

Example tool list from structuring agent:
```
1. Query ClinVar for known pathogenic variants in SCN4A
2. Run SpliceAI on all intronic variants within 50bp of exon boundaries
3. Check gnomAD for population frequency
4. Run AlphaMissense on all missense variants
5. Cross-reference with OMIM for phenotype match
```

**Why this matters for RLHF:**
- Tool lists encode **how experts think**, not just what they conclude
- Reviewers can critique step-by-step reasoning
- Corrections to tool order/selection become training signals
- More granular than binary "correct/incorrect" diagnosis feedback

**Training Signal Generation:**
If clinician corrects tool order or adds missing tool, that becomes a preference signal:
- **Positive:** This tool list was well-structured
- **Negative:** This tool was unnecessary / Wrong tool for this variant type
- **Additive:** Should have included REVEL for this case

---

## 4. Arena-Style Evaluation

### 4.1 Chatbot Arena Model

**Chatbot Arena** (LMSYS, 2023) pioneered crowd-sourced LLM evaluation:
- Users compare outputs from two anonymous models (Model A vs Model B)
- Vote for preferred response
- Aggregate preferences into Elo ratings
- Models ranked by community preference, not benchmark scores

**Key Innovation:** Captures **human preference at scale** without requiring expert labelers

### 4.2 Diagnostic Arena Adaptation

**UH2025 Diagnostic Arena** adapts this for medical AI:

**Differences from Chatbot Arena:**
| Aspect | Chatbot Arena | Diagnostic Arena |
|--------|--------------|-----------------|
| Evaluators | General public | Clinicians/geneticists only |
| Task | Preference voting (A vs B) | Structured correction |
| Data | Real user queries | Synthetic patients |
| Feedback | Binary preference | Field-level edits + rationale |
| Stakes | Low (conversational) | High (medical reasoning) |

**Synthetic Patient Generation:**
To avoid PHI exposure, Arena uses LLM-generated synthetic patients:

```yaml
disease_seed: "Ion Channelopathy"
example_conditions:
  - "Paramyotonia Congenita"
  - "Hyperkalemic Periodic Paralysis"
genes_of_interest: [SCN4A, CLCN1]
phenotype_features:
  - "muscle stiffness"
  - "cold sensitivity"
```

**Generation Process:**
1. Start with disease category seed
2. LLM generates realistic clinical summary with diagnostic complexity
3. Synthetic VCF created with known pathogenic variants + noise
4. Validated by clinicians for realism
5. Becomes Arena test case

**Why Synthetic Patients:**
- **Privacy**: No real PHI exposed
- **Control**: Can target specific diagnostic scenarios
- **Scalability**: Generate unlimited training cases
- **Safety**: Errors don't affect real patients

### 4.3 Quality Control in Expert Evaluation

**Challenge:** Medical expertise varies. How to ensure quality feedback?

**Solutions:**
1. **Calibration Cases**: Known-answer cases to assess reviewer accuracy
2. **Inter-Reviewer Agreement**: Flag cases with high disagreement
3. **Expert Stratification**: Weight feedback by reviewer credentials
4. **Consensus Adjudication**: Senior experts resolve disputes

**Example Aggregation:**
```
Reviewer 1 (Senior Geneticist): Partial Correct, Confidence 0.75
Reviewer 2 (Clinical Geneticist): Correct, Confidence 0.85
Reviewer 3 (Geneticist):        Partial Correct, Confidence 0.70
                                 ────────────────────────────
Aggregated:                      Partial Correct (2/3), Mean Confidence 0.77
```

---

## 5. Discovery 3 Evidence: Real-Time Optimization

### 5.1 The Empirical Observation

**From `paper/sections/02_hackathon/discoveries.md`:**

**Discovery 3: Real-Time Optimization (Human RLHF)**

**What We Observed:**
> "Representatives from Illumina, Oxford Nanopore, and PacBio were present not just as sponsors but as active participants in the 'tech teams,' tweaking their algorithms and pipelines in real-time to meet the needs of the diagnosticians."

**The Dynamic:**
```
Clinician: "This AlphaMissense call doesn't match the phenotype."
Engineer: [adjusts threshold, re-runs]
Clinician: "Better, but now we're missing known pathogenics."
Engineer: [further refinement]
```

**Design Implication:**
→ **Formalize this feedback loop as the Doctor-in-the-Loop RLHF system.**

### 5.2 Why This Matters

**Traditional Model:**
- Clinicians use tools as black boxes
- Feedback reaches developers months later (if ever)
- Tools optimized for benchmark performance, not clinical utility

**Hackathon Model:**
- Tool developers in the room
- Real-time feedback on actual diagnostic cases
- Immediate iteration cycles (minutes, not months)

**Insight:** This is **empirical alignment** happening organically. The hackathon proves that expert feedback can rapidly improve tool performance when the feedback loop is tight.

### 5.3 Scaling the Pattern

**Hackathon (Event):**
- 100 experts, 48 hours
- 10 families benefit
- Knowledge stays in the room

**Rare Arena Network (System):**
- Global expert network, 24/7/365
- Every clinic benefits
- Knowledge captured in model weights

**The Three-Layer Framework:**

| Layer | Hackathon | Arena Network |
|-------|-----------|--------------|
| **Immediate** | 4/10 families diagnosed | Every case improves pipeline |
| **Training** | Experts reason aloud | RLHF captures reasoning |
| **Validation** | Tools tested in real-time | Continuous A/B testing |

**From Discovery 3:**
> "The hackathon doesn't just prove that collaboration works—it reveals how collaboration works."

---

## 6. Regulatory and Safety Considerations

### 6.1 FDA Guidance on AI/ML Medical Devices

**Key Requirements:**
- Human oversight for high-risk decisions
- Transparency in AI reasoning
- Audit trails for all predictions
- Continuous monitoring and updates

**UH2025 Compliance:**
- ✅ Doctor-in-the-loop at every step
- ✅ Transparent tool lists and evidence tables
- ✅ Full provenance logging
- ✅ RLHF enables continuous improvement with human validation

### 6.2 HIPAA and Privacy

**Challenge:** RLHF requires sharing feedback data

**Solution (Federated RLHF):**
- Raw patient data never leaves local site
- Only aggregated gradients shared (with differential privacy)
- Synthetic patients used in Arena (no real PHI)
- Feedback text stripped of identifiers before aggregation

**From `docs/FEDERATED.md`:**
```yaml
privacy:
  differential_privacy:
    enabled: true
    epsilon: 1.0
    delta: 1e-5
  secure_aggregation: true
```

### 6.3 Informed Consent and Human Subjects Research

**IRB Considerations:**
- Real patient feedback may require IRB approval
- Synthetic patient reviews are exempt (no human subjects)
- Federated training on real cases needs multi-site IRB protocol
- De-identification standards must meet HIPAA Safe Harbor

**UH2025 Strategy:**
- **Phase 1:** Synthetic patients only (no IRB required)
- **Phase 2:** Real patients with IRB approval and informed consent
- **Phase 3:** Federated training with consortium IRB

---

## 7. Implications for Democratizing Expert Feedback

### 7.1 The Knowledge Transfer Problem

**Current State:**
- Expert clinical reasoning is **tacit knowledge**
- Concentrated in top academic centers (Mayo Clinic, Stanford, etc.)
- Impossible to scale: limited expert time
- Geographic inequality: rural clinics lack access

**Quote from section 7.3:**
> "A general practitioner in a rural clinic could thus have access to a 'virtual' Mayo Clinic expert via the AI agent, which has been trained and validated by the actual experts."

### 7.2 RLHF as Knowledge Codification

**Mechanism:**
1. Expert reviews AI outputs in Diagnostic Arena
2. Corrections capture clinical reasoning ("Episode pattern suggests HyperKPP")
3. RLHF encodes corrections into model weights
4. Updated model deployed globally

**Result:** Expert intuition becomes **replicable AI behavior**

**Example:**
- Expert geneticist knows: "For SCN4A variants, check potassium-triggered episodes to differentiate HyperKPP from PMC"
- Traditional: This knowledge stays in expert's head
- RLHF: Expert corrects AI ranking, model learns the pattern
- Deployment: Rural clinic's AI now knows this pattern

### 7.3 Global Equity Impact

**The M4 Envelope Standard:**
High-end consumer hardware (M4 MacBook Pro Max, 64-128GB RAM) ensures:
- Hospital in Kenya: Same AI as Mayo Clinic
- Models run locally (no cloud dependency)
- Expert knowledge democratized via RLHF-trained weights

**Economic Impact:**
- Traditional: Expert consultation $500-2000
- UH2025: One-time hardware cost (~$3000), then free inference
- Diagnostic Arena: Free expert review for training cases (citizen science model)

**From README.md:**
> "A hospital in a resource-constrained setting can deploy the exact same diagnostic tools as a top-tier academic center."

### 7.4 Contribution Levels

**From `docs/FEDERATED.md`:**

| Level | Time/Week | Activities | Recognition |
|-------|-----------|------------|-------------|
| **Light** | 15 min | Review 3 Arena cases | Community badge |
| **Medium** | 1 hour | Regular Arena reviews | Paper acknowledgment |
| **Heavy** | 4+ hours | Arena + code contributions | Co-authorship |

**Insight:** This creates a **citizen science model** for medical AI improvement. Experts contribute small amounts of time, aggregate impact is massive.

---

## 8. Technical Implementation Details

### 8.1 RLHF Pipeline Architecture

**From UH2025 System:**

```
┌─────────────────────────────────────────────────────────────────┐
│              RLHF TRAINING PIPELINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. SYNTHETIC PATIENT GENERATION                                │
│     ├── Disease seed prompts                                    │
│     ├── LLM-generated clinical summary                          │
│     └── Synthetic VCF with known + noise variants              │
│                                                                 │
│  2. AGENT PIPELINE EXECUTION                                    │
│     ├── Ingestion → Structuring → Execution → Synthesis        │
│     └── Generate diagnostic outputs                            │
│                                                                 │
│  3. EXPERT REVIEW (Diagnostic Arena)                            │
│     ├── JupyterLab review interface                            │
│     ├── Field-level corrections                                 │
│     └── Clinical rationale capture                              │
│                                                                 │
│  4. FEEDBACK AGGREGATION                                        │
│     ├── Multi-reviewer consensus                                │
│     ├── Inter-rater agreement filtering                         │
│     └── Structured feedback dataset                             │
│                                                                 │
│  5. REWARD MODEL TRAINING                                       │
│     ├── Preference pairs from corrections                       │
│     ├── Train reward model on expert preferences                │
│     └── Validate on hold-out cases                              │
│                                                                 │
│  6. POLICY OPTIMIZATION                                         │
│     ├── PPO/DPO on Structuring Agent                           │
│     ├── Optimize for reward model score                        │
│     └── Validate against clinical guidelines                    │
│                                                                 │
│  7. FEDERATED DISTRIBUTION                                      │
│     ├── Updated weights → global model registry                │
│     ├── Edge devices pull new version                          │
│     └── A/B testing on real deployments                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Review Interface Implementation

**From `code/review_interface.py`:**

Key UI components for doctor-in-the-loop:
- `DiagnosisReviewTable`: Interactive table for correcting diagnosis rankings
- `VariantReviewTable`: Per-variant pathogenicity corrections
- `ToolListReviewer`: Critique tool selection and ordering
- `FreeformNotes`: Capture clinical reasoning

**Design Principle:**
- Minimize clinician time (15 min per case)
- Structured corrections (machine-readable)
- Capture rationale (preserve expert knowledge)
- Confidence quantification

### 8.3 Federated Learning Infrastructure

**Privacy-Preserving Aggregation:**

```python
# Conceptual pseudocode
def federated_rlhf_round():
    # Each site trains locally
    local_gradients = []
    for site in consortium_sites:
        feedback_data = site.get_local_feedback()
        gradients = compute_policy_gradients(feedback_data)
        # Apply differential privacy noise
        gradients = add_dp_noise(gradients, epsilon=1.0)
        local_gradients.append(gradients)

    # Central aggregation (no raw data shared)
    global_update = aggregate_gradients(local_gradients)

    # Distribute updated model
    for site in consortium_sites:
        site.update_model_weights(global_update)
```

**Key Properties:**
- No patient data leaves local site
- Differential privacy guarantees
- Secure aggregation protocols
- Audit logging for compliance

---

## 9. Limitations and Open Questions

### 9.1 Current Limitations

**RLHF Challenges:**
- **Reward hacking**: Model may optimize for surface features rather than true clinical reasoning
- **Annotation consistency**: Inter-reviewer disagreement on edge cases
- **Distribution shift**: Synthetic patients may not capture full real-world complexity
- **Expertise bottleneck**: Scaling expert review to thousands of cases

**Mitigation Strategies:**
- Multiple reviewers per case
- Calibration cases with known answers
- Hybrid real + synthetic training data
- Active learning to prioritize difficult cases

### 9.2 Open Research Questions

1. **Optimal feedback granularity**: Field-level corrections vs holistic preferences?
2. **Expert disagreement resolution**: How to handle 50/50 splits on diagnosis ranking?
3. **Transfer learning**: Can RLHF on one disease category transfer to others?
4. **Long-tail diseases**: How to handle ultra-rare conditions with minimal feedback?
5. **Model size vs accuracy**: Trade-off between M4-deployable models and performance?

### 9.3 Future Directions

**Near-term (2026):**
- Complete Phase 2 synthetic patient generation
- Launch multi-site Diagnostic Arena
- Collect 1000+ expert reviews
- Publish RLHF methodology

**Long-term (2027+):**
- Integrate real patient feedback (with IRB approval)
- Dell Lattice federated infrastructure
- Constitutional AI for automated feedback
- Multi-modal RLHF (WGS + RNA + imaging)

---

## 10. Synthesis for UH2025 Paper Section 7

### 10.1 Key Messages

**Main Thesis:**
The hackathon revealed that real-time expert feedback dramatically improves diagnostic tools. Formalizing this as RLHF enables continuous learning while democratizing expert knowledge globally.

**Three Core Arguments:**

1. **Trust Gap Solution**: RLHF aligns AI reasoning with clinical intuition (section 7.1)
   - Black-box AI fails because clinicians can't verify logic
   - Doctor-in-the-loop enables transparent, correctable reasoning
   - Tool lists make AI thinking auditable

2. **Knowledge Transfer Mechanism**: RLHF captures tacit expert knowledge (section 7.2-7.3)
   - Expert corrections encode clinical reasoning
   - Model weights become "crystallized expertise"
   - Global deployment democratizes access

3. **Empirical Validation**: Discovery 3 proves this works at human scale (section 7.4)
   - Hackathon demonstrated real-time optimization
   - Tool developers improved algorithms in minutes
   - Arena Network scales this to continuous improvement

### 10.2 Key Statistics and Citations

**Statistics to Emphasize:**
- 40% diagnostic rate at hackathon (vs <25% baseline WES)
- Tool developers present in the room (Illumina, PacBio, ONT)
- Real-time feedback cycles: minutes vs months
- 350M rare disease patients globally benefit from democratization

**Citations Needed:**
- [OpenAI InstructGPT] RLHF methodology
- [Anthropic Constitutional AI] Scalable alignment
- [FDA AI/ML Guidance] Regulatory requirements
- [Chatbot Arena] Arena-style evaluation model
- [Medical AI Alignment Paradox] Statistical vs clinical preference
- [Federated Learning in Healthcare] Privacy-preserving training

### 10.3 Novel Contributions

**UH2025-Specific Innovations:**

1. **Medical RLHF Schema**: Field-level corrections with clinical rationale (not just binary preference)
2. **Synthetic Patient Generation**: Disease seed → realistic case pipeline
3. **Tool List as Artifact**: Capturing stepwise reasoning, not just final diagnosis
4. **Three-Layer Framework**: Immediate (diagnosis) + Training (RLHF) + Validation (what works)
5. **Citizen Science Model**: Light/Medium/Heavy contribution tiers

**Comparison to Prior Art:**

| Aspect | Generic RLHF (ChatGPT) | Medical RLHF (UH2025) |
|--------|----------------------|---------------------|
| Feedback Type | Binary preference | Structured corrections |
| Evaluators | Crowd workers | Expert clinicians |
| Data | Real user queries | Synthetic patients |
| Stakes | Low (conversational) | High (diagnostic) |
| Privacy | Anonymized prompts | Federated, PHI-free |
| Artifact | Chat response | Tool list + evidence |

---

## 11. References for Paper

### 11.1 RLHF Methodology

1. **Ouyang et al. (2022).** "Training language models to follow instructions with human feedback." *arXiv:2203.02155* (InstructGPT)
2. **Bai et al. (2022).** "Constitutional AI: Harmlessness from AI Feedback." *arXiv:2212.08073*
3. **Rafailov et al. (2023).** "Direct Preference Optimization: Your Language Model is Secretly a Reward Model." *arXiv:2305.18290*

### 11.2 Medical AI and Clinical Decision Support

4. **Topol, E. (2019).** "High-performance medicine: the convergence of human and artificial intelligence." *Nature Medicine*, 25(1), 44-56.
5. **FDA (2021).** "Artificial Intelligence/Machine Learning (AI/ML)-Based Software as a Medical Device (SaMD) Action Plan."
6. **Sendak et al. (2020).** "Machine Learning in Health Care: A Critical Appraisal of Challenges and Opportunities." *eGEMs*, 8(1).

### 11.3 Doctor-in-the-Loop and Human Oversight

7. **Cabitza et al. (2017).** "Unintended Consequences of Machine Learning in Medicine." *JAMA*, 318(6), 517-518.
8. **Ghassemi et al. (2021).** "The false hope of current approaches to explainable artificial intelligence in health care." *The Lancet Digital Health*, 3(11), e745-e750.
9. **Tonekaboni et al. (2019).** "What Clinicians Want: Contextualizing Explainable Machine Learning for Clinical End Use." *arXiv:1905.05134*

### 11.4 Federated Learning and Privacy

10. **Rieke et al. (2020).** "The future of digital health with federated learning." *NPJ Digital Medicine*, 3(1), 119.
11. **Kaissis et al. (2020).** "Secure, privacy-preserving and federated machine learning in medical imaging." *Nature Machine Intelligence*, 2(6), 305-311.
12. **HIPAA Privacy Rule** (2013). 45 CFR Part 164.

### 11.5 Rare Disease and Genomic Medicine

13. **Wilhelm Foundation.** Undiagnosed Hackathon Mission Statement and Case Studies.
14. **Illumina.** "Bringing the World Together to Solve the Unsolvable" (Hackathon feature).
15. **Mayo Clinic News Network.** "Rare Disease Hackathon Rings Bell for Families."

### 11.6 Arena-Style Evaluation

16. **Zheng et al. (2023).** "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena." *arXiv:2306.05685*
17. **LMSYS Org.** Chatbot Arena leaderboard and methodology documentation.

### 11.7 Hackathon Observations (Internal)

18. **Hackathon Participant Observations** (primary source)
19. **UH2025 Discovery Framework** (`paper/sections/02_hackathon/discoveries.md`)
20. **Federated Architecture Documentation** (`docs/FEDERATED.md`)

---

## 12. Conclusion

**Summary of Key Findings:**

1. **RLHF is proven methodology** for aligning LLMs with human preferences (InstructGPT, Constitutional AI)
2. **Medical AI requires doctor-in-the-loop** for trust, safety, and regulatory compliance
3. **Discovery 3 demonstrates real-time optimization works** at human scale (hackathon evidence)
4. **Diagnostic Arena enables scalable expert feedback** via synthetic patients and structured reviews
5. **Federated RLHF democratizes expertise** while preserving privacy

**For Section 7 of Paper:**

**Main Narrative Arc:**
1. **Problem**: Black-box AI fails in clinical settings (trust gap, alignment paradox)
2. **Observation**: Hackathon proves real-time expert feedback works (Discovery 3)
3. **Solution**: Formalize as RLHF with doctor-in-the-loop checkpoints
4. **Implementation**: Diagnostic Arena + federated training
5. **Impact**: Democratize expert knowledge globally while maintaining privacy

**Key Takeaway:**
> "What happened spontaneously in the hackathon room—tool developers receiving immediate expert feedback and optimizing on the fly—becomes a permanent, scaled, global training loop through RLHF. The hackathon revealed the model; RLHF automates it."

**Novel Contribution:**
Medical RLHF differs from conversational AI: it requires **field-level corrections**, **clinical rationale**, and **federated privacy**. The UH2025 system demonstrates this is achievable using high-end consumer hardware (M4 Envelope), making expert-level AI accessible to any clinic worldwide.

---

**Document Status:** Research Complete
**Next Steps:** Integrate findings into paper Section 7 draft
**Contact:** See UH2025Agent README for consortium collaboration
