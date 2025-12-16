# The Undiagnosed Hackathon: A Playbook for Diagnostic Medicine

> **Status**: Active Development (v3.3.0)
> **Type**: Methods Review & System Architecture
> **Title**: "The Undiagnosed Hackathon as a Playbook: Agentic AI and Federated Learning for Clinical Decision Support in Rare Disease"
> **Narrative**: Hackathon-First — The hackathon is the pattern, the Rare Arena Network is how we scale it

## Core Thesis

> **"The hackathon reveals the model; we automate the model."**

This paper is grounded on a single insight: The Undiagnosed Hackathon is not merely an event—it is an **empirical observation window** into how world-class diagnosticians actually solve impossible cases. By watching experts collaborate, we extracted six transferable principles that became the blueprint for an AI system capable of replicating the hackathon effect at scale.

## Mission Statement

This paper is the operational manual for the **Wilhelm Foundation's Undiagnosed Hackathon** (UH2025). Our goal is to solve the "Diagnostic Odyssey" for 350 million rare disease patients worldwide by democratizing access to clinical-grade genomic analysis. We build **Agentic AI** systems that act as a "Digital Bioinformatician" for every patient, regardless of their location or economic status.

**Origin**: The Wilhelm Foundation was established by Helene and Mikk Cederroth after the tragic loss of three of their children—Wilhelm, Hugo, and Emma—to an undiagnosed degenerative disease. Their mission: *"To ensure no family endures what they did."*

## Hybrid Authorship Model (Human + AI)

This paper is a collaborative effort between human experts (The Publisher) and AI agents (The Editor).

### How to Contribute (For Humans)
1.  **Thesis First**: Do not write the prose yourself. Instead, edit the `AGENTS.md` file in the relevant section.
2.  **Define Constraints**: Use `AGENTS.md` to tell the agent *what* to write, *why* it matters, and *which* references to use.
3.  **Review Diffs**: Treat the agent's output as a first draft. Edit it directly or update `AGENTS.md` to correct the agent's logic.

### How to Contribute (For Agents)
1.  **Read Orders**: Always read `paper/AGENTS.md` (The Editor-in-Chief) and the section's `AGENTS.md` before drafting.
2.  **Grounding**: Never invent statistics. If a number is missing, check `agent_context/RESEARCH_CONTEXT.md` or ask for a search.
3.  **Sync**: If you update the content, check if `CONTEXT_PAYLOAD.md` needs a refresh.

## Roles & Responsibilities

| Role | Responsibility |
|---|---|
| **Editor-in-Chief** | `paper/AGENTS.md` (The Protocol) |
| **Section Owner** | Human Expert (Defines the 'Why' in `sections/XX/AGENTS.md`) |
| **Researcher** | AI Agent (Populates `paper/research/` with findings) |
| **Drafting Agent** | AI Agent (Synthesizes `AGENTS.md` + `research/` into prose) |

## Directory Structure

```
paper/
├── AGENTS.md                        # Editor-in-Chief Manual (Protocol)
├── PRESENTATION_CONTEXT.json        # Presentation metadata
├── README.md                        # This file (Map)
│
├── sections/                        # Modular paper sections
│   ├── 01_introduction/             # The Undiagnosed Program
│   │   ├── AGENTS.md                # Section instructions
│   │   ├── CONTEXT_PAYLOAD.md       # Context definition
│   │   ├── README.md                # Section overview
│   │   ├── diagnostic_odyssey.md    # Problem statement
│   │   ├── economic_burden.md       # Cost analysis
│   │   └── the_undiagnosed_program.md # Mission & origin
│   ├── 02_hackathon/                # The Discovery Engine
│   ├── 03_workflow/                 # Deconstructing the Workflow
│   ├── 04_multiomics/               # The Multi-Omics Frontier
│   ├── 05_agentic_ai/               # Agentic AI
│   ├── 06_federation/               # Federation
│   ├── 07_rlhf/                     # RLHF
│   ├── 08_validation/               # Validation
│   ├── 09_ethics/                   # Ethics
│   └── 10_future/                   # From Event to Network
│
├── research/                        # Deep Research Artifacts
│   ├── 01_introduction/FINDINGS.md  # ✓ Complete
│   ├── 04_multiomics/FINDINGS.md    # ✓ Complete
│   ├── 05_agentic_ai/FINDINGS.md    # ✓ Complete
│   ├── 06_federation/FINDINGS.md    # ✓ Complete
│   └── 09_ethics/FINDINGS.md        # ✓ Complete
│
├── references/                      # Bibliography and citations
│   ├── bibliography.md              # Full reference list
│   └── paper_context.md             # Reference guidelines
│
├── figures/                         # Diagrams and images
├── scripts/                         # Utility scripts
│   └── aggregate_context.py         # Context aggregation
├── templates/                       # File templates
│   ├── AGENTS_TEMPLATE.md
│   └── CONTEXT_PAYLOAD_TEMPLATE.md
└── assets/                          # Additional assets
```

