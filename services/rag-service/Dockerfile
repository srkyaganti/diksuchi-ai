# Stage 1: Builder - Install dependencies
FROM python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - Final minimal image
FROM python:3.11-slim

LABEL maintainer="diksuchi-rag-service"
LABEL description="RAG Document Processing and Retrieval API"
LABEL version="1.0.0"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

RUN useradd -m -u 1000 -s /bin/bash appuser

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --chown=appuser:appuser main.py .
COPY --chown=appuser:appuser worker.py .
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser src ./src

USER appuser

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/health || exit 1

CMD ["python", "main.py"]
