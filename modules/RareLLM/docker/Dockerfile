# RareLLM: Privacy-First Rare Disease Diagnostic LLM
#
# HIPAA-Compliant Container for Local LLM Inference
# NO CLOUD APIs - All inference runs locally via llama-cpp-python
#
# Build: docker build -t rarellm:latest -f docker/Dockerfile .
# Run:   docker run -v $(pwd)/models:/app/models rarellm:latest

# =============================================================================
# Stage 1: Base Image with Python and Build Tools
# =============================================================================
FROM python:3.11-slim-bookworm AS base

# System dependencies for llama-cpp-python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# =============================================================================
# Stage 2: Python Dependencies
# =============================================================================
FROM base AS deps

# Install Python dependencies
COPY requirements.txt .

# Install llama-cpp-python with CPU support (no GPU in container by default)
# For CUDA: CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python
# For ROCm: CMAKE_ARGS="-DLLAMA_HIPBLAS=on" pip install llama-cpp-python
RUN pip install --no-cache-dir \
    llama-cpp-python \
    langchain>=0.3.0 \
    langchain-community>=0.3.0 \
    langgraph>=0.2.0 \
    pydantic>=2.0.0 \
    PyYAML>=6.0 \
    httpx>=0.25.0 \
    duckdb>=0.9.0 \
    zarr>=2.16.0 \
    papermill>=2.4.0 \
    jupyter>=1.0.0 \
    jupytext>=1.15.0

# =============================================================================
# Stage 3: Application
# =============================================================================
FROM deps AS app

# Copy application code
COPY code/ /app/code/
COPY config/ /app/config/
COPY notebooks/ /app/notebooks/

# Create directories for models and outputs
RUN mkdir -p /app/models/base /app/models/lora /app/outputs /app/logs

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV RARELLM_PRIVACY_MODE=true
ENV RARELLM_LOG_DIR=/app/logs

# Privacy enforcement: Only PatientX allowed
ENV RARELLM_ALLOWED_PATIENTS=PatientX

# Model paths (mount volumes at runtime)
ENV RARELLM_MODEL_PATH=/app/models/base/Qwen2.5-32B-Instruct-Q4_K_M.gguf
ENV RARELLM_LORA_PATH=/app/models/lora

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import llama_cpp; print('healthy')" || exit 1

# Default command: Run diagnostic pipeline
CMD ["python", "-m", "code.run_pipeline"]

# =============================================================================
# Stage 4: Development Image (optional)
# =============================================================================
FROM app AS dev

# Additional dev dependencies
RUN pip install --no-cache-dir \
    pytest>=7.0.0 \
    pytest-cov>=4.0.0 \
    black>=23.0.0 \
    ruff>=0.1.0

# Expose JupyterLab port
EXPOSE 8888

# Development command: Start JupyterLab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

# =============================================================================
# Usage Notes
# =============================================================================
#
# Build production image:
#   docker build -t rarellm:latest --target app .
#
# Build development image:
#   docker build -t rarellm:dev --target dev .
#
# Run with model volume:
#   docker run -v /path/to/models:/app/models rarellm:latest
#
# Run interactive pipeline:
#   docker run -it -v /path/to/models:/app/models \
#     -v /path/to/data:/app/data \
#     rarellm:latest python -m code.run_pipeline \
#     --patient-id PatientX \
#     --privacy-mode true
#
# Run JupyterLab (dev mode):
#   docker run -p 8888:8888 -v /path/to/models:/app/models \
#     -v $(pwd)/notebooks:/app/notebooks \
#     rarellm:dev
#
# CUDA Support (requires nvidia-docker):
#   docker build --build-arg CMAKE_ARGS="-DLLAMA_CUDA=on" -t rarellm:cuda .
#   docker run --gpus all -v /path/to/models:/app/models rarellm:cuda
#
# =============================================================================
