# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: tags,-ExecuteTime
#     formats: ipynb,py:percent
#     notebook_metadata_filter: kernelspec,jupytext
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.18.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # RLHF Demonstration: End-to-End Feedback Collection Workflow
#
# **Purpose**: Demonstrate the complete Human-in-the-Loop (HITL) feedback workflow for the UH2025-CDS-Agent pipeline.
#
# This notebook shows:
# 1. **Loading demo data**: Synthetic Dravet syndrome patient case
# 2. **Reviewing pipeline outputs**: Each of the 4 agent stages
# 3. **Collecting expert feedback**: Using DiagnosisReviewTable and FeedbackCollector
# 4. **Aggregating feedback**: Combining all annotations
# 5. **Exporting for training**: Generating RLHF training data
#
# ---
#
# ## The RLHF Vision
#
# The Diagnostic Arena enables a "citizen science" model where clinicians and geneticists worldwide contribute to improving AI diagnostic capabilities:
#
# ```
# Synthetic Patient → Pipeline → Expert Review → Feedback → Training Data → Improved Models
# ```
#
# This demonstration uses **mock pipeline outputs** that simulate what the fully-functional agents will produce.

# %% [markdown]
# ## Setup

# %%
# Standard library
import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for local imports
sys.path.insert(0, str(Path.cwd().parent))

# Display imports
from IPython.display import display, HTML, Markdown

# Widgets (for interactive review)
import ipywidgets as widgets

# %% [markdown]
# ### Load UH2025Agent Code

# %%
# UH2025Agent components
from code.ui.review_interface import DiagnosisReviewTable
from code.ui.output_viewer import OutputBrowser
from code.arena import FeedbackCollector, FeedbackType, FeedbackSource, create_collector

print("✅ UH2025Agent components loaded successfully")

# %% [markdown]
# ## 1. Patient Case Overview
#
# We'll use a **synthetic Dravet syndrome case** for this demonstration. This patient presents with classic features that should lead to a definitive diagnosis.

# %%
# Define paths
BASE_DIR = Path.cwd().parent
DATA_DIR = BASE_DIR / "Data" / "SyntheticDemo"
OUTPUTS_DIR = BASE_DIR / "outputs" / "demo_run"

print(f"📁 Data Directory: {DATA_DIR}")
print(f"📁 Outputs Directory: {OUTPUTS_DIR}")

# %%
# Load patient clinical summary
clinical_file = DATA_DIR / "patient_clinical.md"
with open(clinical_file) as f:
    clinical_summary = f.read()

display(HTML(f'''
<div style="background: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 4px solid #1976d2;">
    <h3 style="color: #1565c0; margin-top: 0;">📋 Patient Clinical Summary</h3>
    <p style="color: #424242;">File: <code>{clinical_file.name}</code></p>
</div>
'''))

# Show first part of clinical summary
display(Markdown(clinical_summary[:2500] + "\n\n*... (truncated for display)*"))

# %%
# Load genomic data
genomic_file = DATA_DIR / "patient_genomic.json"
with open(genomic_file) as f:
    genomic_data = json.load(f)

display(HTML(f'''
<div style="background: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 4px solid #2e7d32;">
    <h3 style="color: #1b5e20; margin-top: 0;">🧬 Genomic Data Summary</h3>
    <p style="color: #424242;"><strong>Patient ID:</strong> {genomic_data['patient_id']}</p>
    <p style="color: #424242;"><strong>Sequencing Method:</strong> {genomic_data['sequencing_method']}</p>
    <p style="color: #424242;"><strong>Variants of Interest:</strong> {len(genomic_data['variants'])}</p>
</div>
'''))

# Display variants table
variants_html = '''
<table style="width: 100%; border-collapse: collapse; margin-top: 12px;">
<tr style="background: #f5f5f5;">
    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Gene</th>
    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Variant</th>
    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Type</th>
    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Inheritance</th>
    <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Classification</th>
</tr>
'''

