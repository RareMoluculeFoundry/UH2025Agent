# Agent Context: Section 05 - Agentic AI Architecture

## 1. The Core Thesis
We are **not** building a chatbot. We are building a **Digital Bioinformatician**.
*   **Old Way**: A human runs 5 different tools (GATK, VEP, SpliceAI), manually piping output from one to another.
*   **New Way (UH2025)**: An **Agentic Workflow** where a "Planner" LLM devises a strategy and an "Executor" code-interpreter runs the tools.

## 2. Key Technical Concepts (Must Include)
*   **Planner-Executor-Evaluator**: Our specific architecture.
    *   *Planner*: The "Prefrontal Cortex" (Claude 3.5 Sonnet / Gemini 1.5 Pro). break down "Diagnose Patient X" into steps.
    *   *Executor*: The "Hands" (Python Sandbox). Runs `bcftools`, `pandas`, and API calls.
    *   *Evaluator*: The "Safety Net" (RLHF Loop). Checks if the output makes biological sense.
*   **Deep Learning Sensors**: The agents don't guess; they read sensors.
    *   *AlphaMissense*: For structural impact.
    *   *AlphaGenome*: For non-coding impact.
    *   *SpliceAI*: For splicing impact.
*   **Hub-and-Spoke Model**: The central Planner coordinates specialized sub-agents (Literature Reviewer, Variant Caller).

## 3. References & Evidence
*   **Industry Validation**: Align our architecture with the "Hub-and-Spoke" models seen in enterprise Agentic AI (e.g., Toyota's production planning, OmniScientist [arXiv:2511.16931]).
*   **State of the Art (2025)**: Reference the shift from "Chat" to "Agency" — autonomous goal seeking (IBM, AWS trends).
*   **DeepMind Legacy**: Cite AlphaFold/AlphaMissense as the "Sensors" that make Agentic AI possible in biology.

## 4. Narrative Arc
1.  **The Bottleneck**: There are only ~5,000 expert bioinformaticians for 350M patients. Humans cannot scale.
2.  **The Solution**: Software that *thinks* like a bioinformatician.
3.  **The Implementation**: How we built it (Python, LangGraph, Elyra).
4.  **The Result**: A system that can navigate from "VCF file" to "Candidate Gene" in minutes, not months.

## 5. Constraints
*   **No Hype**: Do not say "AI cures cancer." Say "AI accelerates candidate prioritization."
*   **Local Execution**: Emphasize that the *Executor* runs locally (privacy), even if the *Planner* is an API.
*   **Hallucination**: Acknowledge it. Explain how the "Evaluator" and "Tool-Use" (Grounding) mitigate it.
