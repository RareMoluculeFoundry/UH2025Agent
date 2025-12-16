# Reinforcement Learning from Human Feedback (RLHF): The Doctor-in-the-Loop

## 7.1 The Trust Gap and Alignment Paradox

Even the most advanced AI model faces the "black box" problem. Clinicians are inherently skeptical of "black box" algorithms and are hesitant to act on AI recommendations they cannot understand or verify.[43] Furthermore, research has identified "alignment paradoxes" in medical AI, where models that are statistically more accurate (e.g., higher F1 score) are sometimes less preferred by clinicians because their reasoning process is opaque or does not align with clinical intuition.[43]

## 7.2 "Roasting" the Model: A Feedback Mechanism

To bridge this gap, the Rare Arena Network proposes a "Doctor-in-the-Loop" workflow using Reinforcement Learning from Human Feedback (RLHF).[45] This is the same technique used to train language models like ChatGPT, but adapted for high-stakes medical reasoning.

### Mechanism

When the AI Agent proposes a diagnosis or a tool list, the clinician reviews it. If the logic is flawed (e.g., "The agent prioritized a recessive variant but the pedigree suggests dominant inheritance") or the "Tool List" is inefficient, the doctor critiques (or "roasts") the output.

### Feedback Signal

This critique serves as a reward signal (negative for errors, positive for insights) that updates the model's policy. The model learns not just what the diagnosis is, but how a clinician prefers to reach it—aligning the AI with medical reasoning standards.[45]

### Feedback Schema

```yaml
step_feedback:
  step_id: "structuring"
  timestamp: "2025-11-25T10:30:00Z"
  reviewer:
    id: "clinician_001"
    role: "geneticist"

  assessment:
    correctness: "partial"  # correct | partial | incorrect
    confidence: 0.75

  corrections:
    - field: "diagnostic_table.diagnosis_1"
      original: "Paramyotonia Congenita"
      corrected: "Hyperkalemic Periodic Paralysis"
      rationale: "Episode pattern suggests HyperKPP over PMC"

  notes: "Good variant identification, needs diagnosis ranking work"
```

## 7.3 Democratizing Expertise

This process captures the tacit knowledge of the world's best diagnosticians—the "Planners" at the Hackathon. As they critique the models during the event, they are effectively transferring their intuition and expertise into the AI's neural network. Once trained, these models can be deployed to community hospitals and primary care centers, effectively democratizing access to expert-level diagnostic reasoning.[13]

A general practitioner in a rural clinic could thus have access to a "virtual" Mayo Clinic expert via the AI agent, which has been trained and validated by the actual experts.