for v in genomic_data['variants']:
    classification = v.get('clinvar', {}).get('clinical_significance', 'Unknown')
    color = {
        'Pathogenic': '#c62828',
        'Uncertain significance': '#f57c00',
        'Likely Benign': '#2e7d32'
    }.get(classification, '#424242')

    variants_html += f'''
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>{v['gene']}</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd;">{v['variant']}</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{v['type']}</td>
        <td style="padding: 8px; border: 1px solid #ddd;">{v['inheritance']}</td>
        <td style="padding: 8px; border: 1px solid #ddd; color: {color};"><strong>{classification}</strong></td>
    </tr>
    '''

variants_html += '</table>'
display(HTML(variants_html))

# %% [markdown]
# ## 2. Pipeline Outputs Review
#
# The pipeline produces outputs at 4 stages. Let's examine each one.

# %% [markdown]
# ### Stage 1: Ingestion Agent Output
#
# The Ingestion Agent normalizes clinical and genomic data into a structured format.

# %%
# Load ingestion output
ingestion_file = OUTPUTS_DIR / "01_ingestion" / "patient_context.json"
with open(ingestion_file) as f:
    ingestion_output = json.load(f)

display(HTML(f'''
<div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #e65100;">
    <h3 style="color: #e65100; margin-top: 0;">🔄 Stage 1: Ingestion Output</h3>
    <p style="color: #424242;"><strong>Agent:</strong> {ingestion_output['agent']} ({ingestion_output.get('model', 'llama-3.2-3b')})</p>
    <p style="color: #424242;"><strong>Timestamp:</strong> {ingestion_output['processing_timestamp']}</p>
    <p style="color: #424242;"><strong>HPO Terms Extracted:</strong> {len(ingestion_output['patient_context']['hpo_terms'])}</p>
    <p style="color: #424242;"><strong>Variants Identified:</strong> {len(ingestion_output['variants_summary']['variants_of_interest'])}</p>
</div>
'''))

# Show extracted HPO terms
print("\n📋 Extracted HPO Terms:")
for hpo in ingestion_output['patient_context']['hpo_terms'][:5]:
    print(f"  • {hpo['id']}: {hpo['label']}")
print(f"  ... and {len(ingestion_output['patient_context']['hpo_terms']) - 5} more")

# %% [markdown]
# ### Stage 2: Structuring Agent Output
#
# The Structuring Agent generates the differential diagnosis and tool execution plan.

# %%
# Load structuring output
structuring_file = OUTPUTS_DIR / "02_structuring" / "diagnostic_table.json"
with open(structuring_file) as f:
    structuring_output = json.load(f)

display(HTML(f'''
<div style="background: #e8eaf6; padding: 20px; border-radius: 8px; border-left: 4px solid #3f51b5;">
    <h3 style="color: #283593; margin-top: 0;">🧠 Stage 2: Structuring Output</h3>
    <p style="color: #424242;"><strong>Agent:</strong> {structuring_output['agent']} ({structuring_output.get('model', 'qwen2.5-14b')})</p>
    <p style="color: #424242;"><strong>Differential Diagnoses:</strong> {len(structuring_output['diagnostic_table']['differential_diagnoses'])}</p>
    <p style="color: #424242;"><strong>Variants Ranked:</strong> {len(structuring_output['variants_table']['variants'])}</p>
    <p style="color: #424242;"><strong>Tools Planned:</strong> {len(structuring_output['tool_usage_plan']['planned_tools'])}</p>
</div>
'''))

# Show differential diagnosis table
diff_dx = structuring_output['diagnostic_table']['differential_diagnoses']
print("\n📊 Differential Diagnosis:")
for dx in diff_dx:
    confidence_bar = "█" * int(dx['confidence'] * 20) + "░" * (20 - int(dx['confidence'] * 20))
    print(f"  {dx['rank']}. {dx['diagnosis']}")
    print(f"     Confidence: [{confidence_bar}] {dx['confidence']:.0%}")
    print(f"     Gene: {dx.get('gene', 'N/A')}")
    print()

# %% [markdown]
# ### Stage 3: Executor Agent Output
#
# The Executor Agent runs bio-tools and collects evidence.

# %%
# Load executor output
executor_file = OUTPUTS_DIR / "03_executor" / "tool_results.json"
with open(executor_file) as f:
    executor_output = json.load(f)

