# Swarm Learning: Decentralized Model Training

## Concept

Swarm Learning removes the central aggregator from federated learning, using blockchain technology for peer-to-peer model synchronization.

## Architecture

```
Hospital A ←→ Hospital B
    ↑↓           ↑↓
Hospital C ←→ Hospital D
```

No central server. Each node trains locally and shares gradients via secure peer-to-peer protocol.

## Advantages

| Aspect | Federated Learning | Swarm Learning |
|:-------|:-------------------|:---------------|
| Central Point | Yes (aggregator) | No |
| Single Entity Control | Risk of bias | Democratic |
| Fault Tolerance | Server dependency | Resilient |
| Regulatory Compliance | May require trust | Trustless |

## Privacy Mechanisms

1. **Differential Privacy**: Add calibrated noise to gradients
2. **Secure Aggregation**: Multi-party computation for weight averaging
3. **Homomorphic Encryption**: Compute on encrypted gradients
4. **Gradient Compression**: Reduce information leakage

## Implementation in Rare Arena Network

The UH2025Agent `export_arena_bundle()` method creates privacy-preserving bundles:

```python
from code.arena.feedback_collector import FeedbackCollector

collector = FeedbackCollector(run_dir)
bundle_path = collector.export_arena_bundle(
    output_path="arena_bundle.json",
    include_patient_context=True,  # De-identified
    include_tool_results=True
)
```

Bundle contents:
- De-identified patient context (PHI removed)
- Diagnostic hypotheses and tool plans
- Expert feedback annotations
- Hashed patient ID (no reversibility)
