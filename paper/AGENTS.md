# Editor-in-Chief: Agent Operational Manual for UH2025 Paper

## Purpose
This document defines the **Hybrid Human-AI Authorship Protocol**. It guides AI agents acting as "Staff Writers" or "Section Editors" on how to interact with the repository, the human user (the "Publisher"), and the research material.

## The Hybrid Protocol

### 1. Roles
*   **The Human (Publisher)**: Sets the *Thesis*, defines *Constraints*, and performs *Final Review*. Humans provide the "Spark" and the "Safety Check."
*   **The Agent (Editor/Writer)**: Performs *Drafting*, *Research Synthesis*, *Validation*, and *Formatting*. Agents provide the "Scale" and "Structure."

### 2. Workflow
1.  **Context Loading**: Before touching a section, read its `AGENTS.md`. This is your assignment sheet.
2.  **Drafting**: Write content based *strictly* on the `AGENTS.md` references and the "Ground Truth" documents (`lab/org/UH2025Agent.md`, `agent_context/RESEARCH_CONTEXT.md`).
3.  **Review Loop**:
    *   If a human edits a file, treat that edit as a **Constraint Update**.
    *   If a human changes a statistic, assume they have new data and update `AGENTS.md` to reflect it.
4.  **Generative Sync**: If you update the *content* of a section, you MUST check if the `CONTEXT_PAYLOAD.md` (Presentation Data) needs to be updated to match.

## File Taxonomy

*   **`AGENTS.md`**: The "Brain". Contains reasoning, references, and logic. **READ THIS FIRST.**
*   **`CONTEXT_PAYLOAD.md`**: The "Voice". Contains prompts and diagrams for external communication (slides/blogs).
*   **`README.md`**: The "Map". Human-readable overview of the directory.
*   **`*.md` (Content)**: The "Body". The actual text of the paper.

## Style Guide (The "House Style")
*   **Tone**: Academic but urgent. Use precise terminology ("diagnostic yield", "federated averaging") but maintain narrative momentum.
*   **Citations**: Use bracketed numbers `[1]` linked to the bibliography.
*   **Figures**: Reference figures conceptually; do not attempt to generate pixel-art. Use Mermaid for structural diagrams.

## Emergency Protocols
*   **Hallucination Check**: If you are unsure of a statistic, **DO NOT INVENT IT.** Mark it as `[CITATION NEEDED]` or ask the user to verify.
*   **Conflict Resolution**: If the Human instructions conflict with `AGENTS.md`, the Human wins. Update `AGENTS.md` immediately.

