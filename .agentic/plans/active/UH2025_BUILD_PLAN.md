# UH2025 Agent Build Plan

**Status:** Active
**Phase:** 2 - Implementation & Validation
**Previous Phase:** [Improvement Plan](UH2025_IMPROVEMENT_PLAN.md) (Completed)

This plan outlines the roadmap for completing the UH2025 Agent build-out, following the initial reorganization and de-stubbing phase.

## 1. Environment & Validation
- [ ] **Dependency Fixes**: Install missing dependencies (`langgraph`, `papermill`, `requests`) in the environment.
- [ ] **E2E Testing**: Fix and pass `tests/test_patientx_e2e.py` and `tests/test_module_e2e.py`.
- [ ] **API Configuration**: Verify `OMIM_API_KEY` and `NCBI_API_KEY` integration for live tools.

## 2. Federation & Privacy
- [ ] **Federation Protocol**: Implement the "Arena Bundle" export format in `code/arena/`.
- [ ] **Privacy Controls**: Implement Differential Privacy (DP) mechanisms for gradient updates (as per `RESEARCH_CONTEXT.md`).
- [ ] **L3 Deployment**: Create Kubeflow pipeline definition matching the Elyra pipeline.

## 3. UI/UX Refinement
- [ ] **Review Interface**: enhance `DiagnosisReviewTable` to support multi-turn re-analysis.
- [ ] **Configurator**: Add validation logic to `TopologyConfigurator` to prevent invalid parameter combinations.
- [ ] **Output Viewer**: Add visualization for `AlphaGenome` regulatory tracks.

## 4. Documentation & Research Alignment
- [ ] **Sync Context**: Ensure `agent_context/RESEARCH_CONTEXT.md` stays updated with any architectural changes.
- [ ] **Paper Draft**: Generate initial draft of the methodology section based on the codebase.

## Execution Instructions
To resume work on this plan:
1.  Read `lab/obs/topologies/UH2025Agent/agent_context/RESEARCH_CONTEXT.md` for scientific grounding.
2.  Check `lab/obs/topologies/UH2025Agent/requirements.txt` against the active environment.
3.  Execute tests: `pytest tests/test_patientx_e2e.py --use-stub`.

