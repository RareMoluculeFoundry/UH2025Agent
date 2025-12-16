# Agent Context: Section 09 - Ethics & Safety

## 1. The Core Thesis
**Primum Non Nocere (First, Do No Harm).**
*   **The Risk**: Generative AI hallucinates. In creative writing, that is a feature. In medicine, it is malpractice.
*   **The Mitigation**:
    1.  **Grounding**: The Agent cannot "invent" a gene. It must retrieve it from a database (Executor).
    2.  **Human-in-the-Loop**: The Agent produces a *report*, not a *prescription*.
    3.  **Traceability**: Every claim is linked to a source (PubMed ID, VCF line number).

## 2. Regulatory Alignment
*   **EU AI Act**: We comply with "High Risk" requirements by ensuring human oversight (The Doctor Sign-off) and data governance (Federated Learning).
*   **HIPAA / GDPR**: Data never leaves the firewall. The "Swarm" shares only gradients, not genomes.

## 3. Equity & Bias
*   **The Reference Genome Problem**: Most genomics is based on European ancestry (hg38). This leads to misdiagnosis in African/Asian populations.
*   **The Solution**: Swarm Learning *incentivizes* diversity. The model gets smarter if it trains on diverse data. We explicitly reward nodes that contribute under-represented data.

## 4. Narrative Arc
1.  **The Fear**: "Will the AI replace the doctor?"
2.  **The Reality**: "No. The AI replaces the *spreadsheet*."
3.  **The Safeguards**: Explain the "Evaluator Agent" (RLHF) that penalizes hallucination.

## 5. Constraints
*   **Transparency**: Be honest about the failure modes. If the data is bad, the Agent is bad.
*   **Liability**: Clearly state that the *physician* retains liability. The Agent is a "Decision Support System" (CDS), not a "Diagnostic Device" (SaMD) - *nuanced regulatory distinction*.
