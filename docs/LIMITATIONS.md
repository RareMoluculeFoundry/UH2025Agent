# Limitations and Appropriate Use

**An Honest Assessment of What UH2025-CDS-Agent Can and Cannot Do**

---

## Critical Disclaimer

**This system is a research and educational tool. It is NOT approved for clinical use.**

The UH2025 Agent is designed to assist research into rare disease diagnosis. It has not been validated through clinical trials, received regulatory approval, or been certified for clinical deployment.

**Do not use this system to make clinical decisions about real patients without appropriate oversight, validation, and regulatory compliance.**

---

## Technical Limitations

### 1. LLM Hallucination Risk

Large Language Models can generate plausible-sounding but incorrect information:

| Risk Area | Manifestation | Mitigation |
|-----------|--------------|------------|
| Fabricated variants | May cite non-existent mutations | Verify all variants against ClinVar/gnomAD |
| Invented references | May create fake paper citations | Check all literature references |
| Incorrect gene-disease links | May associate genes with wrong diseases | Cross-reference with OMIM |
| Confidence miscalibration | May express certainty about uncertain claims | Require expert validation at every step |

**Critical**: Never trust LLM output without verification through authoritative databases.

### 2. Bio-Tool Coverage Gaps

The integrated bio-tools have inherent limitations:

| Tool | Coverage | Known Gaps |
|------|----------|------------|
| **ClinVar** | Curated clinical variants | Novel variants not included; interpretation quality varies |
| **OMIM** | Gene-disease relationships | Not all rare diseases documented; updates lag discovery |
| **AlphaMissense** | 71M missense variants | Non-missense variants not covered; structural variants excluded |
| **SpliceAI** | Splice site predictions | Deep intronic effects may be missed; false positives occur |
| **REVEL** | Ensemble pathogenicity | Training set biases; VUS remain challenging |

**Critical**: A variant not flagged as pathogenic is not proven benign. Absence of evidence is not evidence of absence.

### 3. Data Quality Dependency

The system's output quality depends entirely on input quality:

**Clinical Summary Issues:**
- Incomplete phenotype descriptions reduce diagnostic accuracy
- Inconsistent terminology confuses entity extraction
- Missing medical history limits differential generation
- Subjective symptom descriptions vary in reliability

**Genomic Data Issues:**
- VCF quality affects variant calling accuracy
- Coverage gaps may hide true pathogenic variants
- Structural variants may be missed or miscalled
- Filtering artifacts can exclude relevant variants

**Garbage in, garbage out**: Poor quality input data will produce poor quality diagnostic suggestions.

### 4. Model Size Constraints

The M4 envelope imposes practical limits:

| Model | Size | Capability Trade-off |
|-------|------|---------------------|
| Ingestion (3B) | Small | May miss subtle clinical nuances |
| Structuring (14B) | Medium | May struggle with complex differential diagnoses |
| Synthesis (32B) | Large | Best quality but slower inference |

Larger models exist but require more memory than typical edge deployments allow.

### 5. Context Window Limits

Long clinical histories may exceed context limits:

- Complex cases with years of medical records
- Extensive family histories across generations
- Detailed workup documentation from multiple specialists

**Mitigation**: The ingestion agent summarizes, but summarization may lose relevant details.

---

## Scope Limitations

### 1. Optimized for Rare Mendelian Diseases

The system is designed for:
- **Single-gene disorders** with clear inheritance patterns
- **High-penetrance variants** with strong genotype-phenotype correlations
- **Documented rare diseases** with established diagnostic criteria

The system is NOT designed for:
- **Complex polygenic diseases** (diabetes, heart disease, most cancers)
- **Environmental conditions** masquerading as genetic diseases
- **Novel diseases** not in training data
- **Common diseases** with different diagnostic workflows

### 2. Requires Structured Input

The system expects:
- Clinical summary in markdown or structured text
- Genomic variants in JSON (VCF-derived) format
- Standard phenotype terminology (HPO preferred)

The system cannot process:
- Raw sequencing files (FASTQ, BAM)
- Unstructured clinical notes directly
- Images, scans, or other non-text data
- Audio/video of patient consultations

### 3. English Language Primary

All prompts, documentation, and training are in English:
- Non-English clinical summaries will perform poorly
- Medical terminology varies across languages
- Translation artifacts may introduce errors

### 4. Geographic/Population Bias

Training data reflects:
- Published literature (biased toward well-resourced institutions)
- Available databases (heavily European ancestry)
- Known gene-disease associations (discovery bias)

Populations may be underrepresented:
- African and African-diaspora populations
- South Asian populations
- Indigenous populations
- Admixed populations

**Variant frequency data may be unreliable for underrepresented populations.**

---

## Deployment Considerations

### 1. Hardware Requirements

**Minimum:**
- Apple Silicon M1 or Intel 8-core
- 32 GB memory
- 50 GB storage
- Local only (no GPU required)

**Recommended (M4 Envelope):**
- Apple M4 Max
- 64-128 GB unified memory
- 100 GB storage
- Metal acceleration

