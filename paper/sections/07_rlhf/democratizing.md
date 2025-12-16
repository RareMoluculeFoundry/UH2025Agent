# Democratizing Expertise Through RLHF

## The Knowledge Transfer Pipeline

```
Expert Diagnosticians → RLHF Feedback → Model Updates → Global Deployment
    (Mayo Clinic)          (Arena)        (Federated)     (Edge Nodes)
```

## Before RLHF

| Clinic Type | Access to Expertise | Diagnostic Capacity |
|:------------|:--------------------|:--------------------|
| Academic Medical Center | Direct access to specialists | Full |
| Regional Hospital | Referral-based | Limited |
| Rural Clinic | Teleconsultation only | Minimal |
| Resource-Constrained Setting | None | Near zero |

## After RLHF Deployment

| Clinic Type | Access to Expertise | Diagnostic Capacity |
|:------------|:--------------------|:--------------------|
| All Clinics | AI agent trained by experts | Expert-level |

## Implementation in UH2025Agent

The `DiagnosisReviewTable` widget captures expert feedback:

```python
from code.review_interface import DiagnosisReviewTable

review_table = DiagnosisReviewTable(
    differential_diagnosis_file="outputs/differential_diagnosis.json"
)
# Clinician reviews, adjusts confidence, adds notes
# Feedback saved for training
```

## Contribution Levels

| Level | Contribution | Recognition |
|:------|:-------------|:------------|
| **Heavy** | Code for new bio-tools/agents | Co-authorship |
| **Medium** | Diagnostic Arena reviews | Acknowledgment |
| **Light** | RFC feedback, review calls | Community credit |

## The Citizen Science Model

1. **Generate**: Synthetic patient from disease seed
2. **Run**: Pipeline produces diagnostic outputs
3. **Review**: Expert annotates in JupyterLab
4. **Submit**: Arena bundle to federated pool
5. **Aggregate**: Global model improvement