display(HTML(f'''
<div style="background: #fce4ec; padding: 20px; border-radius: 8px; border-left: 4px solid #c2185b;">
    <h3 style="color: #880e4f; margin-top: 0;">⚙️ Stage 3: Executor Output</h3>
    <p style="color: #424242;"><strong>Agent:</strong> {executor_output['agent']} (Python)</p>
    <p style="color: #424242;"><strong>Tools Executed:</strong> {executor_output['execution_summary']['total_tools_executed']}</p>
    <p style="color: #424242;"><strong>Total Time:</strong> {executor_output['execution_summary']['total_execution_time_ms']} ms</p>
    <p style="color: #424242;"><strong>Successful Queries:</strong> {executor_output['execution_summary']['successful_queries']}</p>
</div>
'''))

# Show tool results summary
print("\n🔬 Tool Results Summary:")
for tool, status in executor_output['execution_summary']['tools_status'].items():
    emoji = "✅" if status == "success" else "❌"
    print(f"  {emoji} {tool.upper()}: {status}")

# Show ClinVar results for primary variant
clinvar_results = executor_output['tool_results']['clinvar']['results']
scn1a_result = next((r for r in clinvar_results if 'SCN1A' in r['query']), None)
if scn1a_result:
    print(f"\n🏥 ClinVar Result for SCN1A variant:")
    print(f"   Classification: {scn1a_result['clinical_significance']}")
    print(f"   Review Status: {'⭐' * scn1a_result['stars']} ({scn1a_result['stars']} stars)")
    print(f"   Submitters: {scn1a_result['submitters']}")

# %% [markdown]
# ### Stage 4: Synthesis Agent Output
#
# The Synthesis Agent generates the final clinical report.

# %%
# Load synthesis output
synthesis_file = OUTPUTS_DIR / "04_synthesis" / "clinical_report.json"
with open(synthesis_file) as f:
    synthesis_output = json.load(f)

display(HTML(f'''
<div style="background: #e0f7fa; padding: 20px; border-radius: 8px; border-left: 4px solid #00838f;">
    <h3 style="color: #006064; margin-top: 0;">📝 Stage 4: Synthesis Output</h3>
    <p style="color: #424242;"><strong>Agent:</strong> {synthesis_output['agent']} ({synthesis_output.get('model', 'qwen2.5-32b')})</p>
    <p style="color: #424242;"><strong>Report Sections:</strong> {len(synthesis_output['report_sections'])}</p>
    <p style="color: #424242;"><strong>Overall Confidence:</strong> {synthesis_output['report_metadata']['confidence']:.0%}</p>
    <p style="color: #424242;"><strong>HITL Status:</strong> {synthesis_output['report_metadata']['status']}</p>
</div>
'''))

# Show executive summary
exec_summary = synthesis_output['executive_summary']
display(HTML(f'''
<div style="background: #f5f5f5; padding: 16px; border-radius: 4px; margin-top: 12px;">
    <h4 style="margin-top: 0;">Executive Summary</h4>
    <p><strong>Primary Finding:</strong> {exec_summary['primary_finding']}</p>
    <p><strong>Variant:</strong> {exec_summary['variant']}</p>
    <p><strong>Inheritance:</strong> {exec_summary['inheritance']}</p>
    <p><strong>Diagnostic Certainty:</strong> <span style="color: #2e7d32; font-weight: bold;">{exec_summary['diagnostic_certainty'].upper()}</span></p>
</div>
'''))

# %% [markdown]
# ## 3. Expert Review Interface
#
# Now we'll use the **DiagnosisReviewTable** to collect expert feedback on the differential diagnosis.
#
# ### Instructions for Reviewers:
# 1. ✅ **Check/Uncheck** each diagnosis as correct or incorrect
# 2. 🎚️ **Adjust confidence** if you disagree with the AI's assessment
# 3. 📝 **Add clinical notes** explaining your reasoning
# 4. 💾 **Save annotations** when done

# %%
# Create the review interface with the structuring output
diagnoses = structuring_output['diagnostic_table']['differential_diagnoses']

# Convert to the format expected by DiagnosisReviewTable
diagnoses_for_review = []
for dx in diagnoses:
    diagnoses_for_review.append({
        'diagnosis': dx['diagnosis'],
        'confidence': dx['confidence'],
        'rank': dx['rank'],
        'gene': dx.get('gene', 'N/A'),
        'supporting_evidence': dx.get('supporting_evidence', []),
        'contradicting_evidence': dx.get('contradicting_evidence', []),
    })