Systems below minimum specs will experience:
- Extremely slow inference
- Potential out-of-memory crashes
- Unreliable operation

### 2. Not Validated for Clinical Use

This system has NOT undergone:
- Clinical validation studies
- FDA 510(k) clearance
- CE marking
- IRB-approved clinical trials
- CLIA laboratory certification

**Using this for clinical decisions without proper oversight and validation may violate regulations and endanger patients.**

### 3. Research/Educational Status

Appropriate uses:
- Research into AI-assisted diagnosis
- Educational demonstrations
- Hypothesis generation for research
- Workflow development and testing
- Synthetic patient analysis

Inappropriate uses:
- Direct clinical decision-making
- Replacement for genetic counseling
- Automated report generation for patients
- Unsupervised diagnostic screening

### 4. IRB Considerations

If using with real patient data (even retrospectively):
- IRB approval likely required
- HIPAA compliance must be ensured
- Informed consent may be needed
- Data handling protocols must be established

Consult your institution's IRB before using real patient data.

---

## Failure Modes

### When the System May Give Wrong Answers

| Scenario | Risk | Detection |
|----------|------|-----------|
| Novel disease | Not in training data | Literature search finds no matches |
| Data entry error | Propagates through pipeline | Clinical review catches inconsistencies |
| Phenocopy | Different disease mimics target | Expert recognizes atypical features |
| VUS overinterpretation | Treats uncertain variants as pathogenic | ACMG classification review |
| Complex inheritance | Multi-gene or modifier effects | Family segregation analysis |
| Mosaicism | Not detected in standard sequencing | Specialized testing required |

### Red Flags to Watch For

**System may be unreliable when:**
- Confidence scores are very high on uncertain cases
- Diagnostic suggestions contradict obvious clinical findings
- Generated report contains internally inconsistent information
- Variant citations don't match database lookups
- Gene-disease links seem implausible to expert

### Escalation Protocols

When system output is questionable:

1. **Flag the case** in the review interface
2. **Document concerns** in feedback notes
3. **Seek additional expert opinion** from relevant specialist
4. **Manual literature review** bypassing system suggestions
5. **Consider alternative diagnoses** not suggested by system

### Human Override Procedures

At any HITL checkpoint, the expert can:

| Override | When to Use |
|----------|-------------|
| **Edit** | Correct specific errors in output |
| **Reject** | Output is fundamentally flawed |
| **Skip** | Case inappropriate for system analysis |
| **Override confidence** | System over/under-confident |
| **Add manual diagnosis** | Expert knows answer system missed |

**All overrides are logged for quality assurance and RLHF training.**

---

## What This System Is Good For

Despite limitations, the system can provide value:

### Strengths

| Capability | Value |
|------------|-------|
| **Data organization** | Structures complex clinical and genomic data |
| **Evidence gathering** | Queries multiple databases systematically |
| **Hypothesis generation** | Suggests diagnoses expert might not consider |
| **Documentation** | Creates structured reports for review |
| **Consistency** | Applies same process to every case |
| **Tirelessness** | Can process many cases without fatigue |

### Appropriate Applications

- **Triage**: Identify cases likely to have diagnosable conditions
- **Checklist**: Ensure no obvious diagnoses are missed
- **Education**: Train students on diagnostic reasoning
- **Research**: Study patterns in rare disease presentation
- **Workflow**: Prototype AI-assisted diagnostic pipelines

---

## Comparison to Human Experts

| Dimension | System | Human Expert |
|-----------|--------|--------------|
| Speed | Fast (minutes) | Slow (hours/days) |
| Consistency | Perfectly consistent | Variable |
| Database access | Comprehensive, simultaneous | Limited, sequential |
| Rare knowledge | Training-dependent | Experience-dependent |
| Intuition | None | Extensive |
| Context integration | Limited | Sophisticated |
| Novel situations | Poor | Adaptable |
| Accountability | None (tool) | Full (clinician) |
| Final judgment | Never | Always |

**The system is a tool to augment experts, not replace them.**

---

## Future Improvements

Areas where future versions may address current limitations:

1. **Larger models** as hardware improves
2. **Multi-modal input** (images, structured EMR data)
3. **Expanded population coverage** in training
4. **Better uncertainty quantification**
5. **Improved hallucination detection**
6. **Clinical validation studies**
7. **Regulatory approval pathways**
8. **Multi-language support**

---

## Summary of Appropriate Use

### DO Use This System To:
- Generate diagnostic hypotheses for expert review
- Organize and structure clinical/genomic data
- Query databases systematically
- Document findings in structured format
- Learn about AI-assisted diagnosis
- Prototype diagnostic workflows

### DO NOT Use This System To:
- Make unsupervised clinical decisions
- Replace genetic counseling
- Generate patient-facing reports without expert review
- Screen populations without validation
- Diagnose novel/undocumented diseases
- Process data without appropriate IRB oversight

---

*"An honest assessment of limitations is not a weakness—it's a prerequisite for trustworthy AI in medicine."*

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Part of**: UH2025-CDS-Agent Documentation
