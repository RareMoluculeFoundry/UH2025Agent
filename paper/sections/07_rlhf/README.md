# Section 7: RLHF — Formalizing Real-Time Optimization

## Overview

**Phase 2: Building on Hackathon Learnings**

This section takes the most remarkable hackathon phenomenon—tool developers adjusting algorithms in real-time based on clinician feedback—and formalizes it as a continuous training system. What happened spontaneously in the room becomes a permanent feedback loop.

**The Transformation:**
| Hackathon (Human RLHF) | Phase 2 (Formalized RLHF) |
|------------------------|---------------------------|
| "This threshold is wrong" (verbal) | Structured feedback signal (JSON) |
| Engineer adjusts parameters manually | Model weights updated automatically |
| Knowledge stays with that engineer | Knowledge distributed to all instances |
| One-time optimization | Continuous improvement |

**Why "Formalizing Real-Time Optimization"?** Because the hackathon showed us what clinicians actually want. RLHF encodes that permanently.

> **Hackathon Foundation**
>
> This component automates what we observed at the Undiagnosed Hackathon:
> - **Human Pattern**: Tool developers from Illumina, PacBio, and Oxford Nanopore tweaked algorithms in real-time based on clinician feedback
> - **Discovery**: Discovery 3 (Real-Time Optimization—Human RLHF)
> - **System Implementation**: Formalized feedback loop where doctors critique ("roast") AI logic, transferring tacit knowledge into the neural network
>
> *"Representatives from Illumina, Oxford Nanopore, and PacBio were present not just as sponsors but as active participants... tweaking their algorithms and pipelines in real-time to meet the needs of the diagnosticians."*

## Files

- `doctor_in_loop.md` - Trust gap, feedback mechanism, and training
- `democratizing.md` - Knowledge transfer and global access
- `ui_implementation.md` - Review interface implementation details

## Code Links

- [code/review_interface.py](../../code/review_interface.py) - DiagnosisReviewTable widget
- [code/arena/feedback_collector.py](../../code/arena/feedback_collector.py) - Feedback aggregation
- [notebooks/RLHF_Demo.ipynb](../../notebooks/RLHF_Demo.ipynb) - Interactive demo

## Key Concepts

- **Trust Gap**: Clinician skepticism of black-box AI
- **Alignment Paradox**: Statistical accuracy vs clinical preference
- **RLHF Mechanism**: "Roasting" the model with expert critique
- **Democratization**: Virtual expert access for all clinics

## Feedback Signal

```yaml
assessment:
  correctness: "partial"  # correct | partial | incorrect
  confidence: 0.75
corrections:
  field: "diagnosis_1"
  original: "Paramyotonia Congenita"
  corrected: "Hyperkalemic Periodic Paralysis"
  rationale: "Episode pattern suggests HyperKPP"
```

## References

- [43] arXiv - Alignment Paradox
- [45] Automate Clinic - Doctor-in-the-Loop
