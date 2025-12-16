# Section 5: Agentic AI — The Digital Hackathon

## Overview

**Phase 2: Building on Hackathon Learnings**

This is the core Phase 2 implementation: translating the hackathon's human swarm dynamics into AI agents. Each agent maps to a hackathon role. The 4-agent concurrent architecture mirrors how parallel teams outperformed sequential specialists.

**The Transformation:**
| Hackathon Role | Phase 2 Agent | What It Does |
|----------------|---------------|--------------|
| Lead Diagnostician | Planner Agent | Hypothesis formation, strategy |
| Clinical Geneticist | Structuring Agent | Phenotype analysis, tool selection |
| Bioinformatician | Executor Agent | Pipeline execution, command translation |
| Cross-Team Synthesis | Synthesis Agent | Report generation, recommendation |

**Why "The Digital Hackathon"?** Because the AI system doesn't replace the hackathon—it replicates its dynamics at scale, available 24/7, everywhere.

> **Hackathon Foundation**
>
> This component automates what we observed at the Undiagnosed Hackathon:
> - **Human Pattern**: Parallel teams working simultaneously, synthesizing findings at milestones (bell ceremony)
> - **Discovery**: Discovery 5 (Swarm Intelligence—Parallel > Sequential)
> - **System Implementation**: 4-agent concurrent processing mirrors the human swarm dynamic
>
> **Human-to-Agent Mapping:**
> | Hackathon Role | Agent | Function |
> |----------------|-------|----------|
> | Lead Diagnostician | Planner Agent | Hypothesis formation |
> | Clinical Geneticist | Structuring Agent | Phenotype analysis, tool selection |
> | Bioinformatician | Executor Agent | Pipeline execution |
> | Cross-Team Synthesis | Synthesis Agent | Report generation |

## Files

- `architecture.md` - Multi-agent framework design
- `deep_learning.md` - AlphaMissense, AlphaGenome, PrimateAI-3D
- `biotools_registry.md` - Complete bio-tool API documentation

## Code Links

- [code/agents/](../../code/agents/) - Agent implementations
- [code/biotools/](../../code/biotools/) - Bio-tool integrations
- [code/uh2025_graph/](../../code/uh2025_graph/) - LangGraph orchestration

## Key Concepts

- **Agentic AI**: Systems capable of perception, reasoning, and autonomous action
- **Planner Agent**: Formulates diagnostic strategy (LLM-based)
- **Executor Agent**: Generates and runs code (deterministic)
- **Evaluator Agent**: Validates biological plausibility

## Models

- AlphaMissense: 89% of 71M variants classified
- AlphaGenome: Sequence-to-function prediction
- PrimateAI-3D: Evolutionary constraint analysis

## References

- [16] Briefings in Bioinformatics - Agentic AI Workflows
- [33] DeepMind Blog - AlphaMissense
- [35] Illumina AI Lab - PrimateAI-3D
