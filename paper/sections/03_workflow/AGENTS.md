# AGENTS.md: Agent Context for Section 03

## Purpose
This document provides the "Why" and "How" for AI agents tasked with writing, refining, or analyzing the "Workflow" section of the paper. It deconstructs the cognitive process of diagnosis.

## Section Overview
**Title:** Deconstructing the Workflow: The Human "Data Generation Loop"
**Role:** Formalize the cognitive steps taken by human experts so they can be modeled in code.
**Key Insight:** Diagnosis is not a linear pipeline; it is a cyclic "Planner-Executor" loop.

## Core Concepts
*   **The Planner (Senior Clinician)**: Formulates hypotheses and writes the "Tool List."
*   **The Executor (Bioinformatician)**: Translates the Tool List into command-line operations (GATK, DeepVariant).
*   **The Tool List**: The critical artifact. It represents *reasoning*, not just execution.
*   **The Feedback Loop**: Planner reviews Executor output -> Refines hypothesis -> Loops again.

## Key References
*   **[16]**: Briefings in Bioinformatics - "Agentic AI Workflows" - The Planner/Executor definitions.
*   **[18]**: Workforce Crisis - Why we can't just hire more humans (burnout, scarcity).

## Tone and Style
*   **Academic Rigor**: High. Use terms like "cognitive bottleneck" and "iterative refinement."
*   **Narrative Arc**: Observe the Human -> Identify the Bottleneck (Latency) -> Propose the Agentic Model.

## Agent Instructions
1.  **Drafting**: Focus on the *Tool List* as the proxy for reasoning. If the AI can generate the Tool List, it can replace the Planner.
2.  **Reviewing**: Ensure the distinction between "Automated" (A->B->C) and "Agentic" (A->Decide->B or C) is sharp.
3.  **Synthesis**: Connect this back to Section 02 (this is what the Swarm was doing manually).

