# Next Session Context: UH2025 Agent

**Last Updated:** 2025-12-02
**Current State:** Phase 1 (Reorganization) Complete. Phase 2 (Build Out) Ready to Start.

## Summary
The UH2025 Agent repository has been successfully reorganized. We have moved UI code to `code/ui/`, implemented live API calls for `SpliceAI` and `gnomAD`, and consolidated documentation.

## Immediate Action Items
The next session should follow the **DeLab home** alpha readiness workflow and gates:

1. **Read**: `.agentic/prompts/UH2025_ALPHA_READINESS_AGENT_PROMPT.md`
2. **Run workflow**: `.agentic/workflows/uh2025_alpha_readiness/README.md`
3. **Track progress**: `.agentic/plans/active/UH2025_GITHUB_ALPHA_READINESS_PLAN.md`

Then continue with **Phase 2: Environment & Validation** of the topology-local build plan: [UH2025 Build Plan](../.agentic/plans/active/UH2025_BUILD_PLAN.md).

1.  **Fix Dependencies**: The E2E tests failed because `langgraph` and `papermill` were missing from the environment, though they are in `requirements.txt`.
2.  **Run Tests**: Once dependencies are fixed, run `python tests/test_patientx_e2e.py --use-stub` to verify the pipeline.
3.  **Continue Build**: Proceed with Federation and UI tasks in the Build Plan.

## Key Resources
*   **Build Plan**: `lab/obs/topologies/UH2025Agent/.agentic/plans/active/UH2025_BUILD_PLAN.md`
*   **Research Context**: `lab/obs/topologies/UH2025Agent/agent_context/RESEARCH_CONTEXT.md`
*   **Codebase**: `lab/obs/topologies/UH2025Agent/code/` (Imports have been updated to `code.ui`, `code.biotools`, etc.)
*   **GitHub Alpha Readiness (DeLab home)**:
    - `.agentic/plans/active/UH2025_GITHUB_ALPHA_READINESS_PLAN.md`
    - `.agentic/workflows/uh2025_alpha_readiness/README.md`
    - `.agentic/prompts/UH2025_ALPHA_READINESS_AGENT_PROMPT.md`