# Create review table (note: using in-memory mode for demo)
review_table = DiagnosisReviewTable(diagnoses=diagnoses_for_review)

display(HTML('''
<div style="background: #fff8e1; padding: 16px; border-radius: 8px; border-left: 4px solid #ffc107; margin-bottom: 16px;">
    <h3 style="color: #f57f17; margin-top: 0;">👨‍⚕️ Expert Review Required</h3>
    <p style="color: #424242;">
        As a clinical expert, please review each diagnosis below. Your feedback will be used to improve the AI model.
    </p>
</div>
'''))

# Display the review interface
display(review_table.get_widget())

# %% [markdown]
# ## 4. Feedback Collection
#
# After reviewing the diagnoses, we'll use the **FeedbackCollector** to aggregate all annotations.

# %%
# Initialize the FeedbackCollector
collector = create_collector(
    run_dir=OUTPUTS_DIR,
    reviewer_id="demo_reviewer"
)

display(HTML(f'''
<div style="background: #f3e5f5; padding: 20px; border-radius: 8px; border-left: 4px solid #7b1fa2;">
    <h3 style="color: #4a148c; margin-top: 0;">📊 Feedback Collector Initialized</h3>
    <p style="color: #424242;"><strong>Run ID:</strong> {collector.run_id}</p>
    <p style="color: #424242;"><strong>Patient ID:</strong> {collector.patient_id}</p>
    <p style="color: #424242;"><strong>Reviewer ID:</strong> {collector.reviewer_id}</p>
</div>
'''))

# %%
# Simulate collecting feedback from the review interface
# In a real scenario, this would come from the widget interaction

# Get current annotations from review table (even without manual changes)
for dx in diagnoses_for_review:
    # Add as feedback (simulating expert review)
    # In this demo, we mark the primary diagnosis as correct
    is_correct = dx['rank'] == 1  # Top diagnosis is correct

    collector.add_diagnosis_correction(
        disease_name=dx['diagnosis'],
        is_correct=is_correct,
        original_confidence=dx['confidence'],
        adjusted_confidence=dx['confidence'] if is_correct else dx['confidence'] * 0.5,
        notes=f"Demo annotation for {dx['diagnosis']}" if not is_correct else "Primary diagnosis confirmed"
    )

print(f"✅ Added {len(collector.feedback_items)} feedback items")

# %%
# View feedback statistics
stats = collector.get_statistics()

display(HTML(f'''
<div style="background: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 4px solid #2e7d32;">
    <h3 style="color: #1b5e20; margin-top: 0;">📈 Feedback Statistics</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr>
            <td style="padding: 8px;"><strong>Total Items:</strong></td>
            <td style="padding: 8px;">{stats['total_items']}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 8px;"><strong>Correct Items:</strong></td>
            <td style="padding: 8px;">{stats['total_correct']}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Incorrect Items:</strong></td>
            <td style="padding: 8px;">{stats['total_incorrect']}</td>
        </tr>
        <tr style="background: #f5f5f5;">
            <td style="padding: 8px;"><strong>Accuracy Rate:</strong></td>
            <td style="padding: 8px;">{stats['accuracy_rate']:.1%}</td>
        </tr>
        <tr>
            <td style="padding: 8px;"><strong>Items with Notes:</strong></td>
            <td style="padding: 8px;">{stats['items_with_notes']}</td>
        </tr>
    </table>
</div>
'''))

# %% [markdown]
# ## 5. Aggregate and Export
#
# Finally, we aggregate all feedback and export it for training.

# %%
# Create feedback directory
feedback_dir = OUTPUTS_DIR / "feedback"
feedback_dir.mkdir(parents=True, exist_ok=True)

# Save aggregated feedback
aggregated_file = collector.save(feedback_dir / "aggregated_feedback.json")
print(f"💾 Saved aggregated feedback to: {aggregated_file}")

# Export for training
training_file = collector.export_for_training(
    feedback_dir / "training_data.jsonl",
    format="jsonl",
    include_correct=True
)
print(f"📤 Exported training data to: {training_file}")

# %%
# Show the aggregated feedback structure
with open(aggregated_file) as f:
    aggregated = json.load(f)

