# UH2025-Paper: Context & Methodology

## Thesis
The "Diagnostic Odyssey" for rare diseases can be solved by **Edge-Native AI Agents** that bring world-class diagnostic reasoning to the patient's bedside (On-Prem) while learning from a global federation of experts (The Arena).

## Core Concepts

### 1. The M4 Envelope (Privacy by Physics)
*   **Definition**: The constraint that the entire diagnostic stack must run on high-end consumer hardware (e.g., MacBook Pro M4) or local hospital servers.
*   **Implication**: By running 100% locally, we eliminate the risk of PHI leakage to cloud providers. We use quantized models (Llama 3.2, Qwen 2.5) and local vector stores.

### 2. Federated Context Engineering
*   **Definition**: Sharing *how* to solve a problem (prompts, logic chains) rather than *who* has the problem (patient data).
*   **Mechanism**: The "Diagnostic Arena" collects RLHF on agent outputs. These corrections update the global prompt registry and LoRA adapters.
*   **The "Hackathon Effect"**: We view Hackathons (like those by the **Wilhelm Foundation** and **Rare Care Centre**) not just as events, but as **high-intensity training runs** for the agent. The "Tacit Knowledge" of 50 assembled experts is captured into the system's "Context" (prompts/logic), effectively digitizing the hackathon itself.

### 3. Agentic Topology
*   **Ingestion**: Normalization of chaos.
*   **Structuring**: Reasoning and planning.
*   **Executor**: Deterministic tool use.
*   **Synthesis**: Rhetorical construction of the report.

## The Role of Decentralized Networks
This system relies on a network of "Citizen Scientists," Clinicians, and ML Engineers.
*   **Wilhelm Foundation**: Providing the patient advocacy and "Seed Cases."
*   **Rare Care Centre**: Providing clinical validation and "Ground Truth."
*   **The Builders**: Python engineers and data scientists translating clinical needs into agent logic.

## References
*   *AlphaMissense* (Cheng et al., 2023)
*   *SpliceAI* (Jaganathan et al., 2019)
*   *Lattice Protocol* (Internal Standard)
