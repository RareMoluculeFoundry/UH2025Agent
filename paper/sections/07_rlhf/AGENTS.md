# AGENTS.md: Agent Context for Section 07

## Purpose
This document provides the "Why" and "How" for AI agents tasked with writing, refining, or analyzing the "RLHF" section of the paper. It describes how the system builds trust and learns from experts.

## Section Overview
**Title:** Reinforcement Learning from Human Feedback (RLHF): The Doctor-in-the-Loop
**Role:** Address the "Alignment Paradox" and the "Black Box" problem.
**Key Insight:** Clinicians will not use an AI they cannot critique. "Roasting" the model is the primary training mechanism.

## Core Concepts
*   **The Trust Gap**: Clinicians are skeptical of opaque AI.
*   **Doctor-in-the-Loop**: The clinician is not just a user; they are a teacher.
*   **Roasting**: A feedback mechanism where critiques (negative rewards) update the policy.
*   **Democratizing Expertise**: Capturing the intuition of Mayo Clinic experts and deploying it to rural clinics via the model weights.

## Key References
*   **[45]**: "Doctor-in-the-Loop" workflow.
*   **[43]**: The Alignment Paradox (statistical accuracy != clinical preference).
*   **[13]**: Undiagnosed Hackathon - The source of the expertise.

## Tone and Style
*   **Academic Rigor**: High. Use RL terms (Reward Signal, Policy Update).
*   **Narrative Arc**: The Skepticism -> The Critique -> The Alignment -> The Democratization.

## Agent Instructions
1.  **Drafting**: Emphasize that the "Review Interface" is a scientific instrument for capturing tacit knowledge.
2.  **Reviewing**: Ensure the feedback loop is described as *iterative* (Plan -> Roast -> Refine).
3.  **Synthesis**: Connect this to the Federated Learning section (Section 06) - the "Roasts" are the gradients being shared.