display(HTML('''
<div style="background: #e1f5fe; padding: 20px; border-radius: 8px; border-left: 4px solid #0288d1;">
    <h3 style="color: #01579b; margin-top: 0;">📦 Aggregated Feedback Structure</h3>
</div>
'''))

# Pretty print (truncated)
print(json.dumps({
    "run_id": aggregated["run_id"],
    "patient_id": aggregated["patient_id"],
    "timestamp": aggregated["timestamp"],
    "summary": aggregated["summary"],
    "feedback": {
        "structuring": f"[{len(aggregated['feedback']['structuring'])} items]",
        "ingestion": f"[{len(aggregated['feedback']['ingestion'])} items]",
        "executor": f"[{len(aggregated['feedback']['executor'])} items]",
        "synthesis": f"[{len(aggregated['feedback']['synthesis'])} items]",
    }
}, indent=2))

# %%
# Show sample training data record
with open(training_file) as f:
    first_record = json.loads(f.readline())

display(HTML('''
<div style="background: #fff3e0; padding: 20px; border-radius: 8px; border-left: 4px solid #e65100;">
    <h3 style="color: #e65100; margin-top: 0;">📄 Sample Training Record</h3>
    <p style="color: #5f6368;">This is what one record in the JSONL training file looks like:</p>
</div>
'''))

print(json.dumps(first_record, indent=2))

# %% [markdown]
# ## 6. Ground Truth Comparison
#
# Let's compare the pipeline output against the ground truth to evaluate performance.

# %%
# Load ground truth
ground_truth_file = DATA_DIR / "ground_truth.json"
with open(ground_truth_file) as f:
    ground_truth = json.load(f)

display(HTML(f'''
<div style="background: #efebe9; padding: 20px; border-radius: 8px; border-left: 4px solid #795548;">
    <h3 style="color: #4e342e; margin-top: 0;">🎯 Ground Truth Comparison</h3>
</div>
'''))

# Compare diagnoses
gt_primary = ground_truth['ground_truth_diagnosis']['primary_diagnosis']
pipeline_primary = structuring_output['diagnostic_table']['diagnostic_summary']['primary_diagnosis']

match_emoji = "✅" if gt_primary['condition'] == pipeline_primary else "❌"
print(f"{match_emoji} Primary Diagnosis Match")
print(f"   Ground Truth: {gt_primary['condition']}")
print(f"   Pipeline:     {pipeline_primary}")
print()

# Compare variant classification
gt_variant = ground_truth['expected_variant_classifications']['SCN1A_c.4933C>T']
pipeline_evidence = executor_output['evidence_synthesis']['SCN1A_c.4933C>T']

match_emoji = "✅" if gt_variant['expected_classification'] == pipeline_evidence['final_classification'] else "❌"
print(f"{match_emoji} Variant Classification Match")
print(f"   Ground Truth: {gt_variant['expected_classification']}")
print(f"   Pipeline:     {pipeline_evidence['final_classification']}")

# %% [markdown]
# ## Summary
#
# This demonstration showed the complete RLHF workflow:
#
# 1. ✅ **Loaded** synthetic patient data (Dravet syndrome case)
# 2. ✅ **Reviewed** all 4 pipeline stage outputs
# 3. ✅ **Collected** expert feedback via DiagnosisReviewTable
# 4. ✅ **Aggregated** feedback using FeedbackCollector
# 5. ✅ **Exported** training data in JSONL format
# 6. ✅ **Compared** against ground truth
#
# ### Next Steps
#
# - **For Contributors**: Use this workflow to review synthetic cases and provide feedback
# - **For Developers**: The exported JSONL can be used for DPO or SFT training
# - **For Clinicians**: The DiagnosisReviewTable captures your expert knowledge

# %%
display(HTML('''
<div style="background: linear-gradient(135deg, #1976d2, #7b1fa2); color: white; padding: 30px; border-radius: 12px; text-align: center; margin-top: 20px;">
    <h2 style="margin-top: 0;">🎉 RLHF Demo Complete!</h2>
    <p style="font-size: 1.1em;">
        Your feedback has been collected and is ready for model training.
    </p>
    <p style="opacity: 0.9;">
        Output files are in: <code style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px;">outputs/demo_run/feedback/</code>
    </p>
</div>
'''))
