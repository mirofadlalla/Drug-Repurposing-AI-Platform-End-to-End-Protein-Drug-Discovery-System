# =============================================================================
# Dockerfile — Drug Repurposing AI Service
# =============================================================================
#
# Dependency resolution strategy:
#   DeepPurpose → moleculeace → PyTDC >= 1.1.0 → scikit-learn == 1.2.2 (exact)
#
#   To avoid pip's conflict resolver and network timeouts:
#     1. Install PyTorch CPU-only wheel first (large, separate layer → cache hit)
#     2. Pre-install scikit-learn==1.2.2 in its own layer BEFORE requirements.txt
#     3. Install git-based deps (descriptastorus) separately with extended timeout
#     4. Install remaining requirements with --default-timeout=1000 to prevent
#        SSL read timeouts on large packages like PyTorch, RDKit, etc.
# =============================================================================

FROM python:3.10-slim

# ── OS-level C/C++ dependencies for RDKit, BioPython, and scipy ──────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxrender1 \
    libxext6 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security best practice
RUN useradd --create-home appuser
WORKDIR /app

# ── Layer 1: PyTorch CPU-only (heaviest download — cached separately) ─────────
RUN pip install --no-cache-dir \
    torch==2.2.2 \
    --index-url https://download.pytorch.org/whl/cpu

# ── Layer 2: scikit-learn pinned BEFORE the main install ─────────────────────
# PyTDC >= 1.1.0 requires scikit-learn==1.2.2 exactly.
# Pre-installing it here prevents pip's resolver from treating it as a conflict.
RUN pip install --no-cache-dir "scikit-learn==1.2.2"

# ── Layer 3: Git-based dependencies (descriptastorus) ─────────────────────────
# Install separately first to avoid timeout on large chains
RUN pip install --no-cache-dir --default-timeout=1000 \
    "descriptastorus@ git+https://github.com/bp-kelley/descriptastorus"

# ── Layer 4: remaining Python dependencies ────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# ── Layer 4: application source code ─────────────────────────────────────────
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

# Health-check so Docker (and Compose) know when the container is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=5 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Production-grade Uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]