## Narrative Structure: Hackathon as Conceptual Foundation

The paper follows a **Hackathon-First** narrative where each technical section explicitly traces back to observations made at the Undiagnosed Hackathon.

### The Three-Layer Framework

| Layer | What Happens | What It Teaches |
|-------|--------------|-----------------|
| **Immediate** | Diagnoses for waiting families (4/10 in 48 hours) | The workflow that actually solves cases |
| **Training** | Experts reason aloud, correct each other, generate tool lists | High-quality RLHF data from natural collaboration |
| **Validation** | Which tools/technologies get used in breakthrough moments | Discovery of what matters vs. what's theoretical |

### The Six Discoveries

Each technical section implements one or more discoveries extracted from hackathon observation:

| Discovery | What We Observed | System Component |
|-----------|------------------|------------------|
| 1. Planner-Executor Dynamic | Clinicians propose, bioinformaticians execute | Planner + Executor Agents |
| 2. Tool List as Reasoning | Experts create explicit analysis lists | Structuring Agent output |
| 3. Real-Time Optimization | Tool developers tweaking in real-time | RLHF training loop |
| 4. Multi-Omics Necessity | WES-unsolvable cases cracked by long-read | Multi-modal orchestration |
| 5. Swarm Intelligence | Parallel teams outperform sequential | Multi-agent concurrency |
| 6. Emotional Milestones | Bell ceremony marks progress | Checkpoint system + HITL |

## Section Overview

| # | Directory | Title | Content Files | Hackathon Connection |
|---|-----------|-------|---------------|---------------------|
| 01 | `01_introduction` | The Undiagnosed Program | diagnostic_odyssey.md, economic_burden.md, the_undiagnosed_program.md | Mission, origin story, Problem-before-Solution |
| 02 | `02_hackathon` | **The Hackathon Playbook** | discoveries.md, methodology.md, swarm_dynamics.md, **tools_ecosystem.md**, **partner_collaboration.md**, **case_studies.md** | **Core Section**: Six Discoveries, Three-Layer Framework, Expanding Possibility |
| 03 | `03_workflow` | Deconstructing the Workflow | planner_executor.md, tool_list.md | Discovery 1 + 2: Planner-Executor + Tool Lists |
| 04 | `04_multiomics` | The Multi-Omics Frontier | beyond_exome.md, data_integration.md | Discovery 4: DNA2 case as validation |
| 05 | `05_agentic_ai` | Agentic AI | architecture.md, biotools_registry.md, deep_learning.md | Discovery 5: Human-to-Agent Mapping |
| 06 | `06_federation` | Federation | privacy_utility.md, swarm_learning.md | Discovery 5 + 3: Distributed hackathon |
| 07 | `07_rlhf` | RLHF | democratizing.md, doctor_in_loop.md, ui_implementation.md | Discovery 3: Formalizing real-time feedback |
| 08 | `08_validation` | Validation | baby_bear.md, case_studies.md | Discovery 6: Bell ceremony as proof point |
| 09 | `09_ethics` | Ethics | challenges.md | Hackathon embeds oversight by design |
| 10 | `10_future` | From Event to Network | outlook.md | All discoveries converge |

> **Note:** Each section directory also contains `AGENTS.md`, `CONTEXT_PAYLOAD.md`, and `README.md` files.

## Phase 2 Framing

Sections 03-07 are framed as **Phase 2: Building on Hackathon Learnings**. Each section explicitly connects to what we observed at the hackathon:

| Section | Phase 2 Title | Transformation |
|---------|---------------|----------------|
| 03 | Automating the Pattern | Human Planner-Executor → Multi-agent architecture |
| 04 | Scaling the Technology Stack | Manual multi-omics → Orchestrated integration |
| 05 | The Digital Hackathon | Human swarm dynamics → AI agent concurrency |
| 06 | Scaling the Playbook Globally | 48-hour event → 24/7 federated network |
| 07 | Formalizing Real-Time Optimization | Human RLHF → Continuous training pipeline |

**The Key Insight:** The hackathon is not Phase 1. It is the **pattern**. The Rare Arena Network is how we **scale** it.

## Research Status

Research artifacts in `research/` directory:

| Section | Research Status | Notes |
|---------|-----------------|-------|
| 01_introduction | ✅ FINDINGS.md | Complete |
| 02_hackathon | ⏳ Pending | Folder exists, needs FINDINGS.md |
| 03_workflow | ❌ Missing | No research folder |
| 04_multiomics | ✅ FINDINGS.md | Complete |
| 05_agentic_ai | ✅ FINDINGS.md | Complete |
| 06_federation | ✅ FINDINGS.md | Complete |
| 07_rlhf | ❌ Missing | No research folder |
| 08_validation | ⏳ Pending | Folder exists, needs FINDINGS.md |
| 09_ethics | ✅ FINDINGS.md | Complete |
| 10_future | ⏳ Pending | Folder exists, needs FINDINGS.md |
