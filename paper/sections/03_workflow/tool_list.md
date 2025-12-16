# The "Tool List" as an Agentic Artifact

## Concept

The Tool List represents the externalized reasoning of expert diagnosticians—a structured plan that determines:
1. Which bioinformatic tools to run
2. In what order
3. With what parameters
4. Based on what clinical hypothesis

## Example Tool List

For a patient with unexplained ataxia:

```
Step 1: Quality control reads (FastQC, MultiQC)
Step 2: Variant calling in ataxia-associated genes (GATK HaplotypeCaller)
Step 3: If negative → Check repeat expansions (ExpansionHunter)
Step 4: If negative → Analyze mitochondrial genome (haplocheck)
Step 5: If negative → Investigate methylation patterns (Nanopore)
```

## From Manual to Agentic

| Manual Process | Agentic Equivalent |
|----------------|-------------------|
| Clinician formulates hypothesis | Planner Agent generates plan |
| Bioinformatician executes tools | Executor Agent runs bio-tools |
| Expert reviews results | Evaluator Agent validates outputs |
| Team iterates | Graph enables conditional loops |

## Key Insight

> The Tool List is the critical artifact that bridges human clinical reasoning and machine execution. An AI system that can generate and adapt Tool Lists dynamically has achieved the core competency of diagnostic reasoning.

## Implementation in UH2025Agent

The Structuring Agent produces a `tool_usage_plan` that mirrors the human Tool List:

```json
{
  "tool_usage_plan": [
    {
      "tool": "clinvar",
      "variant": "chr17:62023005:G:A",
      "rationale": "Check pathogenicity of SCN4A variant"
    },
    {
      "tool": "alphamissense",
      "variant": "chr17:62023005:G:A",
      "rationale": "Predict missense impact"
    }
  ]
}
```
