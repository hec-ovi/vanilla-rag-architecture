# =============================================================================
# Backend - FastAPI Application
# =============================================================================
# Python 3.12 + UV + FastAPI optimized for production
# Uses multi-stage build for smaller image size
# =============================================================================

FROM ubuntu:rolling AS builder

ENV DEBIAN_FRONTEND=noninteractive
ENV UV_CACHE_DIR=/root/.cache/uv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

RUN uv venv .venv --python 3.12

COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt

# =============================================================================
# Production Stage
# =============================================================================

FROM ubuntu:rolling AS production

ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libgomp1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv

WORKDIR /app

COPY src/ ./src/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
