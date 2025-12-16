# Makefile for UH2025Agent Topology
# Provides automated testing, validation, and notebook management

.PHONY: help test test-fast test-slow test-parity test-notebooks test-elyra \
        sync-notebooks validate lint clean install

# Default target
help:
	@echo "UH2025Agent Topology - Available Targets:"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests (excluding slow)"
	@echo "  test-fast      - Run fast validation tests only"
	@echo "  test-slow      - Run slow notebook execution tests"
	@echo "  test-parity    - Run execution parity tests"
	@echo "  test-notebooks - Run all notebook tests"
	@echo "  test-elyra     - Run Elyra integration tests"
	@echo ""
	@echo "Notebooks:"
	@echo "  sync-notebooks - Sync all notebooks with Jupytext"
	@echo "  validate       - Validate pipeline and notebooks"
	@echo ""
	@echo "Development:"
	@echo "  lint           - Run linting checks"
	@echo "  clean          - Remove test outputs and cache"
	@echo "  install        - Install development dependencies"

# =============================================================================
# Testing Targets
# =============================================================================

# Note: Tests run from project root to avoid import conflicts with code/ directory
# This is a known issue with Python's code module shadowing

# Project root directory (4 levels up from topology)
PROJECT_ROOT := $(shell cd ../../../.. && pwd)
TOPOLOGY_PATH := lab/obs/topologies/UH2025Agent

# Python configuration - can be overridden with PYTHON=path/to/python make test
PYTHON ?= python
PYTEST := $(PYTHON) -m pytest

# Run all tests (excluding slow)
test:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/ -v -m "not slow"

# Run fast validation tests only
test-fast:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/ -v -k "validate or structure or metadata" -m "not slow"

# Run slow notebook execution tests
test-slow:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/ -v -m "slow" --run-slow

# Run execution parity tests
test-parity:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/test_execution_parity.py -v --run-slow

# Run all notebook tests
test-notebooks:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/ -v -m "notebook" --run-slow

# Run Elyra integration tests
test-elyra:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/test_elyra_integration.py -v

# Run Elyra tests including slow ones
test-elyra-full:
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/test_elyra_integration.py -v --run-slow

# =============================================================================
# Notebook Management
# =============================================================================

# Paths to module directories
MODULES_DIR := ../../../modules
NOTEBOOKS_DIR := notebooks

# Sync all notebooks with Jupytext
sync-notebooks:
	@echo "Syncing notebooks in modules..."
	@find $(MODULES_DIR)/AlphaMissense/notebooks -name "*.ipynb" -exec jupytext --sync {} \; 2>/dev/null || true
	@find $(MODULES_DIR)/AlphaGenome/notebooks -name "*.ipynb" -exec jupytext --sync {} \; 2>/dev/null || true
	@find $(MODULES_DIR)/RareLLM/notebooks -name "*.ipynb" -exec jupytext --sync {} \; 2>/dev/null || true
	@echo "Syncing notebooks in topology..."
	@find $(NOTEBOOKS_DIR) -name "*.ipynb" -exec jupytext --sync {} \; 2>/dev/null || true
	@echo "Done."

# =============================================================================
# Validation
# =============================================================================

# Validate pipeline and run validation tests
validate:
	@echo "Validating Elyra pipeline..."
	cd $(PROJECT_ROOT)/$(TOPOLOGY_PATH) && $(PYTHON) -c "import sys; sys.path.insert(0, 'code'); from elyra.runner import ElyraRunner; r = ElyraRunner('elyra/UH2025Agent.pipeline'); v, e = r.validate(); print('Valid!' if v else f'Errors: {e}'); sys.exit(0 if v else 1)"
	@echo ""
	@echo "Running validation tests..."
	cd $(PROJECT_ROOT) && PYTHONDONTWRITEBYTECODE=1 $(PYTEST) $(TOPOLOGY_PATH)/tests/test_elyra_integration.py -k "validate" -v

# Validate pipeline only (no tests)
validate-pipeline:
	cd $(PROJECT_ROOT)/$(TOPOLOGY_PATH) && $(PYTHON) -c "import sys; sys.path.insert(0, 'code'); from elyra.runner import ElyraRunner; r = ElyraRunner('elyra/UH2025Agent.pipeline'); v, e = r.validate(); print('Valid!' if v else f'Errors: {e}'); sys.exit(0 if v else 1)"

# =============================================================================
# Development
# =============================================================================

# Run linting checks
lint:
	@echo "Checking code style with ruff..."
	-ruff check code/ tests/ 2>/dev/null || echo "ruff not installed, skipping"
	@echo ""
	@echo "Running type checks with mypy..."
	-mypy code/ --ignore-missing-imports 2>/dev/null || echo "mypy not installed, skipping"

# Install development dependencies
install:
	pip install pytest papermill jupytext ruff mypy pre-commit

# =============================================================================
# Cleanup
# =============================================================================

# Remove test outputs and cache
clean:
	rm -rf .pytest_cache/
	rm -rf tests/__pycache__/
	rm -rf code/__pycache__/
	rm -rf code/**/__pycache__/
	rm -rf /tmp/pytest_output_*
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned up test outputs and cache."

# Deep clean including all generated files
clean-all: clean
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".ipynb_checkpoints" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Deep clean complete."
