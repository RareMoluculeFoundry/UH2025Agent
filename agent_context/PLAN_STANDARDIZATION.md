# Standardization Context: UH2025Agent (DeLab v2.0 Compliance)

## Context
We are finalizing the `UH2025Agent` topology standardization to align with the "FAIR CDS Standard" (DeLab v2.0). The repository has been partially updated, but we need to verify strict compliance with the file structure and documentation standards.

## Execution Plan

### 1. Directory Structure Verification
- **Objective**: Ensure the directory `topology_code/` has been renamed to `code/`.
- **Action**:
    - Check if `code/` exists.
    - Check if `topology_code/` still exists.
    - If `topology_code/` exists, rename it to `code/`.
    - If both exist, merge contents into `code/` and remove `topology_code/`.

### 2. Path Reference Updates
- **Objective**: Ensure no files reference the old `topology_code/` path.
- **Action**:
    - Grep for `topology_code` in `topology.yaml`, `README.md`, `elyra/*.pipeline`, and python scripts.
    - Replace all instances of `topology_code` with `code`.

### 3. Documentation Compliance
- **Objective**: Ensure mandatory documentation files exist and are correct.
- **Action**:
    - **AGENTS.md**: Verify this file exists in the root. If not, create it using the template structure (Overview, Execution Instructions, Workflow Steps).
    - **TOPOLOGY.md**: Verify this file exists in the root. If not, create it with FAIR metadata extracted from `RFC.md`.
    - **README.md**: Ensure the "Directory Structure" section lists `code/` instead of `topology_code/`. Ensure links to `AGENTS.md` and `TOPOLOGY.md` are present.

### 4. Topology Definition Check
- **Objective**: Verify `topology.yaml` points to the correct module paths.
- **Action**:
    - Review `topology.yaml` -> `modules` section.
    - Confirm local modules point to `code/` (if applicable) or external modules point to `../../modules/`.

## Success Criteria
1. Root directory contains `code/`, `AGENTS.md`, `TOPOLOGY.md`.
2. Root directory DOES NOT contain `topology_code/`.
3. `topology.yaml` is valid and references `code/` paths where appropriate.
4. `README.md` accurately reflects the new structure.

