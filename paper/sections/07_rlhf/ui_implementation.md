# UI Implementation: The Review Interface

## 7.4 Interactive Feedback Collection

The UH2025-CDS-Agent implements a comprehensive UI for collecting clinician feedback through Jupyter widgets. This interface serves as the primary mechanism for "Doctor-in-the-Loop" RLHF.

## The DiagnosisReviewTable Widget

The `DiagnosisReviewTable` is the core UI component for clinician review of AI-generated diagnoses.

### Interface Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  Patient ID: DEMO_001                                               │
│  Generated: 2025-11-29 10:00:00                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Diagnosis 1: Myotonia Congenita, Thomsen Type                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ☑ Correct   Confidence: [████████░░] 0.85 → 0.90          │   │
│  │  Genes: CLCN1                                               │   │
│  │  OMIM: 160800                                               │   │
│  │  Notes: [EMG findings strongly support this diagnosis...]   │   │
│  └─────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  Diagnosis 2: Paramyotonia Congenita                                │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ☐ Correct   Confidence: [███████░░░] 0.72 → 0.30          │   │
│  │  Genes: SCN4A                                               │   │
│  │  OMIM: 168300                                               │   │
│  │  Notes: [Symptoms don't worsen with cold...]                │   │
│  └─────────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│  [💾 Save]  [📂 Load]  [🔄 Reset]  [📤 Export]  [🔄 Re-analyze]   │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Components

#### 1. Correctness Checkbox

Each diagnosis row includes a checkbox for marking correctness:

```python
# code/review_interface.py
self.correct_checkbox = widgets.Checkbox(
    value=False,
    description='Correct',
    indent=False,
    layout=widgets.Layout(width='80px')
)
```

#### 2. Confidence Slider

Clinicians can adjust the AI's confidence score:

```python
self.confidence_slider = widgets.FloatSlider(
    value=original_confidence,
    min=0.0,
    max=1.0,
    step=0.05,
    description='Confidence:',
    readout_format='.2f'
)
```

#### 3. Clinical Notes Textarea

Free-text area for clinician rationale:

```python
self.comments_textarea = widgets.Textarea(
    placeholder='Add clinical notes or corrections...',
    layout=widgets.Layout(width='100%', height='80px')
)
```

## Multi-Turn Reanalysis Workflow

The interface supports iterative refinement through the "Request Re-analysis" feature.

### Workflow Diagram

```
                    ┌───────────────────┐
                    │   AI Generates    │
                    │   Diagnoses       │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │   Clinician       │
                    │   Reviews         │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  Approve  │   │  Correct  │   │ Re-analyze│
        └─────┬─────┘   └─────┬─────┘   └─────┬─────┘
              │               │               │
              ▼               ▼               ▼
        ┌───────────┐   ┌───────────┐   ┌───────────┐
        │  Export   │   │   Save    │   │  Pipeline │
        │  Bundle   │   │ Feedback  │   │   Re-run  │
        └───────────┘   └───────────┘   └─────┬─────┘
                                              │
                                              ▼
                                    ┌───────────────────┐
                                    │   Iteration 2     │
                                    │   (with guidance) │
                                    └───────────────────┘
```

### Reanalysis Request

When the clinician clicks "Request Re-analysis":

```python
def _on_reanalysis_requested(self, button):
    """Handle request for re-analysis with feedback."""
    feedback_data = {
        "request_type": "reanalysis",
        "timestamp": datetime.now().isoformat(),
        "iteration": self.current_iteration + 1,
        "diagnoses_to_reconsider": [
            row.get_annotation()
            for row in self.review_rows
            if not row.correct_checkbox.value
        ],
        "clinician_guidance": [
            row.comments_textarea.value
            for row in self.review_rows
            if row.comments_textarea.value.strip()
        ],
    }

    # Save for pipeline to pick up
    feedback_file = self.annotations_dir / "reanalysis_request.json"
    with open(feedback_file, 'w') as f:
        json.dump(feedback_data, f, indent=2)
```

### Guidance Integration

On reanalysis, the Structuring agent receives clinician guidance:

```python
# code/agents/structuring_agent.py
if reanalysis_request:
    prompt += f"""

## Clinician Feedback (Iteration {iteration})

The clinician has reviewed your previous analysis and provided guidance:

{format_clinician_guidance(reanalysis_request)}

Please reconsider your diagnoses based on this feedback.
"""
```

## Feedback Data Schema

### Annotation Record

```json
{
  "diagnosis_name": "Paramyotonia Congenita",
  "original_confidence": 0.72,
  "adjusted_confidence": 0.30,
  "is_correct": false,
  "corrections": {
    "field": "clinical_significance",
    "reason": "Symptoms don't worsen with cold exposure"
  },
  "notes": "Should be lower priority. Consider Myotonia Congenita instead.",
  "timestamp": "2025-11-29T10:30:00Z",
  "reviewer_id": "dr_smith"
}
```

### Aggregated Feedback

```json
{
  "run_id": "demo_run_001",
  "patient_id_hash": "a3f8c9d2e1b4...",
  "total_diagnoses": 5,
  "correct_count": 2,
  "accuracy_rate": 0.40,
  "confidence_adjustments": {
    "count": 3,
    "mean_delta": -0.15,
    "max_increase": 0.05,
    "max_decrease": -0.42
  },
  "reanalysis_iterations": 2,
  "feedback_quality_score": 0.85
}
```

## Arena Bundle Export

The UI enables export of feedback bundles for federated learning:

```python
# Export button handler
def _on_export_clicked(self, button):
    bundle = self.collector.export_arena_bundle(
        institution_id="mayo_clinic",
        anonymize=True,
        include_pipeline_outputs=True
    )
    self.status_message.value = f"Exported to: {bundle}"
```

### Bundle Contents

```
arena_bundle_demo_run_001.zip
├── manifest.json           # Bundle metadata
├── feedback.json           # Aggregated feedback
├── patient_context.json    # De-identified phenotypes
├── diagnostic_table.json   # AI-generated diagnoses
├── tool_results.json       # Bio-tool annotations
└── gradient_summary.json   # Training gradient weights
```

## Integration with Notebooks

### Live Pipeline Workshop

The review interface is demonstrated in the workshop notebook:

```python
# notebooks/Live_Pipeline_Workshop.ipynb - Cell 7

from code.review_interface import create_multiturn_review_interface

# Create interface with reanalysis callback
def on_reanalysis(request):
    print(f"Re-analysis requested: iteration {request.iteration}")
    print(f"Focus genes: {request.focus_genes}")

review = create_multiturn_review_interface(
    outputs_dir=demo_outputs,
    reanalysis_callback=on_reanalysis
)

display(review.get_widget())
```

### RLHF Demo Notebook

A dedicated notebook showcases the full feedback loop:

```python
# notebooks/RLHF_Demo.ipynb

# Load previous run
review = DiagnosisReviewTable(run_dir="outputs/demo_run")

# Display for annotation
display(review.widget)

# After annotation, export for training
collector = review.get_feedback_collector()
training_data = collector.export_for_training(
    format="jsonl",
    output_path="training/rlhf_data.jsonl"
)
```

## Code Location

- **Main Interface**: [code/review_interface.py](../../code/review_interface.py)
- **Feedback Collection**: [code/arena/feedback_collector.py](../../code/arena/feedback_collector.py)
- **Demo Notebook**: [notebooks/RLHF_Demo.ipynb](../../notebooks/RLHF_Demo.ipynb)
- **Workshop Notebook**: [notebooks/Live_Pipeline_Workshop.ipynb](../../notebooks/Live_Pipeline_Workshop.ipynb)

## Future Enhancements

1. **Voice annotation**: Record verbal critiques for richer feedback
2. **Comparative mode**: Side-by-side comparison of iterations
3. **Real-time collaboration**: Multiple reviewers on same case
4. **Feedback quality metrics**: Track annotation consistency

## References

- [43] arXiv - Alignment Paradox in Medical AI
- [45] Automate Clinic - Doctor-in-the-Loop/RLHF
