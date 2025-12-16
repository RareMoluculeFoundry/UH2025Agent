# Section 3: Deconstructing the Workflow — Automating the Pattern

## Overview

**Phase 2: Building on Hackathon Learnings**

This section takes what we observed at the hackathon (Discovery 1 + 2) and automates it. The human Planner-Executor dynamic becomes the multi-agent architecture. The tool lists that clinicians created become structured agent outputs.

**The Transformation:**
| Hackathon (Human) | Phase 2 (Automated) |
|-------------------|---------------------|
| Senior diagnostician formulates hypothesis | Planner Agent generates strategy |
| Bioinformatician translates to commands | Executor Agent runs bio-tools |
| Tool lists written on whiteboards | Structuring Agent produces JSON |
| Hours of back-and-forth | Minutes of agent orchestration |

> **Hackathon Foundation**
>
> This component automates what we observed at the Undiagnosed Hackathon:
> - **Human Pattern**: Senior diagnosticians formulate hypotheses; bioinformaticians translate to command-line operations
> - **Discovery**: Discovery 1 (The Planner-Executor Dynamic) + Discovery 2 (Tool List as Reasoning Artifact)
> - **System Implementation**: Planner Agent formulates strategy; Executor Agent runs bio-tools; Tool Lists become structured outputs
>
> *"The Planner says: 'Check SCN4A for splice variants.' The Executor runs: `spliceai --variant SCN4A:c.1234+5G>A`"*

## Files

- `planner_executor.md` - The manual workflow and cognitive bottlenecks
- `tool_list.md` - The "Tool List" as a proxy for agentic reasoning

## Code Links

- [code/agents/](../../code/agents/) - Agent implementations (Planner→Structuring, Executor)
- [code/uh2025_graph/](../../code/uh2025_graph/) - LangGraph workflow orchestration
- [code/uh2025_graph/nodes.py](../../code/uh2025_graph/nodes.py) - Node definitions

## Key Concepts

- **Planner Role**: Senior diagnosticians formulating high-level hypotheses
- **Executor Role**: Bioinformaticians translating requests to command-line operations
- **Iterative Loop**: Continuous refinement based on results
- **Tool List**: The critical reasoning artifact

## Bottlenecks Identified

1. **Latency**: Hours-long feedback loops
2. **Cognitive Load**: Limited by individual knowledge
3. **Resource Scarcity**: Global shortage of geneticists

## References

- [13] Undiagnosed Hackathon Official Site
- [16] Briefings in Bioinformatics - Agentic AI Workflows
