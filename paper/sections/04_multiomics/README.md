# Section 4: The Multi-Omics Frontier — Scaling the Technology Stack

## Overview

**Phase 2: Building on Hackathon Learnings**

This section takes what we learned about multi-omics necessity at the hackathon (Discovery 4) and systematizes it. The DNA2 case proved that long-read + RNA-seq is essential. Phase 2 makes this accessible to every clinic.

**The Transformation:**
| Hackathon (Human) | Phase 2 (Automated) |
|-------------------|---------------------|
| ONT team manually runs long-read | Agent orchestrates multi-modal data |
| Experts mentally overlay data types | Multi-Omics Tensor integrates computationally |
| "We should try RNA-seq" (intuition) | Diagnostic Stewardship recommends escalation |
| 60%+ yield from hackathon-style analysis | Replicated at every participating institution |

> **Hackathon Foundation**
>
> This component automates what we observed at the Undiagnosed Hackathon:
> - **Human Pattern**: Cases unsolved by WES were cracked using long-read sequencing, RNA-seq, and methylation analysis
> - **Discovery**: Discovery 4 (Multi-Omics Necessity)
> - **System Implementation**: Multi-Omics Tensor integrating 4 data layers that humans cannot mentally overlay
>
> *The DNA2 Rothmund-Thomson case was invisible to standard WGS—found only by long-read sequencing at the Hackathon, validated by RNA-seq.*

## Files

- `beyond_exome.md` - Multi-omics necessity and technologies
- `data_integration.md` - Omic layers comparison table

## Key Technologies

- **Long-Read Sequencing**: PacBio HiFi, Oxford Nanopore
- **Transcriptomics**: RNA-seq for functional validation
- **Methylation**: Episignatures for syndrome detection

## References

- [2] Cell - SpliceAI
- [22] Mayo Clinic - Multi-omics explanation
- [24] PubMed - DNA2 Case Study